"""AI Agent for Evidence Intake and Triage.

Automatically categorizes uploaded evidence, suggests relevant case associations,
identifies duplicate uploads, extracts key information preview, and routes to
appropriate processors. Only operates in Sandbox mode.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# AI/ML imports
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import openai
from transformers import pipeline, AutoTokenizer, AutoModel

# Project imports
from services.shared.models.case import Case, CaseType
from services.shared.models.evidence import Evidence, EvidenceType
from services.shared.security.audit import AuditLogger, AuditEventType
from services.shared.interfaces.storage import StorageInterface


class EvidenceCategory(Enum):
    """Categories for evidence classification."""
    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    FINANCIAL = "financial"
    MEDICAL = "medical"
    PHOTOGRAPH = "photograph"
    AUDIO_RECORDING = "audio_recording"
    VIDEO_RECORDING = "video_recording"
    WITNESS_STATEMENT = "witness_statement"
    EXPERT_REPORT = "expert_report"
    SURVEILLANCE = "surveillance"
    COMMUNICATION = "communication"
    OTHER = "other"


class ProcessingPriority(Enum):
    """Processing priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EvidenceMetadata:
    """Extracted metadata from evidence."""
    category: EvidenceCategory
    confidence_score: float
    key_entities: List[str]
    key_dates: List[str]
    key_amounts: List[float]
    summary: str
    suggested_tags: List[str]
    processing_priority: ProcessingPriority
    estimated_processing_time: int  # minutes
    duplicate_candidates: List[str]  # IDs of potential duplicates


@dataclass
class CaseAssociation:
    """Suggested case association."""
    case_id: str
    case_title: str
    similarity_score: float
    reasoning: str
    suggested_actions: List[str]


