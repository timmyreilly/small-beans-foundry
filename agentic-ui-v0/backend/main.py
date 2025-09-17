from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager for cleanup and telemetry initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Agentic UI v0 Backend with Single AutoGen Agent...")
    
    # Initialize telemetry
    try:
        from app.config.telemetry import telemetry_config
        telemetry_config.initialize(app)
        logger.info("Telemetry initialization completed")
    except Exception as e:
        logger.error(f"Telemetry initialization failed: {e}", exc_info=True)
    
    yield
    # Shutdown
    logger.info("Shutting down... cleaning up AutoGen resources")
    try:
        from app.services.agent import agent_service
        await agent_service.close()
    except Exception as e:
        logger.error(f"Error during agent service cleanup: {e}")

app = FastAPI(
    title="Agentic UI v0 Backend", 
    version="0.1.0",
    description="Simplified FastAPI backend with single AutoGen Azure AI Agent",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import chat

app.include_router(chat.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Agentic UI v0 Backend is running",
        "service": "Single AutoGen Azure AI Agent",
        "version": "0.1.0",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "/api/chat",
            "sessions": "/api/sessions/{session_id}/messages"
        }
    }

@app.get("/health")
async def health_check():
    """Simplified health check for the single agent service"""
    import time
    from datetime import datetime
    from app.config.azure import azure_config
    
    health_result = {
        "timestamp": datetime.now().isoformat(),
        "service": "Agentic UI v0 Backend",
        "version": "0.1.0",
        "overall_status": "unknown",
        "components": {}
    }
    
    try:
        # 1. Basic Service Health
        health_result["components"]["basic"] = {
            "status": "pass",
            "details": "Main FastAPI service is running"
        }
        
        # 2. Azure Configuration Check
        azure_configured = azure_config.is_configured()
        health_result["components"]["azure_config"] = {
            "status": "pass" if azure_configured else "warn",
            "configured": azure_configured,
            "endpoint": azure_config.azure_project_endpoint if azure_configured else "Not configured",
            "deployment": azure_config.get_deployment_name() if azure_configured else "Not configured",
            "details": "Azure AI Foundry configuration"
        }
        
        # 3. Telemetry Check
        try:
            from app.config.telemetry import telemetry_config
            telemetry_enabled = telemetry_config.is_telemetry_enabled()
            health_result["components"]["telemetry"] = {
                "status": "pass" if telemetry_enabled else "warn",
                "enabled": telemetry_enabled,
                "details": "Azure Application Insights telemetry"
            }
        except Exception as e:
            health_result["components"]["telemetry"] = {
                "status": "warn",
                "enabled": False,
                "details": f"Telemetry unavailable: {str(e)}"
            }
        
        # 4. Single Agent Service Check
        health_result["components"]["agent_service"] = {
            "status": "pass",
            "chat_endpoint": "/api/chat",
            "agent_type": "Single AutoGen Assistant",
            "details": "Single agent conversation service"
        }
        
        # Determine overall status
        component_statuses = [comp["status"] for comp in health_result["components"].values()]
        
        if all(status == "pass" for status in component_statuses):
            health_result["overall_status"] = "healthy"
        elif any(status == "fail" for status in component_statuses):
            health_result["overall_status"] = "unhealthy"
        else:
            health_result["overall_status"] = "degraded"
        
        return health_result
        
    except Exception as e:
        health_result["overall_status"] = "unhealthy"
        health_result["error"] = str(e)
        return health_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)