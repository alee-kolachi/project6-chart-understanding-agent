"""
Configuration management for the Chart Understanding Agent.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for managing application settings."""
    
    # API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    EXAMPLES_DIR: Path = BASE_DIR / "examples" / "sample_charts"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Image Processing
    MAX_IMAGE_SIZE: int = 2048  # Maximum dimension in pixels
    SUPPORTED_FORMATS: tuple = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
    
    # Model Parameters
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.1  # Low temperature for consistency
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Validation Thresholds
    MIN_CONFIDENCE: float = 0.7
    MAX_EXTRACTION_RETRIES: int = 3
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        if not cls.GROQ_API_KEY:
            logger.error("GROQ_API_KEY not found in environment variables")
            return False
        
        # Create necessary directories
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        
        return True
    
    @classmethod
    def get_model_config(cls) -> dict:
        """Get model configuration dictionary."""
        return {
            "model": cls.GROQ_MODEL,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
        }


# Configure logging
logger.add(
    Config.LOGS_DIR / "chart_agent_{time}.log",
    rotation="10 MB",
    retention="7 days",
    level=Config.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)