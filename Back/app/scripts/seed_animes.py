import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.anilist_service import AniListService

def main():
    print("=" * 50)
    print("🚀 AniRank - Seed de Animes")
    print("=" * 50)
    
    count = 30
    if len(sys.argv) > 1 and sys.argv[1] == "--count":
        try:
            count = int(sys.argv[2])
        except (IndexError, ValueError):
            print("⚠️ Use: python -m app.scripts.seed_animes --count 50")
            return
    
    print(f"📊 Buscando {count} animes populares...")
    with AniListService() as service:
        saved = service.seed_popular_animes(count)
    
    print("=" * 50)
    print(f"✅ Seed concluído! {len(saved)} animes salvos.")
    print("=" * 50)

if __name__ == "__main__":
    main()