from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Anime
from app.services.anilist_service import AniListService

router = APIRouter(prefix="/animes", tags=["Animes"])


@router.get("/search")
def search_animes(
    query: str = Query(..., min_length=1, max_length=100, description="Nome do anime para buscar"),
    limit: int = Query(10, ge=1, le=50, description="Quantidade de resultados (1-50)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        with AniListService() as service:
            results = service.search_anime(query, per_page=limit)
        
        if not results:
            return {
                "query": query,
                "count": 0,
                "results": [],
                "message": "Nenhum anime encontrado"
            }
        
        external_ids = [anime["id"] for anime in results]
        existing = db.query(Anime).filter(Anime.external_id.in_(external_ids)).all()
        existing_ids = {a.external_id for a in existing}
        
        return {
            "query": query,
            "count": len(results),
            "results": [
                {
                    "external_id": anime["id"],
                    "title": anime["title"]["romaji"],
                    "title_english": anime["title"].get("english"),
                    "title_native": anime["title"].get("native"),
                    "year": anime.get("seasonYear"),
                    "episodes": anime.get("episodes"),
                    "cover": anime["coverImage"]["large"],
                    "genres": anime.get("genres", []),
                    "status": anime.get("status"),
                    "already_in_db": anime["id"] in existing_ids
                }
                for anime in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar animes: {str(e)}"
        )


@router.post("/import/{external_id}")
def import_anime(
    external_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Anime).filter(Anime.external_id == external_id).first()
    if existing:
        return {
            "message": "Anime já está no banco de dados",
            "anime": {
                "id": existing.id,
                "external_id": existing.external_id,
                "title": existing.title,
                "year": existing.release_year,
                "cover": existing.cover_image_url
            }
        }
    
    try:
        with AniListService() as service:
            results = service.search_anime_by_id(external_id)
            if not results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Anime não encontrado no AniList"
                )
            
            saved_anime = service.save_anime_to_db(results)
            
            if not saved_anime:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao salvar anime no banco"
                )
            
            return {
                "message": "Anime importado com sucesso",
                "anime": {
                    "id": saved_anime.id,
                    "external_id": saved_anime.external_id,
                    "title": saved_anime.title,
                    "year": saved_anime.release_year,
                    "cover": saved_anime.cover_image_url,
                    "genres": [g.name for g in saved_anime.genres]
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao importar anime: {str(e)}"
        )


@router.get("/")
def list_animes(
    skip: int = Query(0, ge=0, description="Pular N resultados"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    animes = db.query(Anime).offset(skip).limit(limit).all()
    total = db.query(Anime).count()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [
            {
                "id": a.id,
                "external_id": a.external_id,
                "title": a.title,
                "year": a.release_year,
                "episodes": a.episodes,
                "cover": a.cover_image_url,
                "status": a.airing_status.value if a.airing_status else None,
                "genres": [g.name for g in a.genres]
            }
            for a in animes
        ]
    }


@router.get("/{anime_id}")
def get_anime(
    anime_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    anime = db.query(Anime).filter(Anime.id == anime_id).first()
    
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime não encontrado"
        )
    
    return {
        "id": anime.id,
        "external_id": anime.external_id,
        "title": anime.title,
        "synopsis": anime.synopsis,
        "episodes": anime.episodes,
        "year": anime.release_year,
        "cover": anime.cover_image_url,
        "status": anime.airing_status.value if anime.airing_status else None,
        "genres": [g.name for g in anime.genres],
        "created_at": anime.created_at,
        "updated_at": anime.updated_at
    }
