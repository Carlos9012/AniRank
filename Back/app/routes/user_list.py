from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Anime, UserAnimeStatus
from app.auth.dependencies import get_current_user
from app.schemas.user_anime import UserAnimeCreate, UserAnimeUpdate, UserAnimeResponse

router = APIRouter(prefix="/list", tags=["Lista de Animes"])


@router.post("/", response_model=UserAnimeResponse, status_code=status.HTTP_201_CREATED)
def add_anime_to_list(
    data: UserAnimeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    anime = db.query(Anime).filter(Anime.id == data.anime_id).first()
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime não encontrado"
        )
    
    existing = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == current_user.id,
        UserAnimeStatus.anime_id == data.anime_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anime já está na lista. Use PUT para atualizar"
        )
    
    user_anime = UserAnimeStatus(
        user_id=current_user.id,
        anime_id=data.anime_id,
        status=data.status,
        score=data.score,
        notes=data.notes
    )
    
    db.add(user_anime)
    db.commit()
    db.refresh(user_anime)
    
    return {
        "id": user_anime.id,
        "user_id": user_anime.user_id,
        "anime_id": user_anime.anime_id,
        "status": user_anime.status,
        "score": user_anime.score,
        "notes": user_anime.notes,
        "updated_at": user_anime.updated_at,
        "anime_title": anime.title,
        "anime_cover": anime.cover_image_url,
        "anime_episodes": anime.episodes
    }


@router.get("/", response_model=List[UserAnimeResponse])
def get_user_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_list = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == current_user.id
    ).all()
    
    result = []
    for item in user_list:
        anime = db.query(Anime).filter(Anime.id == item.anime_id).first()
        result.append({
            "id": item.id,
            "user_id": item.user_id,
            "anime_id": item.anime_id,
            "status": item.status,
            "score": item.score,
            "notes": item.notes,
            "updated_at": item.updated_at,
            "anime_title": anime.title if anime else None,
            "anime_cover": anime.cover_image_url if anime else None,
            "anime_episodes": anime.episodes if anime else None
        })
    
    return result


@router.get("/{anime_id}", response_model=UserAnimeResponse)
def get_anime_status(
    anime_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_anime = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == current_user.id,
        UserAnimeStatus.anime_id == anime_id
    ).first()
    
    if not user_anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime não encontrado na sua lista"
        )
    
    anime = db.query(Anime).filter(Anime.id == anime_id).first()
    
    return {
        "id": user_anime.id,
        "user_id": user_anime.user_id,
        "anime_id": user_anime.anime_id,
        "status": user_anime.status,
        "score": user_anime.score,
        "notes": user_anime.notes,
        "updated_at": user_anime.updated_at,
        "anime_title": anime.title if anime else None,
        "anime_cover": anime.cover_image_url if anime else None,
        "anime_episodes": anime.episodes if anime else None
    }


@router.put("/{anime_id}", response_model=UserAnimeResponse)
def update_anime_status(
    anime_id: int,
    data: UserAnimeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_anime = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == current_user.id,
        UserAnimeStatus.anime_id == anime_id
    ).first()
    
    if not user_anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime não encontrado na sua lista"
        )
    
    if data.status is not None:
        user_anime.status = data.status
    if data.score is not None:
        user_anime.score = data.score
    if data.notes is not None:
        user_anime.notes = data.notes
    
    db.commit()
    db.refresh(user_anime)
    
    anime = db.query(Anime).filter(Anime.id == anime_id).first()
    
    return {
        "id": user_anime.id,
        "user_id": user_anime.user_id,
        "anime_id": user_anime.anime_id,
        "status": user_anime.status,
        "score": user_anime.score,
        "notes": user_anime.notes,
        "updated_at": user_anime.updated_at,
        "anime_title": anime.title if anime else None,
        "anime_cover": anime.cover_image_url if anime else None,
        "anime_episodes": anime.episodes if anime else None
    }


@router.delete("/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_anime_from_list(
    anime_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_anime = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == current_user.id,
        UserAnimeStatus.anime_id == anime_id
    ).first()
    
    if not user_anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime não encontrado na sua lista"
        )
    
    db.delete(user_anime)
    db.commit()
    
    return None
