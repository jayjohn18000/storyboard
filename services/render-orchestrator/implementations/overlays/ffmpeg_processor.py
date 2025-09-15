"""FFmpeg-based video post-processing."""

import asyncio
import subprocess
import tempfile
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class OverlayConfig:
    """Configuration for video overlays."""
    text: str
    start_time: float
    duration: float
    x: int = 50
    y: int = 50
    font_size: int = 24
    font_color: str = "white"
    background_color: Optional[str] = None
    font_file: Optional[str] = None


@dataclass
class WatermarkConfig:
    """Configuration for watermarks."""
    mode: str  # "SANDBOX" or "DEMONSTRATIVE"
    position: str = "bottom-right"  # "top-left", "top-right", "bottom-left", "bottom-right"
    opacity: float = 0.7
    font_size: int = 20


class FFmpegProcessor:
    """FFmpeg-based video post-processing processor."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize FFmpeg processor."""
        self.ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
        self.temp_dir = Path(config.get("temp_dir", "/tmp/ffmpeg-processing"))
        self.timeout = config.get("timeout", 1800)  # 30 minutes
        
        # Create temp directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify FFmpeg installation
        asyncio.create_task(self._verify_ffmpeg_installation())
    
    async def _verify_ffmpeg_installation(self) -> None:
        """Verify FFmpeg installation."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg not found at {self.ffmpeg_path}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg command timeout")
        except FileNotFoundError:
            raise RuntimeError(f"FFmpeg not found at {self.ffmpeg_path}")
    
    async def add_text_overlays(
        self, 
        input_video: Path, 
        overlays: List[OverlayConfig],
        output_video: Path
    ) -> Path:
        """Add text overlays to video using FFmpeg."""
        try:
            # Build FFmpeg command with multiple drawtext filters
            filters = []
            for i, overlay in enumerate(overlays):
                filter_str = self._build_drawtext_filter(overlay, i)
                filters.append(filter_str)
            
            # Combine all filters
            filter_complex = ";".join(filters)
            
            cmd = [
                self.ffmpeg_path,
                "-i", str(input_video),
                "-vf", filter_complex,
                "-c:a", "copy",  # Copy audio without re-encoding
                "-y",  # Overwrite output file
                str(output_video)
            ]
            
            # Execute FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            return output_video
            
        except Exception as e:
            raise RuntimeError(f"Text overlay processing failed: {str(e)}")
    
    async def add_watermark(
        self, 
        input_video: Path, 
        watermark_config: WatermarkConfig,
        output_video: Path
    ) -> Path:
        """Add watermark to video."""
        try:
            # Build watermark filter
            watermark_text = f"[{watermark_config.mode}]"
            position = self._get_watermark_position(watermark_config.position)
            
            filter_str = (
                f"drawtext=text='{watermark_text}':"
                f"x={position['x']}:y={position['y']}:"
                f"fontsize={watermark_config.font_size}:"
                f"fontcolor=white@0.7:"
                f"box=1:boxcolor=black@0.5:"
                f"boxborderw=5"
            )
            
            cmd = [
                self.ffmpeg_path,
                "-i", str(input_video),
                "-vf", filter_str,
                "-c:a", "copy",
                "-y",
                str(output_video)
            ]
            
            # Execute FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg watermark failed: {result.stderr}")
            
            return output_video
            
        except Exception as e:
            raise RuntimeError(f"Watermark processing failed: {str(e)}")
    
    async def add_picture_in_picture(
        self, 
        main_video: Path, 
        pip_video: Path,
        pip_config: Dict[str, Any],
        output_video: Path
    ) -> Path:
        """Add picture-in-picture overlay."""
        try:
            # Extract PIP configuration
            x = pip_config.get("x", 50)
            y = pip_config.get("y", 50)
            width = pip_config.get("width", 320)
            height = pip_config.get("height", 240)
            start_time = pip_config.get("start_time", 0.0)
            duration = pip_config.get("duration", 10.0)
            
            # Build PIP filter
            pip_filter = (
                f"[1:v]scale={width}:{height}[pip];"
                f"[0:v][pip]overlay={x}:{y}:"
                f"enable='between(t,{start_time},{start_time + duration})'"
            )
            
            cmd = [
                self.ffmpeg_path,
                "-i", str(main_video),
                "-i", str(pip_video),
                "-filter_complex", pip_filter,
                "-c:a", "copy",
                "-y",
                str(output_video)
            ]
            
            # Execute FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg PIP failed: {result.stderr}")
            
            return output_video
            
        except Exception as e:
            raise RuntimeError(f"Picture-in-picture processing failed: {str(e)}")
    
    async def process_video_pipeline(
        self, 
        input_video: Path,
        pipeline_config: Dict[str, Any]
    ) -> Path:
        """Process video through complete pipeline."""
        try:
            current_video = input_video
            
            # Process each stage in the pipeline
            stages = pipeline_config.get("stages", [])
            
            for i, stage in enumerate(stages):
                stage_type = stage.get("type")
                stage_config = stage.get("config", {})
                
                # Create temporary output file for this stage
                stage_output = self.temp_dir / f"stage_{i}_{current_video.stem}.mp4"
                
                if stage_type == "text_overlays":
                    overlays = [OverlayConfig(**overlay) for overlay in stage_config.get("overlays", [])]
                    current_video = await self.add_text_overlays(current_video, overlays, stage_output)
                
                elif stage_type == "watermark":
                    watermark_config = WatermarkConfig(**stage_config)
                    current_video = await self.add_watermark(current_video, watermark_config, stage_output)
                
                elif stage_type == "picture_in_picture":
                    pip_video = Path(stage_config.get("pip_video"))
                    current_video = await self.add_picture_in_picture(
                        current_video, pip_video, stage_config, stage_output
                    )
                
                else:
                    raise ValueError(f"Unknown stage type: {stage_type}")
            
            return current_video
            
        except Exception as e:
            raise RuntimeError(f"Video pipeline processing failed: {str(e)}")
    
    def _build_drawtext_filter(self, overlay: OverlayConfig, index: int) -> str:
        """Build FFmpeg drawtext filter string."""
        filter_parts = [
            f"drawtext=text='{overlay.text}'",
            f"x={overlay.x}",
            f"y={overlay.y}",
            f"fontsize={overlay.font_size}",
            f"fontcolor={overlay.font_color}",
            f"enable='between(t,{overlay.start_time},{overlay.start_time + overlay.duration})'"
        ]
        
        if overlay.background_color:
            filter_parts.append(f"box=1:boxcolor={overlay.background_color}")
        
        if overlay.font_file:
            filter_parts.append(f"fontfile={overlay.font_file}")
        
        return ":".join(filter_parts)
    
    def _get_watermark_position(self, position: str) -> Dict[str, str]:
        """Get watermark position coordinates."""
        positions = {
            "top-left": {"x": "10", "y": "10"},
            "top-right": {"x": "w-text_w-10", "y": "10"},
            "bottom-left": {"x": "10", "y": "h-text_h-10"},
            "bottom-right": {"x": "w-text_w-10", "y": "h-text_h-10"}
        }
        return positions.get(position, positions["bottom-right"])
