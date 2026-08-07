import pandas as pd
from sqlalchemy.orm import Session

from app.models import UserAnimeStatus


def get_user_anime_matrix(db: Session) -> pd.DataFrame:
    records = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.score.isnot(None)
    ).all()
    
    if not records:
        return pd.DataFrame()
    
    data = []
    for r in records:
        data.append({
            "user_id": r.user_id,
            "anime_id": r.anime_id,
            "score": r.score
        })
    
    df = pd.DataFrame(data)
    
    matrix = df.pivot(
        index="user_id",
        columns="anime_id",
        values="score"
    ).fillna(0)
    
    return matrix


def get_user_rated_animes(db: Session, user_id: int) -> dict:
    records = db.query(UserAnimeStatus).filter(
        UserAnimeStatus.user_id == user_id,
        UserAnimeStatus.score.isnot(None)
    ).all()
    
    return {r.anime_id: r.score for r in records}