"""OpenTimelineIO timeline builder."""

import time
from typing import Dict, Any, List
import opentimelineio as otio


class TimelineBuilder:
    """Builder for OpenTimelineIO timelines."""
    
    def __init__(self):
        self.default_fps = 30.0
        self.default_resolution = (1920, 1080)
    
    async def build_timeline(self, storyboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build OpenTimelineIO timeline from storyboard."""
        try:
            start_time = time.time()
            
            # Parse storyboard
            from ...shared.models.storyboard import Storyboard
            storyboard = Storyboard.from_dict(storyboard_data)
            
            # Create timeline
            timeline = otio.schema.Timeline(
                name=storyboard.metadata.title,
                metadata={
                    "description": storyboard.metadata.description,
                    "case_id": storyboard.metadata.case_id,
                    "created_by": storyboard.metadata.created_by,
                    "version": storyboard.metadata.version,
                }
            )
            
            # Create video track
            video_track = otio.schema.Track(
                name="Video",
                kind=otio.schema.TrackKind.Video
            )
            
            # Create audio track
            audio_track = otio.schema.Track(
                name="Audio",
                kind=otio.schema.TrackKind.Audio
            )
            
            # Process scenes
            current_time = 0.0
            for scene in storyboard.scenes:
                # Create video clip for scene
                video_clip = await self._create_video_clip(scene, current_time)
                if video_clip:
                    video_track.append(video_clip)
                
                # Create audio clip for scene
                audio_clip = await self._create_audio_clip(scene, current_time)
                if audio_clip:
                    audio_track.append(audio_clip)
                
                # Update current time
                current_time += scene.duration_seconds
            
            # Add tracks to timeline
            timeline.tracks.append(video_track)
            timeline.tracks.append(audio_track)
            
            # Set timeline metadata
            timeline.metadata["total_duration"] = current_time
            timeline.metadata["scene_count"] = len(storyboard.scenes)
            timeline.metadata["evidence_count"] = len(storyboard.get_evidence_ids())
            
            # Convert to dictionary
            timeline_dict = self._timeline_to_dict(timeline)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "timeline": timeline_dict,
                "total_duration": current_time,
                "scene_count": len(storyboard.scenes),
                "evidence_count": len(storyboard.get_evidence_ids()),
                "processing_time_ms": processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Timeline building failed: {str(e)}")
    
    async def _create_video_clip(self, scene, start_time: float) -> otio.schema.Clip:
        """Create video clip for scene."""
        try:
            # Create media reference
            media_reference = otio.schema.ExternalReference(
                target_url=f"scene://{scene.id}",
                metadata={
                    "scene_type": scene.scene_type.value,
                    "title": scene.title,
                    "description": scene.description,
                    "evidence_anchors": [
                        {
                            "evidence_id": anchor.evidence_id,
                            "start_time": anchor.start_time,
                            "end_time": anchor.end_time,
                            "description": anchor.description,
                            "confidence": anchor.confidence,
                        }
                        for anchor in scene.evidence_anchors
                    ],
                    "camera_config": scene.camera_config,
                    "lighting_config": scene.lighting_config,
                    "materials": scene.materials,
                }
            )
            
            # Create clip
            clip = otio.schema.Clip(
                name=scene.title,
                media_reference=media_reference,
                source_range=otio.schema.TimeRange(
                    start_time=otio.schema.RationalTime(0, self.default_fps),
                    duration=otio.schema.RationalTime(int(scene.duration_seconds * self.default_fps), self.default_fps)
                ),
                metadata={
                    "scene_id": scene.id,
                    "scene_type": scene.scene_type.value,
                    "duration_seconds": scene.duration_seconds,
                }
            )
            
            return clip
            
        except Exception as e:
            print(f"Failed to create video clip for scene {scene.title}: {e}")
            return None
    
    async def _create_audio_clip(self, scene, start_time: float) -> otio.schema.Clip:
        """Create audio clip for scene."""
        try:
            # Check if scene has audio evidence
            has_audio = any(
                anchor.evidence_id.startswith("audio_") or anchor.evidence_id.startswith("video_")
                for anchor in scene.evidence_anchors
            )
            
            if not has_audio:
                return None
            
            # Create media reference
            media_reference = otio.schema.ExternalReference(
                target_url=f"audio://{scene.id}",
                metadata={
                    "scene_id": scene.id,
                    "has_audio": True,
                }
            )
            
            # Create clip
            clip = otio.schema.Clip(
                name=f"{scene.title} Audio",
                media_reference=media_reference,
                source_range=otio.schema.TimeRange(
                    start_time=otio.schema.RationalTime(0, self.default_fps),
                    duration=otio.schema.RationalTime(int(scene.duration_seconds * self.default_fps), self.default_fps)
                ),
                metadata={
                    "scene_id": scene.id,
                    "duration_seconds": scene.duration_seconds,
                }
            )
            
            return clip
            
        except Exception as e:
            print(f"Failed to create audio clip for scene {scene.title}: {e}")
            return None
    
    def _timeline_to_dict(self, timeline: otio.schema.Timeline) -> Dict[str, Any]:
        """Convert OpenTimelineIO timeline to dictionary."""
        try:
            # Convert to JSON and back to get dictionary
            timeline_json = otio.adapters.write_to_string(timeline, "otio_json")
            timeline_dict = otio.adapters.read_from_string(timeline_json, "otio_json")
            
            # Convert to plain dictionary
            return {
                "name": timeline.name,
                "metadata": timeline.metadata,
                "tracks": [
                    {
                        "name": track.name,
                        "kind": track.kind,
                        "clips": [
                            {
                                "name": clip.name,
                                "media_reference": {
                                    "target_url": clip.media_reference.target_url,
                                    "metadata": clip.media_reference.metadata,
                                },
                                "source_range": {
                                    "start_time": {
                                        "value": clip.source_range.start_time.value,
                                        "rate": clip.source_range.start_time.rate,
                                    },
                                    "duration": {
                                        "value": clip.source_range.duration.value,
                                        "rate": clip.source_range.duration.rate,
                                    },
                                },
                                "metadata": clip.metadata,
                            }
                            for clip in track
                        ],
                    }
                    for track in timeline.tracks
                ],
            }
            
        except Exception as e:
            # Fallback to basic dictionary
            return {
                "name": timeline.name,
                "metadata": timeline.metadata,
                "tracks": [],
            }
    
    def _create_transition(self, transition_type: str, duration: float) -> otio.schema.Transition:
        """Create transition between clips."""
        try:
            # Create transition
            transition = otio.schema.Transition(
                name=f"{transition_type.title()} Transition",
                transition_type=transition_type,
                in_offset=otio.schema.RationalTime(int(duration * self.default_fps), self.default_fps),
                out_offset=otio.schema.RationalTime(int(duration * self.default_fps), self.default_fps),
                metadata={
                    "transition_type": transition_type,
                    "duration": duration,
                }
            )
            
            return transition
            
        except Exception as e:
            print(f"Failed to create transition: {e}")
            return None
    
    def _validate_timeline(self, timeline: otio.schema.Timeline) -> List[str]:
        """Validate timeline for issues."""
        issues = []
        
        # Check for empty timeline
        if not timeline.tracks:
            issues.append("Timeline has no tracks")
        
        # Check for empty tracks
        for track in timeline.tracks:
            if not track:
                issues.append(f"Track '{track.name}' is empty")
        
        # Check for overlapping clips
        for track in timeline.tracks:
            clips = list(track)
            for i in range(len(clips) - 1):
                current_clip = clips[i]
                next_clip = clips[i + 1]
                
                current_end = current_clip.source_range.start_time + current_clip.source_range.duration
                if current_end > next_clip.source_range.start_time:
                    issues.append(
                        f"Track '{track.name}': Overlapping clips '{current_clip.name}' and '{next_clip.name}'"
                    )
        
        return issues
    
    def _optimize_timeline(self, timeline: otio.schema.Timeline) -> otio.schema.Timeline:
        """Optimize timeline for rendering."""
        try:
            # Remove empty tracks
            timeline.tracks = [track for track in timeline.tracks if track]
            
            # Sort clips by start time
            for track in timeline.tracks:
                track[:] = sorted(track, key=lambda clip: clip.source_range.start_time)
            
            return timeline
            
        except Exception as e:
            print(f"Failed to optimize timeline: {e}")
            return timeline
