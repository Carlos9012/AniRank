from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Anime
from app.recommendation.content_based import ContentBasedRecommender
from app.recommendation.anilist_search import AniListSearchRecommender

router = APIRouter(prefix="/recommendations", tags=["Recomendações"])

recommender_cache = {}

def get_recommender(db: Session):
    if "recommender" not in recommender_cache:
        recommender = ContentBasedRecommender(db)
        recommender.fit()
        recommender_cache["recommender"] = recommender
    return recommender_cache["recommender"]


@router.get("/by-anime/{anime_id}")
def recommend_by_anime(
    anime_id: int,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recomenda animes similares (content-based)."""
    anime = db.query(Anime).filter(Anime.id == anime_id).first()
    if not anime:
        raise HTTPException(status_code=404, detail="Anime não encontrado")
    
    recommender = get_recommender(db)
    results = recommender.recommend_by_anime(anime_id, top_n=limit)
    
    return {
        "source": {
            "id": anime.id,
            "title": anime.title
        },
        "recommendations": results,
        "method": "content-based (gêneros + sinopse)"
    }


@router.post("/by-description")
def recommend_by_description(
    description: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RECOMENDAÇÃO INTERATIVA
    Busca animes na API do AniList baseado em descrição.
    """
    if not description or len(description.strip()) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Descrição muito curta. Seja mais específico."
        )
    
    # Usa o AniListSearchRecommender (busca na API)
    search_recommender = AniListSearchRecommender()  # <<< NOVO
    results = search_recommender.search_by_description(description, limit=limit)
    
    if not results:
        return {
            "description": description,
            "recommendations": [],
            "message": "Nenhum anime encontrado para esta descrição"
        }
    
    return {
        "description": description,
        "recommendations": results,
        "method": "API AniList (busca por similaridade)"
    }


@router.get("/similar-to/{anime_title}")
def recommend_by_title(
    anime_title: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Busca animes similares a um título fornecido pelo usuário."""
    from sqlalchemy import func

    anime = db.query(Anime).filter(
        func.lower(Anime.title).contains(anime_title.lower())
    ).first()
    
    if not anime:
        raise HTTPException(
            status_code=404, 
            detail=f"Nenhum anime encontrado com o título '{anime_title}'"
        )
    
    recommender = get_recommender(db)
    results = recommender.recommend_by_anime(anime.id, top_n=limit)
    
    return {
        "source": {
            "id": anime.id,
            "title": anime.title
        },
        "recommendations": results,
        "method": "content-based (título do usuário)"
    }