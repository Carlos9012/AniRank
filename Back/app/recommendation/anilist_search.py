import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional

from app.services.anilist_service import AniListService
from app.config import settings


class AniListSearchRecommender:
    
    def __init__(self):
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        self.anime_vectors = None
        self.anime_data = None
        
        # Configuração do Gemini
        self.use_gemini = settings.use_gemini and settings.gemini_api_key is not None
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
            self.gemini = None

    def _clean_value(self, value):
        if pd.isna(value):
            return None
        if isinstance(value, (np.integer, np.int64)):
            return int(value)
        if isinstance(value, (np.floating, np.float64)):
            return float(value) if not np.isnan(value) else None
        return value
    
    def _extract_keywords(self, description: str, max_keywords: int = 5) -> str:
        stopwords = {
            "quero", "gostaria", "procuro", "busco", "um", "uma", 
            "de", "com", "para", "os", "as", "que", "me", "eu", 
            "em", "por", "na", "no", "da", "do", "se", "mais", 
            "muito", "pouco", "sobre", "entre", "sem"
        }
        
        words = description.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        if not keywords:
            return description[:50]
        
        result = " ".join(keywords[:max_keywords])
        print(f"🔑 Palavras-chave extraídas (fallback): '{result}'")
        return result
    
    def _fetch_animes_from_api(self, query: str, limit: int = 50) -> List[Dict]:
        print(f"🌐 Buscando na API com query: '{query}'")
        with AniListService() as service:
            results = service.search_anime(query, per_page=limit)
        print(f"📦 API retornou {len(results)} resultados")
        return results
    
    def _prepare_data(self, animes: List[Dict]) -> pd.DataFrame:
        data = []
        for anime in animes:
            genres_text = " ".join(anime.get("genres", []))
            synopsis = anime.get("description", "") or ""
            text = f"{genres_text} {synopsis}"
            
            data.append({
                "id": anime["id"],
                "title": anime["title"]["romaji"],
                "text": text,
                "genres": genres_text,
                "year": anime.get("seasonYear"),
                "cover": anime.get("coverImage", {}).get("large"),
                "status": anime.get("status")
            })
        
        return pd.DataFrame(data)
    
    def search_by_description(self, description: str, limit: int = 10) -> List[Dict]:
        print("=" * 60)
        print(f"🔍 BUSCA POR DESCRIÇÃO: '{description}'")
        print("=" * 60)
        
        # CAMADA 1: Interpretação (Gemini ou fallback)
        if self.use_gemini and self.gemini:
            print("🧠 Usando Gemini para interpretar...")
            try:
                interpreted = self.gemini.interpret_query(description)
                print(f"📝 Gemini interpretou:")
                print(json.dumps(interpreted, indent=2, ensure_ascii=False))
                
                search_query = interpreted.get("search_query", description[:50])
                genres = interpreted.get("genres", [])
                year_range = interpreted.get("year_range", None)
                style = interpreted.get("style", None)
                
            except Exception as e:
                print(f"❌ Erro no Gemini: {e}")
                print(f"⚠️ Usando fallback...")
                search_query = self._extract_keywords(description)
                genres = []
                year_range = None
                style = None
        else:
            print(f"⚠️ Gemini DESATIVADO. Usando fallback.")
            search_query = self._extract_keywords(description)
            genres = []
            year_range = None
            style = None
        
        print(f"🔑 Query final para API: '{search_query}'")
        if genres:
            print(f"🏷️ Gêneros filtrados: {genres}")
        if year_range:
            print(f"📅 Filtro de ano: {year_range}")
        
        # CAMADA 2: Busca na API do AniList
        animes = self._fetch_animes_from_api(search_query, limit=50)
        
        if not animes:
            print(f"❌ Nenhum resultado da API")
            return []
        
        print(f"📦 {len(animes)} animes retornados da API")
        
        # CAMADA 3: Filtros (se tiver gêneros ou anos)
        if genres:
            print(f"🏷️ Aplicando filtro de gêneros: {genres}")
            animes = [a for a in animes if any(g in a.get("genres", []) for g in genres)]
            print(f"📦 {len(animes)} após filtro de gêneros")
        
        if year_range and year_range.get("min"):
            print(f"📅 Aplicando filtro de ano: {year_range}")
            animes = [
                a for a in animes 
                if a.get("seasonYear") and year_range["min"] <= a["seasonYear"] <= year_range.get("max", 9999)
            ]
            print(f"📦 {len(animes)} após filtro de ano")
        
        if not animes:
            print(f"❌ Nenhum resultado após filtros")
            return []
        
        # CAMADA 4: Similaridade (TF-IDF)
        print(f"🧮 Calculando similaridade com TF-IDF...")
        df = self._prepare_data(animes)
        
        if df.empty:
            return []
        
        vectors = self.tfidf.fit_transform(df["text"].values)
        query_vector = self.tfidf.transform([description])
        
        similarities = cosine_similarity(query_vector, vectors).flatten()
        top_indices = similarities.argsort()[-limit:][::-1]
        
        print(f"📊 Similaridades calculadas:")
        for i in top_indices:
            print(f"   - {df.iloc[i]['title']}: {similarities[i]:.4f}")
        
        results = []
        for i in top_indices:
            result = {
                "id": int(df.iloc[i]["id"]),
                "title": df.iloc[i]["title"],
                "similarity": float(similarities[i]),
                "year": df.iloc[i]["year"],
                "cover": df.iloc[i]["cover"],
                "genres": df.iloc[i]["genres"],
                "status": df.iloc[i]["status"]
            }
            
            if self.use_gemini:
                result["interpreted"] = {
                    "genres": genres,
                    "year_range": year_range,
                    "style": style
                }
            
            results.append({
                "id": int(df.iloc[i]["id"]),
                "title": df.iloc[i]["title"],
                "similarity": float(similarities[i]) if not np.isnan(similarities[i]) else 0.0,
                "year": int(df.iloc[i]["year"]) if pd.notna(df.iloc[i]["year"]) else None,
                "cover": df.iloc[i]["cover"] if pd.notna(df.iloc[i]["cover"]) else None,
                "genres": df.iloc[i]["genres"] if pd.notna(df.iloc[i]["genres"]) else "",
                "status": df.iloc[i]["status"] if pd.notna(df.iloc[i]["status"]) else None
            })
        
        print(f"✅ Retornando {len(results)} recomendações")
        print("=" * 60)
        return results
