# app/routes/animes.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Anime, UserAnimeStatus
from app.services.anilist_service import AniListService

router = APIRouter(prefix="/animes", tags=["Animes"])


@router.get("/search")
def search_animes(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
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
        raise HTTPException(500, f"Erro ao buscar animes: {str(e)}")

@router.get("/by-external/{external_id}")
def get_anime_by_external(
    external_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    anime = db.query(Anime).filter(Anime.external_id == external_id).first()
    
    if not anime:
        try:
            with AniListService() as service:
                anime_data = service.search_anime_by_id(external_id)
                if not anime_data:
                    raise HTTPException(404, f"Anime com ID {external_id} não encontrado no AniList")
                
                saved_id = service.save_anime_to_db(anime_data)
                if not saved_id:
                    raise HTTPException(500, "Erro ao salvar anime")
                
                anime = db.query(Anime).filter(Anime.id == saved_id).first()
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Erro ao importar anime: {str(e)}")
    
    user_status = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == current_user.id,
        UserAnimeStatus.anime_id == anime.id
    ).first()
    
    return {
        "id": anime.id,
        "external_id": anime.external_id,
        "title": anime.title,
        "synopsis": anime.synopsis,
        "episodes": anime.episodes,
        "year": anime.release_year,
        "cover": anime.cover_image_url,
        "status": anime.airing_status.value if anime.airing_status else None,
        "format": anime.format.value if anime.format else None,
        "source": anime.source.value if anime.source else None,
        "genres": [g.name for g in anime.genres],
        "created_at": anime.created_at.isoformat() if anime.created_at else None,
        "updated_at": anime.updated_at.isoformat() if anime.updated_at else None,
        "user_status": user_status.status if user_status else None,
        "user_score": user_status.score if user_status else None,
        "user_notes": user_status.notes if user_status else None,
        "is_in_list": user_status is not None
    }

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
                "cover": existing.cover_image_url,
                "genres": [g.name for g in existing.genres]
            }
        }
    
    try:
        with AniListService() as service:
            anime_data = service.search_anime_by_id(external_id)
            if not anime_data:
                raise HTTPException(404, "Anime não encontrado no AniList")
            
            saved_anime_id = service.save_anime_to_db(anime_data)
            
            if not saved_anime_id:
                raise HTTPException(500, "Erro ao salvar anime")
            
            saved_anime = db.query(Anime).filter(Anime.id == saved_anime_id).first()
            
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
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erro ao importar anime: {str(e)}")

@router.get("/")
def list_animes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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
        raise HTTPException(404, "Anime não encontrado")
    
    return {
        "id": anime.id,
        "external_id": anime.external_id,
        "title": anime.title,
        "synopsis": anime.synopsis,
        "episodes": anime.episodes,
        "year": anime.release_year,
        "cover": anime.cover_image_url,
        "status": anime.airing_status.value if anime.airing_status else None,
        "format": anime.format.value if anime.format else None,
        "source": anime.source.value if anime.source else None,
        "genres": [g.name for g in anime.genres],
        "created_at": anime.created_at.isoformat() if anime.created_at else None,
        "updated_at": anime.updated_at.isoformat() if anime.updated_at else None
    }
