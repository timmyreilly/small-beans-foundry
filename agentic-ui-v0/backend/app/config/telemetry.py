import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import trace, metrics
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
    TELEMETRY_AVAILABLE = True
    logger.info("Telemetry packages available")
except ImportError as e:
    logger.warning(f"Telemetry packages not available: {e}")
    TELEMETRY_AVAILABLE = False
    
    # Create no-op implementations
    class NoOpTracer:
        def start_span(self, name, **kwargs):
            return NoOpSpan()
    
    class NoOpSpan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_attribute(self, key, value):
            pass
        def record_exception(self, exception):
            pass
        def set_status(self, status):
            pass
    
    class NoOpMeter:
        def create_counter(self, name, **kwargs):
            return NoOpCounter()
        def create_histogram(self, name, **kwargs):
            return NoOpHistogram()
    
    class NoOpCounter:
        def add(self, amount, attributes=None):
            pass
    
    class NoOpHistogram:
        def record(self, amount, attributes=None):
            pass

class TelemetryConfig:
    def __init__(self):
        self.connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        self.is_enabled = bool(self.connection_string) and TELEMETRY_AVAILABLE
        self._initialized = False
        
        if self.connection_string and TELEMETRY_AVAILABLE:
            logger.info("Telemetry configuration loaded with Application Insights")
        elif not self.connection_string:
            logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not found. Telemetry disabled.")
        elif not TELEMETRY_AVAILABLE:
            logger.warning("Telemetry packages not available. Telemetry disabled.")
        
    def initialize(self, app=None):
        """Initialize OpenTelemetry with Azure Monitor"""
        if not self.is_enabled or not TELEMETRY_AVAILABLE:
            logger.warning("Telemetry not available or not configured. Skipping initialization.")
            return
            
        if self._initialized:
            logger.debug("Telemetry already initialized")
            return
            
        try:
            logger.info("Initializing Azure Monitor OpenTelemetry...")
            
            # Configure Azure Monitor
            configure_azure_monitor(
                connection_string=self.connection_string,
                disable_offline_storage=False,
            )
            
            # Instrument FastAPI if app provided
            if app:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI instrumentation enabled")
            
            # Instrument HTTP clients
            HTTPXClientInstrumentor().instrument()
            RequestsInstrumentor().instrument()
            
            # Instrument OpenAI client (for Azure OpenAI)
            try:
                OpenAIInstrumentor().instrument()
                logger.info("OpenAI instrumentation enabled")
            except Exception as e:
                logger.warning(f"OpenAI instrumentation failed (may not affect Azure AI): {e}")
            
            self._initialized = True
            logger.info("Azure Monitor OpenTelemetry initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}", exc_info=True)
    
    def get_tracer(self, name: str):
        """Get a tracer instance"""
        if not self.is_enabled or not TELEMETRY_AVAILABLE:
            return NoOpTracer()
        return trace.get_tracer(name)
    
    def get_meter(self, name: str):
        """Get a meter instance"""
        if not self.is_enabled or not TELEMETRY_AVAILABLE:
            return NoOpMeter()
        return metrics.get_meter(name)
    
    def is_telemetry_enabled(self) -> bool:
        """Check if telemetry is enabled and initialized"""
        return self.is_enabled and self._initialized and TELEMETRY_AVAILABLE

# Global telemetry configuration instance
telemetry_config = TelemetryConfig()
