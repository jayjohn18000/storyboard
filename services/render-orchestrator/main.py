"""Render Orchestrator Service main application."""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .implementations.blender.local_renderer import BlenderLocalRenderer
from .implementations.blender.determinism import DeterminismManager, DeterminismTestSuite
from ..shared.interfaces.renderer import RenderConfig, RenderProfile, RenderEngine, SceneData
from ..shared.utils.monitoring import MonitoringSetup, MetricsCollector


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize monitoring
monitoring = MonitoringSetup(
    service_name=os.getenv("OTEL_SERVICE_NAME", "render-orchestrator"),
    service_version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0")
)

# Initialize metrics collector
metrics = MetricsCollector("render-orchestrator")

# Global service instances
renderer = None
determinism_manager = None
determinism_test_suite = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global renderer, determinism_manager, determinism_test_suite
    
    # Startup
    logger.info("Starting Render Orchestrator Service...")
    monitoring.initialize()
    
    # Initialize services
    try:
        # Initialize Blender renderer
        renderer_config = {
            "blender_path": os.getenv("BLENDER_PATH", "blender"),
            "blender_version": os.getenv("BLENDER_VERSION", "4.0"),
            "temp_dir": os.getenv("RENDER_TEMP_DIR", "/tmp/blender-renders"),
            "memory_limit": int(os.getenv("BLENDER_MEMORY_LIMIT", "8192")),
            "timeout": int(os.getenv("RENDER_TIMEOUT", "3600")),
            "deterministic": os.getenv("DETERMINISM_ENABLED", "true").lower() == "true",
            "seed": int(os.getenv("DETERMINISM_SEED", "42")),
        }
        
        renderer = BlenderLocalRenderer(renderer_config)
        logger.info("Blender renderer initialized")
        
        # Initialize determinism manager
        determinism_manager = DeterminismManager(seed=renderer_config["seed"])
        determinism_test_suite = DeterminismTestSuite(determinism_manager)
        logger.info("Determinism manager initialized")
        
        logger.info("Render Orchestrator Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Render Orchestrator Service...")


