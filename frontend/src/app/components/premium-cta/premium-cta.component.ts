import { Component, Input, inject, signal } from '@angular/core';
import { PremiumService } from '../../services/premium.service';

/** Botão "Assinar Premium": pede a URL do checkout ao backend e redireciona para o Stripe. */
@Component({
  selector: 'app-premium-cta',
  template: `
    <button type="button" class="btn-premium" [class.compacto]="compacto" (click)="assinar()" [disabled]="carregando()">
      {{ carregando() ? 'Abrindo o Stripe...' : rotulo }}
    </button>
    @if (erro()) {
      <p class="premium-erro" role="alert">{{ erro() }}</p>
    }
  `,
  styles: `
    :host { display: inline-flex; flex-direction: column; gap: .4rem; }
    .btn-premium {
      padding: .7rem 1.4rem; border-radius: var(--radius-md); border: 1px solid var(--gold);
      background: var(--gold); color: var(--surface-100); font-family: var(--font); font-size: .85rem;
      font-weight: 700; letter-spacing: .4px; text-transform: uppercase; cursor: pointer;
      box-shadow: var(--shadow-gold-glow); transition: background .2s ease;
    }
    .btn-premium:hover:not(:disabled) { background: var(--gold-hover); }
    .btn-premium:disabled { opacity: .6; cursor: wait; }
    .btn-premium.compacto { padding: .45rem .9rem; font-size: .75rem; box-shadow: none; }
    .premium-erro { color: #ffb3b6; font-size: .8rem; }
  `,
})
export class PremiumCtaComponent {
  @Input() rotulo = 'Assinar Premium · R$ 9,90/mês';
  @Input() compacto = false;

  private premium = inject(PremiumService);

  carregando = signal(false);
  erro = signal('');

  assinar() {
    this.carregando.set(true);
    this.erro.set('');
    this.premium.checkout().subscribe({
      next: ({ url }) => (window.location.href = url),
      error: (e) => {
        this.carregando.set(false);
        this.erro.set(e?.error?.detail || 'Não foi possível abrir o pagamento. Tente novamente.');
      },
    });
  }
}
