import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Usuario } from './auth.service';

export interface UsuarioAdmin extends Usuario {
  role: string;
  permissions: string[];
  criado_em?: string;
}

export interface Permissao {
  id: number;
  action: string;
  resource: string;
  slug: string;
  description?: string;
}

export interface Papel {
  id: number;
  name: string;
  slug: string;
  description?: string;
  permissoes: Permissao[];
}

@Injectable({ providedIn: 'root' })
export class UsuariosService {
  constructor(private http: HttpClient) {}

  listar(): Observable<UsuarioAdmin[]> {
    return this.http.get<UsuarioAdmin[]>('/api/auth/users');
  }

  listarPapeis(): Observable<Papel[]> {
    return this.http.get<Papel[]>('/api/auth/roles');
  }

  listarPermissoes(): Observable<Permissao[]> {
    return this.http.get<Permissao[]>('/api/auth/permissions');
  }

  alterarPlano(userId: number, role: string): Observable<UsuarioAdmin> {
    return this.http.put<UsuarioAdmin>(`/api/auth/users/${userId}/role`, { role });
  }

  alterarPermissoes(userId: number, permissions: string[]): Observable<UsuarioAdmin> {
    return this.http.put<UsuarioAdmin>(`/api/auth/users/${userId}/permissions`, { permissions });
  }

  remover(userId: number): Observable<void> {
    return this.http.delete<void>(`/api/auth/users/${userId}`);
  }
}
