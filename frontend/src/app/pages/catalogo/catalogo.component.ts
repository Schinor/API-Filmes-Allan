import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { FilmesService, Filme } from '../../services/filmes.service';
import { FavoritosService } from '../../services/favoritos.service';
import { MovieCardComponent } from '../../components/movie-card/movie-card.component';
import { MovieModalComponent } from '../../components/movie-modal/movie-modal.component';

@Component({
  selector: 'app-catalogo',
  imports: [FormsModule, MovieCardComponent, MovieModalComponent],
  templateUrl: './catalogo.component.html',
  styleUrl: './catalogo.component.css',
})
export class CatalogoComponent implements OnInit {
  private filmesService = inject(FilmesService);
  private favService = inject(FavoritosService);

  filmes = signal<Filme[]>([]);
  idsFavoritos = signal<Set<number>>(new Set());
  carregando = signal(true);
  erro = signal('');
  busca = signal('');
  filmeAberto = signal<Filme | null>(null);

  filmesFiltrados = computed(() => {
    const q = this.busca().toLowerCase();
    return q
      ? this.filmes().filter((f) => f.titulo.toLowerCase().includes(q))
      : this.filmes();
  });

  ngOnInit() {
    this.carregar();
    this.carregarFavoritos();
  }

  carregar() {
    this.carregando.set(true);
    this.erro.set('');
    this.filmesService.listar().subscribe({
      next: (fs) => {
        this.filmes.set(fs);
        this.carregando.set(false);
      },
      error: (e) => {
        this.erro.set(e.error?.detail || 'Erro ao carregar filmes');
        this.carregando.set(false);
      },
    });
  }

  carregarFavoritos() {
    this.favService.listar().subscribe({
      next: (favs) => this.idsFavoritos.set(new Set(favs.map((f) => f.tmdb_movie_id))),
    });
  }

  abrirModal(filme: Filme) {
    this.filmeAberto.set(filme);
  }

  fecharModal() {
    this.filmeAberto.set(null);
  }

  onFavoritoAlterado({ id, favoritado }: { id: number; favoritado: boolean }) {
    this.idsFavoritos.update((s) => {
      const novo = new Set(s);
      favoritado ? novo.add(id) : novo.delete(id);
      return novo;
    });
  }
}
