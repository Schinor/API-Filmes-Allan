import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Subscription, timer } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';
import { AuthService } from '../../services/auth.service';
import { PremiumService } from '../../services/premium.service';

const INTERVALO_MS = 1500;
const TIMEOUT_MS = 15000;

/**
 * Volta do Stripe após o pagamento. Esta página NÃO ativa nada: quem marca o
 * usuário como Premium é o webhook. Aqui só esperamos ele chegar (polling).
 */
@Component({
  selector: 'app-premium-sucesso',
  imports: [RouterLink],
  templateUrl: './premium-sucesso.component.html',
  styleUrl: './premium.component.css',
})
export class PremiumSucessoComponent implements OnInit, OnDestroy {
  private premium = inject(PremiumService);
  private auth = inject(AuthService);
  private sub?: Subscription;

  estado = signal<'processando' | 'ativo' | 'demorando'>('processando');

  ngOnInit() {
    const inicio = Date.now();
    this.sub = timer(0, INTERVALO_MS)
      .pipe(
        switchMap(() => this.premium.status()),
        takeWhile((s) => !s.premium && Date.now() - inicio < TIMEOUT_MS, true),
      )
      .subscribe({
        next: (s) => {
          if (s.premium) {
            this.estado.set('ativo');
            // O JWT não carrega o plano; só atualiza o usuário guardado no navegador
            this.auth.carregarPerfil();
          } else if (Date.now() - inicio >= TIMEOUT_MS) {
            this.estado.set('demorando');
          }
        },
        error: () => this.estado.set('demorando'),
      });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
