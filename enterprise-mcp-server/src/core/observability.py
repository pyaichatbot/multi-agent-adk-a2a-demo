"""
Simple Observability Module
Clean, maintainable observability following SOLID principles
"""

import logging
import time
from typing import Any, Dict, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from src.config.settings import settings


class SimpleObservability:
    """Simple, clean observability with single flag control"""
    
    def __init__(self):
        self.enabled = settings.enable_telemetry
        self.logger = self._setup_logging()
        
        # Simple metrics storage
        self.metrics = {}
        self.request_count = 0
        self.error_count = 0
    
    def _setup_logging(self) -> logging.Logger:
        """Setup simple logging"""
        logger = logging.getLogger("enterprise-mcp-server")
        logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log(self, level: str, message: str, **kwargs):
        """Simple structured logging"""
        log_data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if level == "error":
            self.logger.error(f"{message} | {kwargs}")
            self.error_count += 1
        elif level == "warning":
            self.logger.warning(f"{message} | {kwargs}")
        elif level == "info":
            self.logger.info(f"{message} | {kwargs}")
        else:
            self.logger.debug(f"{message} | {kwargs}")
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record metric if telemetry enabled"""
        if not self.enabled:
            return
        
        self.metrics[name] = {
            "value": value,
            "labels": labels or {},
            "timestamp": time.time()
        }
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request"""
        self.request_count += 1
        
        if self.enabled:
            self.record_metric(
                "http_requests_total",
                self.request_count,
                {"method": method, "endpoint": endpoint, "status": str(status_code)}
            )
            self.record_metric(
                "http_request_duration_seconds",
                duration,
                {"method": method, "endpoint": endpoint}
            )
    
    def record_tool_execution(self, tool_name: str, status: str):
        """Record tool execution"""
        if self.enabled:
            self.record_metric(
                "tool_executions_total",
                1,
                {"tool": tool_name, "status": status}
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get simple health status"""
        return {
            "status": "healthy",
            "service": "enterprise-mcp-server",
            "version": "1.0.0",
            "telemetry_enabled": self.enabled,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics if telemetry enabled"""
        if not self.enabled:
            return {"message": "Telemetry disabled"}
        
        return {
            "metrics": self.metrics,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @asynccontextmanager
    async def trace_operation(self, operation: str, **metadata):
        """Simple operation tracing"""
        start_time = time.time()
        # Remove operation from metadata to avoid duplicate parameter
        operation_metadata = {k: v for k, v in metadata.items() if k != 'operation'}
        self.log("info", f"Starting operation: {operation}", **operation_metadata)
        
        try:
            yield
            duration = time.time() - start_time
            self.log("info", f"Operation completed: {operation}", 
                    duration=duration, **operation_metadata)
            
            if self.enabled:
                self.record_metric(
                    "operation_duration_seconds",
                    duration,
                    {"operation": operation}
                )
        except Exception as e:
            duration = time.time() - start_time
            self.log("error", f"Operation failed: {operation}", 
                    error=str(e), duration=duration, **metadata)
            raise
    
    def record_authentication(self, status: str, method: str):
        """Record authentication attempt"""
        if self.enabled:
            self.record_metric(
                "authentication_attempts_total",
                1,
                {"status": status, "method": method}
            )
    
    def log_structured(self, level: str, message: str, **kwargs):
        """Structured logging with additional context"""
        self.log(level, message, **kwargs)
    
    def start_metrics_server(self):
        """Start metrics server if telemetry enabled"""
        if self.enabled:
            self.log("info", "Metrics server started")


# Global observability instance
observability = SimpleObservability()
