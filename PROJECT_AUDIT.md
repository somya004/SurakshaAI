# SurakshaAI deep review and deployment plan

## Alignment with the hackathon challenge

The project already covers the strongest parts of the selected challenge: compound-risk fusion, permit intelligence, worker exposure, geospatial zones, incidents, alerts, emergency actions, and two ML models. The main competitive advantage should be demonstrated as **ML + anomaly + operational context outperforming single-sensor rules**, with false-negative rate and prediction lead time shown explicitly.

## Critical defects corrected

1. `app/main.py` used `app.include_router()` before `app` was created and also applied a duplicate ML route prefix.
2. The frontend base URL omitted `/api/v1` when `.env` contained only the backend host, causing every normal page to call nonexistent endpoints.
3. `ml_command_center.py` used `anomaly_result` without creating it.
4. Command Center state was held only in a Python dictionary and disappeared on restart.
5. Frontend ML request types did not include the anomaly-model fields required by the backend.
6. The Command Center page existed but was not registered in React Router.
7. `requirements.txt` was UTF-16, which can break Linux/container installs.
8. The frontend had an unused import that stopped the TypeScript production build.
9. Risk-model loading happened at module import time, preventing the entire API from starting when artifacts were temporarily absent.
10. The uploaded `node_modules` was platform-specific; it must not be committed or deployed.

## Files changed

### Backend

- `app/main.py`
  - Correct router registration.
  - Single `/api/v1` prefix.
  - Environment-controlled CORS.
- `app/database/connection.py`
  - Environment-controlled `DATABASE_URL`.
  - Disabled noisy SQL logging by default.
  - Added `pool_pre_ping` and reliable session cleanup.
- `app/database/schemas.py`
  - Added persistent `CommandCenterAssessment` history.
- `app/api/ml_command_center.py`
  - Correct anomaly mapping.
  - Missing-feature validation.
  - 503 response when model artifacts are unavailable.
  - Database persistence and latest-per-zone overview.
- `app/services/ml_prediction_service.py`
  - Lazy/cached model loading.
  - Artifact validation.
- `scripts/seed_demo_data.py`
  - Idempotent seed for four zones and fifty workers.
- `requirements.txt`
  - Converted to UTF-8.
- `.env.example`, `.gitignore`, `README.md`
  - Added safe deployment and setup defaults.

### Frontend

- `frontend/src/api/client.ts`
  - Normalizes the base URL and always targets `/api/v1` once.
- `frontend/src/api/mlCommandCenterApi.ts`
  - Uses the shared Axios client and correct endpoints.
- `frontend/src/types/mlCommandCenter.ts`
  - Includes all seven anomaly-model inputs.
- `frontend/src/pages/CommandCenter.tsx`
  - Adds safe and critical anomaly inputs to requests.
- `frontend/src/router/AppRouter.tsx`
  - Registers `/command-center`.
- `frontend/src/components/Sidebar.tsx`
  - Correct Command Center navigation and separate Dashboard entry.
- `frontend/src/pages/Maintenance.tsx`
  - Removed the build-blocking unused import.

## Current verified state

- Python compilation succeeds.
- Frontend TypeScript and Vite production build succeed.
- Health, dashboard, workers, plant zones, model metrics, and Command Center overview endpoints return HTTP 200.
- The application can start without model artifacts; only ML assessment returns a clear service-unavailable error until artifacts are restored.

## Model-artifact contract

Restore these under `models_artifacts/`:

- `risk_model.joblib`
- `anomaly_model.joblib`
- `risk_model_metrics.json`
- optionally `anomaly_model_metrics.json`

`risk_model.joblib` must contain:

- `model`
- `model_name`
- `numeric_columns`
- `categorical_columns`

`anomaly_model.joblib` must contain:

- `model`
- `model_name`
- `feature_columns`
- `score_reference.raw_score_min`
- `score_reference.raw_score_max`

Keep the isolated `/api/v1/anomalies/assess` endpoint. It is useful for model testing. The Command Center should orchestrate it through the shared service rather than duplicating the model.

## Data storage for one industry, four zones and fifty workers

### Hackathon/demo

Use SQLite. It is enough for one running backend process and a controlled demo. Run:

```bash
python scripts/seed_demo_data.py
```

This creates four zones and fifty workers with current locations and PPE status.

### Real deployment

Use managed PostgreSQL. Store:

- PostgreSQL: workers, current location, permits, maintenance, sensor aggregates, assessments, incidents, alerts and audit logs.
- Object storage: CCTV clips, images, regulatory PDFs, generated incident reports and versioned ML artifacts.
- Optional Redis: live zone state, websocket fan-out and short-lived alert deduplication.

Recommended retention:

- `worker_locations`: keep the latest row in the live table; archive raw updates for 7–30 days and hourly aggregates longer.
- `sensor_readings`: raw 1–10 second readings for 7 days; one-minute aggregates for 90 days; hourly aggregates for 1–3 years.
- incidents, permits, maintenance, acknowledgements and compliance evidence: retain long-term.
- Command Center assessments: retain all critical/high events; downsample safe assessments.

With 50 workers updating every 15 seconds, raw location events can reach about 288,000 rows/day. Do not keep unlimited raw location history in SQLite. For a demo, update every 30–60 seconds or only on zone change.

## Remaining improvements, in priority order

### P0 — before final demo

1. Restore and smoke-test both trained model artifacts.
2. Run four zone scenarios and confirm the overview persists after a restart.
3. Display backend error details in every page instead of only “Unable to load data.”
4. Add a visible “model unavailable” banner when metrics return `available: false`.
5. Add at least one comparison chart: compound model recall/FNR versus single-sensor baseline.

### P1 — improves judging score

1. Replace manual Command Center worker count with workers queried from the selected zone.
2. Read active permits and maintenance from database by zone instead of accepting only a form permit.
3. Add WebSocket or 5–10 second polling for live map/overview updates.
4. Store model version and feature snapshot with each assessment for auditability.
5. Add calibrated threshold selection prioritising false-negative reduction.
6. Add four fixed demo narratives: safe, gas leak, hot-work conflict, and machine failure with worker exposure.

### P2 — architecture completeness

1. Implement the currently empty RAG/compliance modules for OISD/Factory Act/DGMS evidence.
2. Add Alembic migrations; `create_all()` is acceptable for demo but not schema evolution.
3. Add authentication and role-based access for supervisor, safety officer and emergency team.
4. Add tenant/industry IDs to all operational tables for multi-customer isolation.
5. Add unit/integration tests and CI.
6. Lazy-load frontend routes to reduce the current large JavaScript bundle warning.

## Multi-customer schema note

The wording “50 customers working at different zones” appears to mean fifty workers. The included seed follows that interpretation. If you actually mean fifty industrial customer companies, add `tenant_id` to every table and use PostgreSQL row-level security or strict tenant filtering.
