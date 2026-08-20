import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DatePipe, SlicePipe } from '@angular/common';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ComentariosService, Comentario } from '../../services/comentarios.service';
import { FilmesService, Filme } from '../../services/filmes.service';
import { MovieModalComponent } from '../../components/movie-modal/movie-modal.component';

export interface FilmeComentarios {
  filme: Filme;
  comentarios: Comentario[];
  novoTexto: string;
  adicionando: boolean;
}

@Component({
  selector: 'app-comentarios',
  imports: [RouterLink, FormsModule, DatePipe, SlicePipe, MovieModalComponent],
  templateUrl: './comentarios.component.html',
  styleUrl: './comentarios.component.css',
})
export class ComentariosComponent implements OnInit {
  private comentariosService = inject(ComentariosService);
  private filmesService = inject(FilmesService);

  grupos = signal<FilmeComentarios[]>([]);
  carregando = signal(true);
  filmeAberto = signal<Filme | null>(null);

  totalComentarios = computed(() =>
    this.grupos().reduce((acc, g) => acc + g.comentarios.length, 0)
  );

  ngOnInit() {
    this.carregarComentarios();
  }

  carregarComentarios() {
    this.carregando.set(true);
    this.comentariosService.listarTodos().subscribe({
      next: (todosComentarios) => {
        if (!todosComentarios || todosComentarios.length === 0) {
          this.grupos.set([]);
          this.carregando.set(false);
          return;
        }

        // Agrupa comentários por tmdb_movie_id
        const mapa = new Map<number, Comentario[]>();
        for (const c of todosComentarios) {
          if (!mapa.has(c.tmdb_movie_id)) {
            mapa.set(c.tmdb_movie_id, []);
          }
          mapa.get(c.tmdb_movie_id)!.push(c);
        }

        // Busca detalhes de cada filme com fallback
        const movieIds = Array.from(mapa.keys());
        const requests = movieIds.map((id) =>
          this.filmesService.detalhe(id).pipe(
            catchError(() => {
              const fallback: Filme = {
                id,
                titulo: `Filme #${id}`,
                sinopse: '',
                poster_path: null,
                poster_url: null,
                data_lancamento: '',
                popularidade: 0,
              };
              return of(fallback);
            })
          )
        );

        forkJoin(requests).subscribe({
          next: (filmes) => {
            const lista: FilmeComentarios[] = filmes.map((filme) => ({
              filme,
              comentarios: mapa.get(filme.id) || [],
              novoTexto: '',
              adicionando: false,
            }));
            this.grupos.set(lista);
            this.carregando.set(false);
          },
          error: () => {
            this.carregando.set(false);
          },
        });
      },
      error: () => {
        this.carregando.set(false);
      },
    });
  }

  deletarComentario(comentarioId: number, movieId: number) {
    this.comentariosService.deletar(comentarioId).subscribe({
      next: () => {
        this.grupos.update((gs) =>
          gs
            .map((g) => {
              if (g.filme.id === movieId) {
                return {
                  ...g,
                  comentarios: g.comentarios.filter((c) => c.id !== comentarioId),
                };
              }
              return g;
            })
            .filter((g) => g.comentarios.length > 0)
        );
      },
    });
  }

  adicionarComentario(grupo: FilmeComentarios) {
    const texto = grupo.novoTexto.trim();
    if (!texto) return;

    grupo.adicionando = true;
    this.comentariosService.comentar(grupo.filme.id, texto).subscribe({
      next: (novoComentario) => {
        grupo.novoTexto = '';
        grupo.adicionando = false;
        this.grupos.update((gs) =>
          gs.map((g) => {
            if (g.filme.id === grupo.filme.id) {
              return {
                ...g,
                comentarios: [novoComentario, ...g.comentarios],
              };
            }
            return g;
          })
        );
      },
      error: () => {
        grupo.adicionando = false;
      },
    });
  }

  abrirFilme(filme: Filme) {
    this.filmeAberto.set(filme);
  }

  fecharModal() {
    this.filmeAberto.set(null);
    // Recarrega para sincronizar comentários feitos dentro da modal
    this.carregarComentarios();
  }
}
