# Code style

Conventions for `backend/app/`. These describe what the codebase already does — match
it rather than introducing a parallel style (CLAUDE.md rule #11).

## Imports
- Absolute imports from the package root: `from app.services.rag_pipeline import retrieve`.
  Never relative imports, never `sys.path` manipulation — the package is installable.
- Order: stdlib, third-party, `app.*` (ruff enforces with `I`).

## Layering
`routes → services → components/domain`. Dependencies point one way:
- a **component** never imports a service or a route;
- a **service** never imports a route;
- `domain/` is pure functions — no I/O, no LLM, no DB.

## Async
- All route handlers and DB access are `async`; sessions come from `Depends(get_db)`.
- Blocking libraries (boto3, FlagEmbedding) are called via `asyncio.to_thread`.
- One shared `openai_client` from `app.core.llm` — never construct clients per module or request.

## Errors
- Never `except Exception: pass`. Log with context and `exc_info=True`.
- Optional subsystems (reranker, R2, RAG context) degrade with a `logger.warning` and a
  documented fallback; required ones raise `HTTPException` with a clear message.
- Partial or estimated results must be visible to the caller (confidence field, note, or log).

## Prompts
- No inline prompt strings in routes or services. Every prompt is a versioned builder in
  `app/prompts/templates.py`, reached via `get_prompt("name")`.
- Add `_v2` beside `_v1` and switch the active version in the registry; never edit a
  shipped version in place.

## Config
- Everything through `app.core.config.settings` (pydantic-settings). No hardcoded
  keys, model names, paths, or thresholds; add new settings with a sensible default
  and document them in `.env.example`.

## Naming and comments
- Bulgarian for user-facing coaching text; English for code, identifiers and comments.
- Exercise names are always standard English gym names, kilograms for weight.
- Comment the *why*, not the *what*. Docstrings explain the coaching or domain rationale
  (e.g. why a deload threshold exists), not the syntax.
