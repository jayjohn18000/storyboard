"""PyAnnote diarizer ASR implementation."""

import asyncio
import time
import tempfile
import os
from typing import List, Dict, Any
import torch
import torchaudio
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding

from ...interfaces.asr import ASRInterface, ASRResult, ASRConfig, ASRError, UnsupportedAudioFormatError, TranscriptionError


class PyAnnoteDiarizerASR(ASRInterface):
    """PyAnnote diarizer ASR implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize PyAnnote diarizer ASR."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.language = config.get("language", "en")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.diarization_model = config.get("diarization_model", "pyannote/speaker-diarization")
        self.embedding_model = config.get("embedding_model", "speechbrain/spkrec-ecapa-voxceleb")
        self.clustering_method = config.get("clustering_method", "kmeans")
        self.min_speakers = config.get("min_speakers", 1)
        self.max_speakers = config.get("max_speakers", 10)
        
        # Initialize models
        asyncio.create_task(self._initialize_models())
    
    async def _initialize_models(self) -> None:
        """Initialize PyAnnote models."""
        try:
            # Load diarization pipeline
            self.diarization_pipeline = Pipeline.from_pretrained(
                self.diarization_model,
                use_auth_token=os.getenv("HF_TOKEN")
            ).to(self.device)
            
            # Load embedding model
            self.embedding_model = PretrainedSpeakerEmbedding(
                self.embedding_model,
                device=self.device
            )
            
        except Exception as e:
            raise ASRError(f"Failed to initialize PyAnnote models: {e}")
    
    async def _load_audio(self, audio_data: bytes) -> torch.Tensor:
        """Load audio data into tensor."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Load audio
                waveform, sample_rate = torchaudio.load(temp_file_path)
                
                # Convert to mono if stereo
                if waveform.shape[0] > 1:
                    waveform = torch.mean(waveform, dim=0, keepdim=True)
                
                # Resample to 16kHz if needed
                if sample_rate != 16000:
                    resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                    waveform = resampler(waveform)
                
                # Move to device
                waveform = waveform.to(self.device)
                
                return waveform.squeeze(0)  # Remove channel dimension
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise UnsupportedAudioFormatError(f"Failed to load audio: {e}")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio data to text."""
        # PyAnnote is primarily for diarization, not transcription
        # This would need to be combined with a transcription model
        raise ASRError("PyAnnote diarizer requires transcription model for text output")
    
    async def transcribe_with_diarization(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio with speaker diarization."""
        try:
            start_time = time.time()
            
            # Load audio
            audio_tensor = await self._load_audio(audio_data)
            
            # Perform diarization
            diarization = self.diarization_pipeline(
                audio_tensor.cpu().numpy(),
                min_speakers=config.speaker_count or self.min_speakers,
                max_speakers=config.speaker_count or self.max_speakers
            )
            
            # Convert to ASRResult objects
            results = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # For now, we only have speaker segments without transcription
                # In a real implementation, this would be combined with a transcription model
                results.append(ASRResult(
                    text="",  # Would need transcription model
                    confidence=1.0,  # Diarization confidence
                    start_time=turn.start,
                    end_time=turn.end,
                    speaker_id=speaker,
                    language=config.language or self.language,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    engine_used="pyannote_diarizer"
                ))
            
            return results
            
        except Exception as e:
            raise TranscriptionError(f"Diarization failed: {e}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        # PyAnnote diarization is language-agnostic
        return ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
    
    async def get_available_models(self) -> List[str]:
        """Get list of available model sizes."""
        return [
            "pyannote/speaker-diarization",
            "pyannote/speaker-diarization-3.1",
            "pyannote/speaker-diarization-3.0"
        ]
