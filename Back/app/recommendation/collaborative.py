import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any


def recommend_by_collaborative(
    user_id: int,
    matrix: pd.DataFrame,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    if matrix.empty:
        return []
    
    if user_id not in matrix.index:
        return []
    
    user_row = matrix[matrix.index == user_id].iloc[0]
    if (user_row == 0).all():
        return []
    
    anime_similarity = cosine_similarity(matrix.T)
    anime_similarity_df = pd.DataFrame(
        anime_similarity,
        index=matrix.columns,
        columns=matrix.columns
    )
    
    predictions = {}
    
    for anime_id in matrix.columns:
        if user_row[anime_id] != 0:
            continue
        
        similarities = anime_similarity_df[anime_id]
        
        weighted_sum = 0
        sim_sum = 0
        
        for rated_anime, score in user_row.items():
            if score > 0:
                sim = similarities[rated_anime]
                if sim > 0:
                    weighted_sum += sim * score
                    sim_sum += abs(sim)
        
        if sim_sum > 0:
            predictions[anime_id] = weighted_sum / sim_sum
    
    sorted_predictions = sorted(
        predictions.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    return [
        {
            "anime_id": int(anime_id),
            "predicted_score": round(score, 2)
        }
        for anime_id, score in sorted_predictions
    ]


def get_anime_similarity_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    anime_similarity = cosine_similarity(matrix.T)
    return pd.DataFrame(
        anime_similarity,
        index=matrix.columns,
        columns=matrix.columns
    )