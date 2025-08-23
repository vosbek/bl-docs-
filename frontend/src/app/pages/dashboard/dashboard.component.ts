import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TabViewModule } from 'primeng/tabview';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { AccordionModule } from 'primeng/accordion';
import { BadgeModule } from 'primeng/badge';
import { ChipModule } from 'primeng/chip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService } from 'primeng/api';

import { ApiService, Repository } from '../../services/api.service';
import { ValidationService } from '../../services/validation.service';
import { Task, TaskSummary } from '../../models/task.model';

interface TaskStatusOption {
  label: string;
  value: string;
  severity: 'success' | 'info' | 'warning' | 'danger';
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TabViewModule,
    TableModule,
    TagModule,
    ProgressSpinnerModule,
    MessageModule,
    ToastModule,
    AccordionModule,
    BadgeModule,
    ChipModule,
    ConfirmDialogModule
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <div class="dashboard-container">
      <div class="grid">
        <!-- Task Selection Card -->
        <div class="col-12 lg:col-8">
          <p-card header="Available Tasks from tasks.md" [style]="{'height': '100%'}">
            <div class="task-header mb-3">
              <div class="flex justify-content-between align-items-center">
                <div>
                  <p class="text-600 m-0">
                    Select a task from the architect-defined list to process through the multi-agent workflow
                  </p>
                </div>
                <div class="flex gap-2">
                  <p-button 
                    icon="pi pi-search" 
                    [text]="true"
                    pTooltip="Search tasks"
                    (click)="toggleSearch()"
                  ></p-button>
                  <p-button 
                    icon="pi pi-refresh" 
                    [text]="true"
                    [loading]="isReloadingTasks"
                    pTooltip="Reload tasks from file"
                    (click)="reloadTasks()"
                  ></p-button>
                </div>
              </div>
              
              <!-- Search Bar -->
              <div class="mt-3" *ngIf="showSearch">
                <div class="flex">
                  <input 
                    pInputText 
                    [(ngModel)]="searchQuery" 
                    placeholder="Search tasks by description..."
                    class="flex-1"
                    (keyup.enter)="searchTasks()"
                    (input)="onSearchInput()"
                  />
                  <p-button 
                    icon="pi pi-search" 
                    [text]="true"
                    (click)="searchTasks()"
                  ></p-button>
                  <p-button 
                    icon="pi pi-times" 
                    [text]="true"
                    (click)="clearSearch()"
                  ></p-button>
                </div>
              </div>
              
              <!-- Task Summary -->
              <div class="task-summary mt-3" *ngIf="taskSummary">
                <div class="flex gap-3 align-items-center">
                  <p-chip [label]="'Total: ' + taskSummary.total" icon="pi pi-list"></p-chip>
                  <p-chip [label]="'Not Started: ' + taskSummary.not_started" icon="pi pi-clock" styleClass="p-chip-info"></p-chip>
                  <p-chip [label]="'In Progress: ' + taskSummary.in_progress" icon="pi pi-spin pi-spinner" styleClass="p-chip-warning"></p-chip>
                  <p-chip [label]="'Completed: ' + taskSummary.completed" icon="pi pi-check" styleClass="p-chip-success"></p-chip>
                </div>
              </div>
            </div>
            
            <!-- Tasks Table -->
            <p-table 
              [value]="displayedTasks" 
              [loading]="isLoadingTasks"
              [paginator]="true"
              [rows]="10"
              [responsive]="true"
              [globalFilterFields]="['description']"
              #taskTable
            >
              <ng-template pTemplate="header">
                <tr>
                  <th style="width: 80px">ID</th>
                  <th>Task Description</th>
                  <th style="width: 120px">Status</th>
                  <th style="width: 200px">Actions</th>
                </tr>
              </ng-template>
              
