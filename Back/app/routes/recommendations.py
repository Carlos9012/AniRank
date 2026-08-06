from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Anime
from app.recommendation.anilist_search import AniListSearchRecommender

router = APIRouter(prefix="/recommendations", tags=["Recomendações"])


@router.post("/by-description")
def recommend_by_description(
    description: str = Query(..., description="Descrição do que você procura"),
    limit: int = Query(5, ge=1, le=50, description="Quantidade de resultados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RECOMENDAÇÃO INTERATIVA
    Busca animes na API do AniList baseado em descrição do usuário.
    """
    if not description or len(description.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Descrição muito curta. Seja mais específico."
        )

    recommender = AniListSearchRecommender()
    results = recommender.search_by_description(description, limit=limit)

    if not results:
        return {
            "description": description,
            "recommendations": [],
            "message": "Nenhum anime encontrado para esta descrição"
        }

    return {
        "description": description,
        "recommendations": results,
        "count": len(results),
        "method": "API AniList + Gemini (interpretação de intenção)"
    }


@router.get("/by-anime/{anime_id}")
def recommend_by_anime(
    anime_id: int,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    anime = db.query(Anime).filter(Anime.id == anime_id).first()
    if not anime:
        raise HTTPException(status_code=404, detail="Anime não encontrado")

    return {
        "source": {
            "id": anime.id,
            "title": anime.title
        },
        "recommendations": [],
        "message": "Em breve: recomendações baseadas em similaridade",
        "method": "content-based (gêneros + sinopse)"
    }