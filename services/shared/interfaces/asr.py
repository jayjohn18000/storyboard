"""Abstract ASR interface for speech-to-text conversion."""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ASREngine(Enum):
    """Supported ASR engines."""
    WHISPERX_LOCAL = "whisperx_local"
    WHISPERX_GPU = "whisperx_gpu"
    WHISPERX_DISTRIBUTED = "whisperx_distributed"
    PYANNOTE_DIARIZER = "pyannote_diarizer"


@dataclass
class ASRResult:
    """Result of ASR processing."""
    text: str
    confidence: float
    start_time: float
    end_time: float
    speaker_id: Optional[str] = None
    language: str = "en"
    processing_time_ms: int = 0
    engine_used: str = ""


@dataclass
class ASRConfig:
    """Configuration for ASR processing."""
    language: str = "en"
    model_size: str = "base"
    diarization: bool = False
    speaker_count: Optional[int] = None
    confidence_threshold: float = 0.7
    engine: ASREngine = ASREngine.WHISPERX_LOCAL


class ASRService(Protocol):
    """Protocol for ASR service implementations."""
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio data to text."""
        ...
    
    async def transcribe_with_diarization(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio with speaker diarization."""
        ...
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        ...
    
    async def get_available_models(self) -> List[str]:
        """Get list of available model sizes."""
        ...


class ASRInterface(ABC):
    """Abstract base class for ASR implementations."""
    
    @abstractmethod
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio data to text."""
        pass
    
    @abstractmethod
    async def transcribe_with_diarization(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio with speaker diarization."""
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available model sizes."""
        pass


class ASRError(Exception):
    """Base exception for ASR operations."""
    pass


class UnsupportedAudioFormatError(ASRError):
    """Raised when audio format is not supported."""
    pass


class ModelNotFoundError(ASRError):
    """Raised when requested model is not available."""
    pass


class TranscriptionError(ASRError):
    """Raised when transcription fails."""
    pass


# Import concrete implementations
from ..implementations.asr.whisperx_local import WhisperXLocalASR
from ..implementations.asr.whisperx_gpu import WhisperXGPUASR
from ..implementations.asr.whisperx_distributed import WhisperXDistributedASR
from ..implementations.asr.pyannote_diarizer import PyAnnoteDiarizerASR