              <ng-template pTemplate="body" let-task>
                <tr>
                  <td>
                    <strong>{{task.id}}</strong>
                  </td>
                  <td>
                    <div class="task-description">
                      {{task.description}}
                    </div>
                    <small class="text-600" *ngIf="task.context_id">
                      Context: {{task.context_id}}
                    </small>
                  </td>
                  <td>
                    <p-tag 
                      [value]="getStatusLabel(task.status)" 
                      [severity]="getStatusSeverity(task.status)"
                      [icon]="getStatusIcon(task.status)"
                    ></p-tag>
                  </td>
                  <td>
                    <div class="flex gap-2">
                      <!-- Process Task Button -->
                      <p-button 
                        *ngIf="task.status === 'not_started'"
                        label="Process Task" 
                        icon="pi pi-play"
                        size="small"
                        [loading]="processingTaskIds.includes(task.id)"
                        (click)="processTask(task)"
                      ></p-button>
                      
                      <!-- Continue Workflow Button -->
                      <p-button 
                        *ngIf="task.status === 'in_progress' && task.context_id"
                        label="Continue" 
                        icon="pi pi-arrow-right"
                        size="small"
                        (click)="continueWorkflow(task)"
                      ></p-button>
                      
                      <!-- View Jira Card Button -->
                      <p-button 
                        *ngIf="task.status === 'completed' && task.jira_card_id"
                        label="View Card" 
                        icon="pi pi-external-link"
                        size="small"
                        [text]="true"
                        (click)="viewJiraCard(task)"
                      ></p-button>
                      
                      <!-- Task Details Button -->
                      <p-button 
                        icon="pi pi-info-circle" 
                        [text]="true"
                        size="small"
                        pTooltip="View task details"
                        (click)="viewTaskDetails(task)"
                      ></p-button>
                    </div>
                  </td>
                </tr>
              </ng-template>
              
              <ng-template pTemplate="emptymessage">
                <tr>
                  <td colspan="4" class="text-center p-4">
                    <p-message 
                      *ngIf="!searchQuery"
                      severity="info" 
                      text="No tasks found in tasks.md. Ask your architect to add tasks to the file."
                      [closable]="false"
                    ></p-message>
                    <p-message 
                      *ngIf="searchQuery"
                      severity="info" 
                      [text]="'No tasks match your search: ' + searchQuery"
                      [closable]="false"
                    ></p-message>
                  </td>
                </tr>
              </ng-template>
            </p-table>
          </p-card>
        </div>

        <!-- System Status Card -->
        <div class="col-12 lg:col-4">
          <p-card header="System Status" [style]="{'height': '100%'}">
            <div class="flex flex-column gap-3">
              <div class="flex justify-content-between align-items-center">
                <span>API Health:</span>
                <p-tag 
                  [value]="systemHealth?.status || 'Unknown'" 
                  [severity]="getHealthSeverity(systemHealth?.status)"
                ></p-tag>
              </div>
              
              <div class="flex justify-content-between align-items-center">
                <span>Task Manager:</span>
                <p-tag 
                  [value]="taskManagerStatus" 
                  [severity]="taskManagerStatus === 'Ready' ? 'success' : 'danger'"
                ></p-tag>
              </div>
              
              <div class="flex justify-content-between align-items-center">
                <span>Repository Scanner:</span>
                <p-tag 
                  [value]="systemHealth?.repository_scanner ? 'Active' : 'Inactive'" 
                  [severity]="systemHealth?.repository_scanner ? 'success' : 'danger'"
                ></p-tag>
              </div>
              
              <div class="flex justify-content-between align-items-center">
                <span>Database:</span>
                <p-tag 
                  [value]="systemHealth?.database_connector ? 'Connected' : 'Not Configured'" 
                  [severity]="systemHealth?.database_connector ? 'success' : 'warning'"
                ></p-tag>
              </div>
              
              <div class="flex justify-content-between align-items-center">
                <span>AI Agents:</span>
                <p-tag 
                  [value]="systemHealth?.agent_orchestrator ? 'Ready' : 'Initializing'" 
                  [severity]="systemHealth?.agent_orchestrator ? 'success' : 'warning'"
                ></p-tag>
              </div>
              
              <div class="flex justify-content-between align-items-center">
                <span>Repositories Found:</span>
                <p-tag 
                  [value]="repositories?.length?.toString() || '0'" 
                  severity="info"
                ></p-tag>
              </div>
              
              <p-button 
                label="Refresh Status" 
                icon="pi pi-refresh"
                [text]="true"
                size="small"
                (click)="refreshSystemStatus()"
                class="w-full mt-2"
              ></p-button>
            </div>
          </p-card>
        </div>
      </div>

