"""
DeepBuild - Autonomous Coding Agent API

FastAPI backend providing REST endpoints for:
- Project initialization
- Build plan generation  
- Step-by-step execution with auto-fix
"""

from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services import (
    LLMService,
    ExecutionService,
    WorkspaceManager,
    AgentService
)
from config import (
    OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_MAX_CONTEXT_CHARS,
    EXECUTION_TIMEOUT, WORKSPACE_ROOT, PROMPTS_DIR,
    get_config_summary
)


# =============================================================================
# Application Setup
# =============================================================================

app = FastAPI(
    title="DeepBuild API",
    description="Autonomous coding agent that writes, executes, and debugs code",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Service Initialization
# =============================================================================

PROJECT_ROOT = Path(__file__).parent

# Initialize services
workspace_manager = WorkspaceManager(workspace_root=WORKSPACE_ROOT)

llm_service = LLMService(
    model=OLLAMA_MODEL,
    max_context_chars=OLLAMA_MAX_CONTEXT_CHARS,
    ollama_host=OLLAMA_HOST
)

execution_service = ExecutionService(
    workspace_root=WORKSPACE_ROOT,
    default_timeout=EXECUTION_TIMEOUT
)

agent_service = AgentService(
    workspace_manager=workspace_manager,
    llm_service=llm_service,
    execution_service=execution_service,
    prompts_dir=PROMPTS_DIR
)


# =============================================================================
# Request/Response Models
# =============================================================================

class ProjectInitRequest(BaseModel):
    """Request model for project initialization."""
    project_name: str = Field(..., description="Name of the project")
    user_query: str = Field(..., description="What to build")


class ProjectInitResponse(BaseModel):
    """Response model for project initialization."""
    success: bool
    project_name: str
    project_path: str
    message: str


class BuildRequest(BaseModel):
    """Request model for build plan generation."""
    project_name: str = Field(..., description="Name of the project")
    user_query: str = Field(..., description="What to build")


class BuildResponse(BaseModel):
    """Response model for build plan generation."""
    success: bool
    project_name: str
    plan_content: str
    message: str


class ExecuteTaskRequest(BaseModel):
    """Request model for task execution."""
    project_name: str = Field(..., description="Name of the project")


class ExecuteTaskResponse(BaseModel):
    """Response model for task execution."""
    success: bool
    completed: bool = False
    step_title: Optional[str] = None
    step_type: Optional[str] = None
    result_message: str = ""
    message: str


class ProjectStatusResponse(BaseModel):
    """Response model for project status."""
    project_name: str
    exists: bool
    has_plan: bool
    has_report: bool
    total_steps: int = 0
    completed_steps: int = 0
    progress_percent: float = 0


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    ollama_connected: bool
    workspace_path: str
    config: dict


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DeepBuild API",
        "version": "1.0.0",
        "description": "Autonomous coding agent",
        "endpoints": {
            "health": "GET /api/health",
            "init": "POST /api/project/init",
            "build": "POST /api/agent/build",
            "execute": "POST /api/agent/execute-task",
            "status": "GET /api/project/{project_name}/status"
        }
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    ollama_ok = llm_service.check_connection()
    
    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        ollama_connected=ollama_ok,
        workspace_path=str(workspace_manager.workspace_root),
        config=get_config_summary()
    )


@app.post("/api/project/init", response_model=ProjectInitResponse)
async def init_project(request: ProjectInitRequest):
    """Initialize a new coding project."""
    try:
        project_path = workspace_manager.init_project(
            project_name=request.project_name,
            user_query=request.user_query
        )
        
        return ProjectInitResponse(
            success=True,
            project_name=request.project_name,
            project_path=str(project_path),
            message=f"Project '{request.project_name}' initialized successfully."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize project: {str(e)}"
        )


