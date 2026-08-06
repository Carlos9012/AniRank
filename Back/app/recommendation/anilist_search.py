import json
import requests
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import settings


class AniListSearchRecommender:

    BASE_URL = "https://graphql.anilist.co"

    def __init__(self):
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        self.anime_vectors = None
        self.anime_data = None

        self.use_gemini = settings.use_gemini and settings.gemini_api_key is not None
        self.gemini = None

        print(f"🔍 DEBUG: use_gemini = {self.use_gemini}")

        if self.use_gemini:
            try:
                from app.services.gemini_service import GeminiService
                self.gemini = GeminiService()
                print(f"✅ Gemini inicializado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao inicializar Gemini: {e}")
                self.use_gemini = False
                self.gemini = None
        else:
            print(f"⚠️ Gemini DESATIVADO (use_gemini={self.use_gemini})")

    def _fallback_interpretation(self, description: str) -> Dict:
        stopwords = {
            "quero", "gostaria", "procuro", "busco", "um", "uma", "de", "com",
            "para", "os", "as", "que", "me", "eu", "em", "por", "na", "no",
            "da", "do", "se", "mais", "muito", "pouco", "sobre", "entre", "sem"
        }

        words = description.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

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
            "description_en": " ".join(keywords) if keywords else description
        }

    def _build_variables_declaration(self, variables: dict) -> str:
        declarations = []
        for key, value in variables.items():
            if key == "perPage":
                continue
            if isinstance(value, list):
                declarations.append(f"${key}: [String]")
            elif isinstance(value, bool):
                declarations.append(f"${key}: Boolean")
            elif isinstance(value, int):
                declarations.append(f"${key}: Int")
            else:
                declarations.append(f"${key}: String")
        declarations.append("$perPage: Int")
        return ", ".join(declarations)

    MEDIA_TYPE = "ANIME" 

    def _get_media_type_field(self) -> str:
        return f"type: {self.MEDIA_TYPE}"

    def _build_query(self, interpreted: Dict, limit: int) -> tuple:
        query_fields = []
        variables = {"perPage": limit}

        query_fields.append(self._get_media_type_field())

        # 1. search
        if interpreted.get("search"):
            query_fields.append("search: $search")
            variables["search"] = interpreted["search"]

        # 2. genres
        if interpreted.get("genres"):
            query_fields.append("genre_in: $genres")
            variables["genres"] = interpreted["genres"]

        # 3. excluded_genres
        if interpreted.get("excluded_genres"):
            query_fields.append("genre_not_in: $excludedGenres")
            variables["excludedGenres"] = interpreted["excluded_genres"]

        # 4. year
        if interpreted.get("year") is not None:
            query_fields.append("seasonYear: $year")
            variables["year"] = interpreted["year"]
            print(f"📅 Ano: {interpreted['year']}")

        # 5. score_range
        if interpreted.get("min_score") is not None:
            query_fields.append("averageScore_greater: $minScore")
            variables["minScore"] = interpreted["min_score"]
        if interpreted.get("max_score") is not None:
            query_fields.append("averageScore_lesser: $maxScore")
            variables["maxScore"] = interpreted["max_score"]

        # 6. status
        if interpreted.get("status"):
            query_fields.append("status: $status")
            variables["status"] = interpreted["status"]

        # 7. formats
        """if interpreted.get("formats"):
            query_fields.append("format_in: $formats")
            variables["formats"] = interpreted["formats"]
"""
        # 8. excluded_formats
        if interpreted.get("excluded_formats"):
            query_fields.append("format_not_in: $excludedFormats")
            variables["excludedFormats"] = interpreted["excluded_formats"]

        # 9. country
        if interpreted.get("country"):
            query_fields.append("countryOfOrigin: $country")
            variables["country"] = interpreted["country"]

        # 10. source
        if interpreted.get("source"):
            query_fields.append("source: $source")
            variables["source"] = interpreted["source"]

        # 11. episodes_range
        if interpreted.get("min_episodes") is not None:
            query_fields.append("episodes_greater: $minEpisodes")
            variables["minEpisodes"] = interpreted["min_episodes"]
        if interpreted.get("max_episodes") is not None:
            query_fields.append("episodes_lesser: $maxEpisodes")
            variables["maxEpisodes"] = interpreted["max_episodes"]

        # 12. is_adult
        if interpreted.get("is_adult") is not None:
            query_fields.append("isAdult: $isAdult")
            variables["isAdult"] = interpreted["is_adult"]

        query_fields.append("sort: POPULARITY_DESC")

        var_decl = self._build_variables_declaration(variables)
        fields_str = ", ".join(query_fields)

        query = f"""
        query ({var_decl}) {{
            Page(perPage: $perPage) {{
                media(
                    {fields_str}
                ) {{
                    id
                    title {{ romaji english }}
                    seasonYear
                    genres
                    averageScore
                    status
                    format
                    countryOfOrigin
                    source
                    episodes
                    coverImage {{ large }}
                    description
                }}
            }}
        }}
        """

        print(f"📝 Query gerada com filtros: {fields_str}")
        return query, variables

    def _execute_query(self, query: str, variables: dict) -> List[Dict]:
        try:
            payload = {"query": query, "variables": variables}
            response = requests.post(
                self.BASE_URL,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                print(f"❌ Erro na API: {response.status_code} - {response.text[:200]}")
                return []

            data = response.json()
            if "errors" in data:
                print(f"❌ Erro GraphQL: {data['errors']}")
                return []

            return data.get("data", {}).get("Page", {}).get("media", [])

        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return []

    def search_by_year_range(
        self,
        interpreted: Dict,
        limit_per_year: int = 3,
        max_years: int = 10
    ) -> List[Dict]:
        min_year = interpreted.get("min_year")
        max_year = interpreted.get("max_year", min_year)

        if min_year is None:
            return []

        if min_year == max_year:
            interpreted_copy = interpreted.copy()
            interpreted_copy["year"] = min_year
            query, variables = self._build_query(interpreted_copy, limit_per_year)
            return self._execute_query(query, variables)

        years = list(range(min_year, max_year + 1))
        if len(years) > max_years:
            years = years[:max_years]
            print(f"⚠️ Limitando a {max_years} anos")

        all_results = []
        print(f"📅 Buscando {len(years)} anos ({min_year}-{max_year})...")

        for year in years:
            interpreted_copy = interpreted.copy()
            interpreted_copy["year"] = year
            interpreted_copy.pop("min_year", None)
            interpreted_copy.pop("max_year", None)

            query, variables = self._build_query(interpreted_copy, limit_per_year)
            results = self._execute_query(query, variables)

            if results:
                all_results.extend(results)
                print(f"  ✅ Ano {year}: {len(results)} animes encontrados")
            else:
                print(f"  ⚠️ Ano {year}: nenhum anime encontrado")

        print(f"📊 Total: {len(all_results)} animes encontrados")
        return all_results

    def search_by_description(self, description: str, limit: int = 10) -> List[Dict]:
        print("=" * 60)
        print(f"🔍 BUSCA POR DESCRIÇÃO: '{description}'")
        print("=" * 60)

        # CAMADA 1: IA interpreta a descrição
        if self.use_gemini and self.gemini:
            print("🧠 Usando Gemini para interpretar...")
            try:
                interpreted = self.gemini.interpret_query(description)
                print(f"📝 Gemini interpretou:")
                print(json.dumps(interpreted, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"❌ Erro no Gemini: {e}")
                print("⚠️ Usando fallback...")
                interpreted = self._fallback_interpretation(description)
        else:
            print("⚠️ Gemini DESATIVADO. Usando fallback.")
            interpreted = self._fallback_interpretation(description)

        # CAMADA 2: Verifica se há intervalo de anos
        has_year_range = (
            interpreted.get("min_year") is not None and
            interpreted.get("max_year") is not None and
            interpreted["min_year"] != interpreted["max_year"]
        )

        # CAMADA 3: Executa a busca
        if has_year_range:
            limit_per_year = max(1, limit // (interpreted["max_year"] - interpreted["min_year"] + 1))
            results = self.search_by_year_range(
                interpreted,
                limit_per_year=limit_per_year,
                max_years=10
            )
            results = results[:limit]
        else:
            if interpreted.get("min_year") is not None:
                interpreted["year"] = interpreted["min_year"]
                interpreted.pop("min_year", None)
                interpreted.pop("max_year", None)

            query, variables = self._build_query(interpreted, limit)
            results = self._execute_query(query, variables)

        # CAMADA 4: Formatar resultados
        formatted_results = []
        for anime in results:
            formatted_results.append({
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
                "synopsis": anime.get("description")
            })

        print(f"📦 Total de resultados: {len(formatted_results)}")
        return formatted_results