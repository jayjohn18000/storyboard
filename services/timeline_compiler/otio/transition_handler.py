"""OpenTimelineIO transition handler."""

import time
from typing import Dict, Any, List
import opentimelineio as otio


class TransitionHandler:
    """Handler for transitions in OpenTimelineIO timelines."""
    
    def __init__(self):
        self.default_fps = 30.0
        self.supported_transitions = [
            "fade",
            "cut",
            "dissolve",
            "wipe",
            "slide",
            "zoom",
            "pan",
        ]
    
    async def handle_transitions(self, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle transitions in timeline."""
        try:
            start_time = time.time()
            
            # Parse timeline
            timeline = self._parse_timeline(timeline_data)
            
            # Process transitions
            processed_timeline = await self._process_transitions(timeline)
            
            # Validate transitions
            validation_results = self._validate_transitions(processed_timeline)
            
            # Convert back to dictionary
            timeline_dict = self._timeline_to_dict(processed_timeline)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "timeline": timeline_dict,
                "validation_results": validation_results,
                "processing_time_ms": processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Transition handling failed: {str(e)}")
    
    def _parse_timeline(self, timeline_data: Dict[str, Any]) -> otio.schema.Timeline:
        """Parse timeline from dictionary."""
        try:
            # Create timeline
            timeline = otio.schema.Timeline(
                name=timeline_data.get("name", "Timeline"),
                metadata=timeline_data.get("metadata", {})
            )
            
            # Parse tracks
            for track_data in timeline_data.get("tracks", []):
                track = self._parse_track(track_data)
                timeline.tracks.append(track)
            
            return timeline
            
        except Exception as e:
            raise Exception(f"Failed to parse timeline: {str(e)}")
    
    def _parse_track(self, track_data: Dict[str, Any]) -> otio.schema.Track:
        """Parse track from dictionary."""
        try:
            # Create track
            track = otio.schema.Track(
                name=track_data.get("name", "Track"),
                kind=getattr(otio.schema.TrackKind, track_data.get("kind", "Video"))
            )
            
            # Parse clips
            for clip_data in track_data.get("clips", []):
                clip = self._parse_clip(clip_data)
                track.append(clip)
            
            return track
            
        except Exception as e:
            raise Exception(f"Failed to parse track: {str(e)}")
    
    def _parse_clip(self, clip_data: Dict[str, Any]) -> otio.schema.Clip:
        """Parse clip from dictionary."""
        try:
            # Create media reference
            media_ref_data = clip_data.get("media_reference", {})
            media_reference = otio.ExternalReference(
                target_url=media_ref_data.get("target_url", ""),
                metadata=media_ref_data.get("metadata", {})
            )
            
            # Create source range
            source_range_data = clip_data.get("source_range", {})
            start_time_data = source_range_data.get("start_time", {})
            duration_data = source_range_data.get("duration", {})
            
            source_range = otio.TimeRange(
                start_time=otio.RationalTime(
                    start_time_data.get("value", 0),
                    start_time_data.get("rate", self.default_fps)
                ),
                duration=otio.RationalTime(
                    duration_data.get("value", 0),
                    duration_data.get("rate", self.default_fps)
                )
            )
            
            # Create clip
            clip = otio.schema.Clip(
                name=clip_data.get("name", "Clip"),
                media_reference=media_reference,
                source_range=source_range,
                metadata=clip_data.get("metadata", {})
            )
            
            return clip
            
        except Exception as e:
            raise Exception(f"Failed to parse clip: {str(e)}")
    
    async def _process_transitions(self, timeline: otio.schema.Timeline) -> otio.schema.Timeline:
        """Process transitions in timeline."""
        try:
            # Process each track
            for track in timeline.tracks:
                await self._process_track_transitions(track)
            
            return timeline
            
        except Exception as e:
            raise Exception(f"Failed to process transitions: {str(e)}")
    
    async def _process_track_transitions(self, track: otio.schema.Track):
        """Process transitions in a track."""
        try:
            # Find transition clips
            transition_clips = []
            for i, clip in enumerate(track):
                if self._is_transition_clip(clip):
                    transition_clips.append((i, clip))
            
            # Process transitions
            for i, transition_clip in transition_clips:
                await self._process_transition_clip(track, i, transition_clip)
            
        except Exception as e:
            print(f"Failed to process track transitions: {e}")
    
    async def _process_transition_clip(self, track: otio.schema.Track, index: int, transition_clip: otio.schema.Clip):
        """Process individual transition clip."""
        try:
            # Get transition type
            transition_type = transition_clip.metadata.get("transition_type", "fade")
            
            # Get transition duration
            duration = transition_clip.metadata.get("duration_seconds", 1.0)
            
            # Create transition
            transition = otio.schema.Transition(
                name=f"{transition_type.title()} Transition",
                transition_type=transition_type,
                in_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
                out_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
                metadata={
                    "transition_type": transition_type,
                    "duration": duration,
                }
            )
            
            # Replace clip with transition
            track[index] = transition
            
        except Exception as e:
            print(f"Failed to process transition clip: {e}")
    
    def _is_transition_clip(self, clip: otio.schema.Clip) -> bool:
        """Check if clip is a transition clip."""
        return (
            clip.metadata.get("type") == "transition" or
            "transition_type" in clip.metadata or
            clip.name.lower().find("transition") != -1
        )
    
    def _validate_transitions(self, timeline: otio.schema.Timeline) -> Dict[str, Any]:
        """Validate transitions in timeline."""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "transition_count": 0,
            "supported_transitions": 0,
            "unsupported_transitions": 0,
        }
        
        try:
            # Count transitions
            for track in timeline.tracks:
                for item in track:
                    if isinstance(item, otio.schema.Transition):
                        validation_results["transition_count"] += 1
                        
                        # Check transition type
                        transition_type = item.transition_type
                        if transition_type in self.supported_transitions:
                            validation_results["supported_transitions"] += 1
                        else:
                            validation_results["unsupported_transitions"] += 1
                            validation_results["issues"].append(
                                f"Unsupported transition type: {transition_type}"
                            )
                        
                        # Check transition duration
                        duration = item.in_offset.value / item.in_offset.rate
                        if duration <= 0:
                            validation_results["issues"].append(
                                f"Invalid transition duration: {duration}"
                            )
                        elif duration > 10:
                            validation_results["warnings"].append(
                                f"Very long transition duration: {duration}s"
                            )
            
            # Check for overlapping transitions
            for track in timeline.tracks:
                transitions = [item for item in track if isinstance(item, otio.schema.Transition)]
                for i in range(len(transitions) - 1):
                    current = transitions[i]
                    next_transition = transitions[i + 1]
                    
                    current_end = current.in_offset.value / current.in_offset.rate
                    next_start = next_transition.out_offset.value / next_transition.out_offset.rate
                    
                    if current_end > next_start:
                        validation_results["issues"].append(
                            f"Overlapping transitions in track '{track.name}'"
                        )
            
            # Set overall validity
            validation_results["valid"] = len(validation_results["issues"]) == 0
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Validation failed: {str(e)}")
        
        return validation_results
    
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
                                "name": item.name,
                                "type": "transition" if isinstance(item, otio.schema.Transition) else "clip",
                                "media_reference": {
                                    "target_url": item.media_reference.target_url if hasattr(item, 'media_reference') else "",
                                    "metadata": item.media_reference.metadata if hasattr(item, 'media_reference') else {},
                                },
                                "source_range": {
                                    "start_time": {
                                        "value": item.source_range.start_time.value if hasattr(item, 'source_range') else 0,
                                        "rate": item.source_range.start_time.rate if hasattr(item, 'source_range') else self.default_fps,
                                    },
                                    "duration": {
                                        "value": item.source_range.duration.value if hasattr(item, 'source_range') else 0,
                                        "rate": item.source_range.duration.rate if hasattr(item, 'source_range') else self.default_fps,
                                    },
                                },
                                "metadata": item.metadata,
                            }
                            for item in track
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
    
    def _create_fade_transition(self, duration: float) -> otio.schema.Transition:
        """Create fade transition."""
        return otio.schema.Transition(
            name="Fade Transition",
            transition_type="fade",
            in_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            out_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            metadata={
                "transition_type": "fade",
                "duration": duration,
            }
        )
    
    def _create_dissolve_transition(self, duration: float) -> otio.schema.Transition:
        """Create dissolve transition."""
        return otio.schema.Transition(
            name="Dissolve Transition",
            transition_type="dissolve",
            in_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            out_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            metadata={
                "transition_type": "dissolve",
                "duration": duration,
            }
        )
    
    def _create_wipe_transition(self, duration: float) -> otio.schema.Transition:
        """Create wipe transition."""
        return otio.schema.Transition(
            name="Wipe Transition",
            transition_type="wipe",
            in_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            out_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            metadata={
                "transition_type": "wipe",
                "duration": duration,
            }
        )
    
    def _create_slide_transition(self, duration: float) -> otio.schema.Transition:
        """Create slide transition."""
        return otio.schema.Transition(
            name="Slide Transition",
            transition_type="slide",
            in_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            out_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            metadata={
                "transition_type": "slide",
                "duration": duration,
            }
        )
    
    def _create_zoom_transition(self, duration: float) -> otio.schema.Transition:
        """Create zoom transition."""
        return otio.schema.Transition(
            name="Zoom Transition",
            transition_type="zoom",
            in_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            out_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            metadata={
                "transition_type": "zoom",
                "duration": duration,
            }
        )
    
    def _create_pan_transition(self, duration: float) -> otio.schema.Transition:
        """Create pan transition."""
        return otio.schema.Transition(
            name="Pan Transition",
            transition_type="pan",
            in_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            out_offset=otio.RationalTime(int(duration * self.default_fps), self.default_fps),
            metadata={
                "transition_type": "pan",
                "duration": duration,
            }
        )
