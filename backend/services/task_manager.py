"""
Task Manager Service - Handles reading and parsing tasks from tasks.md
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from ..middleware import ValidationError, ConfigurationError

logger = logging.getLogger(__name__)

@dataclass
class Task:
    """Represents a single task from tasks.md"""
    id: int
    description: str
    raw_line: str
    status: str = "not_started"  # not_started, in_progress, completed
    context_id: Optional[str] = None
    jira_card_id: Optional[str] = None

class TaskManager:
    """Manages tasks from tasks.md file"""
    
    def __init__(self, tasks_file_path: str):
        self.tasks_file_path = Path(tasks_file_path)
        self.tasks: List[Task] = []
        self._task_status_cache: Dict[int, Dict] = {}
        
    def load_tasks(self) -> List[Task]:
        """Load and parse tasks from tasks.md file"""
        try:
            if not self.tasks_file_path.exists():
                raise ConfigurationError(
                    f"Tasks file not found: {self.tasks_file_path}",
                    config_key="tasks_file"
                )
            
            logger.info(f"Loading tasks from: {self.tasks_file_path}")
            
            with open(self.tasks_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tasks = self._parse_tasks(content)
            self.tasks = tasks
            
            logger.info(f"Loaded {len(tasks)} tasks from tasks.md")
            return tasks
            
        except FileNotFoundError:
            raise ConfigurationError(
                f"Tasks file not found: {self.tasks_file_path}",
                config_key="tasks_file"
            )
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            raise ConfigurationError(
                f"Failed to load tasks file: {str(e)}",
                config_key="tasks_file"
            )
    
    def _parse_tasks(self, content: str) -> List[Task]:
        """Parse markdown content and extract tasks"""
        tasks = []
        lines = content.split('\n')
        task_id = 1
        
        for line_num, line in enumerate(lines, 1):
            # Look for lines that start with * (markdown list items)
            line = line.strip()
            if line.startswith('* '):
                # Extract the task description (everything after the *)
                description = line[2:].strip()
                
                if description:  # Only add non-empty descriptions
                    task = Task(
                        id=task_id,
                        description=description,
                        raw_line=line,
                        status="not_started"
                    )
                    tasks.append(task)
                    task_id += 1
                    
                    logger.debug(f"Parsed task {task_id-1}: {description[:50]}...")
        
        return tasks
    
    def get_all_tasks(self) -> List[Task]:
        """Get all available tasks"""
        if not self.tasks:
            self.load_tasks()
        return self.tasks
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get a specific task by ID"""
        if not self.tasks:
            self.load_tasks()
            
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_task_summary(self) -> Dict[str, int]:
        """Get summary statistics of tasks"""
        if not self.tasks:
            self.load_tasks()
            
        summary = {
            "total": len(self.tasks),
            "not_started": 0,
            "in_progress": 0,
            "completed": 0
        }
        
        for task in self.tasks:
            summary[task.status] += 1
            
        return summary
    
    def update_task_status(self, task_id: int, status: str, context_id: str = None, jira_card_id: str = None):
        """Update the status of a specific task"""
        valid_statuses = ["not_started", "in_progress", "completed"]
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                "status",
                status
            )
        
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValidationError(
                f"Task with ID {task_id} not found",
                "task_id",
                task_id
            )
        
        # Update task properties
        task.status = status
        if context_id:
            task.context_id = context_id
        if jira_card_id:
            task.jira_card_id = jira_card_id
            
        # Cache the update (in a real implementation, this might be persisted to a database)
        self._task_status_cache[task_id] = {
            "status": status,
            "context_id": context_id,
            "jira_card_id": jira_card_id,
            "updated_at": self._get_timestamp()
        }
        
        logger.info(f"Updated task {task_id} status to {status}")
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get all tasks with a specific status"""
        if not self.tasks:
            self.load_tasks()
            
        return [task for task in self.tasks if task.status == status]
    
    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by description content"""
        if not self.tasks:
            self.load_tasks()
            
        query_lower = query.lower()
        matching_tasks = []
        
        for task in self.tasks:
            if query_lower in task.description.lower():
                matching_tasks.append(task)
                
        logger.debug(f"Found {len(matching_tasks)} tasks matching query: {query}")
        return matching_tasks
    
    def get_task_categories(self) -> Dict[str, List[Task]]:
        """Categorize tasks by type/technology (based on keywords)"""
        if not self.tasks:
            self.load_tasks()
        
        categories = {
            "GitHub Actions": [],
            "MFE (Micro-frontend)": [],
            "Pipeline Migration": [],
            "Java/Backend": [],
            "GraphQL": [],
            "Launch Darkly": [],
            "Database": [],
            "Other": []
        }
        
        for task in self.tasks:
            desc_lower = task.description.lower()
            categorized = False
            
            # Categorize based on keywords
            if "github action" in desc_lower or "gha" in desc_lower:
                categories["GitHub Actions"].append(task)
                categorized = True
            elif "mfe" in desc_lower or "micro-frontend" in desc_lower or "imedia-" in desc_lower:
                categories["MFE (Micro-frontend)"].append(task)
                categorized = True
            elif "pipeline migration" in desc_lower or "harness deployment" in desc_lower:
                categories["Pipeline Migration"].append(task)
                categorized = True
            elif "java" in desc_lower or "annotation" in desc_lower or "library" in desc_lower:
                categories["Java/Backend"].append(task)
                categorized = True
            elif "graphql" in desc_lower or "nf-graphql" in desc_lower:
                categories["GraphQL"].append(task)
                categorized = True
            elif "launch darkly" in desc_lower or "launchdarkly" in desc_lower:
                categories["Launch Darkly"].append(task)
                categorized = True
            elif "database" in desc_lower or "table" in desc_lower or "cppf" in desc_lower:
                categories["Database"].append(task)
                categorized = True
            
            if not categorized:
                categories["Other"].append(task)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def reload_tasks(self) -> List[Task]:
        """Reload tasks from file (useful if tasks.md is updated)"""
        logger.info("Reloading tasks from file...")
        self.tasks.clear()
        return self.load_tasks()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def validate_task_selection(self, task_id: int) -> Task:
        """Validate that a task can be selected and processed"""
        task = self.get_task_by_id(task_id)
        
        if not task:
            raise ValidationError(
                f"Task with ID {task_id} does not exist",
                "task_id",
                task_id
            )
        
        if task.status == "completed":
            raise ValidationError(
                f"Task {task_id} is already completed",
                "task_id", 
                task_id
            )
        
        if task.status == "in_progress" and task.context_id:
            raise ValidationError(
                f"Task {task_id} is already in progress with context {task.context_id}",
                "task_id",
                task_id
            )
        
        return task
    
    def get_task_details_for_processing(self, task_id: int) -> Dict:
        """Get task details formatted for the agent processing pipeline"""
        task = self.validate_task_selection(task_id)
        
        # Determine task type based on content
        desc_lower = task.description.lower()
        
        if "implement" in desc_lower or "create" in desc_lower or "add" in desc_lower:
            task_type = "feature"
        elif "fix" in desc_lower or "remove" in desc_lower and "issues" in desc_lower:
            task_type = "bug"
        elif "update" in desc_lower or "migrate" in desc_lower or "refactor" in desc_lower:
            task_type = "technical"
        elif "setup" in desc_lower or "pipeline" in desc_lower or "deployment" in desc_lower:
            task_type = "infrastructure"
        else:
            task_type = "feature"  # default
        
        return {
            "task_id": f"TASK-{task.id:03d}",  # Format as TASK-001, TASK-002, etc.
            "description": task.description,
            "task_type": task_type,
            "original_task_id": task.id,
            "raw_line": task.raw_line
        }