"""
Services package for the Multi-Agent Jira Card Creator application.
"""

from .task_manager import TaskManager, Task

__all__ = [
    "TaskManager",
    "Task"
]