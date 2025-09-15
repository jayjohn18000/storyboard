"""Timeline Compiler Service main application."""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn

from .otio.timeline_builder import TimelineBuilder
from .otio.clip_generator import ClipGenerator
from .otio.transition_handler import TransitionHandler
from .scene_graph.usd_builder import USDBuilder
from .scene_graph.spatial_solver import SpatialSolver
from .scene_graph.trajectory_generator import TrajectoryGenerator
from ..shared.utils.monitoring import MonitoringSetup, MetricsCollector


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize monitoring
monitoring = MonitoringSetup(
    service_name=os.getenv("OTEL_SERVICE_NAME", "timeline-compiler"),
    service_version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0")
)

# Initialize metrics collector
metrics = MetricsCollector("timeline-compiler")

# Global service instances
timeline_builder = None
clip_generator = None
transition_handler = None
usd_builder = None
spatial_solver = None
trajectory_generator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global timeline_builder, clip_generator, transition_handler
    global usd_builder, spatial_solver, trajectory_generator
    
    # Startup
    logger.info("Starting Timeline Compiler Service...")
    monitoring.initialize()
    
    # Initialize services
    try:
        # Initialize OTIO components
        timeline_builder = TimelineBuilder()
        clip_generator = ClipGenerator()
        transition_handler = TransitionHandler()
        logger.info("OTIO components initialized")
        
        # Initialize scene graph components
        usd_builder = USDBuilder()
        spatial_solver = SpatialSolver()
        trajectory_generator = TrajectoryGenerator()
        logger.info("Scene graph components initialized")
        
        logger.info("Timeline Compiler Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Timeline Compiler Service...")


# Create FastAPI application
app = FastAPI(
    title="Timeline Compiler Service",
    description="Service for compiling storyboards into timelines and scene graphs",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "service": "timeline-compiler",
        "time": datetime.utcnow().isoformat() + "Z",
        "otio_available": all([timeline_builder, clip_generator, transition_handler]),
        "usd_available": all([usd_builder, spatial_solver, trajectory_generator]),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Timeline Compiler Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/compile")
async def compile_timeline(request: dict):
    """Compile storyboard into timeline."""
    try:
        storyboard_data = request.get("storyboard_data")
        if not storyboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="storyboard_data is required"
            )
        
        # Compile timeline
        result = await timeline_builder.build_timeline(storyboard_data)
        
        # Record metrics
        metrics.record_timeline_compiled("timeline_compilation")
        
        return {
            "status": "compiled",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Timeline compilation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeline compilation failed: {str(e)}"
        )


@app.post("/generate-clips")
async def generate_clips(request: dict):
    """Generate clips from storyboard scenes."""
    try:
        storyboard_data = request.get("storyboard_data")
        if not storyboard_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="storyboard_data is required"
            )
        
        # Generate clips
        result = await clip_generator.generate_clips(storyboard_data)
        
        # Record metrics
        metrics.record_timeline_compiled("clip_generation")
        
        return {
            "status": "generated",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Clip generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clip generation failed: {str(e)}"
        )


@app.post("/handle-transitions")
async def handle_transitions(request: dict):
    """Handle transitions between scenes."""
    try:
        timeline_data = request.get("timeline_data")
        if not timeline_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline_data is required"
            )
        
        # Handle transitions
        result = await transition_handler.handle_transitions(timeline_data)
        
        # Record metrics
        metrics.record_timeline_compiled("transition_handling")
        
        return {
            "status": "processed",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Transition handling failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transition handling failed: {str(e)}"
        )


@app.post("/build-scene-graph")
async def build_scene_graph(request: dict):
    """Build USD scene graph from timeline."""
    try:
        timeline_data = request.get("timeline_data")
        if not timeline_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeline_data is required"
            )
        
        # Build scene graph
        result = await usd_builder.build_scene_graph(timeline_data)
        
        # Record metrics
        metrics.record_timeline_compiled("scene_graph_build")
        
        return {
            "status": "built",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Scene graph building failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scene graph building failed: {str(e)}"
        )


@app.post("/solve-spatial")
async def solve_spatial(request: dict):
    """Solve spatial relationships in scene graph."""
    try:
        scene_graph_data = request.get("scene_graph_data")
        if not scene_graph_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scene_graph_data is required"
            )
        
        # Solve spatial relationships
        result = await spatial_solver.solve_spatial(scene_graph_data)
        
        # Record metrics
        metrics.record_timeline_compiled("spatial_solving")
        
        return {
            "status": "solved",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Spatial solving failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Spatial solving failed: {str(e)}"
        )


@app.post("/generate-trajectory")
async def generate_trajectory(request: dict):
    """Generate camera trajectory for scene."""
    try:
        scene_data = request.get("scene_data")
        if not scene_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scene_data is required"
            )
        
        # Generate trajectory
        result = await trajectory_generator.generate_trajectory(scene_data)
        
        # Record metrics
        metrics.record_timeline_compiled("trajectory_generation")
        
        return {
            "status": "generated",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Trajectory generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trajectory generation failed: {str(e)}"
        )


@app.get("/formats")
async def get_supported_formats():
    """Get supported timeline formats."""
    return {
        "supported_formats": [
            {
                "name": "otio",
                "description": "OpenTimelineIO format",
                "extensions": [".otio", ".otioz"],
            },
            {
                "name": "usd",
                "description": "Universal Scene Description",
                "extensions": [".usd", ".usda", ".usdc"],
            },
            {
                "name": "json",
                "description": "JSON timeline format",
                "extensions": [".json"],
            },
        ],
        "supported_transitions": [
            "fade",
            "cut",
            "dissolve",
            "wipe",
            "slide",
            "zoom",
            "pan",
        ],
        "supported_clip_types": [
            "evidence",
            "transition",
            "text_overlay",
            "audio_narration",
        ]
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    metrics.record_error("http_exception", "timeline-compiler")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    metrics.record_error("unhandled_exception", "timeline-compiler")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url),
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8003")),
        workers=int(os.getenv("API_WORKERS", "1")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
