"""
OpenTelemetry tracing configuration for the Task Management API.
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from app.config import settings


def setup_tracing():
    """
    Configure OpenTelemetry tracing for the application.
    """
    # Create resource with service information
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: settings.app_name,
        ResourceAttributes.SERVICE_VERSION: settings.app_version,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "production" if not settings.debug else "development",
    })
    
    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Configure OTLP exporter (for Jaeger)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"),
        insecure=True,
    )
    
    # Add batch span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Auto-instrument libraries
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    
    # SQLAlchemy instrumentation will be done after engine creation
    
    print(f"✅ Tracing configured - sending to: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://jaeger:4317')}")


def instrument_app(app):
    """
    Instrument the FastAPI application for tracing.
    
    Args:
        app: FastAPI application instance
    """
    FastAPIInstrumentor.instrument_app(
        app,
        server_request_hook=get_server_request_hook(),
        client_request_hook=get_client_request_hook(),
    )
    

def instrument_sqlalchemy(engine):
    """
    Instrument SQLAlchemy for tracing.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    SQLAlchemyInstrumentor().instrument(engine=engine)


def get_server_request_hook():
    """
    Custom server request hook to add additional context to spans.
    """
    def server_request_hook(span, scope):
        # Add custom attributes to the span
        if span and span.is_recording():
            # Add request information
            if "path" in scope:
                span.set_attribute("http.route", scope["path"])
            
            # Add user information if available
            if "user" in scope.get("state", {}):
                user = scope["state"]["user"]
                if hasattr(user, "id"):
                    span.set_attribute("user.id", str(user.id))
                if hasattr(user, "email"):
                    span.set_attribute("user.email", user.email)
    
    return server_request_hook


def get_client_request_hook():
    """
    Custom client request hook to add additional context to outbound spans.
    """
    def client_request_hook(span, scope):
        # Add custom attributes for outbound requests
        if span and span.is_recording():
            span.set_attribute("component", "http-client")
    
    return client_request_hook


def get_tracer(name: str):
    """
    Get a tracer instance.
    
    Args:
        name: Name of the tracer (usually __name__)
        
    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


# Custom decorators for tracing
def trace_function(operation_name: str = None):
    """
    Decorator to trace function calls.
    
    Args:
        operation_name: Optional name for the operation (defaults to function name)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Add function details to span
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Add success status
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    # Record exception in span
                    span.record_exception(e)
                    span.set_status(trace.Status(
                        trace.StatusCode.ERROR,
                        description=str(e)
                    ))
                    raise
        
        return wrapper
    return decorator