@app.post("/api/agent/build", response_model=BuildResponse)
async def generate_build_plan(request: BuildRequest):
    """
    Generate a build plan for a project.
    
    Uses the Engineering Architect prompt to create a structured
    build plan with file creation and command execution steps.
    """
    # Initialize project if it doesn't exist
    if not workspace_manager.project_exists(request.project_name):
        workspace_manager.init_project(
            project_name=request.project_name,
            user_query=request.user_query
        )
    
    try:
        plan_content = agent_service.generate_plan(
            project_name=request.project_name,
            user_query=request.user_query
        )
        
        return BuildResponse(
            success=True,
            project_name=request.project_name,
            plan_content=plan_content,
            message="Build plan generated successfully."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate build plan: {str(e)}"
        )


@app.post("/api/agent/execute-task", response_model=ExecuteTaskResponse)
async def execute_task(request: ExecuteTaskRequest):
    """
    Execute the next unchecked step in the build plan.
    
    For file steps: Generates code using LLM
    For command steps: Executes with auto-fix on failure
    """
    if not workspace_manager.project_exists(request.project_name):
        raise HTTPException(
            status_code=404,
            detail=f"Project '{request.project_name}' not found."
        )
    
    try:
        result = agent_service.execute_next_step(request.project_name)
        
        step = result.get("step")
        
        return ExecuteTaskResponse(
            success=result.get("success", False),
            completed=result.get("completed", False),
            step_title=step["title"] if step else None,
            step_type=step["type"] if step else None,
            result_message=result.get("result", {}).get("message", "") if isinstance(result.get("result"), dict) else "",
            message=result.get("message", "Step executed.")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute step: {str(e)}"
        )


@app.get("/api/project/{project_name}/status", response_model=ProjectStatusResponse)
async def get_project_status(project_name: str):
    """Get the current status of a project."""
    exists = workspace_manager.project_exists(project_name)
    
    if not exists:
        return ProjectStatusResponse(
            project_name=project_name,
            exists=False,
            has_plan=False,
            has_report=False
        )
    
    progress = agent_service.get_plan_progress(project_name)
    has_report = workspace_manager.read_report(project_name) is not None
    
    return ProjectStatusResponse(
        project_name=project_name,
        exists=True,
        has_plan=progress["exists"],
        has_report=has_report,
        total_steps=progress["total_steps"],
        completed_steps=progress["completed_steps"],
        progress_percent=progress["progress_percent"]
    )


@app.get("/api/project/{project_name}/plan")
async def get_plan(project_name: str):
    """Get the build plan content for a project."""
    if not workspace_manager.project_exists(project_name):
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found."
        )
    
    plan_content = workspace_manager.read_plan(project_name)
    
    if plan_content is None:
        raise HTTPException(
            status_code=404,
            detail="Build plan not found. Generate a plan first."
        )
    
    return {"project_name": project_name, "plan_content": plan_content}


@app.get("/api/project/{project_name}/report")
async def get_report(project_name: str):
    """Get the build report content for a project."""
    if not workspace_manager.project_exists(project_name):
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found."
        )
    
    report_content = workspace_manager.read_report(project_name)
    
    if report_content is None:
        raise HTTPException(
            status_code=404,
            detail="Build report not found. Execute steps first."
        )
    
    return {"project_name": project_name, "report_content": report_content}


@app.get("/api/project/{project_name}/logs")
async def get_execution_logs(project_name: str, count: int = 5):
    """Get recent execution logs for a project."""
    if not workspace_manager.project_exists(project_name):
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found."
        )
    
    logs = workspace_manager.get_recent_logs(project_name, count=count)
    
    return {"project_name": project_name, "logs": logs}


@app.get("/api/projects")
async def list_projects():
    """List all projects in the workspace."""
    projects = workspace_manager.list_projects()
    return {"projects": projects}


@app.delete("/api/project/{project_name}")
async def delete_project(project_name: str):
    """Delete a project and all its contents."""
    if not workspace_manager.project_exists(project_name):
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found."
        )
    
    workspace_manager.delete_project(project_name)
    
    return {
        "success": True,
        "message": f"Project '{project_name}' deleted successfully."
    }


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
