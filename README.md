# Quantum-Assisted ML Framework for Drug Repurposing

Production-ready system for rare-disease drug repurposing: ML scoring, QUBO optimization, and secure audit logging.

## Live demo

Replace the URLs below once you deploy (see [Environment](#environment) for required variables).

| | URL |
|--|-----|
| **Frontend** (Vercel) | https://your-vercel-app.vercel.app |
| **Backend health** (Render) | https://your-render-app.onrender.com/api/v1/health |

### Production and platform notes

These are **host limits**, not application bugs:

- **Render free tier** — The web service sleeps after idle time. Expect **roughly 20–60 seconds** on the first request after sleep. **Socket.IO / WebSockets** can be flaky across sleep and cold starts; long-polling fallback may appear. For a stable demo, prefer REST polling over persistent sockets where possible.
- **ML and data** — Full **GNN training**, large **dataset ingestion** (e.g. full ChEMBL/DrugBank pipelines), and heavy batch jobs are **not** suited to free-tier CPU/RAM. Deployed instances are intended for **API + lightweight inference** and demos.
- **MongoDB Atlas (M0)** — Connection count and cold starts apply; the backend URI is tuned with reasonable driver timeouts (see `.env.example`).

## Quick start

### Backend (Flask API + pipeline)

1. **MongoDB** — Start MongoDB locally (or use Docker).
2. **From repo root:**
   ```bash
   cd quantum-drug-repurposing
   pip install -r backend/requirements.txt
   set PYTHONPATH=backend
   python backend/run.py
   ```
   API: http://localhost:5000 — Health: http://localhost:5000/api/v1/health

3. **Submit a query (sync, no Celery):**
   ```bash
   curl -X POST http://localhost:5000/api/v1/query -H "Content-Type: application/json" -d "{\"disease_name\": \"Progeria\", \"top_k\": 5}"
   ```
   Use the returned `task_id` to poll `/api/v1/query/<task_id>/status` and then `/api/v1/results/<task_id>`.

### Frontend (React)

```bash
cd quantum-drug-repurposing/frontend
npm install
npm run dev
```

Open http://localhost:3000 — Dashboard, New Query, Results, Audit trail.

### Docker (full stack)

```bash
cd quantum-drug-repurposing/infra
docker-compose up -d
```

Backend: 5000, Frontend: 3000, MongoDB: 27017, Redis: 6379.

### Tests

```bash
set PYTHONPATH=quantum-drug-repurposing/backend
python -m pytest quantum-drug-repurposing/backend/tests -v
```

## Data engineering (already run)

- **Master audit:** `python backend/data/ingestion/master_audit.py` — SHA-256 seal of raw data.
- **DrugBank:** `python backend/data/ingestion/drugbank_extract_smiles.py` — Drug ID + SMILES.
- **ClinVar:** `python backend/data/ingestion/clinvar_filter_gold_set.py` — Gold set (Pathogenic + rare/orphan).
- **ChEMBL:** `python backend/data/ingestion/chembl_binding_linkage.py` — Binding scores for QUBO.

Processed outputs: `backend/data/processed/` (drugbank_drug_smiles.csv, clinvar_gold_set.tsv, chembl_binding_scores.csv).

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/health | Health check |
| POST | /api/v1/auth/login | JWT login |
| POST | /api/v1/query | Submit repurposing query (202 + task_id) |
| GET | /api/v1/query/<task_id>/status | Task status |
| GET | /api/v1/results/<task_id> | Ranked drug results |
| GET | /api/v1/audit/<task_id> | Audit chain |
| GET | /api/v1/audit/verify/<task_id> | Verify hash chain |
| GET | /api/v1/models | List model versions |
| GET | /api/v1/reports/<task_id>/pdf | PDF report (501 stub) |

## Example: Progeria query output

**Input:** `POST /api/v1/query` with body `{"disease_name": "Progeria", "top_k": 5}`.

After the task completes, **`GET /api/v1/results/<task_id>`** returns ranked candidates (fields depend on data and pipeline path; illustrative shape):

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "disease_name": "Progeria",
  "top_k": 5,
  "qubo_energy": -12.34,
  "ranked_drugs": [
    {
      "rank": 1,
      "score": 0.92,
      "molregno": "12345",
      "canonical_smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
      "target_name": "Example target"
    },
    {
      "rank": 2,
      "score": 0.88,
      "molregno": "12346",
      "canonical_smiles": null,
      "target_name": "Another target"
    }
  ]
}
```

Exact scores, molecule IDs, and SMILES come from your processed datasets and mapping pipeline. Degraded or AI-assisted paths may return fewer rows or placeholders when external keys or local data are unavailable.

## Screenshots

Add captures from your deployed or local UI under `docs/screenshots/` (create the folder if needed), then the images below will render on GitHub.

| Dashboard | Results | Audit |
| --- | --- | --- |
| ![Dashboard](docs/screenshots/dashboard.png) | ![Results](docs/screenshots/results.png) | ![Audit](docs/screenshots/audit.png) |

Suggested captures: main **Dashboard**, **Results** after a Progeria (or similar) run, and **Audit** / audit history or verification view.

## Environment

Copy `.env.example` to `.env` and configure:

- **Backend:** `SECRET_KEY`, `JWT_SECRET_KEY`, `MONGO_URI`, `MONGODB_DB` (must match Atlas DB name if used). For production, set `FLASK_ENV=production` and **`CORS_ORIGINS`** to your frontend origin(s), comma-separated (e.g. `https://your-app.vercel.app`).
- **Optional:** `REDIS_URL` / `CELERY_BROKER_URL` for async workers (not typical on free-tier hosts).
- **Frontend (Vercel / production build):** `VITE_API_BASE_URL` = API **origin only** (no `/api/v1`), e.g. `https://your-render-app.onrender.com`.
