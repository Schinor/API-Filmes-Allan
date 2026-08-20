import { Component, OnInit, signal, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FavoritosService, Favorito } from '../../services/favoritos.service';
import { FilmesService, Filme } from '../../services/filmes.service';
import { MovieModalComponent } from '../../components/movie-modal/movie-modal.component';

@Component({
  selector: 'app-favoritos',
  imports: [RouterLink, MovieModalComponent],
  templateUrl: './favoritos.component.html',
  styleUrl: './favoritos.component.css',
})
export class FavoritosComponent implements OnInit {
  private favService = inject(FavoritosService);
  private filmesService = inject(FilmesService);

  favoritos = signal<Favorito[]>([]);
  carregando = signal(true);
  filmeAberto = signal<Filme | null>(null);

  ngOnInit() {
    this.carregarFavoritos();
  }

  carregarFavoritos() {
    this.carregando.set(true);
    this.favService.listar().subscribe({
      next: (fs) => {
        this.favoritos.set(fs);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }

  abrirFilme(fav: Favorito) {
    this.filmesService.detalhe(fav.tmdb_movie_id).subscribe({
      next: (f) => this.filmeAberto.set(f),
      error: () => {
        // Se não conseguir carregar detalhes, monta um filme básico
        const filmeBasico: Filme = {
          id: fav.tmdb_movie_id,
          titulo: fav.titulo,
          sinopse: '',
          poster_path: fav.poster_path,
          poster_url: fav.poster_path
            ? `https://image.tmdb.org/t/p/w500${fav.poster_path}`
            : null,
          data_lancamento: '',
          popularidade: 0,
        };
        this.filmeAberto.set(filmeBasico);
      },
    });
  }

  fecharModal() {
    this.filmeAberto.set(null);
  }

  remover(fav: Favorito) {
    this.favService.desfavoritar(fav.tmdb_movie_id).subscribe({
      next: () => this.favoritos.update((fs) => fs.filter((f) => f.id !== fav.id)),
    });
  }

  onFavoritoAlterado({ id, favoritado }: { id: number; favoritado: boolean }) {
    if (!favoritado) {
      this.favoritos.update((fs) => fs.filter((f) => f.tmdb_movie_id !== id));
      this.fecharModal();
    }
  }
}
