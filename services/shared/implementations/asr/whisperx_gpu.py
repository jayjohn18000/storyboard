"""WhisperX GPU ASR implementation."""

import asyncio
import time
import tempfile
import os
from typing import List, Dict, Any
import whisperx
import torch
import torchaudio

from ...interfaces.asr import ASRInterface, ASRResult, ASRConfig, ASRError, UnsupportedAudioFormatError, TranscriptionError


class WhisperXGPUASR(ASRInterface):
    """WhisperX GPU ASR implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize WhisperX GPU ASR."""
        self.device = "cuda"
        self.compute_type = config.get("compute_type", "float16")
        self.batch_size = config.get("batch_size", 32)
        self.language = config.get("language", "en")
        self.model_size = config.get("model_size", "base")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.diarization = config.get("diarization", False)
        self.speaker_count = config.get("speaker_count")
        self.gpu_memory_fraction = config.get("gpu_memory_fraction", 0.8)
        
        # Check GPU availability
        if not torch.cuda.is_available():
            raise ASRError("CUDA not available for GPU processing")
        
        # Set GPU memory fraction
        torch.cuda.set_per_process_memory_fraction(self.gpu_memory_fraction)
        
        # Initialize model
        asyncio.create_task(self._initialize_model())
    
    async def _initialize_model(self) -> None:
        """Initialize WhisperX GPU model."""
        try:
            # Load model
            self.model = whisperx.load_model(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                language=self.language
            )
            
            # Load alignment model if needed
            if self.language != "en":
                self.align_model, self.align_metadata = whisperx.load_align_model(
                    language_code=self.language,
                    device=self.device
                )
            else:
                self.align_model = None
                self.align_metadata = None
            
            # Load diarization model if needed
            if self.diarization:
                self.diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=os.getenv("HF_TOKEN"),
                    device=self.device
                )
            else:
                self.diarize_model = None
                
        except Exception as e:
            raise ASRError(f"Failed to initialize WhisperX GPU model: {e}")
    
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
                
                # Move to GPU
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
        try:
            start_time = time.time()
            
            # Load audio
            audio_tensor = await self._load_audio(audio_data)
            
            # Transcribe
            result = self.model.transcribe(
                audio_tensor.cpu().numpy(),
                batch_size=self.batch_size,
                language=config.language or self.language
            )
            
            # Align if needed
            if self.align_model and config.language != "en":
                result = whisperx.align(
                    result["segments"],
                    self.align_model,
                    self.align_metadata,
                    audio_tensor.cpu().numpy(),
                    self.device,
                    return_char_alignments=False
                )
            
            # Convert to ASRResult objects
            results = []
            for segment in result["segments"]:
                if segment.get("avg_logprob", 0) >= self.confidence_threshold:
                    results.append(ASRResult(
                        text=segment["text"].strip(),
                        confidence=segment.get("avg_logprob", 0),
                        start_time=segment["start"],
                        end_time=segment["end"],
                        language=config.language or self.language,
                        processing_time_ms=int((time.time() - start_time) * 1000),
                        engine_used="whisperx_gpu"
                    ))
            
            return results
            
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}")
    
    async def transcribe_with_diarization(
        self, 
        audio_data: bytes, 
        config: ASRConfig
    ) -> List[ASRResult]:
        """Transcribe audio with speaker diarization."""
        if not self.diarize_model:
            raise ASRError("Diarization not enabled for this instance")
        
        try:
            start_time = time.time()
            
            # Load audio
            audio_tensor = await self._load_audio(audio_data)
            
            # Transcribe first
            result = self.model.transcribe(
                audio_tensor.cpu().numpy(),
                batch_size=self.batch_size,
                language=config.language or self.language
            )
            
            # Perform diarization
            diarize_segments = self.diarize_model(
                audio_tensor.cpu().numpy(),
                min_speakers=config.speaker_count or 1,
                max_speakers=config.speaker_count or 10
            )
            
            # Assign speakers to segments
            speaker_segments = whisperx.assign_word_speakers(
                diarize_segments,
                result["segments"]
            )
            
            # Convert to ASRResult objects
            results = []
            for segment in speaker_segments:
                if segment.get("avg_logprob", 0) >= self.confidence_threshold:
                    results.append(ASRResult(
                        text=segment["text"].strip(),
                        confidence=segment.get("avg_logprob", 0),
                        start_time=segment["start"],
                        end_time=segment["end"],
                        speaker_id=segment.get("speaker"),
                        language=config.language or self.language,
                        processing_time_ms=int((time.time() - start_time) * 1000),
                        engine_used="whisperx_gpu"
                    ))
            
            return results
            
        except Exception as e:
            raise TranscriptionError(f"Diarization transcription failed: {e}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "th", "vi", "tr", "pl", "nl", "sv", "da", "no",
            "fi", "cs", "sk", "hu", "ro", "bg", "hr", "sl", "et", "lv",
            "lt", "el", "he", "fa", "ur", "bn", "ta", "te", "ml", "kn"
        ]
    
    async def get_available_models(self) -> List[str]:
        """Get list of available model sizes."""
        return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
