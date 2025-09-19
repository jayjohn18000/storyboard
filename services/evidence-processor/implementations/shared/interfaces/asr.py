"""ASR interface definitions."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ASRConfig:
    """ASR configuration."""
    language: str = "en"
    confidence_threshold: float = 0.7
    diarization: bool = False
    speaker_count: Optional[int] = None
    device: str = "cpu"
    compute_type: str = "int8"
    batch_size: int = 16


@dataclass
class ASRResult:
    """ASR result."""
    text: str
    confidence: float
    segments: List[Dict[str, Any]]
    speakers: List[Dict[str, Any]]
    language: str = "en"
    processing_time_ms: int = 0
    engine_used: str = "unknown"


class ASRError(Exception):
    """ASR processing error."""
    pass


class ASRInterface(ABC):
    """ASR interface."""
    
    @abstractmethod
    async def transcribe(self, audio_data: bytes, config: ASRConfig) -> ASRResult:
        """Transcribe audio data."""
        pass
    
    @abstractmethod
    async def transcribe_file(self, file_path: str, config: ASRConfig) -> ASRResult:
        """Transcribe audio file."""
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass
