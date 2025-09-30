# AG-UI Protocol Integration Guide

## Overview

The AG-UI Protocol provides a standardized communication interface between frontend applications and AI agents in the enterprise multi-agent system. This protocol enables real-time, bidirectional communication with support for session management, message handling, streaming responses, and WebSocket connections.

## Architecture

### Core Components

1. **AG-UI Protocol Server** (`AGUIProtocolServer`)
   - Main facade coordinating all AG-UI components
   - Handles session lifecycle and message routing

2. **Session Manager** (`RedisAGUISessionManager`)
   - Redis-based session storage and management
   - Handles session creation, updates, and cleanup

3. **Message Handler** (`OrchestratorAGUIMessageHandler`)
   - Processes user messages and routes to orchestrator
   - Manages agent responses and error handling

4. **Streaming Handler** (`OrchestratorAGUIStreamingHandler`)
   - Provides real-time streaming responses
   - Chunks responses for progressive delivery

5. **Event Emitter** (`WebSocketAGUIEventEmitter`)
   - Manages WebSocket connections
   - Emits real-time events to connected clients

## File Structure

```
src/
├── adk-shared/
│   └── agui_protocol.py          # Core protocol implementation
└── orchestrator-agent/
    └── src/
        ├── agui_endpoints.py     # FastAPI endpoints
        └── main.py               # Updated with AG-UI integration
```

## API Endpoints

### Session Management

#### Create Session
```http
POST /agui/sessions
Content-Type: application/json

{
  "user_id": "optional-user-id",
  "initial_context": {
    "preferences": {},
    "metadata": {}
  }
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "user_id": "optional-user-id",
  "created_at": "2024-01-01T00:00:00Z",
  "status": "idle"
}
```

#### Get Session
```http
GET /agui/sessions/{session_id}
```

#### Close Session
```http
DELETE /agui/sessions/{session_id}
```

### Message Handling

#### Send Message (Non-streaming)
```http
POST /agui/sessions/{session_id}/messages
Content-Type: application/json

{
  "content": "Hello, I need help with data analysis",
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "message_id": "uuid",
  "role": "agent",
  "content": "I'll help you with data analysis...",
  "timestamp": "2024-01-01T00:00:00Z",
  "metadata": {
    "transaction_id": "uuid",
    "selected_agent": "DataSearchAgent",
    "processing_time_ms": 1500
  }
}
```

#### Send Message (Streaming - SSE)
```http
POST /agui/sessions/{session_id}/messages/stream
Content-Type: application/json

{
  "content": "Generate a comprehensive report"
}
```

**Response:** Server-Sent Events stream
```
data: {"chunk_id": "uuid", "content": "I'll generate", "is_final": false, "metadata": {}}

data: {"chunk_id": "uuid", "content": " a comprehensive", "is_final": false, "metadata": {}}

data: {"chunk_id": "uuid", "content": " report for you.", "is_final": true, "metadata": {"status": "completed"}}
```

#### Get Conversation History
```http
GET /agui/sessions/{session_id}/messages
```

### WebSocket Communication

#### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/agui/sessions/{session_id}/ws');
```

#### Message Types

1. **User Message**
```json
{
  "type": "message",
  "content": "Hello, I need help"
}
```

2. **Ping/Pong (Heartbeat)**
```json
{
  "type": "ping"
}
```

3. **Get History**
```json
{
  "type": "get_history"
}
```

4. **Close Connection**
```json
{
  "type": "close"
}
```

#### Server Responses

1. **Connected**
```json
{
  "type": "connected",
  "session_id": "uuid",
  "message": "Connected to AG-UI protocol"
}
```

2. **Agent Response**
```json
{
  "type": "message",
  "message": {
    "id": "uuid",
    "role": "agent",
    "content": "I'll help you with that...",
    "timestamp": "2024-01-01T00:00:00Z",
    "metadata": {
      "transaction_id": "uuid",
      "selected_agent": "DataSearchAgent"
    }
  }
}
```

3. **Status Updates**
```json
{
  "type": "status",
  "status": "thinking"
}
```

4. **History Response**
```json
{
  "type": "history",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Hello",
      "timestamp": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid", 
      "role": "agent",
      "content": "Hi there!",
      "timestamp": "2024-01-01T00:00:01Z"
    }
  ]
}
```

## Integration Steps

### 1. Dependencies

Add to `requirements.txt`:
```
redis>=5.0.0
websockets>=12.0
```

### 2. Environment Variables

```bash
REDIS_URL=redis://localhost:6379
```

### 3. Orchestrator Integration

The orchestrator's `main.py` is automatically updated with:

```python
from agui_endpoints import create_agui_router
from adk_shared.agui_protocol import (
    AGUIProtocolServer,
    RedisAGUISessionManager,
    OrchestratorAGUIMessageHandler,
    OrchestratorAGUIStreamingHandler,
    WebSocketAGUIEventEmitter
)

