import json
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from app.config import settings


class GeminiService:
    
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY não configurada")
        
        # Novo SDK
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-1.5-flash"
    
    def interpret_query(self, description: str) -> Dict[str, Any]:
        """
        Interpreta a descrição do usuário e extrai: gêneros, anos, estilos.
        """
        prompt = f"""
        Você é um assistente de recomendação de animes.
        
        Analise a seguinte descrição e extraia as informações relevantes.
        
        Descrição: "{description}"
        
        Retorne um JSON VÁLIDO com:
        1. "genres": lista de gêneros (use apenas: Action, Adventure, Comedy, Drama, Fantasy, Horror, Mystery, Romance, Sci-Fi, Sports, Supernatural, Thriller, Psychological)
        2. "year_range": null ou {{"min": ano_inicial, "max": ano_final}} (se mencionar anos ou décadas)
        3. "keywords": lista de palavras-chave relevantes (até 5)
        4. "search_query": uma frase curta (até 5 palavras) para buscar na API
        5. "style": estilo visual/artístico (se mencionado)
        
        Exemplo 1:
        "Quero animes com arte visual dos anos 90"
        -> {{"genres": [], "year_range": {{"min": 1990, "max": 1999}}, "keywords": ["arte visual", "retro"], "search_query": "arte visual anos 90", "style": "retro"}}
        
        Exemplo 2:
        "Quero animes de ação com fantasia"
        -> {{"genres": ["Action", "Fantasy"], "year_range": null, "keywords": ["ação", "fantasia"], "search_query": "ação fantasia", "style": null}}
        
        Retorne APENAS o JSON, sem explicações ou formatação extra.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            text = response.text.strip()
            
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(text)
            
            return {
                "genres": data.get("genres", []),
                "year_range": data.get("year_range", None),
                "keywords": data.get("keywords", []),
                "search_query": data.get("search_query", description[:50]),
                "style": data.get("style", None)
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao parsear JSON: {e}")
            print(f"Resposta recebida: {text[:200]}...")
            # Fallback
            return {
                "genres": [],
                "year_range": None,
                "keywords": [],
                "search_query": description[:50],
                "style": None
            }
        except Exception as e:
            print(f"❌ Erro no Gemini: {e}")
            return {
                "genres": [],
                "year_range": None,
                "keywords": [],
                "search_query": description[:50],
                "style": None
            }