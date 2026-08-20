import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Favorito {
  id: number;
  tmdb_movie_id: number;
  titulo: string;
  poster_path: string | null;
}

export interface FavoritoCreate {
  tmdb_movie_id: number;
  titulo: string;
  poster_path: string | null;
}

@Injectable({ providedIn: 'root' })
export class FavoritosService {
  constructor(private http: HttpClient) {}

  listar(): Observable<Favorito[]> {
    return this.http.get<Favorito[]>('/api/favoritos');
  }

  favoritar(payload: FavoritoCreate): Observable<Favorito> {
    return this.http.post<Favorito>('/api/favoritos', payload);
  }

  desfavoritar(tmdbMovieId: number): Observable<void> {
    return this.http.delete<void>(`/api/favoritos/${tmdbMovieId}`);
  }
}
