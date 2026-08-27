"""Offline RAG evaluation against the golden dataset.

Runs the real retrieval pipeline (app.services.rag_pipeline) over evaluation/
golden_dataset.json and scores it two ways.

Retrieval is scored deterministically against each question's expected_sources -
hit rate and MRR, no judge, seconds per run - so a change to chunking, rewriting or
ranking can be measured cheaply and often. Answer quality is scored by an LLM judge on
four RAGAS-style metrics (faithfulness, answer relevancy, context precision, context
recall) using the same chat prompt the app ships, so the numbers describe the product.

Usage (from backend/):
    python -m evaluation.offline_eval --retrieval-only   # fast, no judge
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
from datetime import datetime
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.llm import openai_client
from app.prompts.registry import active_version, get_prompt
from app.services.rag_pipeline import retrieve

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN = EVAL_DIR / "golden_dataset.json"
RESULTS_DIR = EVAL_DIR / "results"


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
    """Answer with the prompt the chat endpoint ships.

    The eval used to carry its own system prompt, so faithfulness described a system no
    user ever talked to. There is no profile block here - the golden questions are not
    tied to a user.
    """
    context = "\n\n".join(f"[Източник: {c.source}]\n{c.text}" for c in chunks)
    system = get_prompt("chat_system")(settings.RESPONSE_LANGUAGE, "", context)
    resp = await openai_client.chat.completions.create(
        model=settings.PRIMARY_MODEL,
        messages=[
            {"role": "system", "content": system},
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
    # Judge the passage that was actually sent to the model. Truncating here made the
    # judge rate a fused span on its opening lines and call the rest irrelevant.
    chunks_txt = "\n".join(f"Chunk {i+1}: {c}" for i, c in enumerate(contexts))
    d = await _judge(f"""Evaluate the relevance of each retrieved chunk to the question.

Question: {question}

Retrieved chunks:
{chunks_txt}

For each chunk rate 1 (relevant) or 0 (not).
Return JSON: {{"chunk_scores": [1, 0, ...], "score": float (mean)}}. Reply ONLY with valid JSON.""", 200)
    scores = d.get("chunk_scores", [])
    return float(np.mean(scores)) if scores else 0.0


async def score_context_recall(question: str, ground_truth: str, contexts: list[str]) -> float:
    # No cap: a claim that sits past the cut-off is not missing from the context, it is
    # missing from what the judge was shown - which is how recall got underreported as
    # passages grew longer.
    ctx = "\n---\n".join(contexts)
    d = await _judge(f"""You are evaluating a RAG retrieval system.

Question: {question}
Ground truth answer (reference): {ground_truth}
Retrieved context: {ctx}

Identify the KEY FACTUAL CLAIMS in the ground truth. For each, is its SEMANTIC MEANING
present in the retrieved context? Paraphrases count; vague matches do not.

