import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { HasPermissionDirective } from '../../directives/has-permission.directive';

@Component({
  selector: 'app-navbar',
  imports: [CommonModule, RouterLink, RouterLinkActive, HasPermissionDirective],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css',
})
export class NavbarComponent {
  auth = inject(AuthService);
  router = inject(Router);

  get roleBadge(): { name: string; class: string } {
    const role = this.auth.user()?.role;
    switch (role) {
      case 'admin':
        return { name: 'Admin', class: 'badge-admin' };
      case 'capitao-hanks':
        return { name: 'Capitão Hanks', class: 'badge-capitao' };
      case 'houston-temos-acesso':
        return { name: 'Houston, Temos Acesso', class: 'badge-houston' };
      case 'preso-no-terminal':
        return { name: 'Preso no Terminal', class: 'badge-terminal' };
      case 'amigo-do-wilson':
      default:
        return { name: 'Amigo do Wilson', class: 'badge-wilson' };
    }
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
