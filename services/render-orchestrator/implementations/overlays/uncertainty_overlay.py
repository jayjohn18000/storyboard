"""Uncertainty visualization overlays for disputed facts."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class UncertaintyType(Enum):
    """Types of uncertainty indicators."""
    DISPUTED = "disputed"
    CONFIDENCE_LOW = "confidence_low"
    CONFIDENCE_MEDIUM = "confidence_medium"
    CONFIDENCE_HIGH = "confidence_high"
    ALLEGED = "alleged"
    SPECULATIVE = "speculative"


@dataclass
class UncertaintyIndicator:
    """Uncertainty indicator configuration."""
    uncertainty_type: UncertaintyType
    confidence_level: float  # 0.0 to 1.0
    start_time: float
    duration: float
    position: str = "top-right"
    label: Optional[str] = None
    show_percentage: bool = False
    visual_style: str = "outline"  # "outline", "transparency", "pattern"


@dataclass
class DisputedElement:
    """Disputed element in the scene."""
    element_id: str
    element_type: str  # "actor", "object", "location", "action"
    confidence_level: float
    dispute_reason: str
    evidence_support: List[str]
    evidence_contradict: List[str]
    start_time: float
    duration: float
    spatial_bounds: Optional[Dict[str, float]] = None


class UncertaintyOverlay:
    """Creates uncertainty visualization overlays."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize uncertainty overlay."""
        self.visual_styles = config.get("visual_styles", {})
        self.confidence_thresholds = config.get("confidence_thresholds", {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5
        })
        self.dispute_labels = config.get("dispute_labels", {})
        self.color_scheme = config.get("color_scheme", {})
    
    def create_uncertainty_indicators(
        self, 
        disputed_elements: List[DisputedElement]
    ) -> List[UncertaintyIndicator]:
        """Create uncertainty indicators for disputed elements."""
        indicators = []
        
        for element in disputed_elements:
            # Determine uncertainty type based on confidence level
            uncertainty_type = self._determine_uncertainty_type(element.confidence_level)
            
            # Create indicator
            indicator = UncertaintyIndicator(
                uncertainty_type=uncertainty_type,
                confidence_level=element.confidence_level,
                start_time=element.start_time,
                duration=element.duration,
                position=self._calculate_position(element),
                label=self._generate_label(element),
                show_percentage=self._should_show_percentage(element),
                visual_style=self._get_visual_style(element)
            )
            
            indicators.append(indicator)
        
        return indicators
    
    def _determine_uncertainty_type(self, confidence_level: float) -> UncertaintyType:
        """Determine uncertainty type based on confidence level."""
        if confidence_level >= self.confidence_thresholds["high"]:
            return UncertaintyType.CONFIDENCE_HIGH
        elif confidence_level >= self.confidence_thresholds["medium"]:
            return UncertaintyType.CONFIDENCE_MEDIUM
        elif confidence_level >= self.confidence_thresholds["low"]:
            return UncertaintyType.CONFIDENCE_LOW
        else:
            return UncertaintyType.DISPUTED
    
    def _calculate_position(self, element: DisputedElement) -> str:
        """Calculate optimal position for uncertainty indicator."""
        # Use spatial bounds if available
        if element.spatial_bounds:
            bounds = element.spatial_bounds
            center_x = (bounds.get("left", 0) + bounds.get("right", 100)) / 2
            center_y = (bounds.get("top", 0) + bounds.get("bottom", 100)) / 2
            
            # Determine position based on center
            if center_x < 50:
                if center_y < 50:
                    return "top-left"
                else:
                    return "bottom-left"
            else:
                if center_y < 50:
                    return "top-right"
                else:
                    return "bottom-right"
        
        # Default position based on element type
        element_positions = {
            "actor": "top-right",
            "object": "bottom-left",
            "location": "top-left",
            "action": "bottom-right"
        }
        
        return element_positions.get(element.element_type, "top-right")
    
    def _generate_label(self, element: DisputedElement) -> str:
        """Generate label for uncertainty indicator."""
        # Check for custom labels
        if element.element_type in self.dispute_labels:
            template = self.dispute_labels[element.element_type]
            return template.format(
                element_id=element.element_id,
                confidence=element.confidence_level,
                reason=element.dispute_reason
            )
        
        # Generate default label
        if element.confidence_level < self.confidence_thresholds["low"]:
            return "DISPUTED"
        elif element.confidence_level < self.confidence_thresholds["medium"]:
            return "UNCERTAIN"
        else:
            return "ALLEGED"
    
    def _should_show_percentage(self, element: DisputedElement) -> bool:
        """Determine if confidence percentage should be shown."""
        # Show percentage for medium confidence elements
        return (
            self.confidence_thresholds["low"] <= element.confidence_level < 
            self.confidence_thresholds["high"]
        )
    
    def _get_visual_style(self, element: DisputedElement) -> str:
        """Get visual style for uncertainty indicator."""
        # Check for element type specific styles
        element_styles = self.visual_styles.get("element_types", {})
        if element.element_type in element_styles:
            return element_styles[element.element_type]
        
        # Check for confidence level specific styles
        confidence_styles = self.visual_styles.get("confidence_levels", {})
        if element.confidence_level < self.confidence_thresholds["low"]:
            return confidence_styles.get("low", "outline")
        elif element.confidence_level < self.confidence_thresholds["medium"]:
            return confidence_styles.get("medium", "transparency")
        else:
            return confidence_styles.get("high", "pattern")
    
    def create_visual_effects(
        self, 
        indicators: List[UncertaintyIndicator]
    ) -> List[Dict[str, Any]]:
        """Create visual effects for uncertainty indicators."""
        effects = []
        
        for indicator in indicators:
            effect = {
                "type": "uncertainty_indicator",
                "start_time": indicator.start_time,
                "duration": indicator.duration,
                "position": indicator.position,
                "style": indicator.visual_style,
                "label": indicator.label,
                "confidence": indicator.confidence_level,
                "show_percentage": indicator.show_percentage
            }
            
            # Add style-specific properties
            if indicator.visual_style == "outline":
                effect.update({
                    "outline_color": self._get_outline_color(indicator),
                    "outline_width": self._get_outline_width(indicator),
                    "outline_pattern": self._get_outline_pattern(indicator)
                })
            elif indicator.visual_style == "transparency":
                effect.update({
                    "opacity": self._get_transparency_level(indicator),
                    "blur_amount": self._get_blur_amount(indicator)
                })
            elif indicator.visual_style == "pattern":
                effect.update({
                    "pattern_type": self._get_pattern_type(indicator),
                    "pattern_color": self._get_pattern_color(indicator),
                    "pattern_density": self._get_pattern_density(indicator)
                })
            
            effects.append(effect)
        
        return effects
    
    def _get_outline_color(self, indicator: UncertaintyIndicator) -> str:
        """Get outline color for uncertainty indicator."""
        color_map = self.color_scheme.get("outline_colors", {
            "disputed": "red",
            "confidence_low": "orange",
            "confidence_medium": "yellow",
            "confidence_high": "green"
        })
        
        return color_map.get(indicator.uncertainty_type.value, "red")
    
    def _get_outline_width(self, indicator: UncertaintyIndicator) -> int:
        """Get outline width for uncertainty indicator."""
        width_map = self.visual_styles.get("outline_widths", {
            "disputed": 3,
            "confidence_low": 2,
            "confidence_medium": 1,
            "confidence_high": 1
        })
        
        return width_map.get(indicator.uncertainty_type.value, 2)
    
    def _get_outline_pattern(self, indicator: UncertaintyIndicator) -> str:
        """Get outline pattern for uncertainty indicator."""
        pattern_map = self.visual_styles.get("outline_patterns", {
            "disputed": "dashed",
            "confidence_low": "dotted",
            "confidence_medium": "solid",
            "confidence_high": "solid"
        })
        
        return pattern_map.get(indicator.uncertainty_type.value, "dashed")
    
    def _get_transparency_level(self, indicator: UncertaintyIndicator) -> float:
        """Get transparency level for uncertainty indicator."""
        # Lower confidence = more transparent
        return 1.0 - (1.0 - indicator.confidence_level) * 0.5
    
    def _get_blur_amount(self, indicator: UncertaintyIndicator) -> float:
        """Get blur amount for uncertainty indicator."""
        # Lower confidence = more blur
        return (1.0 - indicator.confidence_level) * 5.0
    
    def _get_pattern_type(self, indicator: UncertaintyIndicator) -> str:
        """Get pattern type for uncertainty indicator."""
        pattern_map = self.visual_styles.get("pattern_types", {
            "disputed": "crosshatch",
            "confidence_low": "dots",
            "confidence_medium": "lines",
            "confidence_high": "none"
        })
        
        return pattern_map.get(indicator.uncertainty_type.value, "crosshatch")
    
    def _get_pattern_color(self, indicator: UncertaintyIndicator) -> str:
        """Get pattern color for uncertainty indicator."""
        return self._get_outline_color(indicator)
    
    def _get_pattern_density(self, indicator: UncertaintyIndicator) -> float:
        """Get pattern density for uncertainty indicator."""
        # Lower confidence = higher density
        return (1.0 - indicator.confidence_level) * 0.5 + 0.1
    
    def validate_uncertainty_compliance(
        self, 
        disputed_elements: List[DisputedElement],
        mode: str  # "sandbox" or "demonstrative"
    ) -> Dict[str, Any]:
        """Validate uncertainty visualization compliance."""
        validation_result = {
            "is_compliant": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        for element in disputed_elements:
            # Check if uncertainty is properly indicated
            if element.confidence_level < self.confidence_thresholds["high"]:
                if mode == "demonstrative":
                    # Demonstrative mode requires uncertainty indicators
                    if not self._has_uncertainty_indicator(element):
                        validation_result["errors"].append(
                            f"Disputed element {element.element_id} requires uncertainty indicator in demonstrative mode"
                        )
                        validation_result["is_compliant"] = False
                
                # Check confidence level requirements
                if element.confidence_level < self.confidence_thresholds["low"]:
                    validation_result["warnings"].append(
                        f"Element {element.element_id} has very low confidence ({element.confidence_level:.2f})"
                    )
                
                # Check evidence support
                if len(element.evidence_support) == 0:
                    validation_result["warnings"].append(
                        f"Element {element.element_id} has no supporting evidence"
                    )
        
        return validation_result
    
    def _has_uncertainty_indicator(self, element: DisputedElement) -> bool:
        """Check if element has proper uncertainty indicator."""
        # This would check if the element has been properly marked
        # with uncertainty indicators in the visualization
        return element.confidence_level < self.confidence_thresholds["high"]
