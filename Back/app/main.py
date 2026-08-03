from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.database import get_db, engine
from app.models import User
from app.routes import auth 

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
    """
)

# INCLUIR ROTAS

# Rotas de autenticação
app.include_router(auth.router)

# ENDPOINTS BÁSICOS

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs": "/docs",
        "health": "/health"
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
        "debug": settings.debug
    }


@app.get("/info")
async def info():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "database_url": settings.database_url[:30] + "...",
        "jwt_algorithm": settings.algorithm,
        "token_expire_minutes": settings.access_token_expire_minutes
    }