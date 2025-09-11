import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AzureConfig:
    def __init__(self):
        self.azure_project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT", "")
        self.azure_api_key = os.getenv("AZURE_FOUNDRY_API_KEY", "")
        self.model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")
        
        logger.info("Azure AutoGen Configuration:")
        logger.info(f"  Project Endpoint: {'SET' if self.azure_project_endpoint else 'NOT SET'}")
        logger.info(f"  API Key: {'SET' if self.azure_api_key else 'NOT SET'}")
        logger.info(f"  Model Deployment: {self.model_deployment_name}")
        
        if not self.is_configured():
            logger.warning("Azure configuration is incomplete. Please check environment variables.")
    
    def is_configured(self) -> bool:
        """Check if minimum required configuration is present"""
        return bool(
            self.azure_project_endpoint and 
            self.azure_api_key and
            self.model_deployment_name
        )
    
    def get_project_endpoint(self) -> str:
        """Get the Azure AI Foundry project endpoint"""
        if not self.azure_project_endpoint:
            logger.error("AZURE_PROJECT_ENDPOINT environment variable is not set")
            raise ValueError("AZURE_PROJECT_ENDPOINT environment variable is required")
        return self.azure_project_endpoint
    
    def get_api_key(self) -> str:
        """Get the Azure API key"""
        if not self.azure_api_key:
            logger.error("AZURE_FOUNDRY_API_KEY environment variable is not set")
            raise ValueError("AZURE_FOUNDRY_API_KEY environment variable is required")
        return self.azure_api_key
    
    def get_deployment_name(self) -> str:
        """Get the model deployment name"""
        if not self.model_deployment_name:
            logger.warning("MODEL_DEPLOYMENT_NAME not set, using default: gpt-4o")
        return self.model_deployment_name

azure_config = AzureConfig()