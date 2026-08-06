import json
import requests
from typing import Dict, Any, Optional
from app.config import settings


class GeminiService:

    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY não configurada")

        self.api_key = settings.gemini_api_key
        self.model = "gemini-flash-latest"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def interpret_query(self, description: str) -> Dict[str, Any]:
        prompt = f"""
            Você é um assistente que traduz pedidos de usuários em filtros estruturados
            para busca de animes na API AniList.

            Descrição do usuário: "{description}"

            Retorne um JSON VÁLIDO com os seguintes campos (use null ou lista vazia
            quando o campo não se aplicar ao pedido — NÃO invente valor):

            1. "search": termo de busca (título específico) ou null
            2. "genres": lista de gêneros, apenas destes valores: Action, Adventure,
            Comedy, Drama, Fantasy, Horror, Mystery, Romance, Sci-Fi, Sports,
            Supernatural, Thriller, Psychological, Slice of Life, Mecha, Ecchi,
            Music, School, Shounen, Shoujo, Space, Vampire
            3. "excluded_genres": lista de gêneros a EXCLUIR (mesmos valores acima)
            4. "min_year": ano mínimo de lançamento (int) ou null
            5. "max_year": ano máximo de lançamento (int) ou null
            6. "min_score": nota mínima, escala 0-100 (int) ou null
            7. "max_score": nota máxima, escala 0-100 (int) ou null
            8. "status": um de FINISHED, RELEASING, NOT_YET_RELEASED, CANCELLED, HIATUS, ou null
            9. "formats": lista contendo TV, MOVIE, OVA, ONA, SPECIAL — ou lista vazia
            10. "excluded_formats": lista de formatos a EXCLUIR — ou lista vazia
            11. "country": código de país (ex: "JP" para Japão) ou null
            12. "source": um de ORIGINAL, MANGA, LIGHT_NOVEL, VISUAL_NOVEL, VIDEO_GAME, OTHER, ou null
            13. "min_episodes": número mínimo de episódios (int) ou null
            14. "max_episodes": número máximo de episódios (int) ou null
            15. "is_adult": true/false se mencionar conteúdo adulto, ou null
            16. "description_en": a descrição do usuário traduzida para inglês, mantendo o sentido

            Regra importante: só preencha um filtro se o usuário mencionou algo que
            mapeia CLARAMENTE para ele. "Estética dos anos 90" vira min_year/max_year,
            não um gênero.

            Exemplo 1:
            "Quero animes com arte visual dos anos 90"
            -> {{"search": null, "genres": [], "excluded_genres": [], "min_year": 1990, "max_year": 1999, "min_score": null, "max_score": null, "status": null, "formats": [], "excluded_formats": [], "country": null, "source": null, "min_episodes": null, "max_episodes": null, "is_adult": null, "description_en": "I want anime with 90s visual art style"}}

            Exemplo 2:
            "Quero animes de ação com fantasia, sem romance, bem avaliados"
            -> {{"search": null, "genres": ["Action", "Fantasy"], "excluded_genres": ["Romance"], "min_year": null, "max_year": null, "min_score": 75, "max_score": null, "status": null, "formats": [], "excluded_formats": [], "country": null, "source": null, "min_episodes": null, "max_episodes": null, "is_adult": null, "description_en": "I want action fantasy anime, no romance, highly rated"}}

            Retorne APENAS o JSON, sem explicações ou formatação extra.
            """

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()

            result = json.loads(text)

            return {
                "search": result.get("search"),
                "genres": result.get("genres", []),
                "excluded_genres": result.get("excluded_genres", []),
                "min_year": result.get("min_year"),
                "max_year": result.get("max_year"),
                "min_score": result.get("min_score"),
                "max_score": result.get("max_score"),
                "status": result.get("status"),
                "formats": result.get("formats", []),
                "excluded_formats": result.get("excluded_formats", []),
                "country": result.get("country"),
                "source": result.get("source"),
                "min_episodes": result.get("min_episodes"),
                "max_episodes": result.get("max_episodes"),
                "is_adult": result.get("is_adult"),
                "description_en": result.get("description_en", description)
            }

        except Exception as e:
            print(f"❌ Erro no Gemini: {e}")
            return {
                "search": None,
                "genres": [],
                "excluded_genres": [],
                "min_year": None,
                "max_year": None,
                "min_score": None,
                "max_score": None,
                "status": None,
                "formats": [],
                "excluded_formats": [],
                "country": None,
                "source": None,
                "min_episodes": None,
                "max_episodes": None,
                "is_adult": None,
                "description_en": description
            }