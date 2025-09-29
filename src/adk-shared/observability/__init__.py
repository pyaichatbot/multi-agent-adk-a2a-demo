"""
Observability utilities using OpenTelemetry
Provides tracing, metrics, and logging for the entire system
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from opentelemetry import trace, metrics
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import set_global_textmap


def setup_observability(service_name: str, environment: str = None):
    """Setup complete observability stack"""
    if not environment:
        environment = os.getenv("ENVIRONMENT", "development")
    
    # Setup tracing
    setup_tracing(service_name, environment)
    
    # Setup metrics
    setup_metrics(service_name, environment)
    
    # Setup logging
    setup_logging(service_name, environment)
    
    # Auto-instrument common libraries
    setup_auto_instrumentation()


def setup_tracing(service_name: str, environment: str):
    """Setup distributed tracing"""
    # Create tracer provider
    tracer_provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": environment
        })
    )
    trace.set_tracer_provider(tracer_provider)
    
    # Setup exporter based on environment
    if environment == "production":
        # Use Cloud Trace in production
        exporter = CloudTraceSpanExporter()
    else:
        # Use console exporter for development
        from opentelemetry.exporter.console import ConsoleSpanExporter
        exporter = ConsoleSpanExporter()
    
    # Add span processor
    span_processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(span_processor)


def setup_metrics(service_name: str, environment: str):
    """Setup metrics collection"""
    # Setup exporter
    if environment == "production":
        exporter = CloudMonitoringMetricsExporter()
    else:
        from opentelemetry.exporter.console import ConsoleMetricsExporter
        exporter = ConsoleMetricsExporter()
    
    # Create metric reader
    reader = PeriodicExportingMetricReader(
        exporter=exporter,
        export_interval_millis=60000  # Export every minute
    )
    
    # Create meter provider
    meter_provider = MeterProvider(
        metric_readers=[reader],
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": environment
        })
    )
    metrics.set_meter_provider(meter_provider)


def setup_logging(service_name: str, environment: str):
    """Setup structured logging"""
    log_level = logging.INFO if environment == "production" else logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add service name to all log records
    logger = logging.getLogger()
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service_name = service_name
        record.environment = environment
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    # Auto-instrument logging
    LoggingInstrumentor().instrument(set_logging_format=True)


def setup_auto_instrumentation():
    """Setup automatic instrumentation for common libraries"""
    # Instrument FastAPI
    FastAPIInstrumentor.instrument()
    
    # Instrument HTTP clients
    HTTPXClientInstrumentor().instrument()


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance"""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance"""
    return metrics.get_meter(name)


@contextmanager
def trace_tool_call(tool_name: str, transaction_id: str, parameters: Dict[str, Any]):
    """Context manager for tracing tool calls"""
    tracer = get_tracer("tool-calls")
    
    with tracer.start_as_current_span(f"tool_call_{tool_name}") as span:
        # Set attributes
        span.set_attribute("tool_name", tool_name)
        span.set_attribute("transaction_id", transaction_id)
        span.set_attribute("parameters", str(parameters))
        
        # Increment tool usage counter
        meter = get_meter("enterprise-agents")
        counter = meter.create_counter(
            name="tool_calls_total",
            description="Total number of tool calls"
        )
        counter.add(1, {"tool_name": tool_name})
        
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            
            # Increment error counter
            error_counter = meter.create_counter(
                name="tool_errors_total",
                description="Total number of tool errors"
            )
            error_counter.add(1, {"tool_name": tool_name, "error_type": type(e).__name__})
            raise


@contextmanager
def trace_agent_call(from_agent: str, to_agent: str, transaction_id: str):
    """Context manager for tracing agent-to-agent calls"""
    tracer = get_tracer("agent-calls")
    
    with tracer.start_as_current_span(f"agent_call_{from_agent}_to_{to_agent}") as span:
        # Set attributes
        span.set_attribute("from_agent", from_agent)
        span.set_attribute("to_agent", to_agent)
        span.set_attribute("transaction_id", transaction_id)
        
        # Increment agent call counter
        meter = get_meter("enterprise-agents")
        counter = meter.create_counter(
            name="agent_calls_total",
            description="Total number of agent calls"
        )
        counter.add(1, {"from_agent": from_agent, "to_agent": to_agent})
        
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            
            # Increment error counter
            error_counter = meter.create_counter(
                name="agent_call_errors_total",
                description="Total number of agent call errors"
            )
            error_counter.add(1, {
                "from_agent": from_agent, 
                "to_agent": to_agent,
                "error_type": type(e).__name__
            })
            raise