# In lifespan function:
agui_router = create_agui_router(agui_server)
app.include_router(agui_router)
```

## Frontend Integration Examples

### JavaScript/TypeScript

```javascript
class AGUIClient {
  constructor(baseUrl, sessionId) {
    this.baseUrl = baseUrl;
    this.sessionId = sessionId;
    this.ws = null;
  }

  async createSession(userId = null) {
    const response = await fetch(`${this.baseUrl}/agui/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    });
    return response.json();
  }

  async sendMessage(content) {
    const response = await fetch(`${this.baseUrl}/agui/sessions/${this.sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    return response.json();
  }

  connectWebSocket() {
    this.ws = new WebSocket(`${this.baseUrl.replace('http', 'ws')}/agui/sessions/${this.sessionId}/ws`);
    
    this.ws.onopen = () => console.log('Connected to AG-UI protocol');
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    this.ws.onclose = () => console.log('Disconnected from AG-UI protocol');
  }

  sendWebSocketMessage(content) {
    if (this.ws) {
      this.ws.send(JSON.stringify({ type: 'message', content }));
    }
  }

  handleMessage(data) {
    switch (data.type) {
      case 'connected':
        console.log('Session connected:', data.session_id);
        break;
      case 'message':
        console.log('Agent response:', data.message.content);
        break;
      case 'status':
        console.log('Agent status:', data.status);
        break;
      case 'history':
        console.log('Conversation history:', data.messages);
        break;
    }
  }
}

// Usage
const client = new AGUIClient('http://localhost:8000', 'session-id');
await client.createSession('user-123');
client.connectWebSocket();
client.sendWebSocketMessage('Hello, I need help with data analysis');
```

### React Hook Example

```javascript
import { useState, useEffect, useCallback } from 'react';

export const useAGUI = (baseUrl, sessionId) => {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('disconnected');
  const [ws, setWs] = useState(null);

  const connect = useCallback(() => {
    const websocket = new WebSocket(`${baseUrl.replace('http', 'ws')}/agui/sessions/${sessionId}/ws`);
    
    websocket.onopen = () => setStatus('connected');
    websocket.onclose = () => setStatus('disconnected');
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'message') {
        setMessages(prev => [...prev, data.message]);
      } else if (data.type === 'status') {
        setStatus(data.status);
      }
    };
    
    setWs(websocket);
  }, [baseUrl, sessionId]);

  const sendMessage = useCallback((content) => {
    if (ws) {
      ws.send(JSON.stringify({ type: 'message', content }));
    }
  }, [ws]);

  const getHistory = useCallback(() => {
    if (ws) {
      ws.send(JSON.stringify({ type: 'get_history' }));
    }
  }, [ws]);

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  return {
    messages,
    status,
    connect,
    sendMessage,
    getHistory
  };
};
```

## Error Handling

### HTTP Errors

- **404**: Session not found
- **500**: Internal server error
- **503**: Service unavailable

### WebSocket Errors

```json
{
  "type": "error",
  "message": "Session not found"
}
```

## Security Considerations

1. **Session Validation**: All endpoints validate session existence
2. **User Authentication**: Optional user_id for session tracking
3. **Connection Cleanup**: Automatic cleanup of disconnected WebSockets
4. **Rate Limiting**: Consider implementing rate limiting for production

## Monitoring and Observability

The AG-UI protocol integrates with the existing observability stack:

- **Distributed Tracing**: All AG-UI operations are traced
- **Logging**: Comprehensive logging for debugging
- **Metrics**: Session and message metrics
- **Health Checks**: Built-in health monitoring

## Production Deployment

### Redis Configuration

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Environment Variables

```bash
REDIS_URL=redis://redis:6379
PORT=8000
```

### Health Checks

```bash
# Check orchestrator health
curl http://localhost:8000/health

# Check AG-UI session creation
curl -X POST http://localhost:8000/agui/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check Redis URL configuration
   - Ensure Redis is running and accessible

2. **WebSocket Connection Failed**
   - Verify session exists
   - Check firewall settings
   - Ensure WebSocket support in proxy

3. **Session Not Found**
   - Check session ID format
   - Verify session hasn't expired
   - Check Redis connectivity

### Debug Logging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

1. **Session TTL**: Sessions expire after 1 hour by default
2. **Connection Limits**: Monitor WebSocket connection count
3. **Redis Memory**: Monitor Redis memory usage
4. **Streaming**: Chunk size optimized for real-time delivery

## Future Enhancements

1. **Authentication**: JWT-based authentication
2. **Rate Limiting**: Per-user rate limiting
3. **Message Encryption**: End-to-end encryption
4. **Analytics**: Usage analytics and insights
5. **Multi-tenancy**: Tenant isolation
6. **Message Persistence**: Long-term message storage
