import json
import logging

import faiss
import numpy as np
from fastapi import APIRouter, Depends
from openai import AsyncOpenAI, OpenAI
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.database import get_db
from deps import get_current_user
from models import ChatMessage, User, UserProfile
from prompts.registry import get_prompt
from schemas import ChatMessageCreate, ChatMessageOut, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def _load_index():
    try:
        index = faiss.read_index(str(settings.faiss_index_path))
        meta = json.loads(settings.faiss_metadata_path.read_text(encoding="utf-8"))
        return index, meta
    except Exception:
        logger.warning("FAISS index/metadata could not be loaded from %s; chat will run without RAG context",
                       settings.faiss_index_path, exc_info=True)
        return None, []


index, meta = _load_index()


async def retrieve_context(question: str, k: int | None = None) -> str:
    if index is None or not meta:
        return ""
    try:
        top_k = k if k is not None else settings.RETRIEVAL_TOP_K
        sync_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        emb = np.array(
            sync_client.embeddings.create(model=settings.EMBEDDING_MODEL, input=[question]).data[0].embedding,
            dtype="float32",
        ).reshape(1, -1)
        faiss.normalize_L2(emb)
        k_eff = min(top_k, max(1, len(meta) if isinstance(meta, list) else 1))
        _, ids = index.search(emb, k_eff)
        if isinstance(meta, list):
            return "\n\n".join(meta[i]["text"] for i in ids[0] if i != -1 and i < len(meta))
        return ""
    except Exception:
        logger.warning("RAG retrieval failed for question; answering without course context", exc_info=True)
        return ""


@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(10)
    )
    history = list(reversed(r.scalars().all()))

    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = pr.scalar_one_or_none()

    profile_ctx = ""
    if profile:
        calc = profile.calculator_results or {}
        e = calc.get("energy", {})
        levels = ["Начинаещ", "Средно напреднал", "Напреднал"]
        lvl = levels[profile.training_status - 1] if profile.training_status in (1, 2, 3) else "—"
        profile_ctx = get_prompt("chat_profile_block")(lvl, profile.goal_validated or profile.goal, e)

    context = await retrieve_context(data.content)

    system = get_prompt("chat_system")(settings.RESPONSE_LANGUAGE, profile_ctx, context)

    messages = [{"role": "system", "content": system}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": data.content})

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
