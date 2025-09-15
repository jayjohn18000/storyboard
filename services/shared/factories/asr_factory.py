"""Factory for creating ASR service implementations."""

from typing import Dict, Any, Optional
from ..interfaces.asr import ASRInterface, ASREngine, ASRError
from ..interfaces.asr import (
    WhisperXLocalASR, 
    WhisperXGPUASR, 
    WhisperXDistributedASR, 
    PyAnnoteDiarizerASR
)


class ASRFactory:
    """Factory for creating ASR service instances."""
    
    _implementations: Dict[ASREngine, type] = {
        ASREngine.WHISPERX_LOCAL: WhisperXLocalASR,
        ASREngine.WHISPERX_GPU: WhisperXGPUASR,
        ASREngine.WHISPERX_DISTRIBUTED: WhisperXDistributedASR,
        ASREngine.PYANNOTE_DIARIZER: PyAnnoteDiarizerASR,
    }
    
    @classmethod
    def create_asr(
        cls, 
        engine: ASREngine, 
        config: Dict[str, Any]
    ) -> ASRInterface:
        """Create ASR service instance."""
        if engine not in cls._implementations:
            raise ASRError(f"Unsupported ASR engine: {engine}")
        
        implementation_class = cls._implementations[engine]
        return implementation_class(config)
    
    @classmethod
    def create_from_env(cls, env_config: Dict[str, str]) -> ASRInterface:
        """Create ASR service from environment configuration."""
        engine_str = env_config.get("ASR_ENGINE", "whisperx_local")
        
        try:
            engine = ASREngine(engine_str)
        except ValueError:
            raise ASRError(f"Invalid ASR engine: {engine_str}")
        
        config = cls._build_config(engine, env_config)
        return cls.create_asr(engine, config)
    
    @classmethod
    def _build_config(cls, engine: ASREngine, env_config: Dict[str, str]) -> Dict[str, Any]:
        """Build configuration for ASR engine."""
        base_config = {
            "language": env_config.get("ASR_LANGUAGE", "en"),
            "model_size": env_config.get("WHISPER_MODEL", "base"),
            "confidence_threshold": float(env_config.get("ASR_CONFIDENCE_THRESHOLD", "0.7")),
            "diarization": env_config.get("ASR_DIARIZATION", "false").lower() == "true",
            "speaker_count": int(env_config.get("ASR_SPEAKER_COUNT", "0")) or None,
        }
        
        if engine == ASREngine.WHISPERX_LOCAL:
            return {
                **base_config,
                "device": env_config.get("WHISPERX_DEVICE", "cpu"),
                "compute_type": env_config.get("WHISPERX_COMPUTE_TYPE", "int8"),
                "batch_size": int(env_config.get("WHISPERX_BATCH_SIZE", "16")),
            }
        
        elif engine == ASREngine.WHISPERX_GPU:
            return {
                **base_config,
                "device": "cuda",
                "compute_type": env_config.get("WHISPERX_COMPUTE_TYPE", "float16"),
                "batch_size": int(env_config.get("WHISPERX_BATCH_SIZE", "32")),
                "gpu_memory_fraction": float(env_config.get("WHISPERX_GPU_MEMORY_FRACTION", "0.8")),
            }
        
        elif engine == ASREngine.WHISPERX_DISTRIBUTED:
            return {
                **base_config,
                "worker_endpoints": env_config.get("WHISPERX_WORKERS", "").split(","),
                "timeout": int(env_config.get("WHISPERX_TIMEOUT", "600")),
                "load_balancing": env_config.get("WHISPERX_LOAD_BALANCING", "round_robin"),
            }
        
        elif engine == ASREngine.PYANNOTE_DIARIZER:
            return {
                **base_config,
                "diarization_model": env_config.get("PYANNOTE_MODEL", "pyannote/speaker-diarization"),
                "embedding_model": env_config.get("PYANNOTE_EMBEDDING_MODEL", "speechbrain/spkrec-ecapa-voxceleb"),
                "clustering_method": env_config.get("PYANNOTE_CLUSTERING", "kmeans"),
                "min_speakers": int(env_config.get("PYANNOTE_MIN_SPEAKERS", "1")),
                "max_speakers": int(env_config.get("PYANNOTE_MAX_SPEAKERS", "10")),
            }
        
        else:
            raise ASRError(f"Configuration not implemented for {engine}")
    
    @classmethod
    def register_implementation(
        cls, 
        engine: ASREngine, 
        implementation_class: type
    ) -> None:
        """Register custom ASR implementation."""
        cls._implementations[engine] = implementation_class
