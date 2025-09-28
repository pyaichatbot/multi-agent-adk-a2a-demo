"""
Dynamic Agent Registry for service discovery and orchestration
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import redis.asyncio as redis
from pydantic import BaseModel, Field

from adk_shared.observability import get_tracer, get_meter


class AgentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    """Represents a specific capability of an agent"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    complexity_score: float = 1.0  # For load balancing
    estimated_duration: float = 1.0  # In seconds


@dataclass
class AgentMetadata:
    """Agent metadata for service discovery"""
    agent_id: str
    name: str
    version: str
    description: str
    capabilities: List[AgentCapability]
    endpoint_url: str
    health_check_url: str
    
    # Resource information
    max_concurrent_requests: int = 10
    current_load: int = 0
    cpu_cores: float = 1.0
    memory_gb: float = 1.0
    
    # Service mesh information
    service_name: str = ""
    namespace: str = "default"
    cluster: str = "default"
    
    # Registration information
    registered_at: datetime = None
    last_heartbeat: datetime = None
    status: AgentStatus = AgentStatus.OFFLINE
    
    # Tags for filtering and routing
    tags: Set[str] = None
    priority: int = 1  # Higher is better
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = set()
        if self.registered_at is None:
            self.registered_at = datetime.now()


class AgentRegistryInterface:
    """Interface for agent registry implementations"""
    
    async def register_agent(self, metadata: AgentMetadata) -> bool:
        """Register a new agent"""
        raise NotImplementedError
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        raise NotImplementedError
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, load: int = None) -> bool:
        """Update agent status and load"""
        raise NotImplementedError
    
    async def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID"""
        raise NotImplementedError
    
    async def list_agents(self, 
                         status: AgentStatus = None, 
                         tags: Set[str] = None,
                         capability_name: str = None) -> List[AgentMetadata]:
        """List agents with optional filtering"""
        raise NotImplementedError
    
    async def find_best_agent(self, 
                            required_capability: str,
                            context: Dict[str, Any] = None) -> Optional[AgentMetadata]:
        """Find the best agent for a specific capability"""
        raise NotImplementedError


class RedisAgentRegistry(AgentRegistryInterface):
    """Redis-based agent registry with pub/sub for real-time updates"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self.tracer = get_tracer("agent-registry")
        self.meter = get_meter("agent-registry")
        
        # Metrics
        self.registration_counter = self.meter.create_counter(
            name="agent_registrations_total",
            description="Total number of agent registrations"
        )
        self.lookup_counter = self.meter.create_counter(
            name="agent_lookups_total", 
            description="Total number of agent lookups"
        )
        
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe("agent_events")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe("agent_events")
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
    
    def _agent_key(self, agent_id: str) -> str:
        """Generate Redis key for agent metadata"""
        return f"agent:{agent_id}"
    
    def _capability_key(self, capability_name: str) -> str:
        """Generate Redis key for capability index"""
        return f"capability:{capability_name}"
    
    async def register_agent(self, metadata: AgentMetadata) -> bool:
        """Register agent in Redis with indexing"""
        with self.tracer.start_as_current_span("register_agent") as span:
            span.set_attribute("agent_id", metadata.agent_id)
            span.set_attribute("agent_name", metadata.name)
            
            try:
                await self.connect()
                
                # Store agent metadata
                agent_key = self._agent_key(metadata.agent_id)
                agent_data = asdict(metadata)
                
                # Handle datetime serialization
                agent_data['registered_at'] = metadata.registered_at.isoformat()
                agent_data['last_heartbeat'] = datetime.now().isoformat()
                agent_data['tags'] = list(metadata.tags)
                agent_data['capabilities'] = [asdict(cap) for cap in metadata.capabilities]
                
                await self.redis_client.hset(agent_key, mapping={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in agent_data.items()
                })
                
                # Index by capabilities
                for capability in metadata.capabilities:
                    cap_key = self._capability_key(capability.name)
                    await self.redis_client.sadd(cap_key, metadata.agent_id)
                
                # Index by tags
                for tag in metadata.tags:
                    await self.redis_client.sadd(f"tag:{tag}", metadata.agent_id)
                
                # Set TTL for automatic cleanup
                await self.redis_client.expire(agent_key, 300)  # 5 minutes
                
                # Publish registration event
                await self.redis_client.publish("agent_events", json.dumps({
                    "type": "registration",
                    "agent_id": metadata.agent_id,
                    "agent_name": metadata.name,
                    "timestamp": datetime.now().isoformat()
                }))
                
                self.registration_counter.add(1, {"agent_name": metadata.name})
                logging.info(f"Agent registered: {metadata.agent_id}")
                
                return True
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Failed to register agent {metadata.agent_id}: {str(e)}")
                return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent and clean up indices"""
        with self.tracer.start_as_current_span("unregister_agent") as span:
            span.set_attribute("agent_id", agent_id)
            
            try:
                await self.connect()
                
                # Get agent metadata first
                agent = await self.get_agent(agent_id)
                if not agent:
                    return False
                
                # Remove from capability indices
                for capability in agent.capabilities:
                    cap_key = self._capability_key(capability.name)
                    await self.redis_client.srem(cap_key, agent_id)
                
                # Remove from tag indices
                for tag in agent.tags:
                    await self.redis_client.srem(f"tag:{tag}", agent_id)
                
                # Remove agent metadata
                agent_key = self._agent_key(agent_id)
                await self.redis_client.delete(agent_key)
                
                # Publish unregistration event
                await self.redis_client.publish("agent_events", json.dumps({
                    "type": "unregistration",
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat()
                }))
                
                logging.info(f"Agent unregistered: {agent_id}")
                return True
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Failed to unregister agent {agent_id}: {str(e)}")
                return False
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, load: int = None) -> bool:
        """Update agent status and load"""
        try:
            await self.connect()
            
            agent_key = self._agent_key(agent_id)
            updates = {
                "status": status.value,
                "last_heartbeat": datetime.now().isoformat()
            }
            
            if load is not None:
                updates["current_load"] = str(load)
            
            await self.redis_client.hset(agent_key, mapping=updates)
            
            # Reset TTL
            await self.redis_client.expire(agent_key, 300)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to update agent status {agent_id}: {str(e)}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata"""
        with self.tracer.start_as_current_span("get_agent") as span:
            span.set_attribute("agent_id", agent_id)
            
            try:
                await self.connect()
                
                agent_key = self._agent_key(agent_id)
                agent_data = await self.redis_client.hgetall(agent_key)
                
                if not agent_data:
                    return None
                
                # Deserialize data
                data = {}
                for k, v in agent_data.items():
                    k = k.decode() if isinstance(k, bytes) else k
                    v = v.decode() if isinstance(v, bytes) else v
                    
                    if k in ['capabilities', 'tags']:
                        data[k] = json.loads(v)
                    elif k in ['registered_at', 'last_heartbeat']:
                        data[k] = datetime.fromisoformat(v)
                    elif k in ['max_concurrent_requests', 'current_load', 'priority']:
                        data[k] = int(v)
                    elif k in ['cpu_cores', 'memory_gb', 'complexity_score', 'estimated_duration']:
                        data[k] = float(v)
                    else:
                        data[k] = v
                
                # Convert capabilities back to objects
                capabilities = [
                    AgentCapability(**cap) for cap in data.get('capabilities', [])
                ]
                data['capabilities'] = capabilities
                data['tags'] = set(data.get('tags', []))
                data['status'] = AgentStatus(data.get('status', 'offline'))
                
                self.lookup_counter.add(1, {"agent_id": agent_id})
                
                return AgentMetadata(**data)
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Failed to get agent {agent_id}: {str(e)}")
                return None
    
    async def list_agents(self, 
                         status: AgentStatus = None,
                         tags: Set[str] = None,
                         capability_name: str = None) -> List[AgentMetadata]:
        """List agents with filtering"""
        with self.tracer.start_as_current_span("list_agents") as span:
            try:
                await self.connect()
                
                agent_ids = set()
                
                # Filter by capability
                if capability_name:
                    cap_key = self._capability_key(capability_name)
                    cap_agents = await self.redis_client.smembers(cap_key)
                    agent_ids.update(aid.decode() for aid in cap_agents)
                
                # Filter by tags
                if tags:
                    for tag in tags:
                        tag_agents = await self.redis_client.smembers(f"tag:{tag}")
                        if not agent_ids:  # First filter
                            agent_ids.update(aid.decode() for aid in tag_agents)
                        else:  # Intersection with previous filters
                            agent_ids &= {aid.decode() for aid in tag_agents}
                
                # If no filters, get all agents
                if not agent_ids and not capability_name and not tags:
                    keys = await self.redis_client.keys("agent:*")
                    agent_ids = {key.decode().split(":", 1)[1] for key in keys}
                
                # Get agent metadata
                agents = []
                for agent_id in agent_ids:
                    agent = await self.get_agent(agent_id)
                    if agent and (not status or agent.status == status):
                        agents.append(agent)
                
                span.set_attribute("agents_found", len(agents))
                return agents
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Failed to list agents: {str(e)}")
                return []
    
    async def find_best_agent(self, 
                            required_capability: str,
                            context: Dict[str, Any] = None) -> Optional[AgentMetadata]:
        """Find the best agent using load balancing and capability matching"""
        with self.tracer.start_as_current_span("find_best_agent") as span:
            span.set_attribute("required_capability", required_capability)
            
            try:
                # Get all agents with the required capability
                candidates = await self.list_agents(
                    status=AgentStatus.HEALTHY,
                    capability_name=required_capability
                )
                
                if not candidates:
                    # Try degraded agents if no healthy ones
                    candidates = await self.list_agents(
                        status=AgentStatus.DEGRADED,
                        capability_name=required_capability
                    )
                
                if not candidates:
                    return None
                
                # Score agents based on multiple factors
                best_agent = None
                best_score = -1
                
                for agent in candidates:
                    # Calculate load factor (lower is better)
                    load_factor = agent.current_load / agent.max_concurrent_requests
                    
                    # Calculate capability match score
                    capability_score = 0
                    for cap in agent.capabilities:
                        if cap.name == required_capability:
                            capability_score = 1.0 / cap.complexity_score
                            break
                    
                    # Calculate overall score
                    score = (
                        capability_score * 0.4 +           # 40% capability match
                        (1 - load_factor) * 0.3 +          # 30% load balancing
                        (agent.priority / 10) * 0.2 +      # 20% priority
                        (1 / max(agent.current_load + 1, 1)) * 0.1  # 10% current load
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_agent = agent
                
                span.set_attribute("selected_agent", best_agent.agent_id if best_agent else "none")
                span.set_attribute("selection_score", best_score)
                
                return best_agent
                
            except Exception as e:
                span.record_exception(e)
                logging.error(f"Failed to find best agent for {required_capability}: {str(e)}")
                return None
