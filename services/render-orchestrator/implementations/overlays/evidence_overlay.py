"""Evidence overlay system for embedding actual evidence in videos."""

import asyncio
import tempfile
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class EvidenceDisplayMode(Enum):
    """Evidence display modes."""
    PICTURE_IN_PICTURE = "picture_in_picture"
    FULL_SCREEN = "full_screen"
    SPLIT_SCREEN = "split_screen"
    OVERLAY = "overlay"
    KEN_BURNS = "ken_burns"


@dataclass
class EvidenceItem:
    """Evidence item for overlay."""
    evidence_id: str
    evidence_type: str  # "document", "photo", "video", "audio"
    file_path: Path
    start_time: float
    duration: float
    display_mode: EvidenceDisplayMode
    position: Optional[Dict[str, float]] = None
    size: Optional[Dict[str, float]] = None
    zoom_config: Optional[Dict[str, Any]] = None
    audio_config: Optional[Dict[str, Any]] = None


@dataclass
class KenBurnsConfig:
    """Ken Burns effect configuration."""
    start_scale: float = 1.0
    end_scale: float = 1.2
    start_x: float = 0.0
    start_y: float = 0.0
    end_x: float = 0.1
    end_y: float = 0.1
    easing: str = "ease_in_out"


class EvidenceOverlay:
    """Manages evidence overlays in video."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize evidence overlay."""
        self.temp_dir = Path(config.get("temp_dir", "/tmp/evidence-overlays"))
        self.max_file_size = config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        self.supported_formats = config.get("supported_formats", {
            "document": [".pdf", ".doc", ".docx", ".txt"],
            "photo": [".jpg", ".jpeg", ".png", ".tiff", ".bmp"],
            "video": [".mp4", ".avi", ".mov", ".mkv"],
            "audio": [".mp3", ".wav", ".m4a", ".aac"]
        })
        self.display_configs = config.get("display_configs", {})
        
        # Create temp directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_evidence_overlays(
        self, 
        main_video: Path,
        evidence_items: List[EvidenceItem]
    ) -> Path:
        """Process evidence overlays for main video."""
        try:
            # Sort evidence items by start time
            sorted_items = sorted(evidence_items, key=lambda x: x.start_time)
            
            # Process each evidence item
            current_video = main_video
            
            for i, evidence_item in enumerate(sorted_items):
                # Create temporary output file
                output_file = self.temp_dir / f"evidence_overlay_{i}_{current_video.stem}.mp4"
                
                # Process evidence overlay
                current_video = await self._process_single_evidence(
                    current_video, evidence_item, output_file
                )
            
            return current_video
            
        except Exception as e:
            raise RuntimeError(f"Evidence overlay processing failed: {str(e)}")
    
    async def _process_single_evidence(
        self, 
        main_video: Path, 
        evidence_item: EvidenceItem,
        output_file: Path
    ) -> Path:
        """Process single evidence item overlay."""
        try:
            # Validate evidence file
            if not evidence_item.file_path.exists():
                raise ValueError(f"Evidence file not found: {evidence_item.file_path}")
            
            # Check file size
            file_size = evidence_item.file_path.stat().st_size
            if file_size > self.max_file_size:
                raise ValueError(f"Evidence file too large: {file_size} bytes")
            
            # Check file format
            if not self._is_supported_format(evidence_item):
                raise ValueError(f"Unsupported evidence format: {evidence_item.file_path.suffix}")
            
            # Process based on display mode
            if evidence_item.display_mode == EvidenceDisplayMode.PICTURE_IN_PICTURE:
                return await self._create_picture_in_picture(
                    main_video, evidence_item, output_file
                )
            elif evidence_item.display_mode == EvidenceDisplayMode.FULL_SCREEN:
                return await self._create_full_screen_overlay(
                    main_video, evidence_item, output_file
                )
            elif evidence_item.display_mode == EvidenceDisplayMode.SPLIT_SCREEN:
                return await self._create_split_screen(
                    main_video, evidence_item, output_file
                )
            elif evidence_item.display_mode == EvidenceDisplayMode.OVERLAY:
                return await self._create_overlay(
                    main_video, evidence_item, output_file
                )
            elif evidence_item.display_mode == EvidenceDisplayMode.KEN_BURNS:
                return await self._create_ken_burns(
                    main_video, evidence_item, output_file
                )
            else:
                raise ValueError(f"Unknown display mode: {evidence_item.display_mode}")
                
        except Exception as e:
            raise RuntimeError(f"Single evidence processing failed: {str(e)}")
    
    async def _create_picture_in_picture(
        self, 
        main_video: Path, 
        evidence_item: EvidenceItem,
        output_file: Path
    ) -> Path:
        """Create picture-in-picture overlay."""
        # This would use FFmpeg to create PIP overlay
        # For now, return the main video as placeholder
        return main_video
    
    async def _create_full_screen_overlay(
        self, 
        main_video: Path, 
        evidence_item: EvidenceItem,
        output_file: Path
    ) -> Path:
        """Create full-screen evidence overlay."""
        # This would replace the main video with evidence for the duration
        # For now, return the main video as placeholder
        return main_video
    
    async def _create_split_screen(
        self, 
        main_video: Path, 
        evidence_item: EvidenceItem,
        output_file: Path
    ) -> Path:
        """Create split-screen display."""
        # This would show main video and evidence side by side
        # For now, return the main video as placeholder
        return main_video
    
    async def _create_overlay(
        self, 
        main_video: Path, 
        evidence_item: EvidenceItem,
        output_file: Path
    ) -> Path:
        """Create overlay on main video."""
        # This would overlay evidence on top of main video
        # For now, return the main video as placeholder
        return main_video
    
    async def _create_ken_burns(
        self, 
        main_video: Path, 
        evidence_item: EvidenceItem,
        output_file: Path
    ) -> Path:
        """Create Ken Burns effect for evidence."""
        # This would apply Ken Burns effect to evidence
        # For now, return the main video as placeholder
        return main_video
    
    def _is_supported_format(self, evidence_item: EvidenceItem) -> bool:
        """Check if evidence file format is supported."""
        file_extension = evidence_item.file_path.suffix.lower()
        supported_extensions = self.supported_formats.get(evidence_item.evidence_type, [])
        return file_extension in supported_extensions
    
    def create_evidence_timeline(
        self, 
        evidence_items: List[EvidenceItem]
    ) -> Dict[str, Any]:
        """Create timeline of evidence overlays."""
        timeline = {
            "total_duration": 0.0,
            "evidence_segments": [],
            "overlaps": [],
            "gaps": []
        }
        
        # Sort by start time
        sorted_items = sorted(evidence_items, key=lambda x: x.start_time)
        
        # Calculate total duration
        if sorted_items:
            last_end = max(item.start_time + item.duration for item in sorted_items)
            timeline["total_duration"] = last_end
        
        # Create segments
        for item in sorted_items:
            segment = {
                "evidence_id": item.evidence_id,
                "evidence_type": item.evidence_type,
                "start_time": item.start_time,
                "end_time": item.start_time + item.duration,
                "duration": item.duration,
                "display_mode": item.display_mode.value
            }
            timeline["evidence_segments"].append(segment)
        
        # Find overlaps
        for i in range(len(sorted_items) - 1):
            current_item = sorted_items[i]
            next_item = sorted_items[i + 1]
            
            current_end = current_item.start_time + current_item.duration
            if current_end > next_item.start_time:
                overlap = {
                    "evidence_ids": [current_item.evidence_id, next_item.evidence_id],
                    "start_time": next_item.start_time,
                    "end_time": current_end,
                    "duration": current_end - next_item.start_time
                }
                timeline["overlaps"].append(overlap)
        
        # Find gaps
        for i in range(len(sorted_items) - 1):
            current_item = sorted_items[i]
            next_item = sorted_items[i + 1]
            
            current_end = current_item.start_time + current_item.duration
            if current_end < next_item.start_time:
                gap = {
                    "start_time": current_end,
                    "end_time": next_item.start_time,
                    "duration": next_item.start_time - current_end
                }
                timeline["gaps"].append(gap)
        
        return timeline
    
    def validate_evidence_overlays(
        self, 
        evidence_items: List[EvidenceItem]
    ) -> Dict[str, Any]:
        """Validate evidence overlays for compliance."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        for item in evidence_items:
            # Check file existence
            if not item.file_path.exists():
                validation_result["errors"].append(
                    f"Evidence file not found: {item.file_path}"
                )
                validation_result["is_valid"] = False
            
            # Check file size
            if item.file_path.exists():
                file_size = item.file_path.stat().st_size
                if file_size > self.max_file_size:
                    validation_result["errors"].append(
                        f"Evidence file too large: {item.evidence_id} ({file_size} bytes)"
                    )
                    validation_result["is_valid"] = False
            
            # Check format support
            if not self._is_supported_format(item):
                validation_result["errors"].append(
                    f"Unsupported evidence format: {item.evidence_id} ({item.file_path.suffix})"
                )
                validation_result["is_valid"] = False
            
            # Check duration
            if item.duration <= 0:
                validation_result["errors"].append(
                    f"Invalid duration for evidence: {item.evidence_id}"
                )
                validation_result["is_valid"] = False
            
            # Check start time
            if item.start_time < 0:
                validation_result["errors"].append(
                    f"Invalid start time for evidence: {item.evidence_id}"
                )
                validation_result["is_valid"] = False
        
        # Check for overlaps
        timeline = self.create_evidence_timeline(evidence_items)
        if timeline["overlaps"]:
            validation_result["warnings"].append(
                f"Found {len(timeline['overlaps'])} evidence overlaps"
            )
        
        return validation_result
    
    def optimize_evidence_placement(
        self, 
        evidence_items: List[EvidenceItem],
        main_video_duration: float
    ) -> List[EvidenceItem]:
        """Optimize evidence placement to avoid overlaps."""
        optimized_items = []
        
        # Sort by priority (could be based on evidence importance)
        sorted_items = sorted(evidence_items, key=lambda x: x.start_time)
        
        for item in sorted_items:
            # Check for conflicts with already placed items
            conflict = False
            for placed_item in optimized_items:
                if self._items_overlap(item, placed_item):
                    conflict = True
                    break
            
            if not conflict:
                optimized_items.append(item)
            else:
                # Try to adjust timing
                adjusted_item = self._adjust_item_timing(item, optimized_items)
                if adjusted_item:
                    optimized_items.append(adjusted_item)
        
        return optimized_items
    
    def _items_overlap(self, item1: EvidenceItem, item2: EvidenceItem) -> bool:
        """Check if two evidence items overlap in time."""
        item1_end = item1.start_time + item1.duration
        item2_end = item2.start_time + item2.duration
        
        return not (item1_end <= item2.start_time or item2_end <= item1.start_time)
    
    def _adjust_item_timing(
        self, 
        item: EvidenceItem, 
        placed_items: List[EvidenceItem]
    ) -> Optional[EvidenceItem]:
        """Try to adjust item timing to avoid conflicts."""
        # Find the best time slot
        available_slots = self._find_available_slots(placed_items, item.duration)
        
        if available_slots:
            # Use the first available slot
            best_slot = available_slots[0]
            adjusted_item = EvidenceItem(
                evidence_id=item.evidence_id,
                evidence_type=item.evidence_type,
                file_path=item.file_path,
                start_time=best_slot["start_time"],
                duration=item.duration,
                display_mode=item.display_mode,
                position=item.position,
                size=item.size,
                zoom_config=item.zoom_config,
                audio_config=item.audio_config
            )
            return adjusted_item
        
        return None
    
    def _find_available_slots(
        self, 
        placed_items: List[EvidenceItem], 
        required_duration: float
    ) -> List[Dict[str, float]]:
        """Find available time slots for evidence placement."""
        slots = []
        
        # Sort placed items by start time
        sorted_items = sorted(placed_items, key=lambda x: x.start_time)
        
        # Check slot before first item
        if sorted_items and sorted_items[0].start_time >= required_duration:
            slots.append({
                "start_time": 0.0,
                "end_time": sorted_items[0].start_time,
                "duration": sorted_items[0].start_time
            })
        
        # Check slots between items
        for i in range(len(sorted_items) - 1):
            current_end = sorted_items[i].start_time + sorted_items[i].duration
            next_start = sorted_items[i + 1].start_time
            
            if next_start - current_end >= required_duration:
                slots.append({
                    "start_time": current_end,
                    "end_time": next_start,
                    "duration": next_start - current_end
                })
        
        # Check slot after last item
        if sorted_items:
            last_end = sorted_items[-1].start_time + sorted_items[-1].duration
            slots.append({
                "start_time": last_end,
                "end_time": float('inf'),
                "duration": float('inf')
            })
        
        return slots
