from datetime import datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routes import (
    animes_router,
    auth_router,
    list_router,
    recommendations,
    home_router,
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="""
    AniRank - Plataforma de tracking de animes com recomendação estatística.

    ## Funcionalidades
    - 📋 Lista pessoal de animes (watching/completed/planned/dropped)
    - ⭐ Avaliação de animes (score 0-10)
    - 🔍 Catálogo de animes com busca
    - 🧠 Recomendações personalizadas (collaborative filtering + content-based)
    """,
)

# CONFIGURAÇÃO DE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://anirank.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(list_router)
app.include_router(animes_router)
app.include_router(recommendations)
app.include_router(home_router)

# ENDPOINTS BÁSICOS

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
    }

@app.get("/info")
async def info():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "database_url": settings.database_url[:30] + "...",
        "jwt_algorithm": settings.algorithm,
        "token_expire_minutes": settings.access_token_expire_minutes,
    }