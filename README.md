# Cybernetic Gym Assistant

Personal AI fitness coach built on the **Menno Henselmans** coaching methodology. It plans
training and nutrition, tracks progress, and makes coaching decisions grounded in the course
material via RAG, deterministic sport-science calculators, and (planned) ML. Phone-first.

> Contributor/agent guidelines and the git workflow live in [CLAUDE.md](CLAUDE.md). Read it first.

## Architecture

```
backend/
  app/           the application package (routes → services → components/domain)
    core/        config, security (JWT/bcrypt), shared LLM client
    db/          async SQLAlchemy engine + session
    domain/      deterministic sport science (energy, 1RM, volume, goal validation)
    components/  retrieval building blocks (FAISS retriever, cross-encoder reranker)
    services/    RAG pipeline, fatigue/deload, progression, weight trend, R2 storage
    prompts/     versioned prompt templates + registry
    routes/      FastAPI routers (HTTP layer only)
  evaluation/    golden dataset + offline RAG eval + tracked results
  migrations/    Alembic migrations
  scripts/       healthcheck and operational entry points
  tests/         unit tests for the deterministic engines
  notebooks/     prototypes: extraction, chunking, embeddings, agent experiments
  data/          extracted course material + FAISS vectorstore (git-ignored)
frontend/        React PWA (planned)
docs/            architecture notes
```

- **Backend:** FastAPI + async SQLAlchemy + PostgreSQL.
- **AI:** OpenAI (LLM + embeddings), FAISS retrieval, vision model for body-fat photo assessment.
- **Deterministic first:** all body-composition/energy/volume/1RM numbers come from
  `backend/app/domain/calculators.py` — the LLM explains them, never recomputes them.

See [docs/architecture.md](docs/architecture.md) for the layer rules and RAG pipeline.

## Setup

Requirements: Python 3.12+, PostgreSQL 14+, an OpenAI API key.

```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash;  use venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt

cp .env.example .env              # then edit .env with real values
```

### Database

Create the database (once), then apply migrations:

```bash
# create the DB in your local Postgres, e.g.:
#   createdb -U postgres cybernetic_gym_assistant

cd backend
python -m alembic upgrade head
```

If the tables already exist (e.g. an older DB created by hand), tell Alembic the baseline is
already applied instead of recreating it:

```bash
python -m alembic stamp head
```

Creating a new migration after changing `models.py`:

```bash
python -m alembic revision --autogenerate -m "describe change"
python -m alembic upgrade head
```

### Run the API

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs at `http://localhost:8000/docs`, health check at `/health`.

## Notebooks

`backend/notebooks/` contains the data pipeline and AI prototypes (extraction → chunking →
embeddings → RAG evaluation → agent prototypes). They are prototypes: logic proven there is
ported into `backend/app/` before it counts as shipped.

## Data & secrets

- `backend/.env` holds all secrets and is git-ignored — never commit it. Use `.env.example` as the template.
- `backend/data/` (course material, FAISS index) is git-ignored.
