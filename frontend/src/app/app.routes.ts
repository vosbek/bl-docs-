import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(c => c.DashboardComponent)
  },
  {
    path: 'workflow/:contextId',
    loadComponent: () => import('./pages/workflow/workflow.component').then(c => c.WorkflowComponent)
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];