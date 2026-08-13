from typing import Any, Dict, List

import requests

from app.services.anilist_service import AniListService


def find_similar_by_genres(
    genres: List[str], exclude_id: int, limit: int = 5, min_score: int = 75
) -> List[Dict[str, Any]]:
    """
    Busca animes similares baseados em gêneros.
    """
    if not genres:
        return []

    query = """
    query ($genres: [String], $excludeId: Int, $limit: Int, $minScore: Int) {
        Page(perPage: $limit) {
            media(
                type: ANIME
                genre_in: $genres
                averageScore_greater: $minScore
                id_not: $excludeId
                sort: POPULARITY_DESC
            ) {
                id
                title { romaji english }
                seasonYear
                genres
                averageScore
                status
                format
                countryOfOrigin
                source
                episodes
                coverImage { large }
                description
            }
        }
    }
    """

    variables = {
        "genres": genres[:5],
        "excludeId": exclude_id,
        "limit": limit,
        "minScore": min_score,
    }

    try:
        response = requests.post(
            AniListService.BASE_URL,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("data", {}).get("Page", {}).get("media", [])

        formatted = []
        for anime in results:
            formatted.append(
                {
                    "id": anime.get("id"),
                    "title": anime.get("title", {}).get("romaji", "N/A"),
                    "title_english": anime.get("title", {}).get("english"),
                    "year": anime.get("seasonYear"),
                    "genres": anime.get("genres", []),
                    "score": anime.get("averageScore"),
                    "status": anime.get("status"),
                    "format": anime.get("format"),
                    "country": anime.get("countryOfOrigin"),
                    "source": anime.get("source"),
                    "episodes": anime.get("episodes"),
                    "cover": anime.get("coverImage", {}).get("large"),
                    "synopsis": anime.get("description"),
                }
            )

        return formatted

    except Exception as e:
        print(f"❌ Erro na busca por similaridade: {e}")
        return []
