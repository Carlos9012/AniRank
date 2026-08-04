from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Só mostra SQL se estiver em modo debug
    pool_pre_ping=True,   # Evita conexões mortas
    pool_size=5,           # Máximo de conexões simultâneas
    max_overflow=10        # Conexões extras se necessário
)

# Sessões
#    - sessionmaker retorna uma classe que cria sessões
#    - autocommit=False → gerenciamos transações manualmente
#    - autoflush=False → só enviamos para o banco quando explícito
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para os modelos
Base = declarative_base()

# Dependência para o FastAPI
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)

def drop_tables():
    Base.metadata.drop_all(bind=engine)