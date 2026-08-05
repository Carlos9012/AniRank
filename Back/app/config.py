from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(
        ...,
        description="URL de conexão PostgreSQL (ex: postgresql://user:pass@host:port/db)"
    )
    
    app_name: str = Field(
        default="AniRank",
        description="Nome da aplicação (usado em logs e respostas da API)"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Versão atual da API"
    )
    debug: bool = Field(
        default=False,
        description="Modo debug - ativa logs mais detalhados e recarrega automaticamente"
    )
    
    secret_key: str = Field(
        ...,
        description="Chave secreta para JWT (gerar com: openssl rand -hex 32)"
    )
    algorithm: str = Field(
        default="HS256",
        description="Algoritmo de assinatura JWT"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Tempo de expiração do token JWT em minutos"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    gemini_api_key: Optional[str] = Field(None, description="Chave da API do Gemini")
    use_gemini: bool = Field(default=False, description="Usar Gemini para interpretação")

settings = Settings()

if not settings.database_url:
    raise ValueError("DATABASE_URL não configurada! Verifique seu .env")

if not settings.secret_key:
    raise ValueError("SECRET_KEY não configurada! Verifique seu .env")