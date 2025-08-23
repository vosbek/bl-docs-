import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StepsModule } from 'primeng/steps';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { MultiSelectModule } from 'primeng/multiselect';
import { InputTextModule } from 'primeng/inputtext';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { EditorModule } from 'primeng/editor';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { MenuItem, MessageService, ConfirmationService } from 'primeng/api';

import { ApiService, Repository, WorkflowContext } from '../../services/api.service';

interface JiraCard {
  title: string;
  description: string;
  epic: string;
  labels: string[];
  story_points: number;
  implementation_files: string[];
  database_changes: string[];
}

@Component({
  selector: 'app-workflow',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    StepsModule,
    CardModule,
    ButtonModule,
    MultiSelectModule,
    InputTextModule,
    ProgressSpinnerModule,
    EditorModule,
    TableModule,
    TagModule,
    ToastModule,
    ConfirmDialogModule,
    DialogModule
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <div class="workflow-container">
      <!-- Header with Context Info -->
      <div class="context-header mb-4">
        <p-card>
          <div class="flex justify-content-between align-items-center">
            <div>
              <h2 class="m-0">{{context?.task?.id}} - {{context?.task?.type | titlecase}}</h2>
              <p class="text-600 mt-1 mb-0">{{context?.task?.description}}</p>
            </div>
            <div class="flex gap-2">
              <p-button 
                icon="pi pi-arrow-left" 
                [text]="true" 
                label="Back to Dashboard"
                (click)="backToDashboard()"
              ></p-button>
            </div>
          </div>
        </p-card>
      </div>

      <!-- Workflow Steps -->
      <div class="steps-container mb-4">
        <p-steps 
          [model]="steps" 
          [(activeIndex)]="activeStep"
          [readonly]="true"
        ></p-steps>
      </div>

      <!-- Step Content -->
      <div class="step-content">
        <!-- Step 1: Repository Selection -->
        <p-card *ngIf="activeStep === 0" header="Step 1: Repository Context Selection">
          <div class="grid">
            <div class="col-12 lg:col-8">
              <h4>Select Relevant Repositories</h4>
              <p class="text-600 mb-3">
                Choose repositories that are relevant to this task. The system will analyze these for existing patterns.
              </p>
              
              <div class="field">
                <label for="repoSelect">Available Repositories ({{availableRepositories.length}})</label>
                <p-multiSelect
                  [(ngModel)]="selectedRepositories"
                  [options]="availableRepositories"
                  optionLabel="name"
                  optionValue="name"
                  placeholder="Select repositories..."
                  [filter]="true"
                  filterBy="name,primary_language"
                  class="w-full"
                  [showHeader]="false"
                >
                  <ng-template pTemplate="item" let-repo>
                    <div class="flex align-items-center gap-2">
                      <strong>{{repo.name}}</strong>
                      <p-tag [value]="repo.primary_language" severity="info" class="text-xs"></p-tag>
                      <span class="text-600 text-sm">{{repo.file_count}} files</span>
                    </div>
                  </ng-template>
                </p-multiSelect>
              </div>
              
              <div class="flex gap-2 mt-3">
                <p-button 
                  label="Analyze Relevance" 
                  icon="pi pi-search"
                  [loading]="isAnalyzingRelevance"
                  (click)="analyzeRelevance()"
                  [disabled]="!contextId"
                ></p-button>
                <p-button 
                  label="Select All Recommended" 
                  icon="pi pi-check-circle"
                  severity="secondary"
                  [disabled]="!relevanceAnalysis"
                  (click)="selectRecommendedRepos()"
                ></p-button>
              </div>
            </div>
            
            <div class="col-12 lg:col-4" *ngIf="relevanceAnalysis">
              <h4>Relevance Analysis</h4>
              <div class="recommendations">
                <div 
                  *ngFor="let match of relevanceAnalysis.top_matches.slice(0, 5)" 
                  class="recommendation-item p-2 border-round mb-2"
                  [class.selected]="selectedRepositories.includes(match.name)"
                >
                  <div class="flex justify-content-between align-items-center">
                    <strong>{{match.name}}</strong>
                    <p-tag 
                      [value]="(match.relevance_score * 100 | number:'1.0-0') + '%'" 
                      [severity]="getRelevanceSeverity(match.relevance_score)"
                    ></p-tag>
                  </div>
                  <div class="flex gap-1 mt-1">
                    <small class="text-600">{{match.primary_language}}</small>
                    <small *ngFor="let fw of match.frameworks.slice(0, 2)" class="text-600">• {{fw}}</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="step-actions mt-4">
            <p-button 
              label="Set Repository Context" 
              icon="pi pi-arrow-right"
              [loading]="isSettingRepoContext"
              [disabled]="selectedRepositories.length === 0"
              (click)="setRepositoryContext()"
            ></p-button>
          </div>
        </p-card>

        <!-- Step 2: Questions Generation -->
        <p-card *ngIf="activeStep === 1" header="Step 2: Developer Questions">
          <div class="grid">
            <div class="col-12">
              <div class="flex justify-content-between align-items-center mb-3">
                <h4 class="m-0">AI-Generated Questions</h4>
                <p-button 
                  label="Generate Questions" 
                  icon="pi pi-robot"
                  [loading]="isGeneratingQuestions"
                  (click)="generateQuestions()"
                ></p-button>
              </div>
              
              <div *ngIf="questions.length > 0">
                <p-editor 
                  [(ngModel)]="questionsText" 
                  [style]="{'height':'400px'}"
                  placeholder="AI-generated questions will appear here..."
                >
                </p-editor>
                
                <div class="step-actions mt-4">
                  <div class="flex gap-2">
                    <p-button 
                      label="Back" 
                      icon="pi pi-arrow-left"
                      severity="secondary"
                      (click)="previousStep()"
                    ></p-button>
                    <p-button 
                      label="Approve Questions" 
                      icon="pi pi-arrow-right"
                      (click)="approveQuestions()"
                    ></p-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </p-card>

        <!-- Step 3: Answers Generation -->
        <p-card *ngIf="activeStep === 2" header="Step 3: Technical Lead Analysis">
          <div class="grid">
            <div class="col-12">
              <div class="flex justify-content-between align-items-center mb-3">
                <h4 class="m-0">AI-Generated Technical Answers</h4>
                <p-button 
                  label="Generate Answers" 
                  icon="pi pi-robot"
                  [loading]="isGeneratingAnswers"
                  (click)="generateAnswers()"
                ></p-button>
              </div>
              
              <div *ngIf="answers.length > 0">
                <p-editor 
                  [(ngModel)]="answersText" 
                  [style]="{'height':'500px'}"
                  placeholder="Technical analysis and answers will appear here..."
                >
                </p-editor>
                
                <div class="step-actions mt-4">
                  <div class="flex gap-2">
                    <p-button 
                      label="Back" 
                      icon="pi pi-arrow-left"
                      severity="secondary"
                      (click)="previousStep()"
                    ></p-button>
                    <p-button 
                      label="Approve Answers" 
                      icon="pi pi-arrow-right"
                      (click)="approveAnswers()"
                    ></p-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </p-card>

        <!-- Step 4: Jira Card Generation -->
        <p-card *ngIf="activeStep === 3" header="Step 4: Jira Card Generation">
          <div class="grid">
            <div class="col-12">
              <div class="flex justify-content-between align-items-center mb-3">
                <h4 class="m-0">Generated Jira Card</h4>
                <p-button 
                  label="Generate Card" 
                  icon="pi pi-robot"
                  [loading]="isGeneratingCard"
                  (click)="generateJiraCard()"
                ></p-button>
              </div>
              
              <div *ngIf="jiraCard" class="card-preview">
                <div class="grid">
                  <div class="col-12 lg:col-8">
                    <h5>Card Description</h5>
                    <div [innerHTML]="jiraCard.description" class="card-description p-3 border-round bg-gray-50"></div>
                    
                    <h5 class="mt-4">Implementation Files</h5>
                    <p-table [value]="jiraCard.implementation_files" [scrollable]="true">
                      <ng-template pTemplate="header">
                        <tr>
                          <th>File Path</th>
                        </tr>
                      </ng-template>
                      <ng-template pTemplate="body" let-file>
                        <tr>
                          <td><code>{{file}}</code></td>
                        </tr>
                      </ng-template>
                    </p-table>
                    
                    <div *ngIf="jiraCard.database_changes?.length > 0">
                      <h5 class="mt-4">Database Changes</h5>
                      <div *ngFor="let change of jiraCard.database_changes" class="mb-2">
                        <code class="p-2 bg-gray-100 border-round block">{{change}}</code>
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-12 lg:col-4">
                    <h5>Card Details</h5>
                    <div class="field-group">
                      <div class="field">
                        <label>Title:</label>
                        <p>{{jiraCard.title}}</p>
                      </div>
                      <div class="field">
                        <label>Epic:</label>
                        <p>{{jiraCard.epic}}</p>
                      </div>
                      <div class="field">
                        <label>Story Points:</label>
                        <p-tag [value]="jiraCard.story_points.toString()" severity="info"></p-tag>
                      </div>
                      <div class="field">
                        <label>Labels:</label>
                        <div class="flex flex-wrap gap-1">
                          <p-tag *ngFor="let label of jiraCard.labels" [value]="label" severity="secondary"></p-tag>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="step-actions mt-4">
                  <div class="flex gap-2">
                    <p-button 
                      label="Back" 
                      icon="pi pi-arrow-left"
                      severity="secondary"
                      (click)="previousStep()"
                    ></p-button>
                    <p-button 
                      label="Create Jira Card" 
                      icon="pi pi-external-link"
                      (click)="createJiraCard()"
                      [loading]="isCreatingJiraCard"
                    ></p-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </p-card>
      </div>

      <!-- Template Selection Dialog -->
      <p-dialog 
        header="Select Jira Template" 
        [(visible)]="showTemplateDialog" 
        [modal]="true" 
        [style]="{width: '500px'}"
      >
        <div class="field">
          <label for="templateKey">Template Card Key</label>
          <input 
            pInputText 
            id="templateKey" 
            [(ngModel)]="templateKey"
            placeholder="e.g., PROJ-123"
            class="w-full"
          />
          <small class="text-600">Enter the key of an existing Jira card to use as a template</small>
        </div>
        
        <div class="flex justify-content-end gap-2 mt-4">
          <p-button 
            label="Cancel" 
            severity="secondary"
            (click)="showTemplateDialog = false"
          ></p-button>
          <p-button 
            label="Create Card" 
            [disabled]="!templateKey"
            (click)="confirmCreateJiraCard()"
          ></p-button>
        </div>
      </p-dialog>

      <p-toast></p-toast>
    </div>
  `,
  styles: [`
    .workflow-container {
      padding: 1rem;
      max-width: 1400px;
      margin: 0 auto;
    }

    .context-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 8px;
      padding: 0;
    }

    .context-header p-card {
      background: transparent;
    }

    .context-header h2, .context-header p {
      color: white;
    }

    .steps-container {
      margin-bottom: 2rem;
    }

    .step-actions {
      border-top: 1px solid #e9ecef;
      padding-top: 1rem;
      display: flex;
      justify-content: flex-end;
    }

    .recommendation-item {
      background: #f8f9fa;
      border: 2px solid transparent;
      transition: all 0.2s;
    }

    .recommendation-item.selected {
      border-color: var(--primary-color);
      background: var(--primary-50);
    }

    .card-description {
      max-height: 400px;
      overflow-y: auto;
    }

    .field-group .field {
      margin-bottom: 1rem;
    }

    .field label {
      font-weight: 600;
      display: block;
      margin-bottom: 0.25rem;
    }
  `]
})
export class WorkflowComponent implements OnInit {
  contextId: string = '';
  context: WorkflowContext | null = null;

  steps: MenuItem[] = [
    { label: 'Repository Context' },
    { label: 'Generate Questions' },
    { label: 'Generate Answers' },
    { label: 'Create Jira Card' }
  ];

  activeStep = 0;

  // Repository selection
  availableRepositories: Repository[] = [];
  selectedRepositories: string[] = [];
  relevanceAnalysis: any = null;
  isAnalyzingRelevance = false;
  isSettingRepoContext = false;

  // Questions step
  questions: string[] = [];
  questionsText = '';
  isGeneratingQuestions = false;

  // Answers step
  answers: any[] = [];
  answersText = '';
  isGeneratingAnswers = false;

  // Jira card step
  jiraCard: JiraCard | null = null;
  isGeneratingCard = false;
  isCreatingJiraCard = false;
  showTemplateDialog = false;
  templateKey = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.contextId = this.route.snapshot.paramMap.get('contextId') || '';
    if (this.contextId) {
      this.loadContext();
      this.loadRepositories();
    }
  }

  loadContext() {
    this.apiService.getContext(this.contextId).subscribe({
      next: (response) => {
        this.context = response.context;
        // Set active step based on workflow progress
        this.setActiveStepFromContext();
      },
      error: (error) => {
        console.error('Failed to load context:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Context Loading Failed',
          detail: 'Unable to load workflow context'
        });
      }
    });
  }

  loadRepositories() {
    this.apiService.getRepositories().subscribe({
      next: (response) => {
        this.availableRepositories = response.repositories;
      },
      error: (error) => {
        console.error('Failed to load repositories:', error);
      }
    });
  }

  setActiveStepFromContext() {
    if (!this.context) return;
    
    const step = this.context.task.workflow_step;
    switch (step) {
      case 'questions': this.activeStep = 0; break;
      case 'answers': this.activeStep = 1; break;
      case 'card_generation': this.activeStep = 2; break;
      default: this.activeStep = 0;
    }
  }

  analyzeRelevance() {
    this.isAnalyzingRelevance = true;
    this.apiService.analyzeRepositoryRelevance(this.contextId).subscribe({
      next: (response) => {
        this.relevanceAnalysis = response.analysis;
        this.isAnalyzingRelevance = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Relevance Analysis Complete',
          detail: `Analyzed ${this.relevanceAnalysis.total_repositories} repositories`
        });
      },
      error: (error) => {
        console.error('Relevance analysis failed:', error);
        this.isAnalyzingRelevance = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Analysis Failed',
          detail: 'Unable to analyze repository relevance'
        });
      }
    });
  }

  selectRecommendedRepos() {
    if (!this.relevanceAnalysis) return;
    
    const recommended = this.relevanceAnalysis.top_matches
      .filter((match: any) => match.relevance_score > 0.3)
      .slice(0, 5)
      .map((match: any) => match.name);
    
    this.selectedRepositories = recommended;
    this.messageService.add({
      severity: 'info',
      summary: 'Recommendations Applied',
      detail: `Selected ${recommended.length} recommended repositories`
    });
  }

  setRepositoryContext() {
    this.isSettingRepoContext = true;
    this.apiService.setRepositoryContext(this.contextId, this.selectedRepositories).subscribe({
      next: (response) => {
        this.isSettingRepoContext = false;
        this.activeStep = 1;
        this.messageService.add({
          severity: 'success',
          summary: 'Repository Context Set',
          detail: `Set context for ${this.selectedRepositories.length} repositories`
        });
      },
      error: (error) => {
        console.error('Failed to set repository context:', error);
        this.isSettingRepoContext = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Context Setting Failed',
          detail: error.error?.detail || 'Unable to set repository context'
        });
      }
    });
  }

  generateQuestions() {
    this.isGeneratingQuestions = true;
    const stepData = {
      task_description: this.context?.task?.description,
      selected_repositories: this.selectedRepositories
    };

    this.apiService.generateQuestions({
      context_id: this.contextId,
      step_data: stepData,
      next_step: 'answers'
    }).subscribe({
      next: (response) => {
        this.questions = response.result.questions || [];
        this.questionsText = this.questions.map((q, i) => `${i + 1}. ${q}`).join('\n\n');
        this.isGeneratingQuestions = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Questions Generated',
          detail: `Generated ${this.questions.length} questions`
        });
      },
      error: (error) => {
        console.error('Failed to generate questions:', error);
        this.isGeneratingQuestions = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Question Generation Failed',
          detail: error.error?.detail || 'Unable to generate questions'
        });
      }
    });
  }

  approveQuestions() {
    // Parse questions from editor text
    const lines = this.questionsText.split('\n').filter(line => line.trim());
    this.questions = lines.map(line => line.replace(/^\d+\.\s*/, '').trim()).filter(q => q);
    
    this.activeStep = 2;
    this.messageService.add({
      severity: 'info',
      summary: 'Questions Approved',
      detail: 'Proceeding to answer generation'
    });
  }

  generateAnswers() {
    this.isGeneratingAnswers = true;
    const stepData = {
      questions: this.questions,
      task_description: this.context?.task?.description
    };

    this.apiService.generateAnswers({
      context_id: this.contextId,
      step_data: stepData,
      next_step: 'card_generation'
    }).subscribe({
      next: (response) => {
        this.answers = response.result.answers || [];
        this.answersText = this.formatAnswersForEditor(this.answers);
        this.isGeneratingAnswers = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Answers Generated',
          detail: `Generated ${this.answers.length} detailed answers`
        });
      },
      error: (error) => {
        console.error('Failed to generate answers:', error);
        this.isGeneratingAnswers = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Answer Generation Failed',
          detail: error.error?.detail || 'Unable to generate answers'
        });
      }
    });
  }

  approveAnswers() {
    this.activeStep = 3;
    this.messageService.add({
      severity: 'info',
      summary: 'Answers Approved',
      detail: 'Proceeding to Jira card generation'
    });
  }

  generateJiraCard() {
    this.isGeneratingCard = true;
    const stepData = {
      questions: this.questions,
      answers: this.answers,
      task_description: this.context?.task?.description
    };

    this.apiService.generateJiraCard({
      context_id: this.contextId,
      step_data: stepData,
      next_step: 'complete'
    }).subscribe({
      next: (response) => {
        this.jiraCard = response.result.jira_card;
        this.isGeneratingCard = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Jira Card Generated',
          detail: 'Card is ready for creation'
        });
      },
      error: (error) => {
        console.error('Failed to generate Jira card:', error);
        this.isGeneratingCard = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Card Generation Failed',
          detail: error.error?.detail || 'Unable to generate Jira card'
        });
      }
    });
  }

  createJiraCard() {
    this.showTemplateDialog = true;
  }

  confirmCreateJiraCard() {
    if (!this.templateKey || !this.jiraCard) return;

    this.isCreatingJiraCard = true;
    this.showTemplateDialog = false;

    this.apiService.createJiraCard(this.contextId, this.templateKey, this.jiraCard).subscribe({
      next: (response) => {
        this.isCreatingJiraCard = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Jira Card Created',
          detail: `Card created: ${response.jira_key}`
        });
        
        this.confirmationService.confirm({
          message: `Jira card ${response.jira_key} created successfully! Would you like to view it in Jira?`,
          header: 'Card Created',
          icon: 'pi pi-check-circle',
          accept: () => {
            window.open(response.url, '_blank');
          }
        });
      },
      error: (error) => {
        console.error('Failed to create Jira card:', error);
        this.isCreatingJiraCard = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Card Creation Failed',
          detail: error.error?.detail || 'Unable to create Jira card'
        });
      }
    });
  }

  previousStep() {
    if (this.activeStep > 0) {
      this.activeStep--;
    }
  }

  backToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  getRelevanceSeverity(score: number): 'success' | 'info' | 'warning' | 'danger' {
    if (score > 0.7) return 'success';
    if (score > 0.5) return 'info';
    if (score > 0.3) return 'warning';
    return 'danger';
  }

  formatAnswersForEditor(answers: any[]): string {
    return answers.map((answer, index) => {
      return `### Question ${index + 1}: ${answer.question}\n\n**Answer**: ${answer.answer}\n\n**Code References**: ${answer.code_references?.join(', ') || 'None'}\n\n**Database References**: ${answer.database_references?.join(', ') || 'None'}\n\n---\n\n`;
    }).join('');
  }
}