Return JSON: {{"key_claims": [...], "claims_found": [...], "claims_missing": [...], "score": 0.0-1.0}}
Reply ONLY with valid JSON.""")
    return float(d.get("score", 0.0))


def score_retrieval(expected_sources: list[str], sources: list[str]) -> tuple[float, float]:
    """Did retrieval reach a document that contains the answer, and how high up?

    Deterministic, so a retrieval change can be judged in seconds and for the price of
    the embeddings, instead of 30 questions x 5 judge calls. Returns (hit, reciprocal
    rank of the first expected source).
    """
    if not expected_sources:
        return 0.0, 0.0
    for rank, source in enumerate(sources, 1):
        if source in expected_sources:
            return 1.0, 1.0 / rank
    return 0.0, 0.0


async def evaluate(top_n: int | None = None, judge: bool = True) -> dict:
    top_n = top_n or settings.RERANKING_TOP_N
    questions = json.loads(GOLDEN.read_text(encoding="utf-8"))["questions"]
    results = []
    print(f"Evaluating {len(questions)} questions (top_n={top_n}, "
          f"rerank={settings.RERANK_ENABLED}, rewrite={settings.QUERY_REWRITE_ENABLED}, "
          f"judge={judge})...", flush=True)

    for i, q in enumerate(questions, 1):
        chunks = await retrieve(q["question"], top_n=top_n)
        contexts = [c.text for c in chunks]
        sources = [c.source for c in chunks]
        row = {**q, "contexts": contexts, "sources": sources}
        row["source_hit"], row["source_mrr"] = score_retrieval(q.get("expected_sources", []), sources)
        if not judge:
            row["judge_error"] = None
            print(f'  [{i:02d}/{len(questions)}] {q["id"]} | hit={row["source_hit"]:.0f} '
                  f'mrr={row["source_mrr"]:.2f} | {", ".join(sources[:2])}', flush=True)
            results.append(row)
            continue
        answer = await generate_answer(q["question"], chunks)
        row["answer"] = answer
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
        await asyncio.sleep(0.3)

    # Retrieval metrics stand on their own: they never depend on the judge, so they are
    # averaged over every question, judged or not.
    summary = {
        "source_hit_rate": round(float(np.mean([r["source_hit"] for r in results])), 4),
        "source_mrr": round(float(np.mean([r["source_mrr"] for r in results])), 4),
    }
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "ragas_score"]
    scored = [r for r in results if r.get("judge_error") is None and r.get("ragas_score") is not None]
    if scored:
        summary.update({m: round(float(np.mean([r[m] for r in scored])), 4) for m in metrics})
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
            "chat_prompt_version": active_version("chat_system"),
            "retrieval_min_score": settings.RETRIEVAL_MIN_SCORE,
            "rerank_enabled": settings.RERANK_ENABLED,
            "reranker_model": settings.RERANKER_MODEL if settings.RERANK_ENABLED else None,
            "query_rewrite_enabled": settings.QUERY_REWRITE_ENABLED,
            "candidates": settings.RETRIEVAL_CANDIDATES,
            "top_n": top_n,
        },
        "judged": judge,
        "scored_questions": len(scored),
        "judge_errors": [r["id"] for r in results if r.get("judge_error")],
        # Named, not just counted: a hit rate that drops should say which questions lost
        # their document.
        "source_misses": [r["id"] for r in results if not r["source_hit"]],
        "summary": summary,
        "by_category": by_cat,
        "questions": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Offline RAG evaluation")
    ap.add_argument("--label", default="run", help="name for the result file")
    ap.add_argument("--top-n", type=int, default=settings.RERANKING_TOP_N,
                    help="passages per question (default: the value production retrieves with)")
    ap.add_argument("--retrieval-only", action="store_true",
                    help="score retrieval against expected_sources and skip the LLM judge")
    ap.add_argument("--compare", help="label of a previous run in results/ to diff against")
    args = ap.parse_args()

    report = asyncio.run(evaluate(top_n=args.top_n, judge=not args.retrieval_only))
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{args.label}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    scope = f"{report['scored_questions']} scored" if report["judged"] else "retrieval only"
    print(f"\n==== {args.label} ({scope}"
          f"{', %d judge errors' % len(report['judge_errors']) if report['judge_errors'] else ''}) ====")
    baseline = None
    if args.compare:
        p = RESULTS_DIR / f"{args.compare}.json"
        if p.exists():
            previous = json.loads(p.read_text(encoding="utf-8"))
            baseline = previous["summary"]
            # Two runs are only comparable when the retrieval change is the single
            # variable. Runs made before a config was recorded cannot prove that.
            differences = [
                k for k, v in report["config"].items() if (previous.get("config") or {}).get(k) != v
            ]
            if previous.get("config") is None:
                print(f"(warning: '{args.compare}' recorded no config; the diff below may "
                      f"reflect a different prompt or model, not this run's change)")
            elif differences:
                print(f"(warning: '{args.compare}' differs in {', '.join(differences)})")
        else:
            print(f"(no baseline '{args.compare}' in results/)")
    for m, v in report["summary"].items():
        if baseline and m in baseline:
            print(f"  {m:20} {baseline[m]:.4f} -> {v:.4f}  ({v - baseline[m]:+.4f})")
        else:
            print(f"  {m:20} {v:.4f}")
    if report["source_misses"]:
        print(f"  no expected document retrieved for: {', '.join(report['source_misses'])}")
    print("saved:", out)


if __name__ == "__main__":
    main()
