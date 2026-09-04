"""What users thought of the coach's answers, next to how those answers were built.

Usage (from backend/):
    python -m scripts.review_feedback # every rated answer, newest first
    python -m scripts.review_feedback --down # only the rejected ones
    python -m scripts.review_feedback --limit 50

A rating on its own says an answer was bad. Read beside its trace it says why: which
query retrieval actually ran, which documents came back, how long it took. Rejected
answers are also where the evaluation set should grow from - a question a real user
asked and did not get answered is worth more than one invented at a desk.
"""
from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models import AiInteraction, ChatMessage

VERDICT = {1: "+1", -1: "-1"}


async def review(only_down: bool, limit: int) -> int:
    async with AsyncSessionLocal() as db:
        query = (
            select(ChatMessage, AiInteraction)
            .outerjoin(AiInteraction, AiInteraction.message_id == ChatMessage.id)
            .where(ChatMessage.rating.is_not(None))
            .order_by(ChatMessage.rated_at.desc())
            .limit(limit)
        )
        if only_down:
            query = query.where(ChatMessage.rating < 0)
        rows = (await db.execute(query)).all()
        rated = (await db.execute(
            select(ChatMessage).where(ChatMessage.rating.is_not(None))
        )).scalars().all()

    if not rows:
        print("No rated answers yet.")
        return 0

    for message, trace in rows:
        print()
        print(f"=== {VERDICT.get(message.rating, message.rating)} "
              f"{message.rated_at:%Y-%m-%d %H:%M} ===")
        if message.rating_comment:
            print(f"  said      : {message.rating_comment}")
        if trace is None:
            # Answers logged before tracing existed, and any trace that failed to write.
            # Saying so beats printing blanks that look like retrieval returning nothing.
            print("  (no trace recorded for this answer)")
        else:
            print(f"  asked: {trace.query}")
            print(f"  searched: {trace.resolved_query or '(not rewritten)'}")
            for passage in trace.retrieved or []:
                ordinals = "+".join(str(c).rsplit("__", 1)[-1] for c in passage["chunk_ids"])
                print(f"    {passage['score']:.3f}  {passage['source']}  {ordinals}")
            print(f"  spent: {trace.retrieval_ms} ms retrieval, {trace.generation_ms} ms "
                  f"generation, {trace.input_tokens} in / {trace.output_tokens} out tokens")
            print(f"  prompt: {trace.prompt_name} {trace.prompt_version}")
        print(f"  answered: {message.content[:200].strip()}")

    rejected = sum(1 for m in rated if m.rating < 0)
    print()
    print(f"{len(rated)} rated answers, {rejected} rejected "
          f"({rejected / len(rated):.0%}); showing {len(rows)}.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Read user feedback next to the traces behind it")
    ap.add_argument("--down", action="store_true", help="only answers the user rejected")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    raise SystemExit(asyncio.run(review(args.down, args.limit)))


if __name__ == "__main__":
    main()
