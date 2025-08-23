export interface Task {
  id: number;
  description: string;
  status: 'not_started' | 'in_progress' | 'completed';
  context_id?: string;
  jira_card_id?: string;
  raw_line?: string;
}

export interface TaskSummary {
  total: number;
  not_started: number;
  in_progress: number;
  completed: number;
}

export interface TaskCategory {
  [categoryName: string]: Task[];
}

export interface TaskSearchResult {
  query: string;
  tasks: Task[];
  total_matches: number;
}

export interface ProcessTaskRequest {
  task_id: number;
}

export interface ProcessTaskResponse {
  status: string;
  context_id: string;
  task_id: string;
  message: string;
}