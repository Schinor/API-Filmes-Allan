import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/catalogo', pathMatch: 'full' },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
  },
  {
    path: 'catalogo',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/catalogo/catalogo.component').then(m => m.CatalogoComponent),
  },
  {
    path: 'favoritos',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/favoritos/favoritos.component').then(m => m.FavoritosComponent),
  },
  {
    path: 'comentarios',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/comentarios/comentarios.component').then(m => m.ComentariosComponent),
  },
  { path: '**', redirectTo: '/catalogo' },
];
