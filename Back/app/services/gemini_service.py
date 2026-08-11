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
        prompt = fprompt = f"""
            Você é um assistente que traduz pedidos de usuários em filtros estruturados para busca de animes na API AniList.

            Descrição do usuário: "{description}"

            Retorne um JSON VÁLIDO com os seguintes campos:

            1. "search": termo de busca (título específico) ou null
            - Se o usuário mencionar um título específico com "parecido com", "como", "algo como", "tipo", extraia o título.
            - Exemplo: "algo como Code Geass" → "search": "Code Geass"

            2. "genres": lista de gêneros (Action, Adventure, Comedy, Drama, Fantasy, Horror, Mystery, Romance, Sci-Fi, Sports, Supernatural, Thriller, Psychological, Slice of Life, Mecha, Ecchi, Music, School, Shounen, Shoujo, Space, Vampire)

            3. "excluded_genres": lista de gêneros a EXCLUIR

            4. "min_year": ano mínimo de lançamento (int) ou null

            5. "max_year": ano máximo de lançamento (int) ou null

            6. "min_score": nota mínima, escala 0-100 (int) ou null

            7. "max_score": nota máxima, escala 0-100 (int) ou null

            8. "status": FINISHED, RELEASING, NOT_YET_RELEASED, CANCELLED, HIATUS, ou null

            9. "formats": lista de formatos (TV, MOVIE, OVA, ONA, SPECIAL) ou lista vazia

            10. "excluded_formats": lista de formatos a EXCLUIR

            11. "country": código de país (ex: "JP") ou null

            12. "source": ORIGINAL, MANGA, LIGHT_NOVEL, VISUAL_NOVEL, VIDEO_GAME, OTHER, ou null

            13. "min_episodes": número mínimo de episódios (int) ou null

            14. "max_episodes": número máximo de episódios (int) ou null

            15. "is_adult": true/false se mencionar conteúdo adulto, ou null

            16. "description_en": a descrição do usuário traduzida para inglês

            17. "keywords": lista de palavras-chave relevantes (até 5) que descrevem temas, estilos, ou características subjetivas
                - Exemplos: "protagonista inteligente", "estratégia", "mundo pós-apocalíptico", "anti-herói", "reviravoltas"

            18. "tags": lista de tags do AniList que se aplicam à descrição
                - Mapeie palavras-chave para tags disponíveis:
                - "protagonista inteligente" → "Genius Protagonist", "Tactician"
                - "estratégia" → "Tactician", "Strategy"
                - "anti-herói" → "Anti-Hero"
                - "psicológico" → "Psychological"
                - "mundo pós-apocalíptico" → "Post-Apocalyptic"
                - "mecha" → "Mecha"
                - Use no máximo 3 tags.

            Regras:
            - Só preencha um filtro se o usuário mencionou algo que mapeia CLARAMENTE para ele.
            - "Estética dos anos 90" → min_year: 1990, max_year: 1999.
            - "protagonista inteligente" → keywords: ["protagonista inteligente"], tags: ["Genius Protagonist"].

            Exemplos:

            Exemplo 1:
            "Quero animes com arte visual dos anos 90"
            → {{"search": null, "genres": [], "excluded_genres": [], "min_year": 1990, "max_year": 1999, "min_score": null, "max_score": null, "status": null, "formats": [], "excluded_formats": [], "country": null, "source": null, "min_episodes": null, "max_episodes": null, "is_adult": null, "description_en": "I want anime with 90s visual art style", "keywords": ["arte visual", "retro"], "tags": ["Retro"]}}

            Exemplo 2:
            "Quero animes de ação com fantasia, sem romance, bem avaliados"
            → {{"search": null, "genres": ["Action", "Fantasy"], "excluded_genres": ["Romance"], "min_year": null, "max_year": null, "min_score": 75, "max_score": null, "status": null, "formats": [], "excluded_formats": [], "country": null, "source": null, "min_episodes": null, "max_episodes": null, "is_adult": null, "description_en": "I want action fantasy anime, no romance, highly rated", "keywords": [], "tags": []}}

            Exemplo 3:
            "algo como Code Geass, com protagonista inteligente"
            → {{"search": "Code Geass", "genres": ["Action", "Drama", "Sci-Fi"], "excluded_genres": [], "min_year": null, "max_year": null, "min_score": null, "max_score": null, "status": null, "formats": [], "excluded_formats": [], "country": null, "source": null, "min_episodes": null, "max_episodes": null, "is_adult": null, "description_en": "Something like Code Geass, with a smart protagonist", "keywords": ["protagonista inteligente", "estratégia"], "tags": ["Genius Protagonist", "Tactician"]}}

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