from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.llm import openai_client
from app.db.database import get_db
from app.deps import get_current_user
from app.models import ChatMessage, User, UserProfile
from app.prompts.registry import get_prompt
from app.schemas import ChatMessageCreate, ChatMessageOut, ChatResponse
from app.services.rag_pipeline import retrieve_context

router = APIRouter(prefix="/chat", tags=["chat"])



@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(10)
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

    # The history goes to retrieval too, not just to the model: on its own a follow-up
    # like "а за жени?" retrieves noise, because the subject lives in the previous turn.
    context = await retrieve_context(data.content, history=history)

    system = get_prompt("chat_system")(settings.RESPONSE_LANGUAGE, profile_ctx, context)

    messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": data.content}]

    resp = await openai_client.chat.completions.create(
        model=settings.PRIMARY_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=1000,
    )
    answer = resp.choices[0].message.content

    db.add(ChatMessage(user_id=user.id, role="user", content=data.content))
    assistant_msg = ChatMessage(user_id=user.id, role="assistant", content=answer)
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(answer=answer, message_id=assistant_msg.id)


@router.get("/history", response_model=list[ChatMessageOut])
async def get_history(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(limit)
    )
    return list(reversed(r.scalars().all()))


@router.delete("/history", status_code=204)
async def clear_history(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user.id))
    await db.commit()
