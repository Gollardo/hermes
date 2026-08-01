import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then((module) => module.HomePage),
  },
  {
    path: 'backend-status',
    loadComponent: () =>
      import('./pages/backend-status/backend-status').then((module) => module.BackendStatusPage),
  },
  { path: '**', redirectTo: '' },
];
