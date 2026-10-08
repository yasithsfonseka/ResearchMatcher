# ResearchMatch - Scholarly Paper Discovery, Categorization, and Matching Platform

ResearchMatch is an enterprise-grade full-stack research paper discovery platform. It enables researchers to enter proposed research titles and descriptions, discover relevant academic papers from connected scholarly sources (OpenAlex, Semantic Scholar, Crossref), browse paper taxonomies, compute vector similarity matching, understand evidence-grounded match explanations, and organize literature-review collections.

---

## Architecture Overview

- **Frontend**: Next.js 14 (App Router) with TypeScript, Tailwind CSS, Lucide icons, responsive dark UI.
- **Backend**: Python FastAPI with Pydantic v2 validation, SQLAlchemy 2.0 ORM, and Alembic migrations.
- **Database**: PostgreSQL 16 with `pgvector` extension for storing 384-dimensional vector embeddings.
- **Background Worker**: Python Redis worker for long-running ingestion and embedding generation outside HTTP request threads.
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Apache 2.0 / MIT compatible) producing 384-dim dense vectors.
- **Adapters**:
  - **OpenAlex Adapter**: Primary metadata source with polite mailto header, exponential backoff retries, inverted index abstract decoder.
  - **Semantic Scholar Adapter**: Secondary recommendation & citation enrichment source.
  - **Crossref Adapter**: DOI verification and metadata enrichment.
- **Security & Privacy**: Argon2/BCrypt password hashing, JWT HttpOnly cookies, collection authorization, formula-injection safe CSV export (`=`, `+`, `-`, `@` sanitization).

---

## Repository Structure

```text
ResearchMatch/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/001_initial_schema.py
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── providers/ (openalex, semanticscholar, crossref)
│   │   ├── services/ (normalization, deduplication, search_pipeline, embeddings, explanations, export_csv)
│   │   ├── api/v1/ (auth, search, papers, subjects, collections, feedback, jobs, health)
│   │   └── worker/tasks.py
│   ├── evaluation/
│   │   ├── evaluate.py
│   │   └── benchmark_queries.json
│   └── tests/
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_auth.py
│       └── test_collections.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── src/
    │   ├── app/ (page, search, subjects, papers, collections, auth, settings)
    │   ├── components/ (Header, Footer, PaperCard, SaveToCollectionModal)
    │   └── lib/api.ts
    └── e2e/
        └── search_and_collections.spec.ts
```

---

## Quick Setup Instructions

### Prerequisites
- Docker & Docker Compose (or Python 3.11+, Node.js v20+, PostgreSQL with pgvector, Redis)
- Git & WSL Ubuntu (if using Windows WSL)

---

### Option A: Running with Docker Compose (Recommended)

1. **Clone & Configure Environment**:
   ```bash
   cp .env.example .env
   ```

2. **Start Services**:
   ```bash
   docker compose up --build -d
   ```

3. **Verify Deployment**:
   - Frontend UI: `http://localhost:3000`
   - Backend API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/api/v1/health`

---

### Option B: Non-Docker / Windows WSL Ubuntu Setup

1. **Start PostgreSQL & Redis**:
   ```bash
   # Ensure pgvector extension is enabled in PostgreSQL
   psql -U research_user -d researchmatch -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Run Database Migrations
   alembic upgrade head

   # Start FastAPI App
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start Worker Task Queue**:
   ```bash
   cd backend
   python -m app.worker.tasks
   ```

4. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Running Automated & E2E Tests

### Backend Tests (pytest)
```bash
cd backend
pytest -v
```

### Run Benchmark Evaluation
```bash
cd backend
python evaluation/evaluate.py
```

### Frontend End-to-End Tests (Playwright)
```bash
cd frontend
npx playwright test
```

---

## API Usage Examples

### 1. Execute Search Query
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "research_title": "Conversational AI and Dialogue Personalization using Transformers",
    "research_description": "Adapting language model responses based on user conversational history",
    "keywords": ["conversational ai", "transformers", "user modeling"],
    "year_min": 2020,
    "limit": 10
  }'
```

### 2. Export Collection as Formula-Safe CSV
```bash
curl -X GET "http://localhost:8000/api/v1/collections/{collection_id}/export" \
  -H "Authorization: Bearer <your_access_token>" \
  --output collection.csv
```

---

## Known Limitations & Future Enhancements

1. **OpenAlex Rate Limits**: Requests use polite `User-Agent` headers (`mailto`). For heavy traffic, supply an `OPENALEX_API_KEY`.
2. **Abstract Availability**: Papers whose publishers do not provide abstracts to OpenAlex display a clear "Important metadata missing" indicator and rely on title/subject vector matching.
3. **Multi-Disciplinary Scope**: Current subject hierarchy seeds Computer Science and AI domains; data model supports seamless expansion to biomedical or social sciences.

---

## Deployment Checklist

- [x] Environment variables configured (`SECRET_KEY`, `OPENALEX_POLITE_EMAIL`, `DATABASE_URL`).
- [x] Database migrations applied (`alembic upgrade head`).
- [x] CORS allowed origins configured.
- [x] Formula injection protection enabled on CSV exports.
- [x] Background Redis worker active.
