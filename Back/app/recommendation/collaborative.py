import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models import User, Anime, UserAnimeStatus


class CollaborativeRecommender:
    
    def __init__(self, db: Session):
        self.db = db
    
    def _build_user_anime_matrix(self):
        records = self.db.query(UserAnimeStatus).filter(
            UserAnimeStatus.score.isnot(None)
        ).all()
        
        if not records:
            return pd.DataFrame(), []
        
        data = []
        anime_ids = set()
        for r in records:
            data.append({
                "user_id": r.user_id,
                "anime_id": r.anime_id,
                "score": r.score
            })
            anime_ids.add(r.anime_id)
        
        df = pd.DataFrame(data)
        
        matrix = df.pivot(index="user_id", columns="anime_id", values="score").fillna(0)
        
        return matrix, list(anime_ids)
    
    def recommend_for_user(self, user_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        matrix, anime_ids = self._build_user_anime_matrix()
        
        if matrix.empty:
            return []
        
        anime_similarity = cosine_similarity(matrix.T)
        anime_similarity_df = pd.DataFrame(
            anime_similarity,
            index=matrix.columns,
            columns=matrix.columns
        )
        
        user_row = matrix[matrix.index == user_id]
        if user_row.empty:
            return []
        
        user_scores = user_row.iloc[0]
        
        predictions = {}
        for anime_id in anime_ids:
            if user_scores[anime_id] == 0:
                similarities = anime_similarity_df[anime_id]
                weighted_sum = 0
                sim_sum = 0
                
                for rated_anime, score in user_scores.items():
                    if score > 0:
                        sim = similarities[rated_anime]
                        weighted_sum += sim * score
                        sim_sum += abs(sim)
                
                if sim_sum > 0:
                    predictions[anime_id] = weighted_sum / sim_sum
        
        sorted_predictions = sorted(
            predictions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        results = []
        for anime_id, predicted_score in sorted_predictions:
            anime = self.db.query(Anime).filter(Anime.id == anime_id).first()
            if anime:
                results.append({
                    "id": anime.id,
                    "title": anime.title,
                    "predicted_score": round(predicted_score, 2),
                    "cover": anime.cover_image_url
                })
        
        return results