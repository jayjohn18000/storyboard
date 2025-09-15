"""Local WhisperX ASR implementation."""

import tempfile
import os
import time
from typing import List, Dict, Any
import whisperx
import torch
from ..shared.interfaces.asr import ASRInterface, ASRConfig, ASRResult, ASRError


class WhisperXLocalASR(ASRInterface):
    """Local WhisperX ASR implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = config.get("device", "cpu")
        self.compute_type = config.get("compute_type", "int8")
        self.batch_size = config.get("batch_size", 16)
        self.language = config.get("language", "en")
        self.model_size = config.get("model_size", "base")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.diarization = config.get("diarization", False)
        self.speaker_count = config.get("speaker_count")
        
        # Initialize WhisperX model
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize WhisperX model."""
        try:
            # Load WhisperX model
            self.model = whisperx.load_model(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                language=self.language
            )
            
            # Load alignment model if needed
            self.align_model = None
            self.align_metadata = None
            
            # Load diarization model if needed
            self.diarize_model = None
            if self.diarization:
                self.diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=None,  # Would need HuggingFace token
                    device=self.device
                )
            
        except Exception as e:
            raise ASRError(f"Failed to initialize WhisperX model: {str(e)}")
    
    async def transcribe_audio(self, audio_data: bytes, config: ASRConfig) -> List[ASRResult]:
        """Transcribe audio data to text."""
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
            
            try:
                # Transcribe audio
                result = await self._run_whisperx(temp_audio_path, config)
                
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
        except Exception as e:
            raise ASRError(f"ASR transcription failed: {str(e)}")
    
    async def transcribe_with_diarization(self, audio_data: bytes, config: ASRConfig) -> List[ASRResult]:
        """Transcribe audio with speaker diarization."""
        try:
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
            
            try:
                # Transcribe with diarization
                result = await self._run_whisperx_with_diarization(temp_audio_path, config)
                
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
        except Exception as e:
            raise ASRError(f"ASR transcription with diarization failed: {str(e)}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        # WhisperX supports many languages
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "th", "vi", "tr", "pl", "nl", "sv", "da", "no",
            "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sr", "sl", "et",
            "lv", "lt", "uk", "be", "mk", "sq", "mt", "is", "ga", "cy",
            "eu", "ca", "gl", "af", "sw", "zu", "xh", "st", "tn", "ss",
            "ve", "ts", "nr", "nso", "so", "om", "ti", "am", "ha", "yo",
            "ig", "pcm", "ak", "tw", "ee", "lg", "ln", "kg", "lu", "sg",
            "wo", "bm", "ff", "dy", "sn", "ny", "zu", "xh", "st", "tn",
            "ss", "ve", "ts", "nr", "nso", "so", "om", "ti", "am", "ha",
            "yo", "ig", "pcm", "ak", "tw", "ee", "lg", "ln", "kg", "lu",
            "sg", "wo", "bm", "ff", "dy", "sn", "ny"
        ]
    
    async def get_available_models(self) -> List[str]:
        """Get list of available model sizes."""
        return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    
    async def _run_whisperx(self, audio_path: str, config: ASRConfig) -> List[ASRResult]:
        """Run WhisperX transcription on audio."""
        try:
            start_time = time.time()
            
            # Transcribe audio
            result = self.model.transcribe(
                audio_path,
                batch_size=self.batch_size,
                language=config.language
            )
            
            # Align transcription if needed
            if self.align_model is None:
                self.align_model, self.align_metadata = whisperx.load_align_model(
                    language_code=config.language,
                    device=self.device
                )
            
            # Align segments
            segments = whisperx.align(
                result["segments"],
                self.align_model,
                self.align_metadata,
                audio_path,
                self.device
            )
            
            # Convert to ASRResult objects
            results = []
            for segment in segments:
                result_obj = ASRResult(
                    text=segment["text"],
                    confidence=segment.get("avg_logprob", 0.7),
                    start_time=segment["start"],
                    end_time=segment["end"],
                    language=config.language,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    engine_used="whisperx_local"
                )
                results.append(result_obj)
            
            return results
            
        except Exception as e:
            raise ASRError(f"WhisperX transcription failed: {str(e)}")
    
    async def _run_whisperx_with_diarization(self, audio_path: str, config: ASRConfig) -> List[ASRResult]:
        """Run WhisperX transcription with speaker diarization."""
        try:
            start_time = time.time()
            
            # Transcribe audio
            result = self.model.transcribe(
                audio_path,
                batch_size=self.batch_size,
                language=config.language
            )
            
            # Align transcription if needed
            if self.align_model is None:
                self.align_model, self.align_metadata = whisperx.load_align_model(
                    language_code=config.language,
                    device=self.device
                )
            
            # Align segments
            segments = whisperx.align(
                result["segments"],
                self.align_model,
                self.align_metadata,
                audio_path,
                self.device
            )
            
            # Perform diarization
            if self.diarize_model is not None:
                diarize_segments = self.diarize_model(
                    audio_path,
                    min_speakers=config.speaker_count or 1,
                    max_speakers=config.speaker_count or 10
                )
                
                # Assign speakers to segments
                segments = whisperx.assign_word_speakers(
                    diarize_segments,
                    segments
                )
            
            # Convert to ASRResult objects
            results = []
            for segment in segments:
                result_obj = ASRResult(
                    text=segment["text"],
                    confidence=segment.get("avg_logprob", 0.7),
                    start_time=segment["start"],
                    end_time=segment["end"],
                    speaker_id=segment.get("speaker"),
                    language=config.language,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    engine_used="whisperx_local"
                )
                results.append(result_obj)
            
            return results
            
        except Exception as e:
            raise ASRError(f"WhisperX transcription with diarization failed: {str(e)}")