class EvidenceClassifier:
    """Classifies evidence into categories using ML models."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.category_model = None
        self.entity_extractor = None
        self.sentiment_analyzer = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for classification."""
        try:
            # Initialize entity extraction pipeline
            self.entity_extractor = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple"
            )
            
            # Initialize sentiment analysis
            self.sentiment_analyzer = pipeline("sentiment-analysis")
            
            logging.info("Evidence classification models initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize classification models: {e}")
    
    async def classify_evidence(self, evidence: Evidence, content_preview: str) -> EvidenceMetadata:
        """Classify evidence and extract metadata."""
        
        # Basic classification based on file type and content
        category = self._classify_by_file_type(evidence.evidence_type)
        
        # Enhanced classification using content analysis
        if content_preview:
            enhanced_category = await self._classify_by_content(content_preview)
            if enhanced_category:
                category = enhanced_category
        
        # Extract entities
        entities = await self._extract_entities(content_preview)
        
        # Extract dates and amounts
        dates = self._extract_dates(content_preview)
        amounts = self._extract_amounts(content_preview)
        
        # Generate summary
        summary = await self._generate_summary(content_preview, category)
        
        # Suggest tags
        tags = self._suggest_tags(category, entities, content_preview)
        
        # Determine processing priority
        priority = self._determine_priority(category, entities, evidence.evidence_type)
        
        # Estimate processing time
        processing_time = self._estimate_processing_time(evidence.evidence_type, category)
        
        metadata = EvidenceMetadata(
            category=category,
            confidence_score=0.85,  # Would be calculated by actual ML model
            key_entities=entities,
            key_dates=dates,
            key_amounts=amounts,
            summary=summary,
            suggested_tags=tags,
            processing_priority=priority,
            estimated_processing_time=processing_time,
            duplicate_candidates=[]
        )
        
        return metadata
    
    def _classify_by_file_type(self, evidence_type: EvidenceType) -> EvidenceCategory:
        """Classify evidence based on file type."""
        type_mapping = {
            EvidenceType.DOCUMENT: EvidenceCategory.CORRESPONDENCE,
            EvidenceType.IMAGE: EvidenceCategory.PHOTOGRAPH,
            EvidenceType.AUDIO: EvidenceCategory.AUDIO_RECORDING,
            EvidenceType.VIDEO: EvidenceCategory.VIDEO_RECORDING,
            EvidenceType.EMAIL: EvidenceCategory.COMMUNICATION,
            EvidenceType.TEXT: EvidenceCategory.CORRESPONDENCE
        }
        return type_mapping.get(evidence_type, EvidenceCategory.OTHER)
    
    async def _classify_by_content(self, content: str) -> Optional[EvidenceCategory]:
        """Classify evidence based on content analysis."""
        if not self.entity_extractor:
            return None
        
        try:
            # Extract entities from content
            entities = self.entity_extractor(content)
            
            # Look for category indicators
            content_lower = content.lower()
            
            if any(word in content_lower for word in ['contract', 'agreement', 'terms', 'conditions']):
                return EvidenceCategory.CONTRACT
            elif any(word in content_lower for word in ['payment', 'invoice', 'bill', 'financial', 'money']):
                return EvidenceCategory.FINANCIAL
            elif any(word in content_lower for word in ['medical', 'doctor', 'hospital', 'treatment', 'diagnosis']):
                return EvidenceCategory.MEDICAL
            elif any(word in content_lower for word in ['witness', 'testimony', 'statement', 'deposition']):
                return EvidenceCategory.WITNESS_STATEMENT
            elif any(word in content_lower for word in ['expert', 'report', 'analysis', 'evaluation']):
                return EvidenceCategory.EXPERT_REPORT
            
        except Exception as e:
            logging.error(f"Content classification failed: {e}")
        
        return None
    
    async def _extract_entities(self, content: str) -> List[str]:
        """Extract named entities from content."""
        if not self.entity_extractor or not content:
            return []
        
        try:
            entities = self.entity_extractor(content)
            return [entity['word'] for entity in entities if entity['score'] > 0.8]
        except Exception as e:
            logging.error(f"Entity extraction failed: {e}")
            return []
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from content."""
        import re
        
        # Simple date pattern matching
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates
    
    def _extract_amounts(self, content: str) -> List[float]:
        """Extract monetary amounts from content."""
        import re
        
        # Pattern for monetary amounts
        amount_pattern = r'\$[\d,]+\.?\d*'
        matches = re.findall(amount_pattern, content)
        
        amounts = []
        for match in matches:
            try:
                # Clean and convert to float
                clean_amount = match.replace('$', '').replace(',', '')
                amounts.append(float(clean_amount))
            except ValueError:
                continue
        
        return amounts
    
    async def _generate_summary(self, content: str, category: EvidenceCategory) -> str:
        """Generate a summary of the evidence content."""
        if not content:
            return "No content available for summary generation"
        
        # Truncate content if too long
        max_length = 1000
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        # Generate summary based on category
        if category == EvidenceCategory.CONTRACT:
            return f"Contract document containing {len(content.split())} words. Key terms and conditions likely present."
        elif category == EvidenceCategory.FINANCIAL:
            amounts = self._extract_amounts(content)
            if amounts:
                return f"Financial document with monetary amounts: {amounts}. Contains {len(content.split())} words."
            else:
                return f"Financial document containing {len(content.split())} words."
        elif category == EvidenceCategory.WITNESS_STATEMENT:
            return f"Witness statement containing {len(content.split())} words. Likely contains testimony or deposition content."
        else:
            return f"Document containing {len(content.split())} words. Category: {category.value}"
    
    def _suggest_tags(self, category: EvidenceCategory, entities: List[str], content: str) -> List[str]:
        """Suggest tags for the evidence."""
        tags = [category.value]
        
        # Add entity-based tags
        for entity in entities[:5]:  # Limit to first 5 entities
            if len(entity) > 3:  # Only meaningful entities
                tags.append(entity.lower().replace(' ', '_'))
        
        # Add content-based tags
        content_lower = content.lower()
        if 'confidential' in content_lower:
            tags.append('confidential')
        if 'urgent' in content_lower:
            tags.append('urgent')
        if 'final' in content_lower:
            tags.append('final')
        
        return list(set(tags))  # Remove duplicates
    
    def _determine_priority(self, category: EvidenceCategory, entities: List[str], evidence_type: EvidenceType) -> ProcessingPriority:
        """Determine processing priority based on evidence characteristics."""
        
        # High priority categories
        if category in [EvidenceCategory.WITNESS_STATEMENT, EvidenceCategory.EXPERT_REPORT]:
            return ProcessingPriority.HIGH
        
        # Medium priority for certain types
        if evidence_type in [EvidenceType.VIDEO, EvidenceType.AUDIO]:
            return ProcessingPriority.MEDIUM
        
        # Check for urgent indicators in entities
        urgent_entities = ['urgent', 'emergency', 'asap', 'immediate']
        if any(entity.lower() in urgent_entities for entity in entities):
            return ProcessingPriority.URGENT
        
        return ProcessingPriority.LOW
    
    def _estimate_processing_time(self, evidence_type: EvidenceType, category: EvidenceCategory) -> int:
        """Estimate processing time in minutes."""
        
        base_times = {
            EvidenceType.DOCUMENT: 5,
            EvidenceType.IMAGE: 3,
            EvidenceType.AUDIO: 15,
            EvidenceType.VIDEO: 30,
            EvidenceType.EMAIL: 2,
            EvidenceType.TEXT: 2
        }
        
        base_time = base_times.get(evidence_type, 5)
        
        # Adjust based on category complexity
        category_multipliers = {
            EvidenceCategory.CONTRACT: 1.5,
            EvidenceCategory.FINANCIAL: 1.3,
            EvidenceCategory.MEDICAL: 1.4,
            EvidenceCategory.EXPERT_REPORT: 2.0,
            EvidenceCategory.WITNESS_STATEMENT: 1.2
        }
        
        multiplier = category_multipliers.get(category, 1.0)
        
        return int(base_time * multiplier)


class DuplicateDetector:
    """Detects potential duplicate evidence uploads."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.similarity_threshold = 0.85
    
    async def find_duplicates(self, evidence: Evidence, existing_evidence: List[Evidence]) -> List[str]:
        """Find potential duplicates of the given evidence."""
        
        duplicates = []
        
        for existing in existing_evidence:
            similarity_score = await self._calculate_similarity(evidence, existing)
            
            if similarity_score >= self.similarity_threshold:
                duplicates.append(existing.id)
        
        return duplicates
    
    async def _calculate_similarity(self, evidence1: Evidence, evidence2: Evidence) -> float:
        """Calculate similarity between two pieces of evidence."""
        
        # Check filename similarity
        filename_sim = self._filename_similarity(evidence1.filename, evidence2.filename)
        
        # Check file size similarity (within 10%)
        size_sim = self._size_similarity(evidence1.metadata.size_bytes, evidence2.metadata.size_bytes)
        
        # Check SHA256 hash (exact duplicates)
        hash_sim = 1.0 if evidence1.sha256_hash == evidence2.sha256_hash else 0.0
        
        # Check content similarity if available
        content_sim = 0.0
        if hasattr(evidence1, 'ocr_text') and hasattr(evidence2, 'ocr_text'):
            if evidence1.ocr_text and evidence2.ocr_text:
                content_sim = await self._content_similarity(evidence1.ocr_text, evidence2.ocr_text)
        
        # Weighted combination
        weights = {
            'filename': 0.2,
            'size': 0.1,
            'hash': 0.4,
            'content': 0.3
        }
        
        similarity = (
            filename_sim * weights['filename'] +
            size_sim * weights['size'] +
            hash_sim * weights['hash'] +
            content_sim * weights['content']
        )
        
        return similarity
    
    def _filename_similarity(self, filename1: str, filename2: str) -> float:
        """Calculate filename similarity."""
        # Simple Levenshtein distance-based similarity
        from difflib import SequenceMatcher
        return SequenceMatcher(None, filename1.lower(), filename2.lower()).ratio()
    
    def _size_similarity(self, size1: int, size2: int) -> float:
        """Calculate file size similarity."""
        if size1 == 0 and size2 == 0:
            return 1.0
        
        ratio = min(size1, size2) / max(size1, size2)
        return ratio
    
    async def _content_similarity(self, content1: str, content2: str) -> float:
        """Calculate content similarity using TF-IDF."""
        if not content1 or not content2:
            return 0.0
        
        try:
            # Vectorize content
            tfidf_matrix = self.vectorizer.fit_transform([content1, content2])
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            return similarity_matrix[0][1]
            
        except Exception as e:
            logging.error(f"Content similarity calculation failed: {e}")
            return 0.0


