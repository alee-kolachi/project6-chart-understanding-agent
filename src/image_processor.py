"""
Image preprocessing and enhancement for better chart analysis.
"""

import base64
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image
from loguru import logger

from src.config import Config


class ImageProcessor:
    """Handles image preprocessing and enhancement operations."""
    
    def __init__(self, max_size: int = Config.MAX_IMAGE_SIZE):
        """
        Initialize the ImageProcessor.
        
        Args:
            max_size: Maximum dimension for resized images
        """
        self.max_size = max_size
        logger.info(f"ImageProcessor initialized with max_size={max_size}")
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load an image from file path.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Numpy array of the image or None if loading fails
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Image file not found: {image_path}")
                return None
            
            if path.suffix.lower() not in Config.SUPPORTED_FORMATS:
                logger.error(f"Unsupported image format: {path.suffix}")
                return None
            
            # Load image using OpenCV
            image = cv2.imread(str(path))
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            logger.info(f"Successfully loaded image: {image_path} with shape {image.shape}")
            return image
            
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {str(e)}")
            return None
    
    def resize_image(self, image: np.ndarray, max_size: Optional[int] = None) -> np.ndarray:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            image: Input image as numpy array
            max_size: Maximum dimension (uses instance default if None)
            
        Returns:
            Resized image
        """
        if max_size is None:
            max_size = self.max_size
        
        height, width = image.shape[:2]
        
        # Check if resizing is needed
        if max(height, width) <= max_size:
            return image
        
        # Calculate new dimensions
        if height > width:
            new_height = max_size
            new_width = int(width * (max_size / height))
        else:
            new_width = max_size
            new_height = int(height * (max_size / width))
        
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        return resized
    
    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image for better OCR and analysis.
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
            
            # Slight sharpening
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]]) / 9
            enhanced = cv2.filter2D(enhanced, -1, kernel)
            
            logger.debug("Image enhancement applied")
            return enhanced
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {str(e)}, returning original")
            return image
    
    def encode_image_base64(self, image: np.ndarray) -> str:
        """
        Encode image to base64 string for API transmission.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Base64 encoded string
        """
        try:
            # Convert to PIL Image
            pil_image = Image.fromarray(image)
            
            # Convert to bytes
            from io import BytesIO
            buffer = BytesIO()
            pil_image.save(buffer, format="PNG")
            buffer.seek(0)
            
            # Encode to base64
            encoded = base64.b64encode(buffer.read()).decode('utf-8')
            logger.debug(f"Image encoded to base64 (length: {len(encoded)})")
            return encoded
            
        except Exception as e:
            logger.error(f"Failed to encode image: {str(e)}")
            raise
    
    def process_image(self, image_path: str, enhance: bool = True) -> Optional[str]:
        """
        Complete image processing pipeline.
        
        Args:
            image_path: Path to the image file
            enhance: Whether to apply enhancement
            
        Returns:
            Base64 encoded image string or None if processing fails
        """
        try:
            # Load image
            image = self.load_image(image_path)
            if image is None:
                return None
            
            # Resize
            image = self.resize_image(image)
            
            # Enhance
            if enhance:
                image = self.enhance_image(image)
            
            # Encode
            encoded = self.encode_image_base64(image)
            
            logger.info(f"Successfully processed image: {image_path}")
            return encoded
            
        except Exception as e:
            logger.error(f"Image processing pipeline failed: {str(e)}")
            return None
    
    def get_image_dimensions(self, image_path: str) -> Optional[Tuple[int, int]]:
        """
        Get image dimensions without full loading.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (width, height) or None
        """
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.error(f"Failed to get image dimensions: {str(e)}")
            return None