import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Comentario {
  id: number;
  tmdb_movie_id: number;
  texto: string;
  criado_em: string;
}

@Injectable({ providedIn: 'root' })
export class ComentariosService {
  constructor(private http: HttpClient) {}

  listar(tmdbMovieId: number): Observable<Comentario[]> {
    return this.http.get<Comentario[]>(`/api/comentarios/${tmdbMovieId}`);
  }

  listarTodos(): Observable<Comentario[]> {
    return this.http.get<Comentario[]>('/api/comentarios');
  }

  comentar(tmdbMovieId: number, texto: string): Observable<Comentario> {
    return this.http.post<Comentario>('/api/comentarios', {
      tmdb_movie_id: tmdbMovieId,
      texto,
    });
  }

  deletar(comentarioId: number): Observable<void> {
    return this.http.delete<void>(`/api/comentarios/${comentarioId}`);
  }
}