class CaseAssociationEngine:
    """Suggests case associations for evidence."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    async def suggest_case_associations(self, evidence: Evidence, evidence_metadata: EvidenceMetadata, 
                                      available_cases: List[Case]) -> List[CaseAssociation]:
        """Suggest case associations for evidence."""
        
        associations = []
        
        for case in available_cases:
            similarity_score = await self._calculate_case_similarity(evidence, evidence_metadata, case)
            
            if similarity_score > 0.3:  # Minimum threshold for suggestions
                reasoning = self._generate_reasoning(evidence, evidence_metadata, case, similarity_score)
                suggested_actions = self._suggest_actions(evidence, case, similarity_score)
                
                association = CaseAssociation(
                    case_id=case.id,
                    case_title=case.title,
                    similarity_score=similarity_score,
                    reasoning=reasoning,
                    suggested_actions=suggested_actions
                )
                
                associations.append(association)
        
        # Sort by similarity score
        associations.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return associations[:5]  # Return top 5 suggestions
    
    async def _calculate_case_similarity(self, evidence: Evidence, metadata: EvidenceMetadata, case: Case) -> float:
        """Calculate similarity between evidence and case."""
        
        similarity_score = 0.0
        
        # Check case type alignment
        case_type_similarity = self._case_type_similarity(metadata.category, case.case_type)
        similarity_score += case_type_similarity * 0.3
        
        # Check entity overlap with case description
        entity_similarity = self._entity_similarity(metadata.key_entities, case.description)
        similarity_score += entity_similarity * 0.4
        
        # Check date relevance
        date_similarity = self._date_similarity(metadata.key_dates, case.filing_date)
        similarity_score += date_similarity * 0.2
        
        # Check amount relevance for financial cases
        if metadata.category == EvidenceCategory.FINANCIAL and case.case_type == CaseType.CIVIL:
            amount_similarity = 0.5  # Boost for financial evidence in civil cases
            similarity_score += amount_similarity * 0.1
        
        return min(similarity_score, 1.0)
    
    def _case_type_similarity(self, evidence_category: EvidenceCategory, case_type: CaseType) -> float:
        """Calculate similarity based on case type and evidence category."""
        
        type_mappings = {
            CaseType.CIVIL: {
                EvidenceCategory.CONTRACT: 0.9,
                EvidenceCategory.FINANCIAL: 0.8,
                EvidenceCategory.CORRESPONDENCE: 0.7,
                EvidenceCategory.EXPERT_REPORT: 0.6
            },
            CaseType.CRIMINAL: {
                EvidenceCategory.SURVEILLANCE: 0.9,
                EvidenceCategory.WITNESS_STATEMENT: 0.8,
                EvidenceCategory.PHOTOGRAPH: 0.7,
                EvidenceCategory.EXPERT_REPORT: 0.6
            },
            CaseType.FAMILY: {
                EvidenceCategory.MEDICAL: 0.8,
                EvidenceCategory.FINANCIAL: 0.7,
                EvidenceCategory.CORRESPONDENCE: 0.6
            }
        }
        
        return type_mappings.get(case_type, {}).get(evidence_category, 0.1)
    
    def _entity_similarity(self, entities: List[str], case_description: str) -> float:
        """Calculate similarity based on entity overlap."""
        if not entities or not case_description:
            return 0.0
        
        case_words = set(case_description.lower().split())
        entity_words = set(entity.lower() for entity in entities)
        
        if not case_words or not entity_words:
            return 0.0
        
        intersection = case_words.intersection(entity_words)
        union = case_words.union(entity_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _date_similarity(self, evidence_dates: List[str], case_date: str) -> float:
        """Calculate similarity based on date relevance."""
        if not evidence_dates or not case_date:
            return 0.0
        
        # Simple date proximity check
        # In a real implementation, this would parse dates and calculate temporal proximity
        return 0.5  # Placeholder
    
    def _generate_reasoning(self, evidence: Evidence, metadata: EvidenceMetadata, case: Case, similarity_score: float) -> str:
        """Generate reasoning for case association."""
        
        reasons = []
        
        if metadata.category == EvidenceCategory.CONTRACT and case.case_type == CaseType.CIVIL:
            reasons.append("Contract evidence is highly relevant to civil cases")
        
        if metadata.category == EvidenceCategory.SURVEILLANCE and case.case_type == CaseType.CRIMINAL:
            reasons.append("Surveillance evidence is crucial for criminal cases")
        
        if metadata.key_entities:
            entity_overlap = len(set(entity.lower() for entity in metadata.key_entities) & 
                               set(case.description.lower().split()))
            if entity_overlap > 0:
                reasons.append(f"Shared entities: {entity_overlap} common terms")
        
        if metadata.key_amounts and case.case_type == CaseType.CIVIL:
            reasons.append("Financial amounts relevant to civil case")
        
        if not reasons:
            reasons.append(f"General similarity score: {similarity_score:.2f}")
        
        return "; ".join(reasons)
    
    def _suggest_actions(self, evidence: Evidence, case: Case, similarity_score: float) -> List[str]:
        """Suggest actions based on evidence-case association."""
        
        actions = []
        
        if similarity_score > 0.8:
            actions.append("Strong match - consider immediate association")
            actions.append("Prioritize processing for this case")
        elif similarity_score > 0.6:
            actions.append("Good match - review for association")
            actions.append("Consider case-specific processing")
        else:
            actions.append("Weak match - manual review recommended")
        
        if evidence.evidence_type in [EvidenceType.VIDEO, EvidenceType.AUDIO]:
            actions.append("Consider specialized processing for media content")
        
        if metadata.category == EvidenceCategory.WITNESS_STATEMENT:
            actions.append("Extract witness information for case timeline")
        
        return actions


class IntakeTriageAgent:
    """Main AI agent for evidence intake and triage."""
    
    def __init__(self, storage_service: StorageInterface, audit_logger: AuditLogger):
        self.storage_service = storage_service
        self.audit_logger = audit_logger
        self.classifier = EvidenceClassifier()
        self.duplicate_detector = DuplicateDetector()
        self.case_association_engine = CaseAssociationEngine()
        
        # Sandbox mode enforcement
        self.sandbox_only = True
    
    async def process_evidence_intake(self, evidence: Evidence, case_mode: str, 
                                    available_cases: List[Case] = None) -> Dict[str, Any]:
        """Process evidence intake with AI assistance."""
        
        # Enforce sandbox-only operation
        if not self.sandbox_only or case_mode != "SANDBOX":
            raise ValueError("AI agents only operate in Sandbox mode")
        
        logging.info(f"Processing evidence intake for {evidence.id}")
        
        # Get content preview
        content_preview = await self._get_content_preview(evidence)
        
        # Classify evidence
        metadata = await self.classifier.classify_evidence(evidence, content_preview)
        
        # Find duplicates
        if available_cases:
            all_evidence = []
            for case in available_cases:
                case_evidence = await self.storage_service.get_evidence_by_case(case.id)
                all_evidence.extend(case_evidence)
            
            duplicate_candidates = await self.duplicate_detector.find_duplicates(evidence, all_evidence)
            metadata.duplicate_candidates = duplicate_candidates
        
        # Suggest case associations
        case_associations = []
        if available_cases:
            case_associations = await self.case_association_engine.suggest_case_associations(
                evidence, metadata, available_cases
            )
        
        # Generate processing recommendations
        recommendations = self._generate_processing_recommendations(evidence, metadata)
        
        # Create intake report
        intake_report = {
            "evidence_id": evidence.id,
            "filename": evidence.filename,
            "metadata": {
                "category": metadata.category.value,
                "confidence_score": metadata.confidence_score,
                "key_entities": metadata.key_entities,
                "key_dates": metadata.key_dates,
                "key_amounts": metadata.key_amounts,
                "summary": metadata.summary,
                "suggested_tags": metadata.suggested_tags,
                "processing_priority": metadata.processing_priority.value,
                "estimated_processing_time": metadata.estimated_processing_time
            },
            "duplicate_analysis": {
                "potential_duplicates": metadata.duplicate_candidates,
                "is_likely_duplicate": len(metadata.duplicate_candidates) > 0
            },
            "case_associations": [
                {
                    "case_id": assoc.case_id,
                    "case_title": assoc.case_title,
                    "similarity_score": assoc.similarity_score,
                    "reasoning": assoc.reasoning,
                    "suggested_actions": assoc.suggested_actions
                }
                for assoc in case_associations
            ],
            "processing_recommendations": recommendations,
            "ai_confidence": self._calculate_overall_confidence(metadata, case_associations),
            "processing_timestamp": datetime.utcnow().isoformat()
        }
        
        # Log AI processing event
        self.audit_logger.log_event(
            AuditEventType.SYSTEM_ERROR,  # Using system event for AI processing
            {
                "action": "ai_evidence_intake_processed",
                "evidence_id": evidence.id,
                "ai_confidence": intake_report["ai_confidence"],
                "category": metadata.category.value,
                "duplicates_found": len(metadata.duplicate_candidates),
                "case_associations": len(case_associations)
            },
            case_id=evidence.case_id
        )
        
        return intake_report
    
    async def _get_content_preview(self, evidence: Evidence) -> str:
        """Get content preview for analysis."""
        
        try:
            if evidence.evidence_type == EvidenceType.TEXT:
                # Read text content
                content = await self.storage_service.read(evidence.file_path)
                return content.decode('utf-8')[:2000]  # Limit to 2000 chars
            
            elif evidence.evidence_type == EvidenceType.DOCUMENT:
                # Use existing OCR text if available
                if hasattr(evidence, 'ocr_text') and evidence.ocr_text:
                    return evidence.ocr_text[:2000]
                
                # Otherwise, try to extract text from file
                # This would use actual OCR in production
                return f"Document content preview for {evidence.filename}"
            
            elif evidence.evidence_type == EvidenceType.EMAIL:
                # Extract email content
                return f"Email content from {evidence.filename}"
            
            else:
                return f"Media content: {evidence.evidence_type.value}"
                
        except Exception as e:
            logging.error(f"Failed to get content preview: {e}")
            return ""
    
    def _generate_processing_recommendations(self, evidence: Evidence, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Generate processing recommendations."""
        
        recommendations = {
            "suggested_processors": [],
            "processing_order": [],
            "special_handling": [],
            "quality_checks": []
        }
        
        # Suggest processors based on evidence type and category
        if evidence.evidence_type == EvidenceType.DOCUMENT:
            recommendations["suggested_processors"].append("ocr_processor")
            if metadata.category == EvidenceCategory.FINANCIAL:
                recommendations["suggested_processors"].append("financial_extractor")
        
        elif evidence.evidence_type in [EvidenceType.AUDIO, EvidenceType.VIDEO]:
            recommendations["suggested_processors"].append("asr_processor")
            if metadata.category == EvidenceCategory.WITNESS_STATEMENT:
                recommendations["suggested_processors"].append("testimony_analyzer")
        
        # Determine processing order
        if metadata.processing_priority == ProcessingPriority.URGENT:
            recommendations["processing_order"].append("priority_queue")
        
        # Special handling recommendations
        if metadata.category == EvidenceCategory.MEDICAL:
            recommendations["special_handling"].append("hipaa_compliance_check")
        
        if metadata.key_amounts:
            recommendations["special_handling"].append("financial_validation")
        
        # Quality checks
        recommendations["quality_checks"].append("checksum_verification")
        recommendations["quality_checks"].append("content_validation")
        
        if metadata.duplicate_candidates:
            recommendations["quality_checks"].append("duplicate_review")
        
        return recommendations
    
    def _calculate_overall_confidence(self, metadata: EvidenceMetadata, case_associations: List[CaseAssociation]) -> float:
        """Calculate overall AI confidence score."""
        
        confidence_factors = []
        
        # Classification confidence
        confidence_factors.append(metadata.confidence_score)
        
        # Case association confidence
        if case_associations:
            avg_association_confidence = sum(assoc.similarity_score for assoc in case_associations) / len(case_associations)
            confidence_factors.append(avg_association_confidence)
        
        # Entity extraction confidence (placeholder)
        if metadata.key_entities:
            confidence_factors.append(0.8)
        
        # Date extraction confidence (placeholder)
        if metadata.key_dates:
            confidence_factors.append(0.7)
        
        # Return average confidence
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5


# Example usage and testing
async def main():
    """Example usage of the intake triage agent."""
    
    # Initialize services (would be injected in real implementation)
    storage_service = None  # StorageInterface implementation
    audit_logger = None     # AuditLogger implementation
    
    # Create agent
    agent = IntakeTriageAgent(storage_service, audit_logger)
    
    # Example evidence
    evidence = Evidence(
        id="evid-001",
        case_id="case-001",
        filename="contract_agreement.pdf",
        evidence_type=EvidenceType.DOCUMENT,
        file_path="/path/to/contract.pdf",
        sha256_hash="abc123"
    )
    
    # Example cases
    cases = [
        Case(
            id="case-001",
            title="Contract Dispute Case",
            case_type=CaseType.CIVIL,
            description="Dispute over contract terms and payment"
        )
    ]
    
    try:
        # Process evidence intake
        result = await agent.process_evidence_intake(evidence, "SANDBOX", cases)
        
        print("Intake Triage Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
