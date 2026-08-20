import { Component, Input, Output, EventEmitter } from '@angular/core';
import { SlicePipe } from '@angular/common';
import { Filme } from '../../services/filmes.service';

@Component({
  selector: 'app-movie-card',
  imports: [SlicePipe],
  templateUrl: './movie-card.component.html',
  styleUrl: './movie-card.component.css',
})
export class MovieCardComponent {
  @Input({ required: true }) filme!: Filme;
  @Input() isFavoritado = false;
  @Output() abrir = new EventEmitter<Filme>();
}
