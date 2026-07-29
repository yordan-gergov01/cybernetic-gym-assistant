# Architecture

Personal AI fitness coach built on the Menno Henselmans PT Certification methodology.
Phone-first (React PWA planned), FastAPI backend, PostgreSQL, OpenAI + FAISS for RAG.

## Layout

```
backend/
├── app/                        # the installable application package
│   ├── main.py                 # FastAPI app, CORS, logging
│   ├── router.py               # mounts every route module under /api/v1
│   ├── deps.py                 # shared FastAPI dependencies (current user)
│   ├── models.py               # SQLAlchemy ORM models (15 tables)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── core/                   # config, security (JWT/bcrypt), shared LLM client
│   ├── db/                     # async engine + session factory
│   ├── domain/                 # deterministic sport science (calculators)
│   ├── components/             # retrieval building blocks (retriever, reranker)
│   ├── services/               # business logic & orchestration
│   ├── prompts/                # versioned prompt templates + registry
│   └── routes/                 # HTTP layer only — no business logic
├── evaluation/                 # golden dataset + offline RAG eval + tracked results
├── migrations/                 # Alembic
├── scripts/                    # healthcheck and other operational entry points
├── tests/                      # unit tests for the deterministic engines
├── notebooks/                  # prototypes (data pipeline, embeddings, agents)
├── data/                       # extracted course material + FAISS index (git-ignored)
└── pyproject.toml              # package + pytest + ruff config
frontend/                       # React PWA (planned)
docs/
```

## Layer rules

**routes → services → components/domain.** Dependencies point one way; a component
never imports a service, a service never imports a route.

- **`domain/`** — pure sport-science functions (energy intake, 1RM, optimal volume,
  goal validation). No I/O, no LLM. These numbers are the source of truth.
- **`components/`** — single-responsibility infrastructure pieces. `retriever` owns
  the FAISS index/embeddings/metadata filtering; `reranker` owns the optional
  cross-encoder. Neither knows about prompts or business flows.
- **`services/`** — orchestration and coaching logic: `rag_pipeline` sequences
  rewrite → dual retrieval → rerank; `fatigue`, `progression`, `weight_trend` are the
  deterministic coaching engines; `storage` wraps Cloudflare R2.
- **`prompts/`** — every LLM prompt, versioned (`*_v1`, `*_v2`) behind a registry, so
  prompt changes are reviewable and reversible without touching business code.
- **`routes/`** — parse the request, call a service, shape the response.

## Deterministic first

Anything a formula can answer is answered by code, never by the model
(see [CLAUDE.md](../CLAUDE.md) rule #5):

| Decision | Where | Model's role |
|---|---|---|
| Calories, macros, TDEE, 1RM, weekly volume | `domain/calculators.py` | explains the numbers |
| Deload vs continue | `services/fatigue.py` | phrases the reasoning in Bulgarian |
| Next-session weight/reps | `services/progression.py` | none |
| Weight trend + calorie adjustment | `services/weight_trend.py` | none |
| Coaching answers, program design, food parsing | LLM, grounded in RAG | judgment calls |

## RAG pipeline

```
question (BG)
  → query_rewriter        BG → short EN search query
  → retriever             FAISS search on both queries, merged by chunk_id, metadata-filtered
  → reranker (optional)   cross-encoder; off by default (needs ~2.3 GB RAM)
  → top-N chunks          formatted with [Източник: file.pdf] tags for citation
```

Measured on the 30-question golden set (`evaluation/`): adding BG→EN query rewriting
lifted context recall 0.47 → 0.56 and faithfulness 0.82 → 0.86.

Every stage degrades loudly: a missing index, failed embedding or unavailable
reranker logs a warning and falls back instead of failing the request.

## Data flow

1. Course PDFs/Excel/DOCX → extracted (`notebooks/`) → chunked with metadata
   (topic, level, goal, case-study flags) → embedded → FAISS index in `data/vectorstore/`.
2. User profile → `domain/calculators.py` → macros + volume targets stored on the profile.
3. Daily logs (weight, food, workouts) → deterministic engines → coaching output.
4. Photos → Cloudflare R2; the database stores only the object key.

## Operational

```bash
python -m alembic upgrade head        # schema
python -m scripts.healthcheck         # verify DB, vectorstore, reranker, R2
python -m pytest                      # unit tests
python -m evaluation.offline_eval --label my_run --compare query_rewrite
python -m uvicorn app.main:app --reload
```
