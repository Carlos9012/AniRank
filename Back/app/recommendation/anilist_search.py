import json
from typing import Dict, List

import requests
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import settings

_SIMPLE_FILTERS = [
    ("genres", "genre_in: $genres", "genres"),
    ("tags", "tag_in: $tags", "tags"),
    ("excluded_genres", "genre_not_in: $excludedGenres", "excludedGenres"),
    ("year", "seasonYear: $year", "year"),
    ("min_score", "averageScore_greater: $minScore", "minScore"),
    ("max_score", "averageScore_lesser: $maxScore", "maxScore"),
    ("status", "status: $status", "status"),
    ("country", "countryOfOrigin: $country", "country"),
    ("source", "source: $source", "source"),
    ("min_episodes", "episodes_greater: $minEpisodes", "minEpisodes"),
    ("max_episodes", "episodes_lesser: $maxEpisodes", "maxEpisodes"),
    ("is_adult", "isAdult: $isAdult", "isAdult"),
]


class AniListSearchRecommender:
    BASE_URL = "https://graphql.anilist.co"

    def __init__(self):
        self.tfidf = TfidfVectorizer(stop_words="english", max_features=5000)
        self.anime_vectors = None
        self.anime_data = None

        self.use_gemini = settings.use_gemini and settings.gemini_api_key is not None
        self.gemini = None

        print(f"🔍 DEBUG: use_gemini = {self.use_gemini}")

        if self.use_gemini:
            try:
                from app.services.gemini_service import GeminiService

                self.gemini = GeminiService()
                print("✅ Gemini inicializado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao inicializar Gemini: {e}")
                self.use_gemini = False
                self.gemini = None
        else:
            print(f"⚠️ Gemini DESATIVADO (use_gemini={self.use_gemini})")

    def _fallback_interpretation(self, description: str) -> Dict:
        stopwords = {
            "quero",
            "gostaria",
            "procuro",
            "busco",
            "um",
            "uma",
            "de",
            "com",
            "para",
            "os",
            "as",
            "que",
            "me",
            "eu",
            "em",
            "por",
            "na",
            "no",
            "da",
            "do",
            "se",
            "mais",
            "muito",
            "pouco",
            "sobre",
            "entre",
            "sem",
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
            "description_en": " ".join(keywords) if keywords else description,
        }

    def _build_variables_declaration(self, variables: dict) -> str:
        declarations = []

        for key, value in variables.items():
            if key == "perPage":
                continue

            if key == "allowedFormats":
                declarations.append(f"${key}: [MediaFormat]")
                continue

            if isinstance(value, list):
                if value and isinstance(value[0], int):
                    declarations.append(f"${key}: [Int]")
                else:
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

    def _filter_by_franchise(self, results: List[Dict], limit: int = 5) -> List[Dict]:
        if not results:
            return []

        sequel_keywords = [
            "Season",
            "Part",
            "Chapter",
            "Arc",
            "Final",
            "NEW",
            "BorN",
            "Hero",
            "2",
            "3",
            "4",
            "5",
            "II",
            "III",
            "IV",
            "V",
            "Shippuuden",
            "Z",
            "GT",
            "Super",
            "Remake",
            "Reboot",
        ]

        franchise_map = {}

        for anime in results:
            title = anime.get("title", "")

            base_title = title
            for keyword in sequel_keywords:
                if keyword in title:
                    parts = title.split(keyword)
                    base_title = parts[0].strip()
                    break

            if base_title == title:
                base_title = title

            if base_title not in franchise_map:
                franchise_map[base_title] = anime
            else:
                current_score = franchise_map[base_title].get("score", 0)
                new_score = anime.get("score", 0)
                if new_score > current_score:
                    franchise_map[base_title] = anime

        results = list(franchise_map.values())[:limit]
        print(f"📦 Após filtro de franquia: {len(results)} animes únicos")
        return results

    def _apply_simple_filters(self, interpreted: Dict, query_fields: list, variables: dict) -> None:
        for key, field_template, var_name in _SIMPLE_FILTERS:
            value = interpreted.get(key)
            if value is not None and value != "":
                query_fields.append(field_template)
                variables[var_name] = value

    def _build_query(self, interpreted: Dict, limit: int) -> tuple:
        query_fields = [self._get_media_type_field()]
        variables = {"perPage": limit}

        self._apply_simple_filters(interpreted, query_fields, variables)
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
        return query, variables

    def _execute_query(self, query: str, variables: dict) -> List[Dict]:
        try:
            payload = {"query": query, "variables": variables}
            response = requests.post(self.BASE_URL, json=payload, timeout=30)

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
        self, interpreted: Dict, limit_per_year: int = 3, max_years: int = 10
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

        has_year_range = (
            interpreted.get("min_year") is not None
            and interpreted.get("max_year") is not None
            and interpreted["min_year"] != interpreted["max_year"]
        )

        if has_year_range:
            limit_per_year = max(
                1, limit // (interpreted["max_year"] - interpreted["min_year"] + 1)
            )
            results = self.search_by_year_range(
                interpreted, limit_per_year=limit_per_year, max_years=10
            )
            results = results[:limit]
        else:
            if interpreted.get("min_year") is not None:
                interpreted["year"] = interpreted["min_year"]
                interpreted.pop("min_year", None)
                interpreted.pop("max_year", None)

            query, variables = self._build_query(interpreted, limit)
            results = self._execute_query(query, variables)

        formatted_results = []
        for anime in results:
            formatted_results.append(
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

        filtered_results = self._filter_by_franchise(formatted_results, limit)

        print(f"📦 Total de resultados: {len(formatted_results)}")
        print(f"📦 Após filtro de franquia: {len(filtered_results)}")

        return filtered_results