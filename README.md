# SurakshaAI

Industrial safety intelligence prototype aligned to the ET AI Hackathon 2026 challenge. It combines accident-risk ML, machine-anomaly detection, rule-based compound-risk checks, permit intelligence, worker exposure, incidents, alerts and a plant map.

## Local setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Restore or train these files before using ML assessment:

```text
models_artifacts/risk_model.joblib
models_artifacts/anomaly_model.joblib
models_artifacts/risk_model_metrics.json
```

Start backend:

```bash
uvicorn app.main:app --reload
```

Seed one plant with 4 zones and 50 workers:

```bash
python scripts/seed_demo_data.py
```

Start frontend:

```bash
cd frontend
npm ci
npm run dev
```

Backend: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`  
Frontend: `http://127.0.0.1:5173`

## Production build check

```bash
python -m compileall app scripts
cd frontend && npm ci && npm run build
```

## Storage recommendation

SQLite is enough for a hackathon demo with 4 zones and 50 workers. For a real multi-customer deployment, use PostgreSQL (preferably managed), object storage for CCTV/evidence/documents, and keep ML artifacts in versioned object storage or the deployment image.
