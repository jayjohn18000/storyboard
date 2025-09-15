"""WhisperX distributed ASR implementation."""

import asyncio
import time
import json
from typing import List, Dict, Any
from urllib.parse import urljoin

from ...interfaces.asr import ASRInterface, ASRResult, ASRConfig, ASRError, TranscriptionError
from ...http_client import get_http_client


class WhisperXDistributedASR(ASRInterface):
    """WhisperX distributed ASR implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize WhisperX distributed ASR."""
        self.worker_endpoints = config.get("worker_endpoints", [])
        self.timeout = config.get("timeout", 600)
        self.load_balancing = config.get("load_balancing", "round_robin")
        self.language = config.get("language", "en")
        self.model_size = config.get("model_size", "base")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.diarization = config.get("diarization", False)
        self.speaker_count = config.get("speaker_count")
        
        if not self.worker_endpoints:
            raise ASRError("No worker endpoints provided")
        
        # Current worker index for round-robin
        self.current_worker = 0
        
        # Get shared HTTP client
        self.client = get_http_client()
    
    def _get_next_worker(self) -> str:
        """Get next worker endpoint based on load balancing strategy."""
        if self.load_balancing == "round_robin":
            worker = self.worker_endpoints[self.current_worker]
            self.current_worker = (self.current_worker + 1) % len(self.worker_endpoints)
            return worker
        else:
            # Default to first worker
            return self.worker_endpoints[0]
    
    async def _call_worker(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call worker endpoint."""
        try:
            response = await self.client.post(
                urljoin(endpoint, "/transcribe"),
                json=data,
                timeout=self.timeout
            )
            return response
            
        except Exception as e:
            raise ASRError(f"Worker call failed: {e}")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio data to text."""
        try:
            start_time = time.time()
            
            # Prepare request data
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            request_data = {
                "audio_data": audio_b64,
                "language": config.language or self.language,
                "model_size": self.model_size,
                "confidence_threshold": self.confidence_threshold,
                "diarization": False
            }
            
            # Call worker
            worker_endpoint = self._get_next_worker()
            result = await self._call_worker(worker_endpoint, request_data)
            
            # Convert to ASRResult objects
            results = []
            for segment in result.get("segments", []):
                results.append(ASRResult(
                    text=segment.get("text", "").strip(),
                    confidence=segment.get("confidence", 0),
                    start_time=segment.get("start_time", 0),
                    end_time=segment.get("end_time", 0),
                    language=config.language or self.language,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    engine_used="whisperx_distributed"
                ))
            
            return results
            
        except Exception as e:
            raise TranscriptionError(f"Distributed transcription failed: {e}")
    
    async def transcribe_with_diarization(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio with speaker diarization."""
        try:
            start_time = time.time()
            
            # Prepare request data
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            request_data = {
                "audio_data": audio_b64,
                "language": config.language or self.language,
                "model_size": self.model_size,
                "confidence_threshold": self.confidence_threshold,
                "diarization": True,
                "speaker_count": config.speaker_count or self.speaker_count
            }
            
            # Call worker
            worker_endpoint = self._get_next_worker()
            result = await self._call_worker(worker_endpoint, request_data)
            
            # Convert to ASRResult objects
            results = []
            for segment in result.get("segments", []):
                results.append(ASRResult(
                    text=segment.get("text", "").strip(),
                    confidence=segment.get("confidence", 0),
                    start_time=segment.get("start_time", 0),
                    end_time=segment.get("end_time", 0),
                    speaker_id=segment.get("speaker_id"),
                    language=config.language or self.language,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    engine_used="whisperx_distributed"
                ))
            
            return results
            
        except Exception as e:
            raise TranscriptionError(f"Distributed diarization transcription failed: {e}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        try:
            # Try to get from first worker
            worker_endpoint = self.worker_endpoints[0]
            response = await self.client.get(
                urljoin(worker_endpoint, "/languages"),
                timeout=30
            )
            return response.get("languages", [])
            
        except Exception:
            # Fallback to default list
            return [
                "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
                "ar", "hi", "th", "vi", "tr", "pl", "nl", "sv", "da", "no",
                "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sl", "et", "lv",
                "lt", "el", "he", "fa", "ur", "bn", "ta", "te", "ml", "kn"
            ]
    
    async def get_available_models(self) -> List[str]:
        """Get list of available model sizes."""
        try:
            # Try to get from first worker
            worker_endpoint = self.worker_endpoints[0]
            response = await self.client.get(
                urljoin(worker_endpoint, "/models"),
                timeout=30
            )
            return response.get("models", [])
            
        except Exception:
            # Fallback to default list
            return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Shared HTTP client doesn't need to be closed here
        pass
