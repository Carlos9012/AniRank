# app/routes/home.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import pandas as pd

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, UserAnimeStatus, Anime
from app.recommendation.collaborative import recommend_by_collaborative

router = APIRouter(prefix="/recommendations", tags=["Recomendações"])


@router.get("/collaborative")
def get_collaborative_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    top_n: int = Query(5, ge=1, le=20),
):
    ratings = db.query(UserAnimeStatus).filter(UserAnimeStatus.score.isnot(None)).all()

    if not ratings:
        raise HTTPException(404, "Nenhum rating encontrado para gerar recomendações.")

    data = []
    for r in ratings:
        data.append({
            "user_id": r.user_id,
            "anime_id": r.anime_id,
            "score": r.score
        })
    df = pd.DataFrame(data)

    matrix = df.pivot_table(index="user_id", columns="anime_id", values="score").fillna(0)

    recommended = recommend_by_collaborative(
        user_id=current_user.id,
        matrix=matrix,
        top_n=top_n
    )

    if not recommended:
        return {"message": "Não foi possível gerar recomendações para este usuário.", "recommendations": []}

    anime_ids = [item["anime_id"] for item in recommended]
    animes = db.query(Anime).filter(Anime.id.in_(anime_ids)).all()
    anime_map = {a.id: a for a in animes}

    result = []
    for rec in recommended:
        anime = anime_map.get(rec["anime_id"])
        if anime:
            result.append({
                "anime_id": anime.id,
                "title": anime.title,
                "year": anime.release_year,
                "cover": anime.cover_image_url,
                "predicted_score": rec["predicted_score"],
            })

    return {"user_id": current_user.id, "recommendations": result}