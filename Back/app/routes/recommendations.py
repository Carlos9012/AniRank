from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Anime, User, UserAnimeStatus
from app.recommendation.anilist_search import AniListSearchRecommender
from app.recommendation.anilist_similar import find_similar_by_genres
from app.recommendation.collaborative import recommend_by_collaborative
from app.recommendation.data_prep import get_user_anime_matrix
from app.services.anilist_service import AniListService

COLLAB_AVAILABLE = True

router = APIRouter(prefix="/recommendations", tags=["Recomendações"])


@router.post("/by-description")
def recommend_by_description(
    description: str = Query(..., description="Descrição do que você procura"),
    limit: int = Query(5, ge=1, le=50, description="Quantidade de resultados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not description or len(description.strip()) < 3:
        raise HTTPException(400, "Descrição muito curta.")

    recommender = AniListSearchRecommender()
    results = recommender.search_by_description(description, limit=limit)

    if not results:
        return {
            "description": description,
            "recommendations": [],
            "message": "Nenhum anime encontrado para esta descrição",
        }

    return {
        "description": description,
        "recommendations": results,
        "count": len(results),
        "method": "API AniList + Gemini (interpretação de intenção)",
    }


@router.get("/by-anime/{external_id}")
def recommend_by_anime(
    external_id: int,
    limit: int = Query(5, ge=1, le=20),
    min_score: int = Query(75, ge=0, le=100, description="Nota mínima"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        with AniListService() as service:
            source_anime = service.search_anime_by_id(external_id)

            if not source_anime:
                raise HTTPException(
                    404, f"Anime com ID {external_id} não encontrado no AniList"
                )

        title = source_anime.get("title", {}).get("romaji", "N/A")
        genres = source_anime.get("genres", [])

        if not genres:
            return {
                "source": {"id": external_id, "title": title},
                "recommendations": [],
                "message": "Este anime não tem gêneros para buscar similares.",
                "method": "AniList API",
            }

        recommendations = find_similar_by_genres(
            genres=genres, exclude_id=external_id, limit=limit, min_score=min_score
        )

        if not recommendations:
            return {
                "source": {
                    "id": external_id,
                    "title": title,
                    "genres": genres,
                    "year": source_anime.get("seasonYear"),
                    "score": source_anime.get("averageScore"),
                    "cover": source_anime.get("coverImage", {}).get("large"),
                },
                "recommendations": [],
                "message": "Nenhum anime similar encontrado.",
                "method": "AniList API",
            }

        return {
            "source": {
                "id": external_id,
                "title": title,
                "title_english": source_anime.get("title", {}).get("english"),
                "year": source_anime.get("seasonYear"),
                "genres": genres,
                "score": source_anime.get("averageScore"),
                "status": source_anime.get("status"),
                "format": source_anime.get("format"),
                "cover": source_anime.get("coverImage", {}).get("large"),
            },
            "recommendations": recommendations,
            "count": len(recommendations),
            "message": f"Animes similares a '{title}'",
            "method": "AniList API (busca por gêneros similares)",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise HTTPException(500, f"Erro ao buscar recomendações: {str(e)}")


def _get_rated_genres(db: Session, rated_animes: list) -> set:
    """Calcula, em uma única consulta, o conjunto de gêneros que o usuário
    já avaliou — antes repetido a cada anime candidato dentro do loop."""
    rated_ids = [ua.anime_id for ua in rated_animes]
    rated_anime_objs = db.query(Anime).filter(Anime.id.in_(rated_ids)).all()

    rated_genres = set()
    for anime in rated_anime_objs:
        if anime.genres:
            rated_genres.update(g.name for g in anime.genres)
    return rated_genres


def _score_candidate(anime: Anime, rated_genres: set, avg_score: float) -> dict:
    """Calcula nota prevista e gêneros em comum para um único anime candidato."""
    anime_genres = {g.name for g in anime.genres} if anime.genres else set()
    common_genres = len(anime_genres & rated_genres)

    bonus = min(common_genres * 0.3, 1.5)
    predicted_score = round(min(avg_score + bonus, 10), 1)

    return {
        "id": anime.id,
        "title": anime.title,
        "cover": anime.cover_image_url,
        "year": anime.release_year,
        "genres": list(anime_genres),
        "predicted_score": predicted_score,
        "common_genres": common_genres,
    }


@router.get("/personalized")
def get_personalized_recommendations(
    limit: int = Query(5, ge=1, le=20, description="Número de recomendações"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_animes = (
            db.query(UserAnimeStatus)
            .filter(UserAnimeStatus.user_id == current_user.id)
            .all()
        )
        if not user_animes:
            return _empty_response(
                current_user.id,
                "Adicione animes à sua lista para receber recomendações",
            )

        rated_animes = [ua for ua in user_animes if ua.score is not None]
        if not rated_animes:
            return _empty_response(
                current_user.id,
                "Adicione notas aos animes da sua lista para receber recomendações",
            )

        rated_ids = [ua.anime_id for ua in rated_animes]
        recommended_animes = (
            db.query(Anime)
            .filter(Anime.id.notin_(rated_ids))
            .order_by(Anime.external_id.desc())
            .limit(limit * 2)
            .all()
        )
        if not recommended_animes:
            return _empty_response(
                current_user.id, "Você já avaliou todos os animes disponíveis!"
            )

        avg_score = sum(ua.score for ua in rated_animes) / len(rated_animes)
        rated_genres = _get_rated_genres(db, rated_animes)  # UMA consulta, fora do loop

        recommendations = []
        for anime in recommended_animes[:limit]:
            scored = _score_candidate(anime, rated_genres, avg_score)
            scored["reason"] = (
                f"Baseado em {len(rated_ids)} animes que você avaliou (média: {avg_score:.1f})"
            )
            recommendations.append(scored)

        return {
            "user_id": current_user.id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "total_rated": len(rated_ids),
            "average_score": round(avg_score, 1),
            "method": "simplificado (baseado em gêneros e média)",
            "message": f"Recomendações baseadas em {len(rated_ids)} animes avaliados",
        }

    except Exception as e:
        print(f"❌ ERRO NA RECOMENDAÇÃO: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar recomendações: {str(e)}"
        )


def _empty_response(user_id: int, message: str) -> dict:
    return {
        "user_id": user_id,
        "recommendations": [],
        "count": 0,
        "message": message,
        "method": "simplificado",
    }


@router.get("/personalized/collaborative")
def get_collaborative_recommendations(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not COLLAB_AVAILABLE:
        return {
            "user_id": current_user.id,
            "recommendations": [],
            "count": 0,
            "message": "Collaborative filtering não está disponível. Use /personalized para versão estável.",
            "method": "indisponível",
        }

    try:
        matrix = get_user_anime_matrix(db)

        if matrix.empty:
            return {
                "user_id": current_user.id,
                "recommendations": [],
                "count": 0,
                "message": "Nenhum dado de avaliação disponível",
                "method": "collaborative filtering",
            }

        if current_user.id not in matrix.index:
            return {
                "user_id": current_user.id,
                "recommendations": [],
                "count": 0,
                "message": "Adicione animes com notas para receber recomendações",
                "method": "collaborative filtering",
            }

        user_row = matrix[matrix.index == current_user.id].iloc[0]
        rated_count = (user_row > 0).sum()

        if rated_count == 0:
            return {
                "user_id": current_user.id,
                "recommendations": [],
                "count": 0,
                "message": "Você ainda não avaliou nenhum anime",
                "method": "collaborative filtering",
            }

        collab_results = recommend_by_collaborative(
            user_id=current_user.id, matrix=matrix, top_n=limit
        )

        if not collab_results:
            return {
                "user_id": current_user.id,
                "recommendations": [],
                "count": 0,
                "message": "Não foi possível gerar recomendações com os dados atuais",
                "method": "collaborative filtering",
            }

        anime_ids = [r["anime_id"] for r in collab_results]
        animes = db.query(Anime).filter(Anime.id.in_(anime_ids)).all()
        anime_dict = {a.id: a for a in animes}

        recommendations = []
        for r in collab_results:
            anime = anime_dict.get(r["anime_id"])
            if anime:
                recommendations.append(
                    {
                        "id": anime.id,
                        "title": anime.title,
                        "cover": anime.cover_image_url,
                        "year": anime.release_year,
                        "genres": (
                            [g.name for g in anime.genres] if anime.genres else []
                        ),
                        "predicted_score": r["predicted_score"],
                        "reason": f"Baseado em {rated_count} animes que você avaliou",
                    }
                )

        return {
            "user_id": current_user.id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "total_rated": rated_count,
            "method": "collaborative filtering (item-based)",
            "message": f"Recomendações baseadas em {rated_count} animes avaliados",
        }

    except Exception as e:
        print(f"❌ ERRO NO COLLABORATIVE: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Erro no collaborative filtering: {str(e)}"
        )