# Create FastAPI application
app = FastAPI(
    title="Render Orchestrator Service",
    description="Service for deterministic 3D rendering with Blender",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok", 
        "service": "render-orchestrator", 
        "time": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Render Orchestrator Service", "version": "0.1.0"}


@app.post("/render/scene")
async def render_scene(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Render a 3D scene to video."""
    try:
        # Parse request data
        data = await request.json()
        
        # Extract scene data
        scene_data = SceneData(
            usd_data=bytes(data.get("usd_data", "")),
            timeline_data=bytes(data.get("timeline_data", "")),
            camera_path=data.get("camera_path", []),
            lighting_config=data.get("lighting_config", {}),
            materials=data.get("materials", [])
        )
        
        # Extract render config
        config_data = data.get("config", {})
        config = RenderConfig(
            width=config_data.get("width", 1920),
            height=config_data.get("height", 1080),
            fps=config_data.get("fps", 30),
            duration_seconds=config_data.get("duration_seconds", 10.0),
            profile=RenderProfile(config_data.get("profile", "neutral")),
            engine=RenderEngine(config_data.get("engine", "blender_local")),
            deterministic=config_data.get("deterministic", True),
            seed=config_data.get("seed"),
            output_format=config_data.get("output_format", "mp4"),
            quality=config_data.get("quality", "high")
        )
        
        # Initialize determinism if enabled
        if config.deterministic:
            determinism_manager.initialize_seeds(scene_data.usd_data, config_data)
        
        # Render scene
        result = await renderer.render_scene(scene_data, config)
        
        # Log metrics
        metrics.increment_counter("renders_completed")
        metrics.record_histogram("render_duration", result.render_time_seconds)
        metrics.record_histogram("render_file_size", result.file_size_bytes)
        
        return {
            "success": True,
            "render_id": result.render_id,
            "output_path": result.output_path,
            "duration_seconds": result.duration_seconds,
            "file_size_bytes": result.file_size_bytes,
            "render_time_seconds": result.render_time_seconds,
            "frames_rendered": result.frames_rendered,
            "profile_used": result.profile_used,
            "checksum": result.checksum
        }
        
    except Exception as e:
        logger.error(f"Render scene failed: {e}")
        metrics.increment_counter("renders_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Render failed: {str(e)}"
        )


@app.post("/render/frame")
async def render_frame(request: Request):
    """Render a single frame as image."""
    try:
        # Parse request data
        data = await request.json()
        
        # Extract scene data
        scene_data = SceneData(
            usd_data=bytes(data.get("usd_data", "")),
            timeline_data=bytes(data.get("timeline_data", "")),
            camera_path=data.get("camera_path", []),
            lighting_config=data.get("lighting_config", {}),
            materials=data.get("materials", [])
        )
        
        # Extract render config
        config_data = data.get("config", {})
        config = RenderConfig(
            width=config_data.get("width", 1920),
            height=config_data.get("height", 1080),
            fps=config_data.get("fps", 30),
            duration_seconds=config_data.get("duration_seconds", 10.0),
            profile=RenderProfile(config_data.get("profile", "neutral")),
            engine=RenderEngine(config_data.get("engine", "blender_local")),
            deterministic=config_data.get("deterministic", True),
            seed=config_data.get("seed"),
            output_format=config_data.get("output_format", "png"),
            quality=config_data.get("quality", "high")
        )
        
        frame_number = data.get("frame_number", 1)
        
        # Render frame
        frame_data = await renderer.render_frame(scene_data, frame_number, config)
        
        # Log metrics
        metrics.increment_counter("frames_rendered")
        
        return JSONResponse(
            content={
                "success": True,
                "frame_number": frame_number,
                "image_data": frame_data.hex(),  # Convert to hex string for JSON
                "size_bytes": len(frame_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Render frame failed: {e}")
        metrics.increment_counter("frames_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Frame render failed: {str(e)}"
        )


@app.get("/render/status/{render_id}")
async def get_render_status(render_id: str):
    """Get status of render job."""
    try:
        status = await renderer.get_render_status(render_id)
        
        return {
            "render_id": render_id,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Get render status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get render status: {str(e)}"
        )


@app.get("/render/download/{render_id}")
async def download_render(render_id: str):
    """Download rendered video file."""
    try:
        # Find the output file
        output_files = list(renderer.temp_dir.glob(f"{render_id}.*"))
        
        if not output_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Render output not found: {render_id}"
            )
        
        output_file = output_files[0]
        
        return FileResponse(
            path=str(output_file),
            filename=output_file.name,
            media_type="video/mp4" if output_file.suffix == ".mp4" else "application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"Download render failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


@app.post("/determinism/test")
async def run_determinism_test(request: Request):
    """Run determinism validation test."""
    try:
        # Parse request data
        data = await request.json()
        
        scene_data = bytes(data.get("scene_data", ""))
        config = data.get("config", {})
        num_iterations = data.get("iterations", 3)
        
        # Run determinism test
        test_results = await determinism_test_suite.run_determinism_tests(
            scene_data, config, num_iterations
        )
        
        return {
            "success": True,
            "test_results": test_results
        }
        
    except Exception as e:
        logger.error(f"Determinism test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Determinism test failed: {str(e)}"
        )


@app.get("/profiles")
async def get_render_profiles():
    """Get available render profiles."""
    return {
        "profiles": [
            {
                "name": "neutral",
                "description": "Court-appropriate render settings with neutral lighting and materials",
                "allowed_modes": ["demonstrative", "sandbox"]
            },
            {
                "name": "cinematic",
                "description": "Enhanced render settings with dramatic lighting and effects",
                "allowed_modes": ["sandbox"]
            }
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "services.render-orchestrator.main:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    )
