from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Anime, User, UserAnimeStatus
from app.schemas.user_anime import UserAnimeCreate, UserAnimeResponse, UserAnimeUpdate
from app.services.anilist_service import AniListService

router = APIRouter(prefix="/list", tags=["Lista de Animes"])


def resolve_anime_id(db: Session, anime_id_input: int) -> int:
    anime = db.query(Anime).filter(Anime.id == anime_id_input).first()
    if anime:
        return anime.id
    anime = db.query(Anime).filter(Anime.external_id == anime_id_input).first()
    if anime:
        return anime.id
    return None


@router.post("/", response_model=UserAnimeResponse, status_code=status.HTTP_201_CREATED)
def add_anime_to_list(
    data: UserAnimeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    anime = None
    anime_id_value = data.anime_id

    anime = db.query(Anime).filter(Anime.id == anime_id_value).first()
    if not anime:
        anime = db.query(Anime).filter(Anime.external_id == anime_id_value).first()
    if not anime:
        try:
            with AniListService() as service:
                anime_data = service.search_anime_by_id(anime_id_value)
                if not anime_data:
                    raise HTTPException(
                        404, f"Anime com ID {anime_id_value} não encontrado no AniList"
                    )
                saved_id = service.save_anime_to_db(anime_data)
                if not saved_id:
                    raise HTTPException(500, "Erro ao salvar anime")
                anime = db.query(Anime).filter(Anime.id == saved_id).first()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Erro ao importar anime: {str(e)}")

    if not anime:
        raise HTTPException(404, "Anime não encontrado")

    existing = (
        db.query(UserAnimeStatus)
        .filter(
            UserAnimeStatus.user_id == current_user.id,
            UserAnimeStatus.anime_id == anime.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(400, "Anime já está na lista. Use PUT para atualizar")

    user_anime = UserAnimeStatus(
        user_id=current_user.id,
        anime_id=anime.id,
        status=data.status,
        score=data.score,
        notes=data.notes,
    )

    db.add(user_anime)
    db.commit()
    db.refresh(user_anime)

    return {
        "id": user_anime.id,
        "user_id": user_anime.user_id,
        "anime_id": user_anime.anime_id,
        "external_id": anime.external_id,
        "status": user_anime.status,
        "score": user_anime.score,
        "notes": user_anime.notes,
        "updated_at": user_anime.updated_at,
        "anime_title": anime.title,
        "anime_cover": anime.cover_image_url,
        "anime_episodes": anime.episodes,
    }


@router.get("/", response_model=List[UserAnimeResponse])
def get_user_list(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_list = (
        db.query(UserAnimeStatus)
        .filter(UserAnimeStatus.user_id == current_user.id)
        .all()
    )

    result = []
    for item in user_list:
        anime = db.query(Anime).filter(Anime.id == item.anime_id).first()
        result.append(
            {
                "id": item.id,
                "user_id": item.user_id,
                "anime_id": item.anime_id,
                "external_id": anime.external_id if anime else None,
                "status": item.status,
                "score": item.score,
                "notes": item.notes,
                "updated_at": item.updated_at,
                "anime_title": anime.title if anime else None,
                "anime_cover": anime.cover_image_url if anime else None,
                "anime_episodes": anime.episodes if anime else None,
            }
        )

    return result


@router.get("/{anime_id}", response_model=UserAnimeResponse)
def get_anime_status(
    anime_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    internal_id = resolve_anime_id(db, anime_id)
    if internal_id is None:
        raise HTTPException(404, "Anime não encontrado")

    user_anime = (
        db.query(UserAnimeStatus)
        .filter(
            UserAnimeStatus.user_id == current_user.id,
            UserAnimeStatus.anime_id == internal_id,
        )
        .first()
    )

    if not user_anime:
        raise HTTPException(404, "Anime não encontrado na sua lista")

    anime = db.query(Anime).filter(Anime.id == internal_id).first()

    return {
        "id": user_anime.id,
        "user_id": user_anime.user_id,
        "anime_id": user_anime.anime_id,
        "external_id": anime.external_id if anime else None,
        "status": user_anime.status,
        "score": user_anime.score,
        "notes": user_anime.notes,
        "updated_at": user_anime.updated_at,
        "anime_title": anime.title if anime else None,
        "anime_cover": anime.cover_image_url if anime else None,
        "anime_episodes": anime.episodes if anime else None,
    }


@router.put("/{anime_id}", response_model=UserAnimeResponse)
def update_anime_status(
    anime_id: int,
    data: UserAnimeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    internal_id = resolve_anime_id(db, anime_id)
    if internal_id is None:
        raise HTTPException(404, "Anime não encontrado")

    user_anime = (
        db.query(UserAnimeStatus)
        .filter(
            UserAnimeStatus.user_id == current_user.id,
            UserAnimeStatus.anime_id == internal_id,
        )
        .first()
    )

    if not user_anime:
        raise HTTPException(404, "Anime não encontrado na sua lista")

    if data.status is not None:
        user_anime.status = data.status
    if data.score is not None:
        user_anime.score = data.score
    if data.notes is not None:
        user_anime.notes = data.notes

    db.commit()
    db.refresh(user_anime)

    anime = db.query(Anime).filter(Anime.id == internal_id).first()

    return {
        "id": user_anime.id,
        "user_id": user_anime.user_id,
        "anime_id": user_anime.anime_id,
        "external_id": anime.external_id if anime else None,
        "status": user_anime.status,
        "score": user_anime.score,
        "notes": user_anime.notes,
        "updated_at": user_anime.updated_at,
        "anime_title": anime.title if anime else None,
        "anime_cover": anime.cover_image_url if anime else None,
        "anime_episodes": anime.episodes if anime else None,
    }


@router.delete("/{anime_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_anime_from_list(
    anime_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    internal_id = resolve_anime_id(db, anime_id)
    if internal_id is None:
        raise HTTPException(404, "Anime não encontrado na sua lista")

    user_anime = (
        db.query(UserAnimeStatus)
        .filter(
            UserAnimeStatus.user_id == current_user.id,
            UserAnimeStatus.anime_id == internal_id,
        )
        .first()
    )

    if not user_anime:
        raise HTTPException(404, "Anime não encontrado na sua lista")

    db.delete(user_anime)
    db.commit()

    return None
