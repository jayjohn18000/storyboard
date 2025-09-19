"""OCR interface definitions."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OCRConfig:
    """OCR configuration."""
    language: str = "eng"
    confidence_threshold: float = 0.7
    preprocess: bool = True
    deskew: bool = True
    denoise: bool = True


@dataclass
class OCRResult:
    """OCR result."""
    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]]
    page_number: int = 1
    language: str = "eng"
    processing_time_ms: int = 0
    engine_used: str = "unknown"


class OCRError(Exception):
    """OCR processing error."""
    pass


class OCRInterface(ABC):
    """OCR interface."""
    
    @abstractmethod
    async def extract_text(self, image_data: bytes, config: OCRConfig) -> OCRResult:
        """Extract text from image data."""
        pass
    
    @abstractmethod
    async def extract_text_from_pdf(self, pdf_data: bytes, config: OCRConfig) -> List[OCRResult]:
        """Extract text from PDF document."""
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass
