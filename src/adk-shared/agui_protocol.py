# =============================================================================
# AG-UI Protocol Implementation for Enterprise Multi-Agent System
# Following SOLID Principles
# =============================================================================

"""
AG-UI Protocol Implementation
Enables standardized communication between frontend applications and AI agents
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, AsyncIterator, Callable
from collections import defaultdict

from pydantic import BaseModel, Field, validator

# =============================================================================
# AG-UI Protocol Models (Based on AG-UI Specification)
# =============================================================================

class MessageRole(str, Enum):
    """Message roles in AG-UI protocol"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class MessageType(str, Enum):
    """Types of messages in AG-UI protocol"""
    TEXT = "text"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    THINKING = "thinking"
    ERROR = "error"
    STATUS = "status"

class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"

class AGUIMessage(BaseModel):
    """AG-UI Protocol Message"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    type: MessageType = MessageType.TEXT
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    
    # For function calls/results
    function_name: Optional[str] = None
    function_args: Optional[Dict[str, Any]] = None
    function_result: Optional[Any] = None
    
    # For agent status updates
    agent_status: Optional[AgentStatus] = None
    agent_name: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        data = self.dict(exclude_none=True)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class AGUISession(BaseModel):
    """AG-UI Session representing a conversation"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: List[AGUIMessage] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    status: AgentStatus = AgentStatus.IDLE

    def add_message(self, message: AGUIMessage):
        """Add message to session"""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history in AG-UI format"""
        return [msg.to_dict() for msg in self.messages]

class AGUIStreamChunk(BaseModel):
    """Streaming response chunk"""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    content: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None

# =============================================================================
# AG-UI Protocol Interface (Following Interface Segregation Principle)
# =============================================================================

class IAGUIMessageHandler(ABC):
    """Interface for handling AG-UI messages"""

    @abstractmethod
    async def handle_message(self, session: AGUISession, message: AGUIMessage) -> AGUIMessage:
        """Handle incoming message and return response"""
        pass

class IAGUIStreamingHandler(ABC):
    """Interface for streaming responses"""

    @abstractmethod
    async def stream_response(self, session: AGUISession, message: AGUIMessage) -> AsyncIterator[AGUIStreamChunk]:
        """Stream response chunks"""
        pass

class IAGUISessionManager(ABC):
    """Interface for session management"""

    @abstractmethod
    async def create_session(self, user_id: Optional[str] = None) -> AGUISession:
        """Create new session"""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[AGUISession]:
        """Get existing session"""
        pass

    @abstractmethod
    async def update_session(self, session: AGUISession) -> bool:
        """Update session"""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        pass

class IAGUIEventEmitter(ABC):
    """Interface for event emission"""

    @abstractmethod
    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to connected clients"""
        pass

# =============================================================================
# AG-UI Session Manager Implementation (Single Responsibility Principle)
# =============================================================================

