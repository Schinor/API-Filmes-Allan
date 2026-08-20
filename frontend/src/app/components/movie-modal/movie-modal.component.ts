import { Component, Input, Output, EventEmitter, OnInit, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SlicePipe } from '@angular/common';
import { Filme } from '../../services/filmes.service';
import { FavoritosService } from '../../services/favoritos.service';
import { ComentariosService, Comentario } from '../../services/comentarios.service';

@Component({
  selector: 'app-movie-modal',
  imports: [FormsModule, SlicePipe],
  templateUrl: './movie-modal.component.html',
  styleUrl: './movie-modal.component.css',
})
export class MovieModalComponent implements OnInit {
  @Input({ required: true }) filme!: Filme;
  @Input() favoritadoInicial = false;
  @Output() fechar = new EventEmitter<void>();
  @Output() favoritoAlterado = new EventEmitter<{ id: number; favoritado: boolean }>();

  private favService = inject(FavoritosService);
  private comService = inject(ComentariosService);

  isFavoritado = signal(false);
  loadingFav = signal(false);
  comentarios = signal<Comentario[]>([]);
  loadingCom = signal(false);
  novoComentario = '';

  ngOnInit() {
    this.isFavoritado.set(this.favoritadoInicial);
    this.carregarComentarios();
  }

  carregarComentarios() {
    this.loadingCom.set(true);
    this.comService.listar(this.filme.id).subscribe({
      next: (cs) => {
        this.comentarios.set(cs);
        this.loadingCom.set(false);
      },
      error: () => this.loadingCom.set(false),
    });
  }

  toggleFavorito() {
    this.loadingFav.set(true);
    if (this.isFavoritado()) {
      this.favService.desfavoritar(this.filme.id).subscribe({
        next: () => {
          this.isFavoritado.set(false);
          this.loadingFav.set(false);
          this.favoritoAlterado.emit({ id: this.filme.id, favoritado: false });
        },
        error: () => this.loadingFav.set(false),
      });
    } else {
      this.favService.favoritar({
        tmdb_movie_id: this.filme.id,
        titulo: this.filme.titulo,
        poster_path: this.filme.poster_path,
      }).subscribe({
        next: () => {
          this.isFavoritado.set(true);
          this.loadingFav.set(false);
          this.favoritoAlterado.emit({ id: this.filme.id, favoritado: true });
        },
        error: () => this.loadingFav.set(false),
      });
    }
  }

  addComentario() {
    const texto = this.novoComentario.trim();
    if (!texto) return;
    this.loadingCom.set(true);
    this.comService.comentar(this.filme.id, texto).subscribe({
      next: (c) => {
        this.comentarios.update((cs) => [c, ...cs]);
        this.novoComentario = '';
        this.loadingCom.set(false);
      },
      error: () => this.loadingCom.set(false),
    });
  }

  deletarComentario(id: number) {
    this.comService.deletar(id).subscribe({
      next: () => this.comentarios.update((cs) => cs.filter((c) => c.id !== id)),
    });
  }
}
