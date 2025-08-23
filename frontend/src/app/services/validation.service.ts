import { Injectable } from '@angular/core';

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface TaskFormData {
  task_id: string;
  description: string;
  task_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class ValidationService {

  constructor() { }

  /**
   * Validate task creation form data
   */
  validateTaskForm(data: TaskFormData): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: []
    };

    // Validate task_id
    if (!data.task_id || !data.task_id.trim()) {
      result.errors.push('Task ID is required');
      result.isValid = false;
    } else {
      const taskId = data.task_id.trim();
      
      if (taskId.length < 3) {
        result.errors.push('Task ID must be at least 3 characters long');
        result.isValid = false;
      }
      
      if (taskId.length > 50) {
        result.errors.push('Task ID must be no more than 50 characters long');
        result.isValid = false;
      }
      
      // Check for valid characters (alphanumeric, dash, underscore)
      if (!/^[a-zA-Z0-9_-]+$/.test(taskId)) {
        result.errors.push('Task ID can only contain letters, numbers, dashes, and underscores');
        result.isValid = false;
      }
      
      // Suggest common patterns
      if (!taskId.includes('-') && !taskId.includes('_')) {
        result.warnings.push('Consider using a pattern like "PROJ-123" or "TEAM_FEATURE_001" for better organization');
      }
    }

    // Validate description
    if (!data.description || !data.description.trim()) {
      result.errors.push('Task description is required');
      result.isValid = false;
    } else {
      const description = data.description.trim();
      
      if (description.length < 10) {
        result.errors.push('Task description must be at least 10 characters long');
        result.isValid = false;
      }
      
      if (description.length > 5000) {
        result.errors.push('Task description must be no more than 5000 characters long');
        result.isValid = false;
      }
      
      // Warn about very short descriptions
      if (description.length < 50) {
        result.warnings.push('Consider providing more detail in the description to help the AI agents understand your requirements');
      }
      
      // Check for helpful keywords
      const hasActionWords = /\b(implement|create|add|build|fix|update|improve|remove|refactor|optimize)\b/i.test(description);
      if (!hasActionWords) {
        result.warnings.push('Consider starting your description with an action word (implement, create, fix, etc.) to clarify the goal');
      }
    }

    // Validate task_type
    const validTaskTypes = ['feature', 'bug', 'technical', 'infrastructure'];
    if (!data.task_type || !validTaskTypes.includes(data.task_type)) {
      result.errors.push('Please select a valid task type');
      result.isValid = false;
    }

    return result;
  }

  /**
   * Validate context ID format (UUID)
   */
  validateContextId(contextId: string): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: []
    };

    if (!contextId || !contextId.trim()) {
      result.errors.push('Context ID is required');
      result.isValid = false;
      return result;
    }

    // UUID format validation
    const uuidPattern = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    if (!uuidPattern.test(contextId)) {
      result.errors.push('Invalid context ID format');
      result.isValid = false;
    }

    return result;
  }

  /**
   * Validate repository selection
   */
  validateRepositorySelection(selectedRepos: string[]): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: []
    };

    if (!selectedRepos || selectedRepos.length === 0) {
      result.errors.push('At least one repository must be selected');
      result.isValid = false;
      return result;
    }

    if (selectedRepos.length > 20) {
      result.warnings.push('Selecting many repositories may slow down analysis. Consider selecting only the most relevant ones.');
    }

    if (selectedRepos.length === 1) {
      result.warnings.push('Consider selecting additional repositories if your task involves cross-repository changes or dependencies.');
    }

    return result;
  }

  /**
   * Validate generated questions before sending to tech lead
   */
  validateQuestions(questions: string[]): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: []
    };

    if (!questions || questions.length === 0) {
      result.errors.push('No questions were generated');
      result.isValid = false;
      return result;
    }

    // Check each question
    questions.forEach((question, index) => {
      if (!question || !question.trim()) {
        result.errors.push(`Question ${index + 1} is empty`);
        result.isValid = false;
      } else if (question.trim().length < 10) {
        result.warnings.push(`Question ${index + 1} is very short and may not provide enough context`);
      } else if (!question.trim().endsWith('?')) {
        result.warnings.push(`Question ${index + 1} should end with a question mark`);
      }
    });

    if (questions.length > 20) {
      result.warnings.push('Many questions were generated. Consider reviewing and removing less important ones to focus the analysis.');
    }

    return result;
  }

  /**
   * Validate answers before generating Jira card
   */
  validateAnswers(answers: string[]): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: []
    };

    if (!answers || answers.length === 0) {
      result.errors.push('No answers were generated');
      result.isValid = false;
      return result;
    }

    // Check each answer
    answers.forEach((answer, index) => {
      if (!answer || !answer.trim()) {
        result.errors.push(`Answer ${index + 1} is empty`);
        result.isValid = false;
      } else if (answer.trim().length < 20) {
        result.warnings.push(`Answer ${index + 1} is very brief and may not provide enough implementation detail`);
      }
    });

    // Check for technical depth
    const totalLength = answers.join(' ').length;
    if (totalLength < 500) {
      result.warnings.push('The answers seem brief. Consider asking for more technical detail to improve the Jira card quality.');
    }

    return result;
  }

  /**
   * Validate Jira card data before creation
   */
  validateJiraCard(cardData: any): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      warnings: []
    };

    // Validate title
    if (!cardData.title || !cardData.title.trim()) {
      result.errors.push('Jira card title is required');
      result.isValid = false;
    } else if (cardData.title.trim().length < 5) {
      result.errors.push('Jira card title is too short');
      result.isValid = false;
    } else if (cardData.title.trim().length > 100) {
      result.errors.push('Jira card title is too long (max 100 characters)');
      result.isValid = false;
    }

    // Validate description
    if (!cardData.description || !cardData.description.trim()) {
      result.errors.push('Jira card description is required');
      result.isValid = false;
    } else if (cardData.description.trim().length < 50) {
      result.warnings.push('Jira card description is quite brief. Consider adding more implementation details.');
    }

    // Validate story points
    if (cardData.story_points !== undefined) {
      if (cardData.story_points < 1 || cardData.story_points > 21) {
        result.warnings.push('Story points should typically be between 1 and 21 (Fibonacci sequence)');
      }
    }

    // Check for implementation details
    if (cardData.implementation_files && cardData.implementation_files.length === 0) {
      result.warnings.push('No implementation files identified. This may indicate the analysis needs more depth.');
    }

    if (cardData.database_changes && cardData.database_changes.length === 0 && cardData.description.toLowerCase().includes('database')) {
      result.warnings.push('Task mentions database but no database changes were identified.');
    }

    return result;
  }

  /**
   * Get severity class for UI display
   */
  getSeverityClass(type: 'error' | 'warning'): string {
    return type === 'error' ? 'p-message-error' : 'p-message-warn';
  }

  /**
   * Get severity for PrimeNG message component
   */
  getSeverity(type: 'error' | 'warning'): 'error' | 'warn' {
    return type === 'error' ? 'error' : 'warn';
  }

  /**
   * Format validation messages for display
   */
  formatValidationMessages(result: ValidationResult): { severity: 'error' | 'warn', summary: string, detail: string }[] {
    const messages = [];

    result.errors.forEach(error => {
      messages.push({
        severity: 'error' as const,
        summary: 'Validation Error',
        detail: error
      });
    });

    result.warnings.forEach(warning => {
      messages.push({
        severity: 'warn' as const,
        summary: 'Validation Warning',
        detail: warning
      });
    });

    return messages;
  }
}