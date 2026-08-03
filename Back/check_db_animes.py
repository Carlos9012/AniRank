from app.database import SessionLocal
from app.models import Anime

db = SessionLocal()
animes = db.query(Anime).limit(5).all()

print('📺 Animes no banco:')
print('=' * 60)

for i, anime in enumerate(animes, 1):
    status = anime.airing_status.value if anime.airing_status else 'N/A'
    print(f'{i}. {anime.title}')
    print(f'   ID: {anime.id} (external: {anime.external_id})')
    print(f'   Ano: {anime.release_year}')
    print(f'   Status: {status}')
    print(f'   Episódios: {anime.episodes}')
    print('-' * 60)

db.close()
