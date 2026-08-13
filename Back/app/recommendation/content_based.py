from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models import Anime
from app.services.anilist_service import AniListService


class ContentBasedRecommender:

    def __init__(self, db: Session):
        self.db = db
        self.tfidf = TfidfVectorizer(stop_words="english", max_features=5000)
        self.anime_vectors = None
        self.anime_ids = None
        self.titles = None
        self.anime_cache = {}  # Cache para dados do AniList

    def _fetch_anime_from_anilist(self, anime_id: int):
        if anime_id in self.anime_cache:
            return self.anime_cache[anime_id]

        with AniListService() as service:
            result = service.search_anime_by_id(anime_id)
            if result:
                self.anime_cache[anime_id] = result
            return result

    def _get_anime_data(self):
        animes = self.db.query(Anime).all()

        data = []
        for anime in animes:

            genres_text = " ".join([g.name for g in anime.genres])
            synopsis = anime.synopsis or ""
            text = f"{genres_text} {genres_text} {synopsis}"

            data.append(
                {
                    "id": anime.id,
                    "title": anime.title,
                    "text": text,
                    "genres": genres_text,
                    "synopsis": synopsis[:500],
                    "year": anime.release_year,
                }
            )

        return pd.DataFrame(data)

    def fit(self) -> bool:
        df = self._get_anime_data()
        if df.empty:
            return False

        self.anime_ids = df["id"].values
        self.titles = df["title"].values
        self.anime_vectors = self.tfidf.fit_transform(df["text"].values)
        return True

    def recommend_by_anime(self, anime_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        if self.anime_vectors is None:
            self.fit()

        if self.anime_vectors is None:
            return []

        index = np.where(self.anime_ids == anime_id)[0]
        if len(index) == 0:
            return []
        idx = index[0]

        similarities = cosine_similarity(
            self.anime_vectors[idx], self.anime_vectors
        ).flatten()

        similar_indices = similarities.argsort()[-top_n - 1 : -1][::-1]

        results = []
        for i in similar_indices:
            if self.anime_ids[i] != anime_id:
                anime_id = int(self.anime_ids[i])
                anime = self.db.query(Anime).filter(Anime.id == anime_id).first()

                if similarities[i] > 0.1:
                    results.append(
                        {
                            "id": int(self.anime_ids[i]),
                            "title": self.titles[i],
                            "similarity": float(similarities[i]),
                            "cover": anime.cover_image_url if anime else None,
                            "year": anime.release_year if anime else None,
                        }
                    )

        return results
