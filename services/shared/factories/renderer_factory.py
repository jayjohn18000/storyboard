"""Factory for creating renderer service implementations."""

from typing import Dict, Any, Optional
from ..interfaces.renderer import RendererInterface, RenderEngine, RenderError


class RendererFactory:
    """Factory for creating renderer service instances."""
    
    _implementations: Dict[RenderEngine, type] = {}
    
    @classmethod
    def _load_implementations(cls):
        """Load renderer implementations dynamically."""
        if not cls._implementations:
            try:
                from ..implementations.renderer.blender_local import BlenderLocalRenderer
                cls._implementations[RenderEngine.BLENDER_LOCAL] = BlenderLocalRenderer
            except ImportError:
                pass  # Implementation not available
    
    @classmethod
    def create_renderer(
        cls, 
        engine: RenderEngine, 
        config: Dict[str, Any]
    ) -> RendererInterface:
        """Create renderer service instance."""
        cls._load_implementations()
        
        if engine not in cls._implementations:
            raise RenderError(f"Unsupported render engine: {engine}")
        
        implementation_class = cls._implementations[engine]
        return implementation_class(config)
    
    @classmethod
    def create_from_env(cls, env_config: Dict[str, str]) -> RendererInterface:
        """Create renderer service from environment configuration."""
        engine_str = env_config.get("RENDER_ENGINE", "blender_local")
        
        try:
            engine = RenderEngine(engine_str)
        except ValueError:
            raise RenderError(f"Invalid render engine: {engine_str}")
        
        config = cls._build_config(engine, env_config)
        return cls.create_renderer(engine, config)
    
    @classmethod
    def _build_config(cls, engine: RenderEngine, env_config: Dict[str, str]) -> Dict[str, Any]:
        """Build configuration for render engine."""
        base_config = {
            "blender_version": env_config.get("BLENDER_VERSION", "4.0"),
            "deterministic": env_config.get("DETERMINISM_ENABLED", "true").lower() == "true",
            "seed": int(env_config.get("DETERMINISM_SEED", "42")),
            "timeout": int(env_config.get("RENDER_TIMEOUT", "3600")),
            "max_workers": int(env_config.get("RENDER_WORKERS", "4")),
        }
        
        if engine == RenderEngine.BLENDER_LOCAL:
            return {
                **base_config,
                "blender_path": env_config.get("BLENDER_PATH", "blender"),
                "temp_dir": env_config.get("RENDER_TEMP_DIR", "/tmp/blender-renders"),
                "memory_limit": int(env_config.get("BLENDER_MEMORY_LIMIT", "8192")),
            }
        
        elif engine == RenderEngine.BLENDER_DISTRIBUTED:
            return {
                **base_config,
                "worker_endpoints": env_config.get("BLENDER_WORKERS", "").split(","),
                "load_balancing": env_config.get("BLENDER_LOAD_BALANCING", "round_robin"),
                "job_timeout": int(env_config.get("BLENDER_JOB_TIMEOUT", "7200")),
                "retry_attempts": int(env_config.get("BLENDER_RETRY_ATTEMPTS", "3")),
            }
        
        elif engine == RenderEngine.BLENDER_GPU:
            return {
                **base_config,
                "gpu_device": env_config.get("BLENDER_GPU_DEVICE", "0"),
                "gpu_memory_fraction": float(env_config.get("BLENDER_GPU_MEMORY_FRACTION", "0.8")),
                "use_cuda": env_config.get("BLENDER_USE_CUDA", "true").lower() == "true",
                "use_optix": env_config.get("BLENDER_USE_OPTIX", "false").lower() == "true",
                "cycles_device": env_config.get("BLENDER_CYCLES_DEVICE", "CUDA"),
            }
        
        else:
            raise RenderError(f"Configuration not implemented for {engine}")
    
    @classmethod
    def register_implementation(
        cls, 
        engine: RenderEngine, 
        implementation_class: type
    ) -> None:
        """Register custom renderer implementation."""
        cls._implementations[engine] = implementation_class