      <!-- Repository Overview Tab -->
      <div class="col-12 mt-4">
        <p-tabView>
          <p-tabPanel header="Repository Overview" leftIcon="pi pi-folder">
            <div class="grid">
              <div class="col-12">
                <div class="flex justify-content-between align-items-center mb-3">
                  <h3 class="m-0">Available Repositories ({{repositories?.length || 0}})</h3>
                  <p-button 
                    label="Scan Repositories" 
                    icon="pi pi-search"
                    [loading]="isLoadingRepositories"
                    (click)="loadRepositories()"
                  ></p-button>
                </div>
                
                <p-table 
                  [value]="repositories || []" 
                  [loading]="isLoadingRepositories"
                  [paginator]="true"
                  [rows]="10"
                  [responsive]="true"
                >
                  <ng-template pTemplate="header">
                    <tr>
                      <th>Name</th>
                      <th>Primary Language</th>
                      <th>Frameworks</th>
                      <th>Files</th>
                      <th>Size (MB)</th>
                      <th>Last Scanned</th>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="body" let-repo>
                    <tr>
                      <td>
                        <strong>{{repo.name}}</strong>
                        <br>
                        <small class="text-600">{{repo.path}}</small>
                      </td>
                      <td>
                        <p-tag [value]="repo.primary_language" severity="info"></p-tag>
                      </td>
                      <td>
                        <div class="flex flex-wrap gap-1">
                          <p-tag 
                            *ngFor="let fw of repo.frameworks.slice(0, 3)" 
                            [value]="fw" 
                            severity="secondary"
                            class="text-xs"
                          ></p-tag>
                          <span *ngIf="repo.frameworks.length > 3" class="text-xs text-600">
                            +{{repo.frameworks.length - 3}} more
                          </span>
                        </div>
                      </td>
                      <td>{{repo.file_count | number}}</td>
                      <td>{{repo.size_mb | number:'1.1-2'}}</td>
                      <td>
                        <small>{{formatDate(repo.last_scanned)}}</small>
                      </td>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="emptymessage">
                    <tr>
                      <td colspan="6" class="text-center p-4">
                        <p-message 
                          severity="info" 
                          text="No repositories found. Click 'Scan Repositories' to search for repositories."
                          [closable]="false"
                        ></p-message>
                      </td>
                    </tr>
                  </ng-template>
                </p-table>
              </div>
            </div>
          </p-tabPanel>
          
          <p-tabPanel header="Task Categories" leftIcon="pi pi-tags">
            <div class="grid" *ngIf="taskCategories">
              <div class="col-12">
                <p-accordion [multiple]="true">
                  <p-accordionTab 
                    *ngFor="let category of getCategoryKeys()" 
                    [header]="category + ' (' + taskCategories[category].length + ')'"
                  >
                    <p-table [value]="taskCategories[category]" [paginator]="false">
                      <ng-template pTemplate="header">
                        <tr>
                          <th style="width: 60px">ID</th>
                          <th>Description</th>
                          <th style="width: 100px">Status</th>
                          <th style="width: 120px">Actions</th>
                        </tr>
                      </ng-template>
                      <ng-template pTemplate="body" let-task>
                        <tr>
                          <td>{{task.id}}</td>
                          <td>{{task.description}}</td>
                          <td>
                            <p-tag 
                              [value]="getStatusLabel(task.status)" 
                              [severity]="getStatusSeverity(task.status)"
                            ></p-tag>
                          </td>
                          <td>
                            <p-button 
                              *ngIf="task.status === 'not_started'"
                              label="Process" 
                              icon="pi pi-play"
                              size="small"
                              [loading]="processingTaskIds.includes(task.id)"
                              (click)="processTask(task)"
                            ></p-button>
                            <p-button 
                              *ngIf="task.status === 'in_progress'"
                              label="Continue" 
                              icon="pi pi-arrow-right"
                              size="small"
                              (click)="continueWorkflow(task)"
                            ></p-button>
                          </td>
                        </tr>
                      </ng-template>
                    </p-table>
                  </p-accordionTab>
                </p-accordion>
              </div>
            </div>
          </p-tabPanel>
        </p-tabView>
      </div>

