from typing import Optional
from pydantic import BaseModel, ConfigDict

class FavoritoCreate(BaseModel):
    tmdb_movie_id: int
    titulo: str
    poster_path: Optional[str] = None

class FavoritoOut(BaseModel):
    id: int
    tmdb_movie_id: int
    titulo: str
    poster_path: Optional[str]

    model_config = ConfigDict(from_attributes=True)
