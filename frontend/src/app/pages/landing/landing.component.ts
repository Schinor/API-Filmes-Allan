import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

export interface PlanItem {
  id: string;
  name: string;
  accent: string;
  badge: string;
  actorRole: string;
  filmRef: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  ctaText: string;
  isPopular?: boolean;
  isFlagship?: boolean;
  serialNumber: string;
  iconSvg: string;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.css',
})
export class LandingComponent {
  auth = inject(AuthService);
  router = inject(Router);

  // Selected plan for 3D showcase and interactive modal
  selectedShowcasePlan = signal<string>('capitao');
  selectedPlanForModal = signal<PlanItem | null>(null);

  plans: PlanItem[] = [
    {
      id: 'ilha',
      name: 'ILHA',
      accent: 'var(--accent-ilha)',
      badge: 'ESSENCIAL',
      actorRole: 'Chuck Noland as O Sobrevivente',
      filmRef: 'Náufrago (Cast Away, 2000)',
      price: 'R$ 19,90',
      period: '/ mês',
      description: 'A sobrevivência no essencial: catálogo completo em alta definição para quem quer começar a jornada.',
      features: [
        'Acesso a todos os filmes clássicos de Tom Hanks',
        'Streaming em Full HD 1080p',
        'Comentários e notas da comunidade cinéfila',
        '1 tela simultânea',
      ],
      ctaText: 'Assinar Ilha »',
      serialNumber: '#TH-2000-ILHA-01',
      iconSvg: 'island',
    },
    {
      id: 'terminal',
      name: 'TERMINAL',
      accent: 'var(--accent-terminal)',
      badge: 'EXPLORADOR',
      actorRole: 'Viktor Navorski as O Residente',
      filmRef: 'O Terminal (The Terminal, 2004)',
      price: 'R$ 34,90',
      period: '/ mês',
      description: 'Para quem fez do cinema sua segunda casa: recursos de áudio restaurado e mobilidade total.',
      features: [
        'Catálogo integral Tom Hanks em Full HD+',
        'Faixas de áudio originais restauradas em 5.1',
        'Modo Offline para download no celular/tablet',
        '2 telas simultâneas',
        'Galeria de fotos e cartazes de produção',
      ],
      ctaText: 'Assinar Terminal »',
      serialNumber: '#TH-2004-TERM-02',
      iconSvg: 'terminal',
    },
    {
      id: 'orbita',
      name: 'ÓRBITA',
      accent: 'var(--accent-orbita)',
      badge: 'MAIS POPULAR',
      actorRole: 'Jim Lovell as O Navegador',
      filmRef: 'Apollo 13 (1995)',
      price: 'R$ 49,90',
      period: '/ mês',
      description: 'Uma perspectiva superior: masterização 4K HDR e acesso a arquivos técnicos inéditos.',
      features: [
        'Transmissão em 4K HDR Dolby Vision',
        'Acesso a documentários e bastidores exclusivos',
        'Roteiros digitalizados e storyboards originais',
        '3 telas simultâneas em resolução máxima',
        'Acesso antecipado a novos lançamentos e restaurações',
      ],
      ctaText: 'Assinar Órbita »',
      isPopular: true,
      serialNumber: '#TH-1995-ORBT-03',
      iconSvg: 'orbit',
    },
    {
      id: 'capitao',
      name: 'CAPITÃO',
      accent: 'var(--accent-capitao)',
      badge: 'EXPERIÊNCIA DEFINITIVA',
      actorRole: 'Miller & Phillips as O Comandante',
      filmRef: 'O Resgate do Soldado Ryan / Cap. Phillips / Sully',
      price: 'R$ 79,90',
      period: '/ mês',
      description: 'O comando supremo: privilégios VIP, sessões com curadores e box físico colecionável anual.',
      features: [
        'Master 4K Ultra sem compressão + áudio Dolby Atmos',
        'Convites para sessões comentadas com críticos e dubladores',
        'Box de colecionador físico anual (Livreto de luxo + cartazes)',
        'Telas simultâneas ilimitadas para toda a família',
        'Acesso prioritário a eventos presenciais e workshops',
      ],
      ctaText: 'Garantir Capitão »',
      isFlagship: true,
      serialNumber: '#TH-1998-CAPT-04',
      iconSvg: 'captain',
    },
  ];

  get currentShowcase(): PlanItem {
    return this.plans.find(p => p.id === this.selectedShowcasePlan()) || this.plans[3];
  }

  setShowcase(planId: string) {
    this.selectedShowcasePlan.set(planId);
  }

  scrollToPlans() {
    const el = document.getElementById('planos-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }

  openPlanModal(plan: PlanItem) {
    this.selectedPlanForModal.set(plan);
  }

  closePlanModal() {
    this.selectedPlanForModal.set(null);
  }

  proceedWithPlan(plan: PlanItem) {
    this.closePlanModal();
    if (this.auth.isLoggedIn()) {
      this.router.navigate(['/catalogo']);
    } else {
      this.router.navigate(['/login']);
    }
  }
}
