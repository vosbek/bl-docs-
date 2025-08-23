"""
Multi-Agent Jira Card Creation System - Main Application Entry Point
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from .repository.scanner import RepositoryScanner
from .database.connector import DatabaseConnector
from .context.manager import ContextManager
from .agents.tools import AgentToolRegistry
from .agents.strands_integration import StrandsAgentOrchestrator
from .config import Settings
from .services import TaskManager, Task
from .middleware import (
    ErrorHandlerMiddleware,
    ValidationError,
    ConfigurationError,
    RepositoryError,
    DatabaseError,
    AgentError,
    validate_required_config,
    validate_repository_path,
    validate_context_id,
    validate_task_request,
    log_performance
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
repository_scanner = None
database_connector = None
context_manager = None
agent_registry = None
agent_orchestrator = None
task_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global repository_scanner, database_connector, context_manager, agent_registry, agent_orchestrator, task_manager
    
    logger.info("Starting Multi-Agent Jira Card Creation System...")
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        required_config = {
            "repository_base_path": settings.repository_base_path,
            "aws_region": settings.aws_region
        }
        validate_required_config(required_config, list(required_config.keys()))
        
        # Validate repository path
        validate_repository_path(settings.repository_base_path)
        
        # Initialize repository scanner
        logger.info(f"Initializing repository scanner for: {settings.repository_base_path}")
        repository_scanner = RepositoryScanner(settings.repository_base_path)
        
        # Initialize database connector if configured
        if settings.oracle_jdbc_url and settings.oracle_username and settings.oracle_password:
            logger.info("Initializing database connector...")
            database_connector = DatabaseConnector(
                jdbc_url=settings.oracle_jdbc_url,
                username=settings.oracle_username,
                password=settings.oracle_password
            )
            await database_connector.initialize()
        else:
            logger.warning("Database configuration not found - running without database support")
        
        # Initialize context manager
        logger.info("Initializing context manager...")
        context_manager = ContextManager(repository_scanner, database_connector)
        
        # Initialize agent registry
        logger.info("Initializing agent tools...")
        database_config = None
        if database_connector:
            database_config = {
                "jdbc_url": settings.oracle_jdbc_url,
                "username": settings.oracle_username,
                "password": settings.oracle_password
            }
        
        agent_registry = AgentToolRegistry(settings.repository_base_path, database_config)
        await agent_registry.initialize()
        
        # Initialize Strands agent orchestrator
        logger.info("Initializing Strands agents...")
        agent_orchestrator = StrandsAgentOrchestrator(
            aws_profile=settings.aws_profile,
            bedrock_region=settings.aws_region,
            agent_registry=agent_registry,
            context_manager=context_manager
        )
        await agent_orchestrator.initialize()
        
        # Initialize task manager
        logger.info("Initializing task manager...")
        tasks_file_path = os.path.join(os.path.dirname(__file__), "..", "tasks.md")
        task_manager = TaskManager(tasks_file_path)
        # Load tasks at startup to validate the file exists
        await asyncio.get_event_loop().run_in_executor(None, task_manager.load_tasks)
        
        logger.info("System initialization completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down system...")
        if agent_registry:
            agent_registry.cleanup()
        if database_connector:
            database_connector.close()


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Jira Card Creation System",
    description="AI-powered Jira card creation with codebase analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handling middleware
app.add_middleware(ErrorHandlerMiddleware)


# Pydantic models
class TaskSelectionRequest(BaseModel):
    task_id: int


class RepositoryContextRequest(BaseModel):
    context_id: str
    repository_names: List[str]


class DatabaseContextRequest(BaseModel):
    context_id: str
    schema_name: str


class WorkflowStepRequest(BaseModel):
    context_id: str
    step_data: Dict[str, Any]
    next_step: str


# API Routes
@app.get("/")
async def root():
    """Root endpoint - serve Angular app."""
    return FileResponse("frontend/dist/index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "repository_scanner": repository_scanner is not None,
        "database_connector": database_connector is not None,
        "context_manager": context_manager is not None,
        "agent_orchestrator": agent_orchestrator is not None
    }


@app.get("/api/repositories")
async def get_repositories():
    """Get list of available repositories."""
    if not repository_scanner:
        raise HTTPException(status_code=500, detail="Repository scanner not initialized")
    
    try:
        repositories = await repository_scanner.scan_repositories()
        return {
            "status": "success",
            "count": len(repositories),
            "repositories": [
                {
                    "name": repo.name,
                    "path": repo.path,
                    "primary_language": repo.primary_language,
                    "languages": repo.languages,
                    "frameworks": repo.frameworks,
                    "file_count": repo.file_count,
                    "size_mb": round(repo.size_bytes / (1024 * 1024), 2),
                    "last_scanned": repo.last_scanned.isoformat()
                }
                for repo in repositories
            ]
        }
    except Exception as e:
        logger.error(f"Error getting repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/database/test")
async def test_database_connection():
    """Test database connection."""
    if not database_connector:
        return {"status": "error", "message": "Database not configured"}
    
    try:
        is_connected = await database_connector.test_connection()
        return {
            "status": "success" if is_connected else "error",
            "connected": is_connected
        }
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/tasks")
@log_performance
async def get_all_tasks():
    """Get all available tasks from tasks.md"""
    if not task_manager:
        raise ConfigurationError("Task manager not initialized")
    
    tasks = task_manager.get_all_tasks()
    summary = task_manager.get_task_summary()
    categories = task_manager.get_task_categories()
    
    return {
        "status": "success",
        "tasks": [
            {
                "id": task.id,
                "description": task.description,
                "status": task.status,
                "context_id": task.context_id,
                "jira_card_id": task.jira_card_id
            }
            for task in tasks
        ],
        "summary": summary,
        "categories": {k: len(v) for k, v in categories.items()},
        "total_tasks": len(tasks)
    }


@app.get("/api/tasks/categories")
@log_performance
async def get_task_categories():
    """Get tasks organized by categories"""
    if not task_manager:
        raise ConfigurationError("Task manager not initialized")
    
    categories = task_manager.get_task_categories()
    
    return {
        "status": "success",
        "categories": {
            category: [
                {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status,
                    "context_id": task.context_id,
                    "jira_card_id": task.jira_card_id
                }
                for task in tasks
            ]
            for category, tasks in categories.items()
        }
    }


@app.get("/api/tasks/search")
@log_performance
async def search_tasks(query: str):
    """Search tasks by description"""
    if not task_manager:
        raise ConfigurationError("Task manager not initialized")
    
    if not query or not query.strip():
        raise ValidationError("Search query cannot be empty", "query")
    
    matching_tasks = task_manager.search_tasks(query.strip())
    
    return {
        "status": "success",
        "query": query,
        "tasks": [
            {
                "id": task.id,
                "description": task.description,
                "status": task.status,
                "context_id": task.context_id,
                "jira_card_id": task.jira_card_id
            }
            for task in matching_tasks
        ],
        "total_matches": len(matching_tasks)
    }


@app.get("/api/tasks/{task_id}")
@log_performance
async def get_task_details(task_id: int):
    """Get details for a specific task"""
    if not task_manager:
        raise ConfigurationError("Task manager not initialized")
    
    task = task_manager.get_task_by_id(task_id)
    if not task:
        raise ValidationError(f"Task with ID {task_id} not found", "task_id", task_id)
    
    return {
        "status": "success",
        "task": {
            "id": task.id,
            "description": task.description,
            "status": task.status,
            "context_id": task.context_id,
            "jira_card_id": task.jira_card_id,
            "raw_line": task.raw_line
        }
    }


@app.post("/api/tasks/{task_id}/process")
@log_performance
async def process_task(task_id: int):
    """Start processing a task through the agent pipeline"""
    if not task_manager:
        raise ConfigurationError("Task manager not initialized")
    if not context_manager:
        raise ConfigurationError("Context manager not initialized")
    
    # Validate and get task details
    task_details = task_manager.get_task_details_for_processing(task_id)
    
    # Create workflow context
    context_id = await context_manager.create_task_context(
        task_id=task_details["task_id"],
        task_description=task_details["description"],
        task_type=task_details["task_type"]
    )
    
    # Update task status to in_progress
    task_manager.update_task_status(task_id, "in_progress", context_id)
    
    return {
        "status": "success",
        "context_id": context_id,
        "task_id": task_details["task_id"],
        "message": f"Started processing task {task_id}: {task_details['description'][:50]}..."
    }


@app.post("/api/tasks/reload")
@log_performance
async def reload_tasks():
    """Reload tasks from tasks.md file"""
    if not task_manager:
        raise ConfigurationError("Task manager not initialized")
    
    tasks = await asyncio.get_event_loop().run_in_executor(None, task_manager.reload_tasks)
    
    return {
        "status": "success",
        "message": f"Reloaded {len(tasks)} tasks from tasks.md",
        "total_tasks": len(tasks)
    }


@app.post("/api/context/repository")
@log_performance
async def set_repository_context(request: RepositoryContextRequest):
    """Set repository context for a workflow."""
    if not context_manager:
        raise ConfigurationError("Context manager not initialized")
    
    # Validate request data
    validate_context_id(request.context_id)
    
    if not request.repository_names:
        raise ValidationError("At least one repository must be selected", "repository_names")
    
    success = await context_manager.set_repository_context(
        context_id=request.context_id,
        repository_names=request.repository_names
    )
    
    if not success:
        raise RepositoryError("Failed to set repository context", operation="set_context")
    
    return {
        "status": "success",
        "message": f"Repository context set for {len(request.repository_names)} repositories"
    }


@app.post("/api/context/database")
async def set_database_context(request: DatabaseContextRequest):
    """Set database context for a workflow."""
    if not context_manager:
        raise HTTPException(status_code=500, detail="Context manager not initialized")
    
    if not database_connector:
        raise HTTPException(status_code=400, detail="Database not configured")
    
    try:
        success = await context_manager.set_database_context(
            context_id=request.context_id,
            schema_name=request.schema_name
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to set database context")
        
        return {
            "status": "success",
            "message": f"Database context set for schema: {request.schema_name}"
        }
    except Exception as e:
        logger.error(f"Error setting database context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/{context_id}")
async def get_context(context_id: str):
    """Get context information."""
    if not context_manager:
        raise HTTPException(status_code=500, detail="Context manager not initialized")
    
    try:
        summary = await context_manager.get_context_summary(context_id)
        return {"status": "success", "context": summary}
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context/{context_id}/relevance")
async def analyze_repository_relevance(context_id: str):
    """Analyze repository relevance for a context."""
    if not context_manager:
        raise HTTPException(status_code=500, detail="Context manager not initialized")
    
    try:
        analysis = await context_manager.analyze_repository_relevance(context_id)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        logger.error(f"Error analyzing relevance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/questions")
async def generate_questions(request: WorkflowStepRequest):
    """Generate questions using Jr Developer agent."""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")
    
    try:
        result = await agent_orchestrator.run_jr_developer_agent(
            context_id=request.context_id,
            step_data=request.step_data
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/answers")
async def generate_answers(request: WorkflowStepRequest):
    """Generate answers using Tech Lead agent."""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")
    
    try:
        result = await agent_orchestrator.run_tech_lead_agent(
            context_id=request.context_id,
            step_data=request.step_data
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error generating answers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/card")
async def generate_jira_card(request: WorkflowStepRequest):
    """Generate Jira card using Jira Card agent."""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")
    
    try:
        result = await agent_orchestrator.run_jira_card_agent(
            context_id=request.context_id,
            step_data=request.step_data
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error generating Jira card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jira/create")
async def create_jira_card(
    context_id: str,
    template_key: str,
    card_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Create Jira card using template cloning."""
    if not agent_orchestrator:
        raise HTTPException(status_code=500, detail="Agent orchestrator not initialized")
    
    try:
        # This would integrate with Jira API
        # For now, return mock response
        return {
            "status": "success",
            "jira_key": f"PROJ-{hash(context_id) % 10000}",
            "url": f"https://your-jira.atlassian.net/browse/PROJ-{hash(context_id) % 10000}",
            "message": "Jira card created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating Jira card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Serve Angular static files
@app.on_event("startup")
async def mount_static_files():
    """Mount static files for Angular frontend."""
    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )