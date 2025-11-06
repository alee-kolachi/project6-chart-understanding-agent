"""
Core chart analysis using Groq Vision API.
"""

import json
from typing import Dict, Optional, Any
from groq import Groq
from loguru import logger

from src.config import Config
from src.prompts import PromptTemplates
from src.image_processor import ImageProcessor


class ChartAnalyzer:
    """Main class for analyzing charts using Groq Vision API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ChartAnalyzer.
        
        Args:
            api_key: Groq API key (uses Config default if None)
        """
        self.api_key = api_key or Config.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not provided")
        
        self.client = Groq(api_key=self.api_key)
        self.image_processor = ImageProcessor()
        self.model_config = Config.get_model_config()
        logger.info(f"ChartAnalyzer initialized with model: {self.model_config['model']}")
    
    def _call_vision_api(self, image_base64: str, prompt: str) -> Optional[str]:
        """
        Make a call to Groq Vision API.
        
        Args:
            image_base64: Base64 encoded image
            prompt: Text prompt for analysis
            
        Returns:
            API response text or None if call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_config["model"],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.model_config["max_tokens"],
                temperature=self.model_config["temperature"]
            )
            
            content = response.choices[0].message.content
            logger.debug(f"API response received (length: {len(content)})")
            return content
            
        except Exception as e:
            logger.error(f"Vision API call failed: {str(e)}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Parse JSON response from API, handling markdown code blocks.
        
        Args:
            response: Raw API response
            
        Returns:
            Parsed JSON dict or None
        """
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            parsed = json.loads(response)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}\nResponse: {response[:200]}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {str(e)}")
            return None
    
    def detect_chart_type(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect the type of chart in the image.
        
        Args:
            image_path: Path to chart image
            
        Returns:
            Dictionary with chart_type, confidence, and reasoning
        """
        logger.info(f"Detecting chart type for: {image_path}")
        
        # Process image
        image_base64 = self.image_processor.process_image(image_path)
        if not image_base64:
            logger.error("Failed to process image")
            return None
        
        # Call API
        response = self._call_vision_api(
            image_base64,
            PromptTemplates.CHART_TYPE_DETECTION
        )
        
        if not response:
            return None
        
        # Parse response
        result = self._parse_json_response(response)
        if result:
            logger.info(f"Detected chart type: {result.get('chart_type')} "
                       f"(confidence: {result.get('confidence')})")
        
        return result
    
    def extract_data(self, image_path: str, chart_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from chart.
        
        Args:
            image_path: Path to chart image
            chart_type: Type of chart (auto-detected if None)
            
        Returns:
            Extracted data as dictionary
        """
        logger.info(f"Extracting data from: {image_path}")
        
        # Detect chart type if not provided
        if not chart_type:
            detection = self.detect_chart_type(image_path)
            if not detection:
                logger.error("Failed to detect chart type")
                return None
            chart_type = detection.get("chart_type")
        
        logger.info(f"Using chart type: {chart_type}")
        
        # Process image
        image_base64 = self.image_processor.process_image(image_path)
        if not image_base64:
            return None
        
        # Get appropriate prompt
        prompt = PromptTemplates.get_extraction_prompt(chart_type)
        
        # Call API with retry logic
        for attempt in range(Config.MAX_EXTRACTION_RETRIES):
            logger.debug(f"Extraction attempt {attempt + 1}/{Config.MAX_EXTRACTION_RETRIES}")
            
            response = self._call_vision_api(image_base64, prompt)
            if not response:
                continue
            
            result = self._parse_json_response(response)
            if result:
                result["chart_type"] = chart_type
                logger.info("Successfully extracted data")
                return result
        
        logger.error(f"Failed to extract data after {Config.MAX_EXTRACTION_RETRIES} attempts")
        return None
    
    def answer_question(self, image_path: str, question: str, 
                       context: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Answer a specific question about the chart.
        
        Args:
            image_path: Path to chart image
            question: Question to answer
            context: Optional context from previous extraction
            
        Returns:
            Answer dictionary with answer, evidence, and confidence
        """
        logger.info(f"Answering question: {question}")
        
        # Process image
        image_base64 = self.image_processor.process_image(image_path)
        if not image_base64:
            return None
        
        # Prepare context string
        context_str = json.dumps(context, indent=2) if context else "No prior context available"
        
        # Format prompt
        prompt = PromptTemplates.format_question_prompt(context_str, question)
        
        # Call API
        response = self._call_vision_api(image_base64, prompt)
        if not response:
            return None
        
        result = self._parse_json_response(response)
        if result:
            logger.info(f"Question answered (confidence: {result.get('confidence')})")
        
        return result
    
    def analyze_chart(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Complete chart analysis pipeline.
        
        Args:
            image_path: Path to chart image
            
        Returns:
            Complete analysis including type detection and data extraction
        """
        logger.info(f"Starting complete analysis for: {image_path}")
        
        # Detect chart type
        detection = self.detect_chart_type(image_path)
        if not detection:
            return None
        
        # Extract data
        extraction = self.extract_data(image_path, detection.get("chart_type"))
        if not extraction:
            return None
        
        # Combine results
        result = {
            "image_path": image_path,
            "detection": detection,
            "extraction": extraction,
            "timestamp": self._get_timestamp()
        }
        
        logger.info("Complete analysis finished successfully")
        return result
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp as ISO format string."""
        from datetime import datetime
        return datetime.now().isoformat()