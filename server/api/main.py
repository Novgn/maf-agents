"""
FastAPI server for maf-agents workflow system.

Provides REST and WebSocket APIs for managing detector development workflows
from a Next.js frontend.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
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

# Import session storage
from storage import create_session_store_from_env, WorkflowSession, AzureTableSessionStore


# Global state management
workflows: Dict[str, Any] = {}
websocket_connections: Dict[str, WebSocket] = {}
# Conversation queues for agent interaction (workflow_id -> asyncio.Queue)
conversation_queues: Dict[str, asyncio.Queue] = {}
# Session store (will be initialized in lifespan)
session_store: AzureTableSessionStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global session_store

    # Startup
    print("🚀 maf-agents API Server starting...")

    # Initialize session store from environment
    try:
        session_store = create_session_store_from_env()
        print("✓ Session store initialized from environment")
    except Exception as e:
        print(f"⚠️  Session store initialization failed: {e}")
        print("ℹ️  Server will run without persistent session storage")
        session_store = None

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
        # Create conversation queue for this workflow
        conversation_queues[workflow_id] = asyncio.Queue()
        print(f"✓ Created conversation queue for workflow {workflow_id[:8]}")

        # Build workflow with conversation support (pass both broadcast functions)
        workflow = await build_detector_workflow(
            workflow_id,
            conversation_queues[workflow_id],
            broadcast_workflow_update,
            broadcast_chat_message
        )

        # Initialize workflow state
        workflows[workflow_id] = {
            "status": "running",
            "current_step": "detector_triage",
            "step_number": 1,
            "data": input_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Update session in Azure Table Storage
        if session_store:
            try:
                session = await session_store.get_session(workflow_id, "anonymous")
                if session:
                    session.status = "running"
                    session.current_step = 1
                    await session_store.save_session(session)
            except Exception as e:
                print(f"⚠️  Failed to update session status: {e}")

        # Send initial status update
        await broadcast_workflow_update(workflow_id)

        # Run workflow with streaming
        async for event in workflow.run_stream(input_data):
            if isinstance(event, WorkflowOutputEvent):
                # Workflow completed successfully
                workflows[workflow_id]["status"] = "completed"
                workflows[workflow_id]["data"] = event.data
                workflows[workflow_id]["updated_at"] = datetime.now().isoformat()

                # Update session in Azure Table Storage
                if session_store:
                    try:
                        session = await session_store.get_session(workflow_id, "anonymous")
                        if session:
                            session.status = "completed"
                            session.workflow_data = event.data if isinstance(event.data, dict) else {}
                            await session_store.save_session(session)
                    except Exception as e:
                        print(f"⚠️  Failed to update session on completion: {e}")

                await broadcast_workflow_update(workflow_id, {
                    "type": "workflow_complete",
                    "data": event.data
                })

            elif isinstance(event, WorkflowFailedEvent):
                # Workflow failed
                workflows[workflow_id]["status"] = "failed"
                workflows[workflow_id]["error"] = event.details.message
                workflows[workflow_id]["updated_at"] = datetime.now().isoformat()

                # Update session in Azure Table Storage
                if session_store:
                    try:
                        session = await session_store.get_session(workflow_id, "anonymous")
                        if session:
                            session.status = "failed"
                            session.metadata["error"] = event.details.message
                            await session_store.save_session(session)
                    except Exception as e:
                        print(f"⚠️  Failed to update session on failure: {e}")

                await broadcast_workflow_update(workflow_id, {
                    "type": "workflow_failed",
                    "error": event.details.message,
                    "traceback": event.details.traceback
                })

    except Exception as e:
        workflows[workflow_id]["status"] = "failed"
        workflows[workflow_id]["error"] = str(e)
        workflows[workflow_id]["updated_at"] = datetime.now().isoformat()

        # Update session in Azure Table Storage
        if session_store:
            try:
                session = await session_store.get_session(workflow_id, "anonymous")
                if session:
                    session.status = "failed"
                    session.metadata["error"] = str(e)
                    await session_store.save_session(session)
            except Exception as ex:
                print(f"⚠️  Failed to update session on exception: {ex}")

        await broadcast_workflow_update(workflow_id, {
            "type": "workflow_error",
            "error": str(e)
        })
    finally:
        # Cleanup conversation queue
        if workflow_id in conversation_queues:
            del conversation_queues[workflow_id]
            print(f"✓ Cleaned up conversation queue for workflow {workflow_id[:8]}")


async def broadcast_chat_message(
    workflow_id: str,
    message_type: str,
    content: str,
    metadata: Dict[str, Any] | None = None
):
    """
    Broadcast a chat message to the workflow's WebSocket connection.

    This sends rich message types that render as different UI components in the frontend.

    Args:
        workflow_id: Workflow identifier
        message_type: Type of message (agent, system, step_transition, form_request, etc.)
        content: Message content (markdown supported)
        metadata: Additional metadata (formFields, approvalData, progress, etc.)
    """
    if workflow_id in websocket_connections:
        ws = websocket_connections[workflow_id]

        message_data = {
            "type": "chat_message",
            "message_type": message_type,
            "message": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }

        # Save to session history
        if session_store:
            try:
                session = await session_store.get_session(workflow_id, "anonymous")
                if session:
                    session.conversation_history.append({
                        "type": message_type,
                        "content": content,
                        "timestamp": message_data["timestamp"],
                        "metadata": metadata or {}
                    })
                    await session_store.save_session(session)
            except Exception as e:
                print(f"⚠️  Failed to save chat message to session: {e}")

        try:
            await ws.send_json(message_data)
        except Exception as e:
            print(f"Error broadcasting chat message to {workflow_id}: {e}")
            if workflow_id in websocket_connections:
                del websocket_connections[workflow_id]


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

        # Save agent messages to conversation history in Azure Table Storage
        if extra_data and extra_data.get("type") == "agent_message" and session_store:
            try:
                session = await session_store.get_session(workflow_id, "anonymous")
                if session:
                    session.conversation_history.append({
                        "role": "assistant",
                        "content": extra_data.get("message", ""),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    # Update current step if provided
                    if "step_number" in extra_data:
                        session.current_step = extra_data["step_number"]
                    await session_store.save_session(session)
                    print(f"✓ Saved agent message to session history")
            except Exception as e:
                print(f"⚠️  Failed to save agent message to session: {e}")

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

    # Create initial session in Azure Table Storage
    # TODO: Replace "anonymous" with actual user_id from JWT token after Azure AD auth
    if session_store:
        session = WorkflowSession(
            workflow_id=workflow_id,
            user_id="anonymous",  # TODO: Extract from JWT after Azure AD auth
            status="starting",
            current_step=0,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            conversation_history=[],
            workflow_data={},
            metadata={
                "created_from": "api",
                "client_ip": "unknown",  # TODO: Extract from request
            }
        )
        try:
            await session_store.save_session(session)
            print(f"✓ Created session in Azure Table Storage for workflow {workflow_id[:8]}")
        except Exception as e:
            print(f"⚠️  Failed to save initial session: {e}")

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
    # Check in-memory workflows first
    if workflow_id in workflows:
        workflow = workflows[workflow_id]
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=workflow["status"],
            current_step=workflow.get("current_step"),
            step_number=workflow.get("step_number"),
            data=workflow.get("data", {}),
            error=workflow.get("error")
        )

    # If not in memory, try to restore from Azure Table Storage
    if session_store:
        try:
            session = await session_store.get_session(workflow_id, "anonymous")
            if session:
                print(f"✓ Restored session from Azure Table Storage for workflow {workflow_id[:8]}")
                # Restore to in-memory workflows (but don't restart the workflow)
                workflows[workflow_id] = {
                    "status": session.status,
                    "current_step": session.current_step,
                    "step_number": session.current_step,
                    "data": session.workflow_data,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                }
                return WorkflowStatusResponse(
                    workflow_id=workflow_id,
                    status=session.status,
                    current_step=str(session.current_step) if session.current_step else None,
                    step_number=session.current_step,
                    data=session.workflow_data,
                    error=session.metadata.get("error")
                )
        except Exception as e:
            print(f"⚠️  Failed to restore session from storage: {e}")

    # Workflow not found in memory or storage
    raise HTTPException(status_code=404, detail="Workflow not found")


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

    # Handle triage message - put in conversation queue for agent
    if request.input_type == "triage_message":
        if workflow_id in conversation_queues:
            message = request.data.get("message", "")
            await conversation_queues[workflow_id].put(message)
            print(f"📨 Queued user message for workflow {workflow_id[:8]}: {message}")

            # Save user message to conversation history in Azure Table Storage
            if session_store:
                try:
                    session = await session_store.get_session(workflow_id, "anonymous")
                    if session:
                        session.conversation_history.append({
                            "role": "user",
                            "content": message,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        await session_store.save_session(session)
                        print(f"✓ Saved user message to session history")
                except Exception as e:
                    print(f"⚠️  Failed to save conversation history: {e}")
        else:
            print(f"⚠️  No conversation queue for workflow {workflow_id[:8]}")

    # Handle ETW input - put full data in conversation queue
    elif request.input_type == "etw_input":
        if workflow_id in conversation_queues:
            await conversation_queues[workflow_id].put(request.data)
            print(f"📨 Queued ETW input for workflow {workflow_id[:8]}: providerGuid={request.data.get('providerGuid', 'N/A')}, ruleId={request.data.get('ruleId', 'N/A')}")
        else:
            print(f"⚠️  No conversation queue for workflow {workflow_id[:8]}")

    # Handle approval - put approval data in conversation queue
    elif request.input_type == "approval":
        if workflow_id in conversation_queues:
            await conversation_queues[workflow_id].put(request.data)
            approved = request.data.get("approved", False)
            print(f"📨 Queued approval for workflow {workflow_id[:8]}: approved={approved}")
        else:
            print(f"⚠️  No conversation queue for workflow {workflow_id[:8]}")

    # Handle generic form data
    elif request.input_type == "form_data":
        if workflow_id in conversation_queues:
            await conversation_queues[workflow_id].put(request.data)
            print(f"📨 Queued form data for workflow {workflow_id[:8]}: {request.data}")
        else:
            print(f"⚠️  No conversation queue for workflow {workflow_id[:8]}")

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
    """List all workflows (in-memory only)."""
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


@app.get("/api/sessions")
async def list_user_sessions(user_id: str = "anonymous", limit: int = 100):
    """
    List all workflow sessions for a user from Azure Table Storage.

    Args:
        user_id: User identifier (default: "anonymous")
        limit: Maximum number of sessions to return (default: 100)

    Returns:
        List of workflow sessions with conversation history
    """
    if not session_store:
        raise HTTPException(
            status_code=503,
            detail="Session storage not configured. Set AZURE_STORAGE_ENDPOINT environment variable."
        )

    try:
        sessions = await session_store.list_user_sessions(user_id, limit)
        return {
            "sessions": [
                {
                    "workflow_id": s.workflow_id,
                    "status": s.status,
                    "current_step": s.current_step,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                    "conversation_length": len(s.conversation_history),
                    # Optionally include full conversation history
                    "conversation_history": s.conversation_history,
                    "workflow_data": s.workflow_data,
                }
                for s in sessions
            ],
            "total": len(sessions),
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.post("/api/sessions/cleanup")
async def cleanup_old_sessions(days: int = 30):
    """
    Delete workflow sessions older than specified days.

    Args:
        days: Number of days to keep sessions (default: 30)

    Returns:
        Number of sessions deleted
    """
    if not session_store:
        raise HTTPException(
            status_code=503,
            detail="Session storage not configured. Set AZURE_STORAGE_ENDPOINT environment variable."
        )

    try:
        deleted_count = await session_store.cleanup_old_sessions(days)
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup sessions: {str(e)}")


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
