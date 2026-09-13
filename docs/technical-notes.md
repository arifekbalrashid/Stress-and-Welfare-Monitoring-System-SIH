# SAATHI — Technical Notes

> This document covers DB schema, ML pipeline, API reference, and security/privacy design.  
> Living document — updated as the prototype evolves.

## 1. Database Schema

See the 12 SQLAlchemy ORM models in `backend/app/models/`. Key design decisions:

- **Privacy separation**: Identity fields (`first_name`, `last_name`, `contact_number`) live only in `users`/`personnel`. All ML-facing tables reference `personnel_id` as a pseudonymous key.
- **Consolidated operational data**: One `operational_data` table instead of 4 separate duty/shift/deployment/leave tables. Simpler to import, query, and maintain.
- **JSON fields**: `risk_predictions.shap_factors` and `model_versions.metrics` use JSON columns for flexible schema within structured records.
- **Soft timestamps**: All tables include `created_at`; mutable tables include `updated_at`.

## 2. ML Pipeline

### Feature Set
Declared in `ml/configs/model_features_v1.json`. The model consumes exactly 8 features:
- 6 organizational: `duty_hours`, `night_shifts`, `consecutive_duty_days`, `rest_hours`, `deployment_days`, `leave_gap_days`
- 2 derived from wellness: `sleep_quality`, `workload_score` (= mean of `workload_perception` and `5 - recovery`)

### Models
1. **Logistic Regression** — interpretable baseline with coefficient analysis
2. **XGBoost** — primary model with SHAP explainability

### Scoring
- Raw model probability → calibrated to 0–100 welfare risk score
- Bucketed: Low (0–30), Moderate (31–50), Elevated (51–75), High (76–100)
- Trend: Compare to previous 2–3 predictions → Increasing/Stable/Decreasing

### Synthetic Data
- 10,000 rows, `seed=42`, clearly labeled as synthetic
- Documented generation formula in `ml/data_generation/`

## 3. API Reference

Base URL: `/api/v1/`

Standard envelope:
```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional message"
}
```

Error envelope:
```json
{
  "status": "error",
  "message": "Description of the error",
  "detail": { ... }
}
```

### Endpoints
See `backend/app/routes/` for full implementation. Summary in the implementation plan.

## 4. Security & Privacy

- JWT access tokens (30min) + httpOnly refresh cookies (7 days)
- bcrypt password hashing (12 rounds)
- Server-side RBAC via FastAPI dependencies — every route checks role
- Parameterized queries via SQLAlchemy ORM — no raw SQL
- Input validation via Pydantic schemas
- Audit logging for sensitive reads (case views, risk data access)
- CORS restricted to frontend origin
- All secrets in `.env`, never committed

### Limitations
- No TLS termination in dev (handled by reverse proxy in production)
- Rate limiting is basic (slowapi on auth endpoints only)
- No key rotation for JWT secret in prototype
- No data encryption at rest beyond MySQL's built-in encryption
