# SAATHI — AI-Based Predictive Personnel Stress & Welfare Monitoring System

> **Prototype** built for Smart India Hackathon 2026.  
> Uses synthetic data only. Not clinically validated. AI output is decision-support, never a final decision.

## Overview

SAATHI is a privacy-preserving, welfare-focused decision-support system for uniformed force personnel. It combines organizational duty data with voluntary wellness check-ins to flag patterns associated with rising welfare risk — so welfare officers and commanders can intervene early.

**What it is:** A non-clinical welfare risk indicator using workload, duty patterns, and optional self-reported wellness data.

**What it is NOT:** A diagnostic tool, surveillance system, or basis for disciplinary action.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS + Recharts |
| State/Routing | TanStack Query + React Router |
| Backend | Python + FastAPI + Pydantic + Uvicorn |
| Database | MySQL 8+ |
| ORM/Migrations | SQLAlchemy + PyMySQL + Alembic |
| ML | Pandas, NumPy, Scikit-learn, XGBoost, SHAP |
| Auth | JWT + bcrypt |
| Deploy | Local Development |

## Quick Start

### Prerequisites
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)
- MySQL 8+

### Setup Environment
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Seed Demo Data
```bash
cd backend
python -m app.seed
```

## Roles

| Role | Access |
|------|--------|
| Personnel | Own risk dashboard, wellness check-in, consent management, support requests |
| Welfare Officer | Flagged cases with explanations, log interventions |
| Commander | Unit-level aggregate trends only (no individual data) |
| Admin/HR | Personnel/unit management, CSV import, user management, model status, audit logs |

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Personnel | `p1024` | `demo1234` |
| Welfare Officer | `wo_sharma` | `demo1234` |
| Commander | `cmd_singh` | `demo1234` |
| Admin | `admin` | `admin1234` |

## Limitations

- **Synthetic data only** — no real force data was used
- **Not clinically validated** — risk thresholds are arbitrary for demo purposes
- **Prototype** — not production-ready (no TLS, no key rotation, simplified rate limiting)
- **Human oversight mandatory** — all AI output requires review by welfare officers
- **Real deployment requires** — institutional ethics review, informed consent processes, data protection assessment, clinical expert calibration, governance framework

## License

This project was built for SIH 2026 evaluation purposes.
