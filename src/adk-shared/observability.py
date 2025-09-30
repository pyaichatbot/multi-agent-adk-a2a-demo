"""
Enterprise-ready observability module using OpenTelemetry
Works in Docker without external cloud dependencies
Provides distributed tracing, metrics, and structured logging
"""
import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import set_global_textmap
try:
    from opentelemetry.propagator.b3 import B3MultiFormat
except ImportError:
    B3MultiFormat = None

try:
    from opentelemetry.propagator.jaeger import JaegerPropagator
except ImportError:
    JaegerPropagator = None


def setup_observability(service_name: str, environment: str = None):
    """Setup enterprise observability stack"""
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
    
    logging.info(f"Enterprise observability setup for {service_name} in {environment} mode")


def setup_tracing(service_name: str, environment: str):
    """Setup distributed tracing with proper exporters"""
    # Create tracer provider
    tracer_provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": environment,
            "service.instance.id": os.getenv("HOSTNAME", "unknown")
        })
    )
    trace.set_tracer_provider(tracer_provider)
    
    # Setup exporter based on environment
    if environment == "production":
        # In production, try OTLP exporter first (for OpenTelemetry Collector)
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
        except ImportError:
            # Fallback to console exporter
            exporter = ConsoleSpanExporter()
    else:
        # Development: Use console exporter for immediate visibility
        exporter = ConsoleSpanExporter()
    
    # Add span processor
    span_processor = BatchSpanProcessor(exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Setup propagation (only if B3MultiFormat is available)
    if B3MultiFormat is not None:
        set_global_textmap(B3MultiFormat())
    else:
        # Use default propagation if B3 is not available
        try:
            from opentelemetry.propagator.tracecontext import TraceContextTextMapPropagator
            from opentelemetry.propagator.baggage import BaggageTextMapPropagator
            from opentelemetry.propagator.composite import CompositeHTTPPropagator
            
            propagator = CompositeHTTPPropagator([
                TraceContextTextMapPropagator(),
                BaggageTextMapPropagator()
            ])
            set_global_textmap(propagator)
        except ImportError:
            # If no propagators are available, skip propagation setup
            pass


def setup_metrics(service_name: str, environment: str):
    """Setup metrics collection with proper exporters"""
    # Setup exporter
    if environment == "production":
        # In production, try OTLP exporter first
        try:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            exporter = OTLPMetricExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
        except ImportError:
            # Fallback to console exporter
            exporter = ConsoleMetricExporter()
    else:
        # Development: Use console exporter
        exporter = ConsoleMetricExporter()
    
    # Create metric reader
    reader = PeriodicExportingMetricReader(
        exporter=exporter,
        export_interval_millis=30000  # Export every 30 seconds
    )
    
    # Create meter provider
    meter_provider = MeterProvider(
        metric_readers=[reader],
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": environment,
            "service.instance.id": os.getenv("HOSTNAME", "unknown")
        })
    )
    metrics.set_meter_provider(meter_provider)


def setup_logging(service_name: str, environment: str):
    """Setup structured logging with correlation IDs"""
    log_level = logging.INFO if environment == "production" else logging.DEBUG
    
    # Create structured formatter
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "service": service_name,
                "environment": environment,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Add correlation ID if available
            if hasattr(record, 'trace_id'):
                log_entry["trace_id"] = record.trace_id
            if hasattr(record, 'span_id'):
                log_entry["span_id"] = record.span_id
            
            # Add any extra fields
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'getMessage', 'exc_info', 
                              'exc_text', 'stack_info']:
                    log_entry[key] = value
            
            return json.dumps(log_entry)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler with structured formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # Auto-instrument logging
    LoggingInstrumentor().instrument(set_logging_format=True)


def setup_auto_instrumentation():
    """Setup automatic instrumentation for common libraries"""
    # Instrument FastAPI
    FastAPIInstrumentor().instrument()
    
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


def trace_agent_call_simple(agent, target, transaction_id):
    """Simple agent call tracing for compatibility"""
    tracer = get_tracer("agent-calls")
    with tracer.start_as_current_span(f"agent_call_{agent.__class__.__name__}_to_{target}") as span:
        span.set_attribute("agent", agent.__class__.__name__)
        span.set_attribute("target", target)
        span.set_attribute("transaction_id", transaction_id)
        
        # Log the call
        logger = logging.getLogger(agent.__class__.__name__)
        logger.info(f"Agent call: {agent.__class__.__name__} -> {target} (txn: {transaction_id})")
