"""Offline RAG evaluation against the golden dataset.

Runs the real retrieval pipeline (app.services.rag_pipeline) over evaluation/
golden_dataset.json, generates an answer per question, and scores four RAGAS-style
metrics with an LLM judge: faithfulness, answer relevancy, context precision and
context recall.

Usage (from backend/):
    python -m evaluation.offline_eval                    # writes evaluation/results/<label>.json
    python -m evaluation.offline_eval --label rerank_on  # name the run
    python -m evaluation.offline_eval --compare query_rewrite

Results are written to evaluation/results/ so runs can be compared over time; keep
the retrieval change as the only variable when comparing two runs.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.llm import openai_client
from app.services.rag_pipeline import retrieve

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN = EVAL_DIR / "golden_dataset.json"
RESULTS_DIR = EVAL_DIR / "results"

ANSWER_SYSTEM_PROMPT = """Ти си персонален фитнес треньор и нутриционист. Работиш изцяло по научно-обоснованата методология на Menno Henselmans.

ПРАВИЛА - следвай ги стриктно:
1. Отговаряй ВИНАГИ на БЪЛГАРСКИ
2. Ползвай КИЛОГРАМИ и метри, никога pounds или inches
3. Бъди ДИРЕКТЕН и ПРАКТИЧЕН - давай конкретни числа и препоръки
4. НЕ изнасяй лекции и НЕ цитирай проучвания, ако не са поискани
5. Говори като треньор, не като учебник - просто, ясно, приложимо
6. Ако нещо не е покрито в контекста, кажи го честно
7. Адаптирай отговора спрямо нивото и целта на потребителя
8. Посочвай винаги имената на упражненията единствено и САМО на английски език
9. Задължително базирай всичките си отговори САМО на ресурсите от курса

Контекст от курса на Henselmans (използвай САМО тази информация за факти):
{context}"""


async def _judge(prompt: str, max_tokens: int = 500) -> dict:
    resp = await openai_client.chat.completions.create(
        model=settings.PRIMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return json.loads(resp.choices[0].message.content)


async def generate_answer(question: str, chunks) -> str:
    context = "\n\n".join(f"[{c.source}]\n{c.text}" for c in chunks)
    resp = await openai_client.chat.completions.create(
        model=settings.PRIMARY_MODEL,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT.format(context=context)},
            {"role": "user", "content": question},
        ],
        temperature=0.4,
        max_tokens=1200,
    )
    return resp.choices[0].message.content


async def score_faithfulness(question: str, answer: str, contexts: list[str]) -> float:
    d = await _judge(f"""You are evaluating a RAG system.

Question: {question}

Retrieved context:
{chr(10).join(contexts)}

Generated answer:
{answer}

TASK: Identify each factual claim in the answer. For each claim, determine if it is
directly supported by the retrieved context above (not general knowledge).

Return JSON with "supported_claims", "unsupported_claims" and "score" (float 0.0-1.0,
supported / total claims). Reply ONLY with valid JSON.""")
    return float(d.get("score", 0.0))


async def score_answer_relevancy(question: str, answer: str) -> float:
    d = await _judge(f"""Evaluate how relevant this answer is to the question.

Question: {question}
Answer: {answer}

Score 0.0-1.0 (1.0 fully addresses, 0.5 partially, 0.0 not at all).
Return JSON: {{"score": float, "reason": "brief"}}. Reply ONLY with valid JSON.""", 200)
    return float(d.get("score", 0.0))


async def score_context_precision(question: str, contexts: list[str]) -> float:
    chunks_txt = "\n".join(f"Chunk {i+1}: {c[:300]}" for i, c in enumerate(contexts))
    d = await _judge(f"""Evaluate the relevance of each retrieved chunk to the question.

Question: {question}

Retrieved chunks:
{chunks_txt}

For each chunk rate 1 (relevant) or 0 (not).
Return JSON: {{"chunk_scores": [1, 0, ...], "score": float (mean)}}. Reply ONLY with valid JSON.""", 200)
    scores = d.get("chunk_scores", [])
    return float(np.mean(scores)) if scores else 0.0


async def score_context_recall(question: str, ground_truth: str, contexts: list[str]) -> float:
    ctx = "\n---\n".join(contexts)[:2000]
    d = await _judge(f"""You are evaluating a RAG retrieval system.

Question: {question}
Ground truth answer (reference): {ground_truth}
Retrieved context: {ctx}

Identify the KEY FACTUAL CLAIMS in the ground truth. For each, is its SEMANTIC MEANING
present in the retrieved context? Paraphrases count; vague matches do not.

