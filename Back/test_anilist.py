from app.services.anilist_service import AniListService
import json

print('🔍 Buscando animes populares...')
print('=' * 60)

with AniListService() as service:
    animes = service.get_popular_anime(5)  # Busca apenas 5 para teste
    
    print(f'📦 Encontrados {len(animes)} animes:')
    print('=' * 60)
    
    for i, anime in enumerate(animes, 1):
        print(f'\n{i}. {anime.get("title", {}).get("romaji", "N/A")}')
        print(f'   ID: {anime.get("id")}')
        print(f'   Título EN: {anime.get("title", {}).get("english", "N/A")}')
        print(f'   Episódios: {anime.get("episodes")}')
        print(f'   Ano: {anime.get("seasonYear")}')
        print(f'   Status: {anime.get("status")}')
        print(f'   Gêneros: {", ".join(anime.get("genres", []))}')
        print(f'   Sinopse: {anime.get("description", "N/A")[:100]}...')
        print('-' * 60)

print('\n✅ Teste concluído!')
