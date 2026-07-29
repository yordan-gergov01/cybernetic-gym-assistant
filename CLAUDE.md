# CLAUDE.md — Cybernetic Gym Assistant

Guidance for AI assistants (and humans) working in this repository. Read this before making any change.

---

## 0. Project context

Personal AI fitness coach for a single primary user, built on the **Menno Henselmans** coaching methodology (PT Certification course materials). The app plans training and nutrition, tracks progress, and makes coaching decisions grounded in the course content via RAG, calculators, and (planned) ML.

- **Primary surface:** mobile (phone-first UI). The frontend does not exist yet — the planned stack is a **React PWA** (installable web app, phone-first). Lives in `frontend/` (currently empty).
- **Backend:** FastAPI + async SQLAlchemy + PostgreSQL, OpenAI for LLM/embeddings, FAISS for retrieval, Gemini Vision for body-fat photo assessment. Located in `backend/app/`.
- **Domain logic:** deterministic sport-science calculators live in `backend/app/domain/calculators.py` (energy intake, 1RM, optimal volume, goal validation). These are the source of truth for numbers — the LLM must not recompute them.
- **Knowledge base:** course PDFs/Excel/DOCX are extracted to `backend/data/processed/` and embedded into a FAISS index. Prototyping happens in `backend/notebooks/`; production code lives in `backend/app/`.

When a task is LLM-shaped and the provider is unstated, the stack is **OpenAI** (see `PRIMARY_MODEL`, `EMBEDDING_MODEL` in `backend/app/core/config.py`).

---

## 1. Git & approval workflow — MANDATORY

These rules are non-negotiable and override any default behavior:

1. **Every change goes on a new branch.** Never work directly on `master`. Branch naming: `feat/…`, `fix/…`, `docs/…`, `chore/…`, `refactor/…`.
2. **Never commit or push without the user's explicit approval.** Make the edits in the working tree, then stop and ask for review. Wait for a clear "yes" before `git commit`. Wait for a separate explicit approval before `git push`.
3. **Commit messages must never mention Claude, AI, an assistant, or any automated authorship.** No `Co-Authored-By` AI trailers, no "Generated with…" footers, no "🤖" markers. Write commit messages as if authored by the user, in plain descriptive terms.
4. Never use `--no-verify`, `--force`, or skip hooks unless the user explicitly asks.
5. Do not amend or rewrite existing commits unless explicitly asked.

---

## 2. Engineering principles

1. **Think before coding.** State your assumptions explicitly and confirm the unknowns. Do not guess intent — if the request is ambiguous, ask. The model cannot read the user's mind.
2. **Simplicity first.** Write the minimum code that solves the task. No speculative abstractions, no "for future flexibility" layers. Every abstraction must earn its place today.
3. **Surgical changes.** Touch only what the task requires. Do not "improve" adjacent code, reformat unrelated lines, or refactor in passing. Keep diffs small and reviewable.
4. **Goal-driven execution.** Define explicit success criteria before starting, then loop until they are verifiably met — no earlier, no later. State how you will know you are done.
5. **Use the model only for judgment calls** — classification, drafting, summarization, extraction. NOT for routing, retries, status-code handling, or deterministic transforms. **If code can answer, code answers.** (E.g. macros come from `calculators.py`, not from an LLM guess.)
6. **Respect token/effort budgets.** Keep tasks scoped (~4000 tokens per task, ~30000 per session as a guide). If a debug loop is repeating suggestions already rejected, stop and re-plan instead of grinding.
7. **Surface conflicts, don't average them.** If two patterns exist in the codebase, pick one deliberately and say why. Never blend two approaches into a compromise that hides the disagreement.
8. **Read before you write.** Read the exports, callers, and shared utilities in the area you're changing. Never add a function next to an identical one you never checked for.
9. **Tests verify intent, not just behavior.** A test that still passes when the business logic is broken is worthless. Assert the meaningful result, not a constant the function happens to return.
10. **Checkpoint every significant step.** Verify each step actually works before building the next on top of it. Never stack steps 5 and 6 on an unverified (possibly broken) step 4.
11. **Match codebase conventions.** Follow the existing style, structure, and patterns (async SQLAlchemy sessions, FastAPI routers, Pydantic schemas, dataclass calculators). Don't silently fork to a different paradigm.
12. **Fail loud.** Surface uncertainty and partial failures. "Completed successfully" while silently skipping records is the worst class of bug. If something was skipped, estimated, or is low-confidence, say so and make it visible in the output.

---

## 3. Project-specific conventions

- **Deterministic first:** all body-composition, energy, volume, and 1RM numbers come from `backend/app/domain/calculators.py`. The LLM may explain them but must never recompute or override them.
- **Language:** user-facing coaching text is Bulgarian (`RESPONSE_LANGUAGE=bulgarian`). Exercise names are always standard **English** gym names (e.g. "Barbell Row"). Units are kilograms.
- **RAG grounding:** coaching advice should be grounded in retrieved Henselmans course context, not the model's general knowledge. Keep retrieval + citation intact when editing chat/program/food flows.
- **Config:** all settings and secrets go through `backend/app/core/config.py` (`Settings`). Never hardcode keys, models, or paths — add them to config and `.env`.
- **Notebooks are prototypes.** Logic proven in `backend/notebooks/` must be ported into `backend/app/` (not imported from notebooks) before it counts as shipped.
- **Secrets:** `.env` is git-ignored and must stay that way. Never commit API keys or credentials.

---

## 4. Before you finish a task

- [ ] Change is on a dedicated branch (not `master`).
- [ ] Nothing committed or pushed without explicit approval.
- [ ] Diff is minimal and scoped to the task.
- [ ] Numbers come from calculators, not the LLM, where applicable.
- [ ] New behavior is verified end-to-end (not just "it imports").
- [ ] Uncertainty / skipped items are surfaced, not hidden.
