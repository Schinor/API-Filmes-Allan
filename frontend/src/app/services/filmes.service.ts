import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Filme {
  id: number;
  titulo: string;
  sinopse: string;
  poster_path: string | null;
  poster_url: string | null;
  data_lancamento: string;
  popularidade: number;
}

@Injectable({ providedIn: 'root' })
export class FilmesService {
  constructor(private http: HttpClient) {}

  listar(): Observable<Filme[]> {
    return this.http.get<Filme[]>('/api/filmes');
  }

  detalhe(id: number): Observable<Filme> {
    return this.http.get<Filme>(`/api/filmes/${id}`);
  }
}
