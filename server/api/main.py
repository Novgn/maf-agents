"""
FastAPI server for maf-agents workflow system.

Provides REST and WebSocket APIs for managing detector development workflows
from a Next.js frontend.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import workflow components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.detector_workflow import build_detector_workflow
from agent_framework import WorkflowOutputEvent, WorkflowFailedEvent


# Global state management
workflows: Dict[str, Any] = {}
websocket_connections: Dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    # Startup
    print("🚀 maf-agents API Server starting...")
    yield
    # Shutdown
    print("👋 maf-agents API Server shutting down...")


app = FastAPI(
    title="MAF Agents API",
    description="API for managing ETW detector development workflows",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models
# ============================================================================

class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow."""
    workflow_id: str | None = None


class WorkflowCreateResponse(BaseModel):
    """Response after creating a workflow."""
    workflow_id: str
    status: str
    created_at: str


class UserInputRequest(BaseModel):
    """User input for workflow steps."""
    input_type: str = Field(..., description="Type of input: triage_response, etw_input, approval, etc.")
    data: Dict[str, Any] = Field(..., description="Input data")


class WorkflowStatusResponse(BaseModel):
    """Current workflow status."""
    workflow_id: str
    status: str
    current_step: str | None
    step_number: int | None
    total_steps: int = 9
    data: Dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# ============================================================================
# Workflow Management
# ============================================================================

async def run_workflow_async(workflow_id: str, input_data: Dict[str, Any]):
    """
    Run workflow asynchronously and stream events via WebSocket.

    Args:
        workflow_id: Unique workflow identifier
        input_data: Initial workflow data
    """
    try:
        # Build workflow
        workflow = await build_detector_workflow()

        # Initialize workflow state
        workflows[workflow_id] = {
            "status": "running",
            "current_step": "initializing",
            "step_number": 0,
            "data": input_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Send initial status update
        await broadcast_workflow_update(workflow_id)

        # Run workflow with streaming
        async for event in workflow.run_stream(input_data):
            if isinstance(event, WorkflowOutputEvent):
                # Workflow completed successfully
                workflows[workflow_id]["status"] = "completed"
                workflows[workflow_id]["data"] = event.data
                workflows[workflow_id]["updated_at"] = datetime.now().isoformat()

                await broadcast_workflow_update(workflow_id, {
                    "type": "workflow_complete",
                    "data": event.data
                })

            elif isinstance(event, WorkflowFailedEvent):
                # Workflow failed
                workflows[workflow_id]["status"] = "failed"
                workflows[workflow_id]["error"] = event.details.message
                workflows[workflow_id]["updated_at"] = datetime.now().isoformat()

                await broadcast_workflow_update(workflow_id, {
                    "type": "workflow_failed",
                    "error": event.details.message,
                    "traceback": event.details.traceback
                })

    except Exception as e:
        workflows[workflow_id]["status"] = "failed"
        workflows[workflow_id]["error"] = str(e)
        workflows[workflow_id]["updated_at"] = datetime.now().isoformat()

        await broadcast_workflow_update(workflow_id, {
            "type": "workflow_error",
            "error": str(e)
        })


async def broadcast_workflow_update(workflow_id: str, extra_data: Dict[str, Any] | None = None):
    """
    Broadcast workflow status update to connected WebSocket clients.

    Args:
        workflow_id: Workflow to broadcast
        extra_data: Additional data to include in broadcast
    """
    if workflow_id in websocket_connections:
        ws = websocket_connections[workflow_id]

        message = {
            **workflows[workflow_id],
            **(extra_data or {})
        }

        try:
            await ws.send_json(message)
        except Exception as e:
            print(f"Error broadcasting to {workflow_id}: {e}")
            # Remove dead connection
            if workflow_id in websocket_connections:
                del websocket_connections[workflow_id]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "MAF Agents API",
        "version": "1.0.0",
        "status": "running",
        "workflows": len(workflows),
        "connections": len(websocket_connections)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/workflows", response_model=WorkflowCreateResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new detector development workflow.

    Workflow will run in the background and can be monitored via WebSocket.
    """
    workflow_id = request.workflow_id or str(uuid4())

    # Check if workflow already exists
    if workflow_id in workflows:
        raise HTTPException(status_code=400, detail="Workflow already exists")

    # Prepare initial input data
    input_data = {
        "workflow_id": workflow_id,
    }

    # Start workflow in background
    background_tasks.add_task(run_workflow_async, workflow_id, input_data)

    return WorkflowCreateResponse(
        workflow_id=workflow_id,
        status="starting",
        created_at=datetime.now().isoformat()
    )


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get current status of a workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows[workflow_id]

    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        status=workflow["status"],
        current_step=workflow.get("current_step"),
        step_number=workflow.get("step_number"),
        data=workflow.get("data", {}),
        error=workflow.get("error")
    )


@app.post("/api/workflows/{workflow_id}/input")
async def submit_workflow_input(workflow_id: str, request: UserInputRequest):
    """
    Submit user input to a running workflow.

    Used for:
    - Triage conversation responses
    - ETW provider GUID and rule ID
    - PR approval decisions
    - Results confirmation
    """
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = workflows[workflow_id]

    # Update workflow data with user input
    if "user_inputs" not in workflow["data"]:
        workflow["data"]["user_inputs"] = []

    workflow["data"]["user_inputs"].append({
        "type": request.input_type,
        "data": request.data,
        "timestamp": datetime.now().isoformat()
    })

    workflow["updated_at"] = datetime.now().isoformat()

    # Broadcast update
    await broadcast_workflow_update(workflow_id, {
        "type": "user_input_received",
        "input_type": request.input_type
    })

    return {"status": "accepted", "workflow_id": workflow_id}


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow (cleanup)."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Remove workflow
    del workflows[workflow_id]

    # Close WebSocket connection if exists
    if workflow_id in websocket_connections:
        try:
            await websocket_connections[workflow_id].close()
        except:
            pass
        del websocket_connections[workflow_id]

    return {"status": "deleted", "workflow_id": workflow_id}


@app.get("/api/workflows")
async def list_workflows():
    """List all workflows."""
    return {
        "workflows": [
            {
                "workflow_id": wid,
                "status": w["status"],
                "current_step": w.get("current_step"),
                "created_at": w["created_at"],
                "updated_at": w["updated_at"]
            }
            for wid, w in workflows.items()
        ],
        "total": len(workflows)
    }


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/workflows/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """
    WebSocket connection for real-time workflow updates.

    Clients connect to this endpoint to receive live updates about
    workflow progress, step completion, user input requests, etc.
    """
    await websocket.accept()

    # Register connection
    websocket_connections[workflow_id] = websocket

    try:
        # Send initial status if workflow exists
        if workflow_id in workflows:
            await websocket.send_json({
                "type": "connected",
                **workflows[workflow_id]
            })
        else:
            await websocket.send_json({
                "type": "connected",
                "message": "Waiting for workflow to start..."
            })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client messages (e.g., ping/pong)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error for {workflow_id}: {e}")
                break

    finally:
        # Cleanup connection
        if workflow_id in websocket_connections:
            del websocket_connections[workflow_id]
        print(f"WebSocket closed for workflow: {workflow_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
