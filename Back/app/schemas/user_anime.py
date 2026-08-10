from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

from app.models import WatchStatus


class UserAnimeCreate(BaseModel):
    anime_id: int = Field(..., description="ID do anime no banco")
    status: WatchStatus = Field(..., description="Status na lista (watching, completed, planned, dropped)")
    score: Optional[float] = Field(None, ge=0, le=10, description="Nota de 0 a 10 (opcional)")
    notes: Optional[str] = Field(None, max_length=500, description="Notas pessoais (opcional)")
    
    @validator('score')
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Score deve ser entre 0 e 10')
        return v


class UserAnimeUpdate(BaseModel):
    status: Optional[WatchStatus] = Field(None, description="Novo status")
    score: Optional[float] = Field(None, ge=0, le=10, description="Nova nota")
    notes: Optional[str] = Field(None, max_length=500, description="Novas notas")
    
    @validator('score')
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Score deve ser entre 0 e 10')
        return v


class UserAnimeResponse(BaseModel):
    id: int
    external_id: Optional[int] = None
    user_id: int
    anime_id: int
    status: WatchStatus
    score: Optional[float]
    notes: Optional[str]
    updated_at: datetime
    
    anime_title: Optional[str] = None
    anime_cover: Optional[str] = None
    anime_episodes: Optional[int] = None
    
    class Config:
        from_attributes = True
