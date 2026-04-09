# Quantum-Assisted ML Framework for Drug Repurposing

Production-ready system for rare-disease drug repurposing: ML scoring, QUBO optimization, and secure audit logging.

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

## Environment

Copy `.env.example` to `.env` and set `SECRET_KEY`, `JWT_SECRET_KEY`, `MONGO_URI`, and optionally `REDIS_URL` / `CELERY_BROKER_URL` for async workers.