      <p-toast></p-toast>
      <p-confirmDialog></p-confirmDialog>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 1rem;
      max-width: 1400px;
      margin: 0 auto;
    }

    .task-description {
      max-width: 500px;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.4;
    }

    .task-summary .p-chip {
      font-size: 0.875rem;
    }

    .task-header {
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 1rem;
    }

    .field-group .field {
      margin-bottom: 1rem;
    }

    .field label {
      font-weight: 600;
      display: block;
      margin-bottom: 0.25rem;
    }

    /* Status-specific styling */
    .p-chip.p-chip-info {
      background-color: #eff6ff;
      color: #1d4ed8;
    }

    .p-chip.p-chip-warning {
      background-color: #fef3c7;
      color: #d97706;
    }

    .p-chip.p-chip-success {
      background-color: #d1fae5;
      color: #065f46;
    }
  `]
})
export class DashboardComponent implements OnInit {
  // Task management
  tasks: Task[] = [];
  displayedTasks: Task[] = [];
  taskSummary: TaskSummary | null = null;
  taskCategories: any = {};
  taskManagerStatus = 'Unknown';
  
  // UI state
  isLoadingTasks = false;
  isReloadingTasks = false;
  processingTaskIds: number[] = [];
  showSearch = false;
  searchQuery = '';
  
  // System status
  repositories: Repository[] = [];
  systemHealth: any = null;
  isLoadingRepositories = false;

  constructor(
    private apiService: ApiService,
    private router: Router,
    private messageService: MessageService,
    private validationService: ValidationService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.refreshSystemStatus();
    this.loadTasks();
    this.loadRepositories();
    this.loadTaskCategories();
  }

  loadTasks() {
    this.isLoadingTasks = true;
    this.apiService.getAllTasks().subscribe({
      next: (response) => {
        this.tasks = response.tasks;
        this.displayedTasks = [...this.tasks];
        this.taskSummary = response.summary;
        this.taskManagerStatus = 'Ready';
        this.isLoadingTasks = false;
        
        this.messageService.add({
          severity: 'success',
          summary: 'Tasks Loaded',
          detail: `Found ${response.total_tasks} tasks from tasks.md`
        });
      },
      error: (error) => {
        console.error('Failed to load tasks:', error);
        this.isLoadingTasks = false;
        this.taskManagerStatus = 'Error';
        
        if (error.error?.error?.error_id) {
          const errorResponse = error.error.error;
          this.messageService.add({
            severity: 'error',
            summary: 'Task Loading Failed',
            detail: `${errorResponse.message} (Error ID: ${errorResponse.error_id})`
          });
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Task Loading Failed',
            detail: error.error?.detail || error.message || 'Unable to load tasks'
          });
        }
      }
    });
  }

  loadTaskCategories() {
    this.apiService.getTaskCategories().subscribe({
      next: (response) => {
        this.taskCategories = response.categories;
      },
      error: (error) => {
        console.error('Failed to load task categories:', error);
      }
    });
  }

  processTask(task: Task) {
    this.confirmationService.confirm({
      message: `Process task "${task.description.substring(0, 50)}..."?`,
      header: 'Confirm Task Processing',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.processingTaskIds.push(task.id);
        
        this.apiService.processTask(task.id).subscribe({
          next: (response) => {
            this.processingTaskIds = this.processingTaskIds.filter(id => id !== task.id);
            
            // Update local task status
            const taskIndex = this.tasks.findIndex(t => t.id === task.id);
            if (taskIndex !== -1) {
              this.tasks[taskIndex].status = 'in_progress';
              this.tasks[taskIndex].context_id = response.context_id;
            }
            
            this.messageService.add({
              severity: 'success',
              summary: 'Task Processing Started',
              detail: response.message
            });
            
            // Navigate to workflow
            this.apiService.setCurrentContext(response.context_id);
            this.router.navigate(['/workflow', response.context_id]);
          },
          error: (error) => {
            this.processingTaskIds = this.processingTaskIds.filter(id => id !== task.id);
            console.error('Failed to process task:', error);
            
            if (error.error?.error?.error_id) {
              const errorResponse = error.error.error;
              this.messageService.add({
                severity: 'error',
                summary: 'Task Processing Failed',
                detail: `${errorResponse.message} (Error ID: ${errorResponse.error_id})`
              });
            } else {
              this.messageService.add({
                severity: 'error',
                summary: 'Task Processing Failed',
                detail: error.error?.detail || error.message || 'Unable to process task'
              });
            }
          }
        });
      }
    });
  }

  continueWorkflow(task: Task) {
    if (task.context_id) {
      this.apiService.setCurrentContext(task.context_id);
      this.router.navigate(['/workflow', task.context_id]);
    }
  }

  viewJiraCard(task: Task) {
    if (task.jira_card_id) {
      // This would open Jira card in new tab - implement based on your Jira URL structure
      this.messageService.add({
        severity: 'info',
        summary: 'Jira Card',
        detail: `Card ID: ${task.jira_card_id}`
      });
    }
  }

  viewTaskDetails(task: Task) {
    this.messageService.add({
      severity: 'info',
      summary: 'Task Details',
      detail: `Task ${task.id}: ${task.description}`,
      life: 6000
    });
  }

  reloadTasks() {
    this.isReloadingTasks = true;
    this.apiService.reloadTasks().subscribe({
      next: (response) => {
        this.isReloadingTasks = false;
        this.loadTasks(); // Reload the tasks
        this.loadTaskCategories(); // Reload categories
        
        this.messageService.add({
          severity: 'success',
          summary: 'Tasks Reloaded',
          detail: response.message
        });
      },
      error: (error) => {
        this.isReloadingTasks = false;
        console.error('Failed to reload tasks:', error);
        
        this.messageService.add({
          severity: 'error',
          summary: 'Task Reload Failed',
          detail: error.error?.detail || error.message || 'Unable to reload tasks'
        });
      }
    });
  }

  toggleSearch() {
    this.showSearch = !this.showSearch;
    if (!this.showSearch) {
      this.clearSearch();
    }
  }

  searchTasks() {
    if (!this.searchQuery.trim()) {
      this.clearSearch();
      return;
    }

    this.apiService.searchTasks(this.searchQuery.trim()).subscribe({
      next: (response) => {
        this.displayedTasks = response.tasks;
        this.messageService.add({
          severity: 'info',
          summary: 'Search Results',
          detail: `Found ${response.total_matches} matching tasks`
        });
      },
      error: (error) => {
        console.error('Search failed:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Search Failed',
          detail: 'Unable to search tasks'
        });
      }
    });
  }

  onSearchInput() {
    // Auto-search after typing stops (debounced)
    if (this.searchQuery.trim() === '') {
      this.clearSearch();
    }
  }

  clearSearch() {
    this.searchQuery = '';
    this.displayedTasks = [...this.tasks];
  }

  getCategoryKeys(): string[] {
    return Object.keys(this.taskCategories);
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'not_started': return 'Not Started';
      case 'in_progress': return 'In Progress';
      case 'completed': return 'Completed';
      default: return status;
    }
  }

  getStatusSeverity(status: string): 'success' | 'info' | 'warning' | 'danger' {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'not_started': return 'info';
      default: return 'info';
    }
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'completed': return 'pi pi-check';
      case 'in_progress': return 'pi pi-spin pi-spinner';
      case 'not_started': return 'pi pi-clock';
      default: return 'pi pi-question';
    }
  }

  refreshSystemStatus() {
    this.apiService.checkHealth().subscribe({
      next: (health) => {
        this.systemHealth = health;
        this.messageService.add({
          severity: 'success',
          summary: 'System Status Updated',
          detail: `System is ${health.status}`
        });
      },
      error: (error) => {
        console.error('Health check failed:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'System Check Failed',
          detail: 'Unable to connect to backend API'
        });
      }
    });
  }

  loadRepositories() {
    this.isLoadingRepositories = true;
    this.apiService.getRepositories().subscribe({
      next: (response) => {
        this.repositories = response.repositories;
        this.isLoadingRepositories = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Repositories Loaded',
          detail: `Found ${response.repositories.length} repositories`
        });
      },
      error: (error) => {
        console.error('Failed to load repositories:', error);
        this.isLoadingRepositories = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Repository Scan Failed',
          detail: 'Unable to scan repositories'
        });
      }
    });
  }

  getHealthSeverity(status: string): 'success' | 'info' | 'warning' | 'danger' {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'danger';
      default: return 'info';
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
}