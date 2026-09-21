import logging
from collections.abc import AsyncGenerator
from datetime import date, datetime, timezone
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import EventSourceResponse
from fastapi.sse import ServerSentEvent
from sqlalchemy import case, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.llm import openai_client
from app.db.database import get_db
from app.deps import get_current_user
from app.models import AiInteraction, ChatMessage, User, UserProfile
from app.prompts.registry import active_version, get_prompt
from app.schemas import ChatMessageCreate, ChatMessageOut, ChatMessageRating
from app.services.rag_pipeline import format_context, retrieve
from app.services.nutrition import daily_intake
from app.services.tracing import ms_since, record_interaction, summarize_chunks
from app.services.training_week import build_today

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Within one exchange a question comes before its answer, whatever the clock says. The
# two can be written in the same microsecond - a stubbed or cached model answers that
# fast - and equal timestamps leave the order to the database, which showed answers
# above the questions that caused them.
_QUESTION_FIRST = case((ChatMessage.role == "user", 0), else_=1)

# Warm enough for coaching language, cool enough to keep the numbers it is given.
CHAT_TEMPERATURE = 0.4

# Shown instead of the answer when generation breaks. The stream is already open by
# then, so there is no status code left to carry a message - the client only ever sees
# this sentence.
GENERATION_FAILED = "Треньорът не успя да отговори. Опитай пак след малко."


@router.post("", response_class=EventSourceResponse)
async def chat(
    data: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[ServerSentEvent, None]:
    """Answer one question, a token at a time.

    Retrieval plus generation is 3-6 seconds; delivered in one piece that is 3-6 seconds
    of a blank screen. The answer is streamed so reading can start on the first sentence,
    and the turn is only written down once it is whole: a truncated coaching answer saved
    as if it were complete is worse than no answer at all.
    """
    started = perf_counter()
    # The question was asked now; the answer is saved seconds later, once the model has
    # replied. Stamping both at save time gave a pair one identical timestamp, and the
    # history then ordered them arbitrarily - answers showed above their own questions.
    asked_at = datetime.now(timezone.utc)
    r = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc(), _QUESTION_FIRST.desc())
        .limit(10)
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(r.scalars().all())]

    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = pr.scalar_one_or_none()

    profile_ctx = ""
    if profile:
        calc = profile.calculator_results or {}
        e = calc.get("energy", {})
        levels = ["Начинаещ", "Средно напреднал", "Напреднал"]
        lvl = levels[profile.training_status - 1] if profile.training_status in (1, 2, 3) else "—"
        profile_ctx = get_prompt("chat_profile_block")(lvl, profile.goal_validated or profile.goal, e)

    # What the program says about today, as facts rather than as something to reason
    # about: asked what to train, the coach used to answer from the course material and
    # invent a session that was not the user's.
    today = await build_today(db, user.id, date.today())
    today_ctx = ""
    if today:
        today_ctx = get_prompt("chat_today_block")(
            day_name=today.day_name,
            is_rest_day=today.is_rest_day,
            trained_today=today.trained_today,
            week_number=today.week_number,
            total_weeks=today.total_weeks,
            exercises=[
                {
                    "name": e.exercise_name,
                    "sets": e.sets_prescribed,
                    "reps_min": e.reps_min,
                    "reps_max": e.reps_max,
                    "rir": e.rir_target,
                    "target_weight_kg": e.target_weight_kg,
                    "note": e.target_note,
                }
                for e in today.exercises
            ],
        )

    intake = await daily_intake(db, user.id, date.today())
    nutrition_ctx = get_prompt("chat_nutrition_block")(
        totals=intake.totals,
        targets=intake.targets,
        remaining=intake.remaining,
        has_targets=intake.has_targets,
    )

    # The history goes to retrieval too, not just to the model: on its own a follow-up
    # like "а за жени?" retrieves noise, because the subject lives in the previous turn.
    retrieval_started = perf_counter()
    retrieval = await retrieve(data.content, history=history)
    retrieval_ms = ms_since(retrieval_started)
    context = format_context(retrieval.chunks)

    system = get_prompt("chat_system")(
        settings.RESPONSE_LANGUAGE, "\n".join(part for part in (profile_ctx, today_ctx) if part), context
    )

    messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": data.content}]

    def trace(**outcome) -> AiInteraction:
        """Everything known about this answer before it was generated; the call site adds
        how it ended."""
        return AiInteraction(
            user_id=user.id,
            surface="chat",
            query=data.content,
            resolved_query=retrieval.resolved_query,
            retrieved=summarize_chunks(retrieval.chunks),
            prompt_name="chat_system",
            prompt_version=active_version("chat_system"),
            model=settings.PRIMARY_MODEL,
            temperature=CHAT_TEMPERATURE,
            retrieval_ms=retrieval_ms,
            total_ms=ms_since(started),
            **outcome,
        )

    generation_started = perf_counter()
    pieces: list[str] = []
    # A streamed response carries no usage by default, and the trace is worth little
    # without it: cost per answer is the number that decides whether a model stays.
    usage = None
    try:
        stream = await openai_client.chat.completions.create(
            model=settings.PRIMARY_MODEL,
            messages=messages,
            temperature=CHAT_TEMPERATURE,
            max_tokens=1000,
            stream=True,
            stream_options={"include_usage": True},
        )
        async for chunk in stream:
            # The usage chunk arrives last and carries no choices; a content chunk
            # carries no usage. Neither may be read as if it were the other.
            if chunk.usage is not None:
                usage = chunk.usage
            if not chunk.choices:
                continue
            piece = chunk.choices[0].delta.content
            if piece:
                pieces.append(piece)
                yield ServerSentEvent(event="delta", data={"text": piece})
    except Exception as exc:
        # The calls worth investigating are the ones that failed, so the trace is written
        # before the failure is reported.
        await record_interaction(db, trace(error=str(exc), generation_ms=ms_since(generation_started)))
        logger.warning("Chat generation failed for user %s", user.id, exc_info=True)
        yield ServerSentEvent(event="error", data={"detail": GENERATION_FAILED})
        return
    generation_ms = ms_since(generation_started)
    answer = "".join(pieces)

    if not answer.strip():
        # The call succeeded and said nothing. Storing that as an answer would leave an
        # empty coach bubble in the history with no way to tell it from a lost message.
        await record_interaction(db, trace(
            error="the model returned an empty answer",
            generation_ms=generation_ms,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        ))
        yield ServerSentEvent(event="error", data={"detail": GENERATION_FAILED})
        return

    db.add(ChatMessage(user_id=user.id, role="user", content=data.content, created_at=asked_at))
    # Stamped from the same clock as the question, and explicitly: the column stores a
    # timezone, while the model's default fills it with a naive value, and mixing the two
    # in one exchange puts the answer hours away from its own question.
    assistant_msg = ChatMessage(
        user_id=user.id, role="assistant", content=answer, created_at=datetime.now(timezone.utc)
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    await record_interaction(db, trace(
        message_id=assistant_msg.id,
        generation_ms=generation_ms,
        input_tokens=getattr(usage, "prompt_tokens", None),
        output_tokens=getattr(usage, "completion_tokens", None),
    ))

    # Closes the turn: the client swaps the text it streamed for the stored message, and
    # the id is what lets the answer be rated afterwards.
    yield ServerSentEvent(event="done", data={"message_id": assistant_msg.id})


@router.get("/history", response_model=list[ChatMessageOut])
async def get_history(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc(), _QUESTION_FIRST.desc())
        .limit(limit)
    )
    return list(reversed(r.scalars().all()))


@router.post("/messages/{message_id}/rating", status_code=204)
async def rate_message(
    message_id: str,
    data: ChatMessageRating,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record what the user thought of one answer.

    This is the only judgement of answer quality that comes from the person the answer was
    written for. Joined with the trace behind the message it says which retrieval and which
    prompt version produced a reply worth keeping - and a rejected answer is a candidate
    for the evaluation set, where questions otherwise have to be invented.

    Re-rating replaces the previous verdict; people change their minds after reading again.
    """
    r = await db.execute(
        select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.user_id == user.id)
    )
    message = r.scalar_one_or_none()
    if message is None:
        raise HTTPException(404, "Съобщението не е намерено.")
    if message.role != "assistant":
        raise HTTPException(400, "Оценява се отговорът на треньора, не собственият ти въпрос.")

    message.rating = data.rating
    message.rating_comment = (data.comment or "").strip() or None
    message.rated_at = datetime.now(timezone.utc)
    await db.commit()


@router.delete("/history", status_code=204)
async def clear_history(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Erase the conversation, and what was recorded about it.

    The user is told the history is deleted, and a trace holds their question verbatim,
    so it cannot stay behind. Traces of answered turns would follow their message through
    the foreign key anyway; the ones left by a failed generation have no message to
    follow and are removed here.
    """
    await db.execute(
        delete(AiInteraction).where(
            AiInteraction.user_id == user.id, AiInteraction.surface == "chat"
        )
    )
    await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user.id))
    await db.commit()
