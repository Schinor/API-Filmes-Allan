import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './guards/auth.guard';
import { permissionGuard } from './guards/permission.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/landing/landing.component').then(m => m.LandingComponent),
  },
  {
    path: 'planos',
    loadComponent: () => import('./pages/landing/landing.component').then(m => m.LandingComponent),
  },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
  },
  {
    path: 'reset-password',
    loadComponent: () => import('./pages/reset-password/reset-password.component').then(m => m.ResetPasswordComponent),
  },
  {
    path: 'catalogo',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/catalogo/catalogo.component').then(m => m.CatalogoComponent),
  },
  {
    path: 'favoritos',
    canActivate: [authGuard, permissionGuard('listar:favoritos')],
    loadComponent: () => import('./pages/favoritos/favoritos.component').then(m => m.FavoritosComponent),
  },
  {
    path: 'comentarios',
    canActivate: [authGuard, permissionGuard('listar:comentarios')],
    loadComponent: () => import('./pages/comentarios/comentarios.component').then(m => m.ComentariosComponent),
  },
  { path: '**', redirectTo: '' },
];
