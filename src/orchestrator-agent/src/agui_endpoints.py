# =============================================================================
# AG-UI Protocol FastAPI Endpoints
# File: orchestrator-agent/agui_endpoints.py
# =============================================================================

"""
FastAPI endpoints for AG-UI protocol
Add these to your orchestrator's main.py
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from adk_shared.agui_protocol import (
    AGUIProtocolServer,
    AGUIMessage,
    AGUISession,
    AGUIStreamChunk,
    MessageRole,
    MessageType
)

# =============================================================================
# Request/Response Models
# =============================================================================

class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None
    initial_context: Optional[dict] = None

class SendMessageRequest(BaseModel):
    content: str
    user_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    user_id: Optional[str]
    created_at: str
    status: str

class MessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None

# =============================================================================
# AG-UI Router
# =============================================================================

def create_agui_router(agui_server: AGUIProtocolServer) -> APIRouter:
    """Create FastAPI router with AG-UI endpoints"""
    
    router = APIRouter(prefix="/agui", tags=["AG-UI Protocol"])
    
    
    @router.post("/sessions", response_model=SessionResponse)
    async def create_session(request: CreateSessionRequest):
        """
        Create new AG-UI session
        
        This is the entry point for frontend applications to start
        a conversation with the multi-agent system.
        """
        try:
            session = await agui_server.create_session(user_id=request.user_id)
            
            # Add initial context if provided
            if request.initial_context:
                session.context.update(request.initial_context)
                await agui_server.session_manager.update_session(session)
            
            return SessionResponse(
                session_id=session.session_id,
                user_id=session.user_id,
                created_at=session.created_at.isoformat(),
                status=session.status.value
            )
            
        except Exception as e:
            logging.error(f"Failed to create AG-UI session: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.get("/sessions/{session_id}", response_model=SessionResponse)
    async def get_session(session_id: str):
        """Get session details"""
        try:
            session = await agui_server.session_manager.get_session(session_id)
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return SessionResponse(
                session_id=session.session_id,
                user_id=session.user_id,
                created_at=session.created_at.isoformat(),
                status=session.status.value
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Failed to get session: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.delete("/sessions/{session_id}")
    async def close_session(session_id: str):
        """Close and cleanup session"""
        try:
            await agui_server.close_session(session_id)
            return {"status": "closed", "session_id": session_id}
            
        except Exception as e:
            logging.error(f"Failed to close session: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
    async def send_message(session_id: str, request: SendMessageRequest):
        """
        Send message to agent (non-streaming)
        
        Frontend sends user message, receives complete agent response.
        """
        try:
            response_message = await agui_server.send_message(
                session_id=session_id,
                content=request.content,
                user_id=request.user_id
            )
            
            return MessageResponse(
                message_id=response_message.id,
                role=response_message.role.value,
                content=response_message.content,
                timestamp=response_message.timestamp.isoformat(),
                metadata=response_message.metadata
            )
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logging.error(f"Failed to send message: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.get("/sessions/{session_id}/messages")
    async def get_conversation_history(session_id: str):
        """Get full conversation history"""
        try:
            history = await agui_server.get_session_history(session_id)
            return {
                "session_id": session_id,
                "messages": history,
                "total_messages": len(history)
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logging.error(f"Failed to get history: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @router.post("/sessions/{session_id}/messages/stream")
    async def send_message_streaming(session_id: str, request: SendMessageRequest):
        """
        Send message with streaming response (SSE)
        
        Frontend sends message, receives streamed agent response chunks.
        """
        
        async def event_generator():
            """Generate SSE events"""
            try:
                async for chunk in agui_server.stream_message(session_id, request.content):
                    # Format as Server-Sent Event
                    event_data = {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "is_final": chunk.is_final,
                        "metadata": chunk.metadata
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                    if chunk.is_final:
                        break
                        
            except Exception as e:
                error_event = {
                    "error": str(e),
                    "is_final": True
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    
    
    @router.websocket("/sessions/{session_id}/ws")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """
        WebSocket endpoint for real-time bidirectional communication
        
        Provides the most interactive experience for frontend applications.
        """
        await websocket.accept()
        
        # Register connection with event emitter
        agui_server.event_emitter.register_connection(session_id, websocket)
        
        try:
            # Verify session exists
            session = await agui_server.session_manager.get_session(session_id)
            if not session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found"
                })
                await websocket.close()
                return
            
            # Send welcome message
            await websocket.send_json({
                "type": "connected",
                "session_id": session_id,
                "message": "Connected to AG-UI protocol"
            })
            
            # Message loop
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                message_type = data.get("type")
                
                if message_type == "message":
                    # User sending a message
                    content = data.get("content")
                    
                    # Send typing indicator
                    await websocket.send_json({
                        "type": "status",
                        "status": "thinking"
                    })
                    
                    # Process message
                    response = await agui_server.send_message(
                        session_id=session_id,
                        content=content
                    )
                    
                    # Send response
                    await websocket.send_json({
                        "type": "message",
                        "message": {
                            "id": response.id,
                            "role": response.role.value,
                            "content": response.content,
                            "timestamp": response.timestamp.isoformat(),
                            "metadata": response.metadata
                        }
                    })
                
                elif message_type == "ping":
                    # Heartbeat - send pong
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                
                elif message_type == "get_history":
                    # Client requesting conversation history
                    history = await agui_server.get_session_history(session_id)
                    await websocket.send_json({
                        "type": "history",
                        "messages": history
                    })
                
                elif message_type == "close":
                    # Client requesting to close connection
                    await websocket.send_json({
                        "type": "closing",
                        "message": "Closing connection"
                    })
                    break
                
                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                    
        except WebSocketDisconnect:
            logging.info(f"WebSocket disconnected for session: {session_id}")
            
        except Exception as e:
            logging.error(f"WebSocket error for session {session_id}: {str(e)}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass  # Connection might be already closed
                
        finally:
            # Cleanup - unregister connection
            agui_server.event_emitter.unregister_connection(session_id, websocket)
            logging.info(f"WebSocket connection cleaned up for session: {session_id}")
    
    
    return router


# =============================================================================
# Usage Example
# =============================================================================

"""
# In your orchestrator's main.py:

from agui_endpoints import create_agui_router
from adk_shared.agui_protocol import (
    AGUIProtocolServer,
    RedisAGUISessionManager,
    OrchestratorAGUIMessageHandler,
    OrchestratorAGUIStreamingHandler,
    WebSocketAGUIEventEmitter
)

# In the lifespan function:
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # ... (existing orchestrator initialization)
    
    # Initialize AG-UI components
    session_manager = RedisAGUISessionManager(redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"))
    message_handler = OrchestratorAGUIMessageHandler(orchestrator)
    streaming_handler = OrchestratorAGUIStreamingHandler(orchestrator)
    event_emitter = WebSocketAGUIEventEmitter()
    
    # Create AG-UI server
    agui_server = AGUIProtocolServer(
        orchestrator,
        session_manager,
        message_handler,
        streaming_handler,
        event_emitter
    )
    
    # Create and include router
    agui_router = create_agui_router(agui_server)
    app.include_router(agui_router)
    
    yield
    
    # Cleanup
    await session_manager.disconnect()

"""
