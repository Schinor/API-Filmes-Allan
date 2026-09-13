import { Directive, Input, TemplateRef, ViewContainerRef, inject, effect } from '@angular/core';
import { AuthService } from '../services/auth.service';

@Directive({
  selector: '[hasPermission]',
  standalone: true,
})
export class HasPermissionDirective {
  private templateRef = inject(TemplateRef<any>);
  private viewContainer = inject(ViewContainerRef);
  private auth = inject(AuthService);

  private requiredPermission: string | string[] | null = null;
  private isRendered = false;

  constructor() {
    effect(() => {
      // Re-executa sempre que o usuário ou suas permissões mudarem
      this.auth.user();
      this.updateView();
    });
  }

  @Input() set hasPermission(permission: string | string[]) {
    this.requiredPermission = permission;
    this.updateView();
  }

  private updateView(): void {
    if (!this.requiredPermission) {
      if (!this.isRendered) {
        this.viewContainer.createEmbeddedView(this.templateRef);
        this.isRendered = true;
      }
      return;
    }

    const hasAccess = Array.isArray(this.requiredPermission)
      ? this.auth.hasAnyPermission(this.requiredPermission)
      : this.auth.hasPermission(this.requiredPermission);

    if (hasAccess && !this.isRendered) {
      this.viewContainer.createEmbeddedView(this.templateRef);
      this.isRendered = true;
    } else if (!hasAccess && this.isRendered) {
      this.viewContainer.clear();
      this.isRendered = false;
    }
  }
}