Return JSON: {{"key_claims": [...], "claims_found": [...], "claims_missing": [...], "score": 0.0-1.0}}
Reply ONLY with valid JSON.""")
    return float(d.get("score", 0.0))


async def evaluate(top_n: int = 5) -> dict:
    questions = json.loads(GOLDEN.read_text(encoding="utf-8"))["questions"]
    results = []
    print(f"Evaluating {len(questions)} questions (top_n={top_n}, "
          f"rerank={settings.RERANK_ENABLED}, rewrite={settings.QUERY_REWRITE_ENABLED})...", flush=True)

    for i, q in enumerate(questions, 1):
        chunks = await retrieve(q["question"], top_n=top_n)
        contexts = [c.text for c in chunks]
        answer = await generate_answer(q["question"], chunks)
        row = {**q, "answer": answer, "contexts": contexts, "sources": [c.source for c in chunks]}
        try:
            row["faithfulness"] = await score_faithfulness(q["question"], answer, contexts)
            row["answer_relevancy"] = await score_answer_relevancy(q["question"], answer)
            row["context_precision"] = await score_context_precision(q["question"], contexts)
            row["context_recall"] = await score_context_recall(q["question"], q["ground_truth"], contexts)
            row["ragas_score"] = float(np.mean([row["faithfulness"], row["answer_relevancy"],
                                                row["context_precision"], row["context_recall"]]))
            row["judge_error"] = None
            print(f'  [{i:02d}/{len(questions)}] {q["id"]} | F={row["faithfulness"]:.2f} '
                  f'AR={row["answer_relevancy"]:.2f} CP={row["context_precision"]:.2f} '
                  f'CR={row["context_recall"]:.2f} -> {row["ragas_score"]:.2f}', flush=True)
        except Exception as e:
            # Judge failures are eval noise, not product failures — record them instead of
            # silently scoring 0, which would skew the summary (CLAUDE.md rule #12).
            for k in ("faithfulness", "answer_relevancy", "context_precision", "context_recall", "ragas_score"):
                row[k] = None
            row["judge_error"] = str(e)
            print(f'  [{i:02d}/{len(questions)}] {q["id"]} JUDGE ERROR: {e}', flush=True)
        results.append(row)
        time.sleep(0.3)

    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "ragas_score"]
    scored = [r for r in results if r["judge_error"] is None]
    summary = {m: round(float(np.mean([r[m] for r in scored])), 4) for m in metrics} if scored else {}
    cats = sorted({q["category"] for q in questions})
    by_cat = {
        c: round(float(np.mean([r["ragas_score"] for r in scored if r["category"] == c])), 4)
        for c in cats if any(r["category"] == c for r in scored)
    }
    return {
        "generated_at": datetime.now().isoformat(),
        "config": {
            "llm": settings.PRIMARY_MODEL,
            "embedding": settings.EMBEDDING_MODEL,
            "rerank_enabled": settings.RERANK_ENABLED,
            "reranker_model": settings.RERANKER_MODEL if settings.RERANK_ENABLED else None,
            "query_rewrite_enabled": settings.QUERY_REWRITE_ENABLED,
            "candidates": settings.RETRIEVAL_CANDIDATES,
            "top_n": top_n,
        },
        "scored_questions": len(scored),
        "judge_errors": [r["id"] for r in results if r["judge_error"]],
        "summary": summary,
        "by_category": by_cat,
        "questions": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Offline RAG evaluation")
    ap.add_argument("--label", default="run", help="name for the result file")
    ap.add_argument("--top-n", type=int, default=5)
    ap.add_argument("--compare", help="label of a previous run in results/ to diff against")
    args = ap.parse_args()

    report = asyncio.run(evaluate(top_n=args.top_n))
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{args.label}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n==== {args.label} ({report['scored_questions']} scored"
          f"{', %d judge errors' % len(report['judge_errors']) if report['judge_errors'] else ''}) ====")
    baseline = None
    if args.compare:
        p = RESULTS_DIR / f"{args.compare}.json"
        if p.exists():
            baseline = json.loads(p.read_text(encoding="utf-8"))["summary"]
        else:
            print(f"(no baseline '{args.compare}' in results/)")
    for m, v in report["summary"].items():
        if baseline and m in baseline:
            print(f"  {m:20} {baseline[m]:.4f} -> {v:.4f}  ({v - baseline[m]:+.4f})")
        else:
            print(f"  {m:20} {v:.4f}")
    print("saved:", out)


if __name__ == "__main__":
    main()
