import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { Task, TaskSummary, TaskCategory, TaskSearchResult, ProcessTaskResponse } from '../models/task.model';

export interface Repository {
  name: string;
  path: string;
  primary_language: string;
  languages: string[];
  frameworks: string[];
  file_count: number;
  size_mb: number;
  last_scanned: string;
}

export interface TaskCreateRequest {
  task_id: string;
  description: string;
  task_type: string;
}

export interface WorkflowContext {
  context_id: string;
  task: {
    id: string;
    description: string;
    type: string;
    technologies: string[];
    workflow_step: string;
  };
  repositories?: {
    selected: string[];
    count: number;
    relevance_scores: { [key: string]: number };
  };
  database?: {
    schema: string;
    connection_status: boolean;
    relevant_tables: string[];
    table_count: number;
  };
}

export interface WorkflowStep {
  context_id: string;
  step_data: any;
  next_step: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:8000/api';
  private currentContextSubject = new BehaviorSubject<string | null>(null);
  public currentContext$ = this.currentContextSubject.asObservable();

  constructor(private http: HttpClient) {}

  // System Health
  checkHealth(): Observable<any> {
    return this.http.get(`${this.baseUrl}/health`);
  }

  // Repository Management
  getRepositories(): Observable<{ status: string; repositories: Repository[] }> {
    return this.http.get<{ status: string; repositories: Repository[] }>(`${this.baseUrl}/repositories`);
  }

  // Database Management
  testDatabaseConnection(): Observable<any> {
    return this.http.get(`${this.baseUrl}/database/test`);
  }

  // Task Management (New - from tasks.md)
  getAllTasks(): Observable<{ status: string; tasks: Task[]; summary: TaskSummary; categories: any; total_tasks: number }> {
    return this.http.get<{ status: string; tasks: Task[]; summary: TaskSummary; categories: any; total_tasks: number }>(`${this.baseUrl}/tasks`);
  }

  getTaskCategories(): Observable<{ status: string; categories: TaskCategory }> {
    return this.http.get<{ status: string; categories: TaskCategory }>(`${this.baseUrl}/tasks/categories`);
  }

  searchTasks(query: string): Observable<{ status: string } & TaskSearchResult> {
    return this.http.get<{ status: string } & TaskSearchResult>(`${this.baseUrl}/tasks/search?query=${encodeURIComponent(query)}`);
  }

  getTaskDetails(taskId: number): Observable<{ status: string; task: Task }> {
    return this.http.get<{ status: string; task: Task }>(`${this.baseUrl}/tasks/${taskId}`);
  }

  processTask(taskId: number): Observable<ProcessTaskResponse> {
    return this.http.post<ProcessTaskResponse>(`${this.baseUrl}/tasks/${taskId}/process`, {});
  }

  reloadTasks(): Observable<{ status: string; message: string; total_tasks: number }> {
    return this.http.post<{ status: string; message: string; total_tasks: number }>(`${this.baseUrl}/tasks/reload`, {});
  }

  // Task Management (Legacy - keeping for compatibility)
  createTask(request: TaskCreateRequest): Observable<{ status: string; context_id: string }> {
    return this.http.post<{ status: string; context_id: string }>(`${this.baseUrl}/tasks`, request);
  }

  // Context Management
  setRepositoryContext(contextId: string, repositoryNames: string[]): Observable<any> {
    return this.http.post(`${this.baseUrl}/context/repository`, {
      context_id: contextId,
      repository_names: repositoryNames
    });
  }

  setDatabaseContext(contextId: string, schemaName: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/context/database`, {
      context_id: contextId,
      schema_name: schemaName
    });
  }

  getContext(contextId: string): Observable<{ status: string; context: WorkflowContext }> {
    return this.http.get<{ status: string; context: WorkflowContext }>(`${this.baseUrl}/context/${contextId}`);
  }

  analyzeRepositoryRelevance(contextId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/context/${contextId}/relevance`);
  }

  // Workflow Steps
  generateQuestions(workflowStep: WorkflowStep): Observable<any> {
    return this.http.post(`${this.baseUrl}/workflow/questions`, workflowStep);
  }

  generateAnswers(workflowStep: WorkflowStep): Observable<any> {
    return this.http.post(`${this.baseUrl}/workflow/answers`, workflowStep);
  }

  generateJiraCard(workflowStep: WorkflowStep): Observable<any> {
    return this.http.post(`${this.baseUrl}/workflow/card`, workflowStep);
  }

  // Jira Integration
  createJiraCard(contextId: string, templateKey: string, cardData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/jira/create`, null, {
      params: {
        context_id: contextId,
        template_key: templateKey,
        card_data: JSON.stringify(cardData)
      }
    });
  }

  // Current Context Management
  setCurrentContext(contextId: string) {
    this.currentContextSubject.next(contextId);
  }

  getCurrentContext(): string | null {
    return this.currentContextSubject.value;
  }
}