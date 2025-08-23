"""
Context Management System

This module provides centralized management of repository and database contexts
for the AI agents. It handles context switching, caching, and state management
to provide consistent context across the agent workflow.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager

from ..repository.scanner import RepositoryScanner, RepositoryInfo
from ..database.connector import DatabaseConnector, SchemaAnalysis, TableInfo

logger = logging.getLogger(__name__)


@dataclass
class RepositoryContext:
    """Repository context information."""
    selected_repositories: List[str]
    repository_info: Dict[str, RepositoryInfo]
    relevance_scores: Dict[str, float]
    last_updated: datetime
    task_keywords: List[str]


@dataclass
class DatabaseContext:
    """Database context information."""
    selected_schema: str
    schema_analysis: Optional[SchemaAnalysis]
    relevant_tables: List[str]
    table_relationships: Dict[str, Dict[str, List[str]]]
    last_updated: datetime
    connection_status: bool


@dataclass
class TaskContext:
    """Task-specific context information."""
    task_id: str
    task_description: str
    task_type: str  # 'feature', 'bug', 'technical', 'infrastructure'
    technologies: List[str]
    keywords: List[str]
    created_at: datetime
    workflow_step: str  # 'questions', 'answers', 'card_generation'


@dataclass
class WorkflowContext:
    """Complete workflow context combining all context types."""
    task_context: TaskContext
    repository_context: Optional[RepositoryContext]
    database_context: Optional[DatabaseContext]
    context_id: str
    created_at: datetime
    last_accessed: datetime


class ContextRelevanceAnalyzer:
    """Analyzes relevance of repositories and database elements to tasks."""
    
    # Technology keywords that indicate specific types of work
    TECHNOLOGY_KEYWORDS = {
        'java': ['java', 'spring', 'maven', 'gradle', 'jpa', 'hibernate'],
        'javascript': ['javascript', 'js', 'node', 'npm', 'react', 'angular', 'vue'],
        'typescript': ['typescript', 'ts', 'angular', 'react'],
        'python': ['python', 'django', 'flask', 'pip', 'fastapi'],
        'database': ['database', 'sql', 'oracle', 'mysql', 'postgres', 'table', 'schema'],
        'api': ['api', 'rest', 'graphql', 'endpoint', 'service'],
        'frontend': ['frontend', 'ui', 'component', 'css', 'html', 'angular', 'react'],
        'backend': ['backend', 'service', 'api', 'database', 'server']
    }
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=30)
    
    def analyze_task_relevance(self, task_description: str, repositories: List[RepositoryInfo]) -> Dict[str, float]:
        """
        Analyze how relevant each repository is to a given task.
        
        Args:
            task_description: Description of the task
            repositories: List of available repositories
            
        Returns:
            Dictionary mapping repository names to relevance scores (0-1)
        """
        cache_key = f"relevance_{hash(task_description)}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_result
        
        task_keywords = self._extract_keywords(task_description)
        task_technologies = self._identify_technologies(task_description, task_keywords)
        
        relevance_scores = {}
        
        for repo in repositories:
            score = self._calculate_repository_relevance(
                repo, task_keywords, task_technologies
            )
            relevance_scores[repo.name] = score
        
        # Cache the result
        self.cache[cache_key] = (relevance_scores, datetime.now())
        
        return relevance_scores
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        import re
        
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'our', 'their', 'what',
            'when', 'where', 'why', 'how', 'who', 'which'
        }
        
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _identify_technologies(self, text: str, keywords: List[str]) -> List[str]:
        """Identify technologies mentioned in the text."""
        identified_technologies = []
        text_lower = text.lower()
        
        for tech_category, tech_keywords in self.TECHNOLOGY_KEYWORDS.items():
            if any(keyword in text_lower for keyword in tech_keywords):
                identified_technologies.append(tech_category)
        
        return identified_technologies
    
    def _calculate_repository_relevance(
        self, 
        repo: RepositoryInfo, 
        task_keywords: List[str], 
        task_technologies: List[str]
    ) -> float:
        """Calculate relevance score for a repository."""
        score = 0.0
        max_score = 10.0  # Maximum possible score
        
        # Repository name relevance (weight: 3.0)
        repo_name_lower = repo.name.lower()
        name_matches = sum(1 for keyword in task_keywords if keyword in repo_name_lower)
        if name_matches > 0:
            score += min(3.0, name_matches * 1.0)
        
        # Primary language relevance (weight: 2.0)
        if repo.primary_language.lower() in task_technologies:
            score += 2.0
        
        # All languages relevance (weight: 1.0)
        language_matches = sum(1 for lang in repo.languages if lang.lower() in task_technologies)
        if language_matches > 0:
            score += min(1.0, language_matches * 0.5)
        
        # Framework relevance (weight: 2.0)
        framework_matches = sum(1 for fw in repo.frameworks if fw.lower() in task_keywords)
        if framework_matches > 0:
            score += min(2.0, framework_matches * 0.7)
        
        # Repository size factor (larger repos might be more comprehensive)
        if repo.file_count > 100:
            score += 0.5
        elif repo.file_count > 50:
            score += 0.3
        
        # Recent activity bonus
        if repo.git_info and repo.git_info.last_commit_date:
            days_since_commit = (datetime.now() - repo.git_info.last_commit_date).days
            if days_since_commit < 30:
                score += 0.5
            elif days_since_commit < 90:
                score += 0.3
        
        # Technology stack alignment
        tech_alignment = self._calculate_tech_alignment(repo, task_technologies)
        score += tech_alignment * 1.5
        
        # Normalize score to 0-1 range
        return min(1.0, score / max_score)
    
    def _calculate_tech_alignment(self, repo: RepositoryInfo, task_technologies: List[str]) -> float:
        """Calculate how well repository's technology stack aligns with task."""
        if not task_technologies:
            return 0.0
        
        repo_tech_indicators = []
        repo_tech_indicators.extend(repo.languages)
        repo_tech_indicators.extend(repo.frameworks)
        
        # Check for technology alignment
        alignments = 0
        for task_tech in task_technologies:
            for tech_keyword_list in self.TECHNOLOGY_KEYWORDS.get(task_tech, []):
                if any(tech_keyword_list in indicator.lower() for indicator in repo_tech_indicators):
                    alignments += 1
                    break
        
        return alignments / len(task_technologies) if task_technologies else 0.0


class ContextManager:
    """Central context management system."""
    
    def __init__(
        self, 
        repository_scanner: RepositoryScanner,
        database_connector: Optional[DatabaseConnector] = None,
        cache_dir: str = ".context_cache"
    ):
        self.repository_scanner = repository_scanner
        self.database_connector = database_connector
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.relevance_analyzer = ContextRelevanceAnalyzer()
        
        # In-memory context storage
        self._active_contexts: Dict[str, WorkflowContext] = {}
        self._current_context_id: Optional[str] = None
        
        # Load persisted contexts
        self._load_persisted_contexts()
    
    async def create_task_context(
        self, 
        task_id: str, 
        task_description: str, 
        task_type: str = 'feature'
    ) -> str:
        """
        Create a new task context.
        
        Args:
            task_id: Unique task identifier
            task_description: Task description
            task_type: Type of task (feature, bug, technical, infrastructure)
            
        Returns:
            Context ID for the created context
        """
        # Extract keywords and technologies
        keywords = self.relevance_analyzer._extract_keywords(task_description)
        technologies = self.relevance_analyzer._identify_technologies(task_description, keywords)
        
        # Create task context
        task_context = TaskContext(
            task_id=task_id,
            task_description=task_description,
            task_type=task_type,
            technologies=technologies,
            keywords=keywords,
            created_at=datetime.now(),
            workflow_step='questions'
        )
        
        # Create workflow context
        context_id = f"ctx_{task_id}_{int(datetime.now().timestamp())}"
        workflow_context = WorkflowContext(
            task_context=task_context,
            repository_context=None,
            database_context=None,
            context_id=context_id,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        # Store context
        self._active_contexts[context_id] = workflow_context
        self._current_context_id = context_id
        
        # Persist context
        await self._persist_context(context_id)
        
        logger.info(f"Created task context: {context_id} for task: {task_id}")
        return context_id
    
    async def set_repository_context(
        self, 
        context_id: str, 
        repository_names: List[str],
        auto_analyze_relevance: bool = True
    ) -> bool:
        """
        Set repository context for a workflow.
        
        Args:
            context_id: Context ID to update
            repository_names: List of repository names to include
            auto_analyze_relevance: Whether to automatically analyze relevance
            
        Returns:
            True if context was updated successfully
        """
        if context_id not in self._active_contexts:
            logger.error(f"Context {context_id} not found")
            return False
        
        workflow_context = self._active_contexts[context_id]
        
        # Validate repository names
        available_repos = list(self.repository_scanner._cache.values())
        available_names = {repo.name for repo in available_repos}
        
        invalid_names = set(repository_names) - available_names
        if invalid_names:
            logger.error(f"Invalid repository names: {invalid_names}")
            return False
        
        # Get repository info
        repository_info = {}
        selected_repos = []
        for repo in available_repos:
            if repo.name in repository_names:
                repository_info[repo.name] = repo
                selected_repos.append(repo)
        
        # Calculate relevance scores
        relevance_scores = {}
        if auto_analyze_relevance:
            task_description = workflow_context.task_context.task_description
            all_scores = self.relevance_analyzer.analyze_task_relevance(task_description, available_repos)
            relevance_scores = {name: all_scores.get(name, 0.0) for name in repository_names}
        
        # Create repository context
        repo_context = RepositoryContext(
            selected_repositories=repository_names,
            repository_info=repository_info,
            relevance_scores=relevance_scores,
            last_updated=datetime.now(),
            task_keywords=workflow_context.task_context.keywords
        )
        
        # Update workflow context
        workflow_context.repository_context = repo_context
        workflow_context.last_accessed = datetime.now()
        
        # Persist context
        await self._persist_context(context_id)
        
        logger.info(f"Set repository context for {context_id}: {repository_names}")
        return True
    
    async def set_database_context(
        self, 
        context_id: str, 
        schema_name: str,
        analyze_schema: bool = True
    ) -> bool:
        """
        Set database context for a workflow.
        
        Args:
            context_id: Context ID to update
            schema_name: Database schema name
            analyze_schema: Whether to analyze the schema immediately
            
        Returns:
            True if context was updated successfully
        """
        if context_id not in self._active_contexts:
            logger.error(f"Context {context_id} not found")
            return False
        
        if not self.database_connector:
            logger.error("Database connector not available")
            return False
        
        workflow_context = self._active_contexts[context_id]
        
        # Test database connection
        connection_status = await self.database_connector.test_connection()
        if not connection_status:
            logger.error("Database connection failed")
            return False
        
        # Analyze schema if requested
        schema_analysis = None
        relevant_tables = []
        table_relationships = {}
        
        if analyze_schema:
            try:
                schema_analysis = await self.database_connector.analyze_schema(schema_name)
                
                # Extract relevant tables based on task keywords
                task_keywords = workflow_context.task_context.keywords
                relevant_tables = self._identify_relevant_tables(schema_analysis, task_keywords)
                
                # Get relationships for relevant tables
                for table_name in relevant_tables[:5]:  # Limit to top 5 for performance
                    relationships = await self.database_connector.get_table_relationships(schema_name, table_name)
                    table_relationships[table_name] = relationships
                    
            except Exception as e:
                logger.warning(f"Schema analysis failed: {e}")
        
        # Create database context
        db_context = DatabaseContext(
            selected_schema=schema_name,
            schema_analysis=schema_analysis,
            relevant_tables=relevant_tables,
            table_relationships=table_relationships,
            last_updated=datetime.now(),
            connection_status=connection_status
        )
        
        # Update workflow context
        workflow_context.database_context = db_context
        workflow_context.last_accessed = datetime.now()
        
        # Persist context
        await self._persist_context(context_id)
        
        logger.info(f"Set database context for {context_id}: {schema_name}")
        return True
    
    def _identify_relevant_tables(self, schema_analysis: SchemaAnalysis, task_keywords: List[str]) -> List[str]:
        """Identify database tables relevant to task keywords."""
        relevant_tables = []
        
        for table in schema_analysis.tables:
            table_score = 0
            
            # Check table name relevance
            table_name_lower = table.name.lower()
            for keyword in task_keywords:
                if keyword.lower() in table_name_lower:
                    table_score += 3
            
            # Check column name relevance
            for column in table.columns:
                column_name_lower = column.name.lower()
                for keyword in task_keywords:
                    if keyword.lower() in column_name_lower:
                        table_score += 1
            
            # Check comments relevance
            if table.comments:
                comments_lower = table.comments.lower()
                for keyword in task_keywords:
                    if keyword.lower() in comments_lower:
                        table_score += 2
            
            if table_score > 0:
                relevant_tables.append((table.name, table_score))
        
        # Sort by relevance score and return top tables
        relevant_tables.sort(key=lambda x: x[1], reverse=True)
        return [table_name for table_name, _ in relevant_tables[:10]]
    
    async def get_context(self, context_id: str) -> Optional[WorkflowContext]:
        """Get workflow context by ID."""
        if context_id in self._active_contexts:
            context = self._active_contexts[context_id]
            context.last_accessed = datetime.now()
            return context
        
        # Try to load from persistent storage
        return await self._load_context(context_id)
    
    async def get_current_context(self) -> Optional[WorkflowContext]:
        """Get the current active context."""
        if self._current_context_id:
            return await self.get_context(self._current_context_id)
        return None
    
    def set_current_context(self, context_id: str) -> bool:
        """Set the current active context."""
        if context_id in self._active_contexts:
            self._current_context_id = context_id
            return True
        return False
    
    async def update_workflow_step(self, context_id: str, step: str) -> bool:
        """Update the current workflow step."""
        if context_id not in self._active_contexts:
            return False
        
        workflow_context = self._active_contexts[context_id]
        workflow_context.task_context.workflow_step = step
        workflow_context.last_accessed = datetime.now()
        
        await self._persist_context(context_id)
        return True
    
    async def analyze_repository_relevance(self, context_id: str) -> Dict[str, Any]:
        """Analyze repository relevance for the current task."""
        workflow_context = await self.get_context(context_id)
        if not workflow_context:
            return {"error": "Context not found"}
        
        # Get all available repositories
        available_repos = list(self.repository_scanner._cache.values())
        if not available_repos:
            return {"error": "No repositories available"}
        
        # Analyze relevance
        task_description = workflow_context.task_context.task_description
        relevance_scores = self.relevance_analyzer.analyze_task_relevance(task_description, available_repos)
        
        # Sort by relevance
        sorted_repos = sorted(relevance_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get repository details for top matches
        top_matches = []
        for repo_name, score in sorted_repos[:10]:
            repo_info = self.repository_scanner.get_repository_by_name(repo_name)
            if repo_info:
                top_matches.append({
                    "name": repo_name,
                    "relevance_score": score,
                    "primary_language": repo_info.primary_language,
                    "frameworks": repo_info.frameworks,
                    "file_count": repo_info.file_count
                })
        
        return {
            "task_id": workflow_context.task_context.task_id,
            "task_technologies": workflow_context.task_context.technologies,
            "task_keywords": workflow_context.task_context.keywords,
            "top_matches": top_matches,
            "total_repositories": len(available_repos),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def get_context_summary(self, context_id: str) -> Dict[str, Any]:
        """Get a summary of the current context."""
        workflow_context = await self.get_context(context_id)
        if not workflow_context:
            return {"error": "Context not found"}
        
        summary = {
            "context_id": context_id,
            "task": {
                "id": workflow_context.task_context.task_id,
                "description": workflow_context.task_context.task_description,
                "type": workflow_context.task_context.task_type,
                "technologies": workflow_context.task_context.technologies,
                "workflow_step": workflow_context.task_context.workflow_step
            },
            "created_at": workflow_context.created_at.isoformat(),
            "last_accessed": workflow_context.last_accessed.isoformat()
        }
        
        # Add repository context if available
        if workflow_context.repository_context:
            repo_context = workflow_context.repository_context
            summary["repositories"] = {
                "selected": repo_context.selected_repositories,
                "count": len(repo_context.selected_repositories),
                "relevance_scores": repo_context.relevance_scores,
                "last_updated": repo_context.last_updated.isoformat()
            }
        
        # Add database context if available
        if workflow_context.database_context:
            db_context = workflow_context.database_context
            summary["database"] = {
                "schema": db_context.selected_schema,
                "connection_status": db_context.connection_status,
                "relevant_tables": db_context.relevant_tables,
                "table_count": len(db_context.relevant_tables),
                "last_updated": db_context.last_updated.isoformat()
            }
        
        return summary
    
    async def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """Clean up old contexts."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        contexts_to_remove = []
        
        for context_id, context in self._active_contexts.items():
            if context.last_accessed < cutoff_time:
                contexts_to_remove.append(context_id)
        
        # Remove old contexts
        for context_id in contexts_to_remove:
            del self._active_contexts[context_id]
            
            # Remove persistent file
            context_file = self.cache_dir / f"{context_id}.json"
            if context_file.exists():
                context_file.unlink()
        
        logger.info(f"Cleaned up {len(contexts_to_remove)} old contexts")
        return len(contexts_to_remove)
    
    async def _persist_context(self, context_id: str):
        """Persist context to disk."""
        if context_id not in self._active_contexts:
            return
        
        context = self._active_contexts[context_id]
        context_file = self.cache_dir / f"{context_id}.json"
        
        try:
            # Convert to JSON-serializable format
            context_data = self._serialize_context(context)
            
            with open(context_file, 'w') as f:
                json.dump(context_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error persisting context {context_id}: {e}")
    
    async def _load_context(self, context_id: str) -> Optional[WorkflowContext]:
        """Load context from disk."""
        context_file = self.cache_dir / f"{context_id}.json"
        
        if not context_file.exists():
            return None
        
        try:
            with open(context_file, 'r') as f:
                context_data = json.load(f)
            
            context = self._deserialize_context(context_data)
            self._active_contexts[context_id] = context
            
            return context
            
        except Exception as e:
            logger.error(f"Error loading context {context_id}: {e}")
            return None
    
    def _load_persisted_contexts(self):
        """Load all persisted contexts on startup."""
        if not self.cache_dir.exists():
            return
        
        for context_file in self.cache_dir.glob("ctx_*.json"):
            context_id = context_file.stem
            asyncio.create_task(self._load_context(context_id))
    
    def _serialize_context(self, context: WorkflowContext) -> Dict[str, Any]:
        """Serialize context to JSON-compatible format."""
        data = {
            "context_id": context.context_id,
            "created_at": context.created_at.isoformat(),
            "last_accessed": context.last_accessed.isoformat(),
            "task_context": asdict(context.task_context)
        }
        
        # Convert datetime fields in task context
        data["task_context"]["created_at"] = context.task_context.created_at.isoformat()
        
        # Add repository context if available
        if context.repository_context:
            repo_data = asdict(context.repository_context)
            repo_data["last_updated"] = context.repository_context.last_updated.isoformat()
            
            # Convert repository info to serializable format
            repo_info_data = {}
            for name, repo in context.repository_context.repository_info.items():
                repo_dict = asdict(repo)
                repo_dict["last_scanned"] = repo.last_scanned.isoformat()
                if repo.git_info and repo.git_info.last_commit_date:
                    repo_dict["git_info"]["last_commit_date"] = repo.git_info.last_commit_date.isoformat()
                repo_info_data[name] = repo_dict
            
            repo_data["repository_info"] = repo_info_data
            data["repository_context"] = repo_data
        
        # Add database context if available
        if context.database_context:
            db_data = asdict(context.database_context)
            db_data["last_updated"] = context.database_context.last_updated.isoformat()
            
            # Handle schema analysis
            if context.database_context.schema_analysis:
                schema_dict = asdict(context.database_context.schema_analysis)
                schema_dict["analysis_date"] = context.database_context.schema_analysis.analysis_date.isoformat()
                
                # Convert table info
                for table_dict in schema_dict["tables"]:
                    table_dict["last_analyzed"] = datetime.fromisoformat(table_dict["last_analyzed"]).isoformat()
                
                db_data["schema_analysis"] = schema_dict
            
            data["database_context"] = db_data
        
        return data
    
    def _deserialize_context(self, data: Dict[str, Any]) -> WorkflowContext:
        """Deserialize context from JSON format."""
        # Deserialize task context
        task_data = data["task_context"]
        task_data["created_at"] = datetime.fromisoformat(task_data["created_at"])
        task_context = TaskContext(**task_data)
        
        # Deserialize repository context if available
        repository_context = None
        if "repository_context" in data:
            repo_data = data["repository_context"]
            repo_data["last_updated"] = datetime.fromisoformat(repo_data["last_updated"])
            
            # Deserialize repository info
            repository_info = {}
            for name, repo_dict in repo_data["repository_info"].items():
                repo_dict["last_scanned"] = datetime.fromisoformat(repo_dict["last_scanned"])
                if repo_dict.get("git_info") and repo_dict["git_info"].get("last_commit_date"):
                    repo_dict["git_info"]["last_commit_date"] = datetime.fromisoformat(repo_dict["git_info"]["last_commit_date"])
                
                # This is simplified - in reality you'd need to properly reconstruct RepositoryInfo objects
                # For now, we'll skip the full reconstruction
                repository_info[name] = repo_dict
            
            repo_data["repository_info"] = repository_info
            repository_context = RepositoryContext(**repo_data)
        
        # Deserialize database context if available
        database_context = None
        if "database_context" in data:
            db_data = data["database_context"]
            db_data["last_updated"] = datetime.fromisoformat(db_data["last_updated"])
            
            # Handle schema analysis deserialization (simplified)
            if db_data.get("schema_analysis"):
                schema_data = db_data["schema_analysis"]
                schema_data["analysis_date"] = datetime.fromisoformat(schema_data["analysis_date"])
                # Simplified - would need full SchemaAnalysis reconstruction
                db_data["schema_analysis"] = schema_data
            
            database_context = DatabaseContext(**db_data)
        
        # Create workflow context
        workflow_context = WorkflowContext(
            task_context=task_context,
            repository_context=repository_context,
            database_context=database_context,
            context_id=data["context_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"])
        )
        
        return workflow_context


# Example usage
async def main():
    """Example usage of the context manager."""
    # Initialize components
    repository_scanner = RepositoryScanner("/path/to/repositories")
    database_connector = DatabaseConnector("jdbc:oracle:thin:@localhost:1521:xe", "user", "pass")
    
    # Create context manager
    context_manager = ContextManager(repository_scanner, database_connector)
    
    # Create a task context
    context_id = await context_manager.create_task_context(
        task_id="TASK-123",
        task_description="Create a new user authentication service with database integration",
        task_type="feature"
    )
    
    # Analyze repository relevance
    relevance_analysis = await context_manager.analyze_repository_relevance(context_id)
    print(f"Repository relevance: {relevance_analysis}")
    
    # Set repository context based on relevance
    top_repos = [match["name"] for match in relevance_analysis["top_matches"][:3]]
    await context_manager.set_repository_context(context_id, top_repos)
    
    # Set database context
    await context_manager.set_database_context(context_id, "AUTH_SCHEMA")
    
    # Get context summary
    summary = await context_manager.get_context_summary(context_id)
    print(f"Context summary: {summary}")


if __name__ == "__main__":
    asyncio.run(main())