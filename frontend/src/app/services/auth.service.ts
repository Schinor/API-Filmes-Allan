import { Injectable, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface Usuario {
  id: number;
  nome: string;
  email: string;
  role?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user?: Usuario;
}

export interface ForgotPasswordResponse {
  message: string;
  token?: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface ValidateTokenResponse {
  valid: boolean;
  email?: string;
  message?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly TOKEN_KEY = 'tomhanks_token';
  private readonly USER_KEY = 'tomhanks_user';

  private _token = signal<string | null>(localStorage.getItem(this.TOKEN_KEY));
  private _user = signal<Usuario | null>(
    JSON.parse(localStorage.getItem(this.USER_KEY) || 'null')
  );

  readonly token = this._token.asReadonly();
  readonly user = this._user.asReadonly();
  readonly isLoggedIn = computed(() => !!this._token());
  readonly isAdmin = computed(() => this._user()?.role === 'admin');

  constructor(private http: HttpClient) {
    if (this._token()) {
      this.carregarPerfil();
    }
  }

  cadastrar(nome: string, email: string, senha: string, role: string = 'usuario'): Observable<Usuario> {
    return this.http.post<Usuario>('/api/auth/cadastro', {
      nome: nome.trim(),
      email: email.trim(),
      senha,
      role,
    });
  }

  login(email: string, senha: string): Observable<Token> {
    const body = new HttpParams()
      .set('username', email.trim())
      .set('password', senha);

    return this.http
      .post<Token>('/api/auth/login', body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .pipe(
        tap((res) => {
          this._token.set(res.access_token);
          localStorage.setItem(this.TOKEN_KEY, res.access_token);
          if (res.user) {
            this._user.set(res.user);
            localStorage.setItem(this.USER_KEY, JSON.stringify(res.user));
          } else {
            this.carregarPerfil();
          }
        })
      );
  }

  carregarPerfil(): void {
    this.http.get<Usuario>('/api/auth/me').subscribe({
      next: (user) => {
        this._user.set(user);
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
      },
      error: () => {
        // Se o token estiver expirado ou inválido, limpa a sessão
        this.logout();
      },
    });
  }

  esqueciSenha(email: string): Observable<ForgotPasswordResponse> {
    return this.http.post<ForgotPasswordResponse>('/api/auth/forgot-password', {
      email: email.trim(),
    });
  }

  validarTokenReset(token: string): Observable<ValidateTokenResponse> {
    return this.http.get<ValidateTokenResponse>(`/api/auth/validate-reset-token/${encodeURIComponent(token)}`);
  }

  redefinirSenha(token: string, novaSenha: string): Observable<ResetPasswordResponse> {
    return this.http.post<ResetPasswordResponse>('/api/auth/reset-password', {
      token,
      nova_senha: novaSenha,
    });
  }

  logout(): void {
    this._token.set(null);
    this._user.set(null);
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }
}
