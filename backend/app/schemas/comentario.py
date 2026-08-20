from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ComentarioCreate(BaseModel):
    tmdb_movie_id: int
    texto: str

class ComentarioOut(BaseModel):
    id: int
    tmdb_movie_id: int
    texto: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)