class RedisAGUISessionManager(IAGUISessionManager):
    """Redis-based session manager for AG-UI protocol"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.sessions_cache: Dict[str, AGUISession] = {}

    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(self.redis_url)

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    def _session_key(self, session_id: str) -> str:
        return f"agui:session:{session_id}"

    async def create_session(self, user_id: Optional[str] = None, agent_id: Optional[str] = None) -> AGUISession:
        """Create new AG-UI session"""
        await self.connect()
        
        session = AGUISession(
            user_id=user_id,
            agent_id=agent_id
        )
        
        # Store in Redis
        session_key = self._session_key(session.session_id)
        await self.redis_client.set(
            session_key,
            session.json(),
            ex=3600  # 1 hour TTL
        )
        
        # Cache locally
        self.sessions_cache[session.session_id] = session
        
        logging.info(f"AG-UI session created: {session.session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[AGUISession]:
        """Get session by ID"""
        # Check cache first
        if session_id in self.sessions_cache:
            return self.sessions_cache[session_id]
        
        await self.connect()
        
        # Get from Redis
        session_key = self._session_key(session_id)
        session_data = await self.redis_client.get(session_key)
        
        if session_data:
            session = AGUISession.parse_raw(session_data)
            self.sessions_cache[session_id] = session
            return session
        
        return None

    async def update_session(self, session: AGUISession) -> bool:
        """Update session"""
        await self.connect()
        
        session.updated_at = datetime.now()
        
        # Update Redis
        session_key = self._session_key(session.session_id)
        await self.redis_client.set(
            session_key,
            session.json(),
            ex=3600
        )
        
        # Update cache
        self.sessions_cache[session.session_id] = session
        
        return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        await self.connect()
        
        # Remove from Redis
        session_key = self._session_key(session_id)
        await self.redis_client.delete(session_key)
        
        # Remove from cache
        self.sessions_cache.pop(session_id, None)
        
        logging.info(f"AG-UI session deleted: {session_id}")
        return True

# =============================================================================
# AG-UI Message Handler Implementation (Open/Closed Principle)
# =============================================================================

class OrchestratorAGUIMessageHandler(IAGUIMessageHandler):
    """AG-UI message handler that integrates with our orchestrator"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("agui-message-handler")

    async def handle_message(self, session: AGUISession, message: AGUIMessage) -> AGUIMessage:
        """Handle user message and route to orchestrator"""
        
        try:
            # Update session status
            session.status = AgentStatus.THINKING
            
            # Create thinking message
            thinking_message = AGUIMessage(
                role=MessageRole.AGENT,
                type=MessageType.THINKING,
                content="Processing your request...",
                agent_status=AgentStatus.THINKING,
                metadata={"session_id": session.session_id}
            )
            session.add_message(thinking_message)
            
            # Route to orchestrator
            orchestrator_response = await self.orchestrator.route_request(
                query=message.content,
                context={
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "conversation_history": session.get_conversation_history()
                }
            )
            
            # Create agent response message
            response_message = AGUIMessage(
                role=MessageRole.AGENT,
                type=MessageType.TEXT,
                content=orchestrator_response.get('response', {}).get('response', ''),
                agent_status=AgentStatus.COMPLETED,
                agent_name=orchestrator_response.get('selected_agent', {}).get('name', 'Unknown'),
                metadata={
                    "transaction_id": orchestrator_response.get('transaction_id'),
                    "selected_agent": orchestrator_response.get('selected_agent'),
                    "processing_time_ms": orchestrator_response.get('response', {}).get('processing_time_ms')
                }
            )
            
            session.add_message(response_message)
            session.status = AgentStatus.COMPLETED
            
            return response_message
            
        except Exception as e:
            self.logger.error(f"Error handling AG-UI message: {str(e)}")
            
            # Create error message
            error_message = AGUIMessage(
                role=MessageRole.AGENT,
                type=MessageType.ERROR,
                content=f"Error processing request: {str(e)}",
                agent_status=AgentStatus.ERROR,
                metadata={"error": str(e)}
            )
            
            session.add_message(error_message)
            session.status = AgentStatus.ERROR
            
            return error_message

# =============================================================================
# AG-UI Streaming Handler Implementation
# =============================================================================

class OrchestratorAGUIStreamingHandler(IAGUIStreamingHandler):
    """Streaming handler for AG-UI protocol"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("agui-streaming-handler")

    async def stream_response(self, session: AGUISession, message: AGUIMessage) -> AsyncIterator[AGUIStreamChunk]:
        """Stream response chunks"""
        
        try:
            # Yield thinking status
            yield AGUIStreamChunk(
                session_id=session.session_id,
                content="",
                is_final=False,
                metadata={"status": "thinking"}
            )
            
            # Get orchestrator response
            response = await self.orchestrator.route_request(
                query=message.content,
                context={
                    "session_id": session.session_id,
                    "streaming": True
                }
            )
            
            # Stream the response in chunks
            full_response = response.get('response', {}).get('response', '')
            
            # Simulate streaming (in practice, this would stream from LLM)
            chunk_size = 20
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i + chunk_size]
                
                yield AGUIStreamChunk(
                    session_id=session.session_id,
                    content=chunk,
                    is_final=(i + chunk_size >= len(full_response)),
                    metadata={
                        "chunk_index": i // chunk_size,
                        "agent_name": response.get('selected_agent', {}).get('name')
                    }
                )
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.05)
            
            # Final chunk with metadata
            yield AGUIStreamChunk(
                session_id=session.session_id,
                content="",
                is_final=True,
                metadata={
                    "status": "completed",
                    "transaction_id": response.get('transaction_id'),
                    "processing_time_ms": response.get('response', {}).get('processing_time_ms')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error streaming AG-UI response: {str(e)}")
            
            yield AGUIStreamChunk(
                session_id=session.session_id,
                content=f"Error: {str(e)}",
                is_final=True,
                metadata={"status": "error", "error": str(e)}
            )

# =============================================================================
# AG-UI Event Emitter Implementation (Dependency Inversion Principle)
# =============================================================================

class WebSocketAGUIEventEmitter(IAGUIEventEmitter):
    """WebSocket-based event emitter for AG-UI protocol"""

    def __init__(self):
        self.connections: Dict[str, List] = defaultdict(list)  # session_id -> [websockets]
        self.logger = logging.getLogger("agui-event-emitter")

    def register_connection(self, session_id: str, websocket):
        """Register WebSocket connection for session"""
        self.connections[session_id].append(websocket)
        self.logger.info(f"WebSocket registered for session: {session_id}")

    def unregister_connection(self, session_id: str, websocket):
        """Unregister WebSocket connection"""
        if session_id in self.connections:
            self.connections[session_id].remove(websocket)
            if not self.connections[session_id]:
                del self.connections[session_id]

    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to all connections in session"""
        session_id = data.get('session_id')
        
        if not session_id or session_id not in self.connections:
            return
        
        event_payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connections in this session
        disconnected = []
        for websocket in self.connections[session_id]:
            try:
                await websocket.send_json(event_payload)
            except Exception as e:
                self.logger.warning(f"Failed to send to WebSocket: {str(e)}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            self.unregister_connection(session_id, ws)

# =============================================================================
# AG-UI Protocol Server (Facade Pattern for easy integration)
# =============================================================================

class AGUIProtocolServer:
    """
    Main AG-UI Protocol Server
    Facade that coordinates all AG-UI components
    """

    def __init__(self, 
                 orchestrator,
                 session_manager: IAGUISessionManager,
                 message_handler: IAGUIMessageHandler,
                 streaming_handler: IAGUIStreamingHandler,
                 event_emitter: IAGUIEventEmitter):
        
        self.orchestrator = orchestrator
        self.session_manager = session_manager
        self.message_handler = message_handler
        self.streaming_handler = streaming_handler
        self.event_emitter = event_emitter
        self.logger = logging.getLogger("agui-protocol-server")

    async def create_session(self, user_id: Optional[str] = None) -> AGUISession:
        """Create new AG-UI session"""
        session = await self.session_manager.create_session(user_id)
        
        # Emit session created event
        await self.event_emitter.emit_event("session_created", {
            "session_id": session.session_id,
            "user_id": user_id
        })
        
        return session

    async def send_message(self, 
                          session_id: str, 
                          content: str, 
                          user_id: Optional[str] = None) -> AGUIMessage:
        """Send message and get response"""
        
        # Get session
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Create user message
        user_message = AGUIMessage(
            role=MessageRole.USER,
            type=MessageType.TEXT,
            content=content,
            metadata={"user_id": user_id}
        )
        session.add_message(user_message)
        
        # Emit message received event
        await self.event_emitter.emit_event("message_received", {
            "session_id": session_id,
            "message": user_message.to_dict()
        })
        
        # Handle message
        response_message = await self.message_handler.handle_message(session, user_message)
        
        # Update session
        await self.session_manager.update_session(session)
        
        # Emit response event
        await self.event_emitter.emit_event("message_sent", {
            "session_id": session_id,
            "message": response_message.to_dict()
        })
        
        return response_message

    async def stream_message(self, 
                           session_id: str, 
                           content: str) -> AsyncIterator[AGUIStreamChunk]:
        """Send message and stream response"""
        
        # Get session
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Create user message
        user_message = AGUIMessage(
            role=MessageRole.USER,
            type=MessageType.TEXT,
            content=content
        )
        session.add_message(user_message)
        
        # Stream response
        async for chunk in self.streaming_handler.stream_response(session, user_message):
            # Emit chunk event
            await self.event_emitter.emit_event("stream_chunk", {
                "session_id": session_id,
                "chunk": chunk.dict()
            })
            
            yield chunk
        
        # Update session
        await self.session_manager.update_session(session)

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        return session.get_conversation_history()

    async def close_session(self, session_id: str):
        """Close and cleanup session"""
        await self.session_manager.delete_session(session_id)
        
        await self.event_emitter.emit_event("session_closed", {
            "session_id": session_id
        })

# =============================================================================
# Export all public classes and functions
# =============================================================================

__all__ = [
    # Models
    'AGUIMessage',
    'AGUISession', 
    'AGUIStreamChunk',
    'MessageRole',
    'MessageType',
    'AgentStatus',
    
    # Interfaces
    'IAGUIMessageHandler',
    'IAGUIStreamingHandler',
    'IAGUISessionManager',
    'IAGUIEventEmitter',
    
    # Implementations
    'RedisAGUISessionManager',
    'OrchestratorAGUIMessageHandler',
    'OrchestratorAGUIStreamingHandler',
    'WebSocketAGUIEventEmitter',
    'AGUIProtocolServer'
]
