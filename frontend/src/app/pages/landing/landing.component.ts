import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { catchError, of } from 'rxjs';
import { AuthService } from '../../services/auth.service';

interface ApiPermission {
  id: number;
  action: string;
  resource: string;
  description?: string;
  slug: string;
}

interface ApiRole {
  id: number;
  name: string;
  slug: string;
  description?: string;
  permissoes: ApiPermission[];
}

export interface PlanItem {
  id: string;
  name: string;
  accent: string;
  badge: string;
  filmRef: string;
  description: string;
  features: string[];
  permissionCount: number;
  ctaText: string;
  isPopular?: boolean;
  isFlagship?: boolean;
  serialNumber: string;
}

interface PlanPresentation {
  accent: string;
  badge: string;
  filmRef: string;
  ctaText: string;
  serialNumber: string;
  isPopular?: boolean;
  isFlagship?: boolean;
}

const PLAN_PRESENTATION: Record<string, PlanPresentation> = {
  'amigo-do-wilson': {
    accent: 'var(--accent-ilha)', badge: 'ACESSO ESSENCIAL',
    filmRef: 'Náufrago · comece pelo essencial', ctaText: 'Escolher Amigo do Wilson', serialNumber: 'NÍVEL 01',
  },
  'preso-no-terminal': {
    accent: 'var(--accent-terminal)', badge: 'INTERMEDIÁRIO',
    filmRef: 'O Terminal · organize sua jornada', ctaText: 'Escolher Preso no Terminal', serialNumber: 'NÍVEL 02',
  },
  'houston-temos-acesso': {
    accent: 'var(--accent-orbita)', badge: 'MAIS ESCOLHIDO',
    filmRef: 'Apollo 13 · participe da comunidade', ctaText: 'Escolher Houston', serialNumber: 'NÍVEL 03', isPopular: true,
  },
  'capitao-hanks': {
    accent: 'var(--accent-capitao)', badge: 'ACESSO MÁXIMO',
    filmRef: 'Capitão Phillips · assuma o comando', ctaText: 'Escolher Capitão Hanks', serialNumber: 'NÍVEL 04', isFlagship: true,
  },
};

const PERMISSION_DESCRIPTIONS: Record<string, string> = {
  'assistir:catalogo': 'Visualizar e buscar filmes no catálogo',
  'detalhes:filmes': 'Visualizar detalhes e ficha técnica de filmes',
  'listar:comentarios': 'Visualizar comentários da comunidade',
  'listar:favoritos': 'Visualizar a lista de filmes favoritos',
  'adicionar:favoritos': 'Adicionar filmes à lista de favoritos',
  'remover:favoritos': 'Remover filmes da lista de favoritos',
  'criar:comentarios': 'Publicar novos comentários em filmes',
  'apagar:comentario-proprio': 'Excluir os próprios comentários',
  'assistir:catalogo-premium': 'Acesso a conteúdos 4K, bastidores e edições exclusivas',
};

const makePermissions = (slugs: string[]): ApiPermission[] => slugs.map((slug, index) => {
  const [action, resource] = slug.split(':');
  return { id: index + 1, action, resource, slug, description: PERMISSION_DESCRIPTIONS[slug] };
});

const BASE_PERMISSIONS = ['assistir:catalogo', 'detalhes:filmes', 'listar:comentarios'];
const FAVORITE_PERMISSIONS = ['listar:favoritos', 'adicionar:favoritos', 'remover:favoritos'];
const COMMENT_PERMISSIONS = ['criar:comentarios', 'apagar:comentario-proprio'];

const FALLBACK_ROLES: ApiRole[] = [
  { id: 1, name: 'Amigo do Wilson (Náufrago)', slug: 'amigo-do-wilson', description: 'Catálogo e permissões bem limitados — isolado, poucas ações liberadas', permissoes: makePermissions(BASE_PERMISSIONS) },
  { id: 2, name: 'Preso no Terminal (O Terminal)', slug: 'preso-no-terminal', description: 'Acesso a várias áreas, mas ainda não circula livremente por tudo', permissoes: makePermissions([...BASE_PERMISSIONS, ...FAVORITE_PERMISSIONS]) },
  { id: 3, name: 'Houston, Temos Acesso (Apollo 13)', slug: 'houston-temos-acesso', description: 'Quase sem restrições — favoritos e comentários liberados', permissoes: makePermissions([...BASE_PERMISSIONS, ...FAVORITE_PERMISSIONS, ...COMMENT_PERMISSIONS]) },
  { id: 4, name: 'Capitão Hanks (Capitão Phillips)', slug: 'capitao-hanks', description: 'Máximo de permissões dentre os planos de usuário comum — acervo premium', permissoes: makePermissions([...BASE_PERMISSIONS, ...FAVORITE_PERMISSIONS, ...COMMENT_PERMISSIONS, 'assistir:catalogo-premium']) },
];

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.css',
})
export class LandingComponent implements OnInit {
  auth = inject(AuthService);
  private router = inject(Router);
  private http = inject(HttpClient);

  plans = signal<PlanItem[]>(this.toPlans(FALLBACK_ROLES));
  loadingPlans = signal(true);
  usingFallback = signal(false);
  selectedPlanForModal = signal<PlanItem | null>(null);

  ngOnInit(): void {
    this.http.get<ApiRole[]>('/api/auth/roles').pipe(
      catchError(() => {
        this.usingFallback.set(true);
        return of(FALLBACK_ROLES);
      })
    ).subscribe((roles) => {
      this.plans.set(this.toPlans(roles));
      this.loadingPlans.set(false);
    });
  }

  private toPlans(roles: ApiRole[]): PlanItem[] {
    const order = Object.keys(PLAN_PRESENTATION);
    return roles
      .filter((role) => role.slug !== 'admin' && PLAN_PRESENTATION[role.slug])
      .sort((a, b) => order.indexOf(a.slug) - order.indexOf(b.slug))
      .map((role) => {
        const presentation = PLAN_PRESENTATION[role.slug];
        return {
          id: role.slug,
          name: role.name,
          accent: presentation.accent,
          badge: presentation.badge,
          filmRef: presentation.filmRef,
          description: role.description || '',
          features: role.permissoes.map((permission) => permission.description || permission.slug),
          permissionCount: role.permissoes.length,
          ctaText: presentation.ctaText,
          serialNumber: presentation.serialNumber,
          isPopular: presentation.isPopular,
          isFlagship: presentation.isFlagship,
        };
      });
  }

  scrollToPlans(): void {
    document.getElementById('planos-section')?.scrollIntoView({ behavior: 'smooth' });
  }

  openPlanModal(plan: PlanItem): void { this.selectedPlanForModal.set(plan); }
  closePlanModal(): void { this.selectedPlanForModal.set(null); }

  proceedWithPlan(plan: PlanItem): void {
    this.closePlanModal();
    if (this.auth.isLoggedIn()) {
      this.router.navigate(['/catalogo']);
      return;
    }
    this.router.navigate(['/login'], { queryParams: { role: plan.id } });
  }
}
