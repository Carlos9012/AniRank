import httpx
from typing import List, Dict, Any, Optional
from app.models import Anime, Genre, AiringStatus, MediaFormat, MediaSource
from app.database import SessionLocal

class AniListService:
    BASE_URL = "https://graphql.anilist.co"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def _parse_airing_status(self, status: str) -> Optional[AiringStatus]:
        mapping = {
            "FINISHED": AiringStatus.finished,
            "RELEASING": AiringStatus.releasing,
            "NOT_YET_RELEASED": AiringStatus.not_yet_released,
            "CANCELLED": AiringStatus.cancelled,
            "HIATUS": AiringStatus.hiatus,
        }
        return mapping.get(status)

    def _parse_media_format(self, format_str: str) -> Optional[MediaFormat]:
        mapping = {
            "TV": MediaFormat.TV,
            "TV_SHORT": MediaFormat.TV_SHORT,
            "MOVIE": MediaFormat.MOVIE,
            "OVA": MediaFormat.OVA,
            "SPECIAL": MediaFormat.SPECIAL,
            "ONA": MediaFormat.ONA,  
        }
        return mapping.get(format_str)


    def _parse_media_source(self, source_str: str) -> Optional[MediaSource]:
        mapping = {
            "ORIGINAL": MediaSource.ORIGINAL,
            "ANIME": MediaSource.ANIME,
        }
        return mapping.get(source_str)
    
    def get_popular_anime(self, per_page: int = 50) -> List[Dict[str, Any]]:
        query = """
        query ($perPage: Int) {
            Page(perPage: $perPage) {
                media(type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title { romaji english native }
                    description
                    episodes
                    seasonYear
                    coverImage { large }
                    status
                    genres
                }
            }
        }
        """
        response = self.client.post(
            self.BASE_URL,
            json={"query": query, "variables": {"perPage": min(per_page, 50)}}
        )
        response.raise_for_status()
        return response.json().get("data", {}).get("Page", {}).get("media", [])
    
    # app/services/anilist_service.py

    def save_anime_to_db(self, anime_data: Dict[str, Any]) -> Optional[int]:
        db = SessionLocal()
        try:
            existing = db.query(Anime).filter(Anime.external_id == anime_data["id"]).first()
            if existing:
                print(f"ℹ️ Anime {anime_data['title']['romaji']} já existe. ID: {existing.id}")
                return existing.id
            
            title = (
                anime_data.get("title", {}).get("english") or
                anime_data.get("title", {}).get("romaji") or
                anime_data.get("title", {}).get("native") or
                "Unknown"
            )
            
            anime = Anime(
                external_id=anime_data["id"],
                title=title,
                synopsis=anime_data.get("description"),
                episodes=anime_data.get("episodes"),
                release_year=anime_data.get("seasonYear"),
                cover_image_url=anime_data.get("coverImage", {}).get("large"),
                airing_status=self._parse_airing_status(anime_data.get("status")),
                format=self._parse_media_format(anime_data.get("format")),
                source=self._parse_media_source(anime_data.get("source"))
            )
            db.add(anime)
            db.flush()
            
            for genre_name in anime_data.get("genres", []):
                genre = db.query(Genre).filter(Genre.name == genre_name).first()
                if not genre:
                    genre = Genre(name=genre_name)
                    db.add(genre)
                    db.flush()
                if genre not in anime.genres:
                    anime.genres.append(genre)
            
            db.commit()
            print(f"✅ Anime '{title}' salvo! ID: {anime.id}")
            return anime.id
            
        except Exception as e:
            db.rollback()
            print(f"❌ Erro ao salvar anime: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            db.close()
    
    def seed_popular_animes(self, count: int = 30) -> List[Anime]:
        print(f"🔍 Buscando {count} animes populares...")
        animes_data = self.get_popular_anime(count)
        print(f"📦 Encontrados {len(animes_data)} animes")
        saved = []
        for anime_data in animes_data:
            anime = self.save_anime_to_db(anime_data)
            if anime:
                saved.append(anime)
        print(f"✅ {len(saved)} animes salvos!")
        return saved

    def search_anime(self, query: str, per_page: int = 10) -> List[Dict[str, Any]]:
        graphql_query = """
        query ($query: String, $perPage: Int) {
            Page(perPage: $perPage) {
                media(search: $query, type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title { romaji english native }
                    description
                    episodes
                    seasonYear
                    coverImage { large }
                    status
                    genres
                }
            }
        }
        """
        
        response = self.client.post(
            self.BASE_URL,
            json={"query": graphql_query, "variables": {"query": query, "perPage": per_page}}
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", {}).get("Page", {}).get("media", [])

    def search_anime_by_id(self, anime_id: int) -> Optional[Dict[str, Any]]:
        graphql_query = """
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title { romaji english native }
                description
                episodes
                seasonYear
                coverImage { large }
                status
                genres
            }
        }
        """
        
        response = self.client.post(
            self.BASE_URL,
            json={"query": graphql_query, "variables": {"id": anime_id}}
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", {}).get("Media")