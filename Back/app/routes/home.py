from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, UserAnimeStatus
from app.recommendation.collaborative import CollaborativeRecommender

router = APIRouter(prefix="/home", tags=["Home"])


@router.get("/dashboard")
def get_home(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    watching = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == current_user.id,
        UserAnimeStatus.status == "watching"
    ).all()
    
    watching_animes = []
    for item in watching:
        anime = db.query(Anime).filter(Anime.id == item.anime_id).first()
        if anime:
            watching_animes.append({
                "id": anime.id,
                "title": anime.title,
                "cover": anime.cover_image_url,
                "status": item.status,
                "score": item.score
            })
    
    recommender = CollaborativeRecommender(db)
    recommendations = recommender.recommend_for_user(current_user.id, top_n=5)
    
    return {
        "watching": watching_animes,
        "recommendations": recommendations,
        "total_watching": len(watching_animes)
    }