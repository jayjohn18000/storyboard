"""Abstract OCR interface for text extraction from documents."""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class OCREngine(Enum):
    """Supported OCR engines."""
    TESSERACT_LOCAL = "tesseract_local"
    TESSERACT_DISTRIBUTED = "tesseract_distributed"
    OCRMYPDF = "ocrmypdf"
    PADDLEOCR = "paddleocr"
    TEXTRACT = "textract"


@dataclass
class OCRResult:
    """Result of OCR processing."""
    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]]
    page_number: int
    language: str
    processing_time_ms: int
    engine_used: str


@dataclass
class OCRConfig:
    """Configuration for OCR processing."""
    language: str = "eng"
    confidence_threshold: float = 0.7
    preprocess: bool = True
    deskew: bool = True
    denoise: bool = True
    engine: OCREngine = OCREngine.TESSERACT_LOCAL


class OCRService(Protocol):
    """Protocol for OCR service implementations."""
    
    async def extract_text(
        self, 
        image_data: bytes, 
        config: OCRConfig
    ) -> OCRResult:
        """Extract text from image data."""
        ...
    
    async def extract_text_from_pdf(
        self, 
        pdf_data: bytes, 
        config: OCRConfig
    ) -> List[OCRResult]:
        """Extract text from PDF document."""
        ...
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        ...


class OCRInterface(ABC):
    """Abstract base class for OCR implementations."""
    
    @abstractmethod
    async def extract_text(
        self, 
        image_data: bytes, 
        config: OCRConfig
    ) -> OCRResult:
        """Extract text from image data."""
        pass
    
    @abstractmethod
    async def extract_text_from_pdf(
        self, 
        pdf_data: bytes, 
        config: OCRConfig
    ) -> List[OCRResult]:
        """Extract text from PDF document."""
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass


class OCRError(Exception):
    """Base exception for OCR operations."""
    pass


class UnsupportedFormatError(OCRError):
    """Raised when image format is not supported."""
    pass


class LanguageNotSupportedError(OCRError):
    """Raised when requested language is not supported."""
    pass


class TranscriptionError(OCRError):
    """Raised when transcription fails."""
    pass


# Concrete implementations are imported where needed to avoid circular imports
