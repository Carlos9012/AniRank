from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas de variáveis de ambiente.
    
    Pydantic automaticamente:
    - Lê do .env (quando existe)
    - Lê de variáveis de ambiente do sistema
    - Valida tipos e obrigatoriedade
    """
    database_url: str = Field(
        ...,
        description="URL de conexão PostgreSQL (ex: postgresql://user:pass@host:port/db)"
    )
    
    # Configuração da aplicação
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
    
    # Configuração de segurança (JWT)
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

settings = Settings()

if not settings.database_url:
    raise ValueError("DATABASE_URL não configurada! Verifique seu .env")