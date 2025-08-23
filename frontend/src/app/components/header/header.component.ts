import { Component } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { MenubarModule } from 'primeng/menubar';
import { MenuItem } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [MenubarModule, ButtonModule, RouterModule, ToastModule],
  template: `
    <div class="header-container">
      <p-menubar [model]="items" class="custom-menubar">
        <ng-template pTemplate="start">
          <div class="flex align-items-center">
            <i class="pi pi-code text-2xl mr-2"></i>
            <span class="text-xl font-bold">Multi-Agent Jira Card Creator</span>
          </div>
        </ng-template>
        <ng-template pTemplate="end">
          <p-button 
            icon="pi pi-refresh" 
            [text]="true" 
            [rounded]="true" 
            severity="secondary"
            pTooltip="Refresh System"
            (click)="refreshSystem()"
          ></p-button>
        </ng-template>
      </p-menubar>
    </div>
  `,
  styles: [`
    .header-container {
      margin-bottom: 1rem;
    }
    
    .custom-menubar {
      border-radius: 0;
      border-left: none;
      border-right: none;
      border-top: none;
    }
  `]
})
export class HeaderComponent {
  items: MenuItem[] = [
    {
      label: 'Dashboard',
      icon: 'pi pi-home',
      routerLink: '/dashboard'
    },
    {
      label: 'Help',
      icon: 'pi pi-question-circle',
      items: [
        {
          label: 'User Guide',
          icon: 'pi pi-book',
          command: () => this.openUserGuide()
        },
        {
          label: 'API Status',
          icon: 'pi pi-server',
          command: () => this.checkApiStatus()
        }
      ]
    }
  ];

  constructor(private router: Router) {}

  refreshSystem() {
    window.location.reload();
  }

  openUserGuide() {
    // Open user guide in new tab
    window.open('/assets/user-guide.html', '_blank');
  }

  checkApiStatus() {
    // Navigate to API health check
    this.router.navigate(['/dashboard'], { queryParams: { tab: 'system' } });
  }
}