"""
SAATHI Backend — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import auth, personnel, wellness, risk, consent, welfare, commander, admin, support, chat

settings = get_settings()

app = FastAPI(
    title="SAATHI API",
    description="AI-Based Predictive Personnel Stress & Welfare Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(personnel.router, prefix="/api/v1/personnel", tags=["Personnel"])
app.include_router(wellness.router, prefix="/api/v1/wellness", tags=["Wellness"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["Risk"])
app.include_router(consent.router, prefix="/api/v1/consent", tags=["Consent"])
app.include_router(support.router, prefix="/api/v1/support", tags=["Support"])
app.include_router(welfare.router, prefix="/api/v1/welfare", tags=["Welfare"])
app.include_router(commander.router, prefix="/api/v1/commander", tags=["Commander"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chatbot"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "saathi-api"}
