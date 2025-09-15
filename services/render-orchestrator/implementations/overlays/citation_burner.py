"""Legal citation burner for video overlays."""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class CitationFormat(Enum):
    """Legal citation formats."""
    BLUEBOOK = "bluebook"
    APA = "apa"
    MLA = "mla"
    CUSTOM = "custom"


@dataclass
class Citation:
    """Legal citation data."""
    evidence_id: str
    evidence_type: str
    page_number: Optional[int] = None
    timestamp: Optional[float] = None
    jurisdiction: Optional[str] = None
    case_name: Optional[str] = None
    court: Optional[str] = None
    date: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None


@dataclass
class CitationDisplay:
    """Citation display configuration."""
    citation: Citation
    start_time: float
    duration: float
    position: str = "bottom-left"
    font_size: int = 18
    font_color: str = "white"
    background_color: str = "black@0.7"
    fade_in: float = 0.5
    fade_out: float = 0.5


class CitationBurner:
    """Burns legal citations into video overlays."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize citation burner."""
        self.default_format = CitationFormat(config.get("default_format", "bluebook"))
        self.jurisdiction_rules = config.get("jurisdiction_rules", {})
        self.font_config = config.get("font", {})
        self.positioning_config = config.get("positioning", {})
    
    def format_citation(
        self, 
        citation: Citation, 
        format_type: Optional[CitationFormat] = None
    ) -> str:
        """Format citation according to specified format."""
        if format_type is None:
            format_type = self.default_format
        
        if format_type == CitationFormat.BLUEBOOK:
            return self._format_bluebook(citation)
        elif format_type == CitationFormat.APA:
            return self._format_apa(citation)
        elif format_type == CitationFormat.MLA:
            return self._format_mla(citation)
        else:
            return self._format_custom(citation)
    
    def _format_bluebook(self, citation: Citation) -> str:
        """Format citation in Bluebook style."""
        parts = []
        
        # Case name (italicized)
        if citation.case_name:
            parts.append(f"*{citation.case_name}*")
        
        # Volume and reporter
        if citation.volume and citation.reporter:
            parts.append(f"{citation.volume} {citation.reporter}")
        
        # Page numbers
        if citation.page_start:
            if citation.page_end and citation.page_end != citation.page_start:
                parts.append(f"{citation.page_start}-{citation.page_end}")
            else:
                parts.append(str(citation.page_start))
        
        # Court and date
        if citation.court and citation.date:
            parts.append(f"({citation.court} {citation.date})")
        
        # Evidence reference
        if citation.evidence_id:
            parts.append(f"[{citation.evidence_id}]")
        
        return ", ".join(parts)
    
    def _format_apa(self, citation: Citation) -> str:
        """Format citation in APA style."""
        parts = []
        
        # Case name
        if citation.case_name:
            parts.append(citation.case_name)
        
        # Court and date
        if citation.court and citation.date:
            parts.append(f"({citation.court}, {citation.date})")
        
        # Reporter information
        if citation.volume and citation.reporter:
            parts.append(f"{citation.volume} {citation.reporter}")
        
        # Page numbers
        if citation.page_start:
            if citation.page_end and citation.page_end != citation.page_start:
                parts.append(f"{citation.page_start}-{citation.page_end}")
            else:
                parts.append(str(citation.page_start))
        
        # Evidence reference
        if citation.evidence_id:
            parts.append(f"[{citation.evidence_id}]")
        
        return " ".join(parts)
    
    def _format_mla(self, citation: Citation) -> str:
        """Format citation in MLA style."""
        parts = []
        
        # Case name
        if citation.case_name:
            parts.append(f'"{citation.case_name}"')
        
        # Court
        if citation.court:
            parts.append(citation.court)
        
        # Date
        if citation.date:
            parts.append(citation.date)
        
        # Reporter information
        if citation.volume and citation.reporter:
            parts.append(f"{citation.volume} {citation.reporter}")
        
        # Page numbers
        if citation.page_start:
            if citation.page_end and citation.page_end != citation.page_start:
                parts.append(f"{citation.page_start}-{citation.page_end}")
            else:
                parts.append(str(citation.page_start))
        
        # Evidence reference
        if citation.evidence_id:
            parts.append(f"[{citation.evidence_id}]")
        
        return ". ".join(parts)
    
    def _format_custom(self, citation: Citation) -> str:
        """Format citation using custom rules."""
        # Get jurisdiction-specific rules
        jurisdiction = citation.jurisdiction or "default"
        rules = self.jurisdiction_rules.get(jurisdiction, {})
        
        # Apply custom formatting
        format_template = rules.get("template", "{evidence_id}: {case_name}")
        
        formatted = format_template.format(
            evidence_id=citation.evidence_id,
            case_name=citation.case_name or "",
            court=citation.court or "",
            date=citation.date or "",
            volume=citation.volume or "",
            reporter=citation.reporter or "",
            page_start=citation.page_start or "",
            page_end=citation.page_end or "",
            page_number=citation.page_number or ""
        )
        
        return formatted
    
    def create_citation_displays(
        self, 
        citations: List[Citation],
        timeline_data: Dict[str, Any]
    ) -> List[CitationDisplay]:
        """Create citation display configurations from citations and timeline."""
        displays = []
        
        for citation in citations:
            # Find relevant timeline events
            relevant_events = self._find_relevant_events(citation, timeline_data)
            
            for event in relevant_events:
                display = CitationDisplay(
                    citation=citation,
                    start_time=event.get("start_time", 0.0),
                    duration=event.get("duration", 3.0),
                    position=self._calculate_position(citation, event),
                    font_size=self._calculate_font_size(citation),
                    font_color=self._get_font_color(citation),
                    background_color=self._get_background_color(citation),
                    fade_in=0.5,
                    fade_out=0.5
                )
                displays.append(display)
        
        return displays
    
    def _find_relevant_events(
        self, 
        citation: Citation, 
        timeline_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find timeline events relevant to citation."""
        events = timeline_data.get("events", [])
        relevant_events = []
        
        for event in events:
            # Check if event references this evidence
            event_evidence_ids = event.get("evidence_ids", [])
            if citation.evidence_id in event_evidence_ids:
                relevant_events.append(event)
        
        return relevant_events
    
    def _calculate_position(
        self, 
        citation: Citation, 
        event: Dict[str, Any]
    ) -> str:
        """Calculate optimal position for citation."""
        # Get positioning rules
        positioning_rules = self.positioning_config.get("rules", {})
        
        # Check for evidence type specific positioning
        evidence_type = citation.evidence_type
        if evidence_type in positioning_rules:
            return positioning_rules[evidence_type]
        
        # Check for jurisdiction specific positioning
        jurisdiction = citation.jurisdiction
        if jurisdiction and jurisdiction in positioning_rules:
            return positioning_rules[jurisdiction]
        
        # Default positioning
        return positioning_rules.get("default", "bottom-left")
    
    def _calculate_font_size(self, citation: Citation) -> int:
        """Calculate appropriate font size for citation."""
        base_size = self.font_config.get("base_size", 18)
        
        # Adjust based on citation length
        citation_text = self.format_citation(citation)
        if len(citation_text) > 100:
            return max(base_size - 4, 12)
        elif len(citation_text) > 50:
            return base_size - 2
        else:
            return base_size
    
    def _get_font_color(self, citation: Citation) -> str:
        """Get font color for citation."""
        # Check for evidence type specific colors
        evidence_type = citation.evidence_type
        type_colors = self.font_config.get("type_colors", {})
        
        if evidence_type in type_colors:
            return type_colors[evidence_type]
        
        # Default color
        return self.font_config.get("default_color", "white")
    
    def _get_background_color(self, citation: Citation) -> str:
        """Get background color for citation."""
        # Check for evidence type specific backgrounds
        evidence_type = citation.evidence_type
        type_backgrounds = self.font_config.get("type_backgrounds", {})
        
        if evidence_type in type_backgrounds:
            return type_backgrounds[evidence_type]
        
        # Default background
        return self.font_config.get("default_background", "black@0.7")
    
    def validate_citation_compliance(
        self, 
        citations: List[Citation],
        jurisdiction: str
    ) -> Dict[str, Any]:
        """Validate citation compliance for jurisdiction."""
        validation_result = {
            "is_compliant": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Get jurisdiction rules
        rules = self.jurisdiction_rules.get(jurisdiction, {})
        
        for citation in citations:
            # Check required fields
            required_fields = rules.get("required_fields", [])
            for field in required_fields:
                if not getattr(citation, field, None):
                    validation_result["errors"].append(
                        f"Missing required field '{field}' for citation {citation.evidence_id}"
                    )
                    validation_result["is_compliant"] = False
            
            # Check format compliance
            if "format_requirements" in rules:
                format_req = rules["format_requirements"]
                citation_text = self.format_citation(citation)
                
                # Check length requirements
                if "max_length" in format_req:
                    if len(citation_text) > format_req["max_length"]:
                        validation_result["warnings"].append(
                            f"Citation {citation.evidence_id} exceeds maximum length"
                        )
                
                # Check required elements
                if "required_elements" in format_req:
                    for element in format_req["required_elements"]:
                        if element not in citation_text:
                            validation_result["errors"].append(
                                f"Citation {citation.evidence_id} missing required element '{element}'"
                            )
                            validation_result["is_compliant"] = False
        
        return validation_result
