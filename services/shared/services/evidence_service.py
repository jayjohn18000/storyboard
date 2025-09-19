"""Evidence service for managing evidence files and processing."""

import logging
import hashlib
from typing import List, Optional, Dict, Any, BinaryIO
from datetime import datetime
import uuid

from ..models.database_models import Evidence as DBEvidence
from ..models.evidence import Evidence, EvidenceType, EvidenceStatus, EvidenceMetadata, ProcessingResult
from ..interfaces.storage import StorageInterface
from ..factories.storage_factory import StorageFactory
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class EvidenceService:
    """Service for managing evidence files and processing."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.storage: StorageInterface = StorageFactory.create_storage()
    
    async def store_evidence(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        evidence_type: EvidenceType,
        case_id: str,
        uploaded_by: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Evidence:
        """Store evidence file and create evidence record."""
        try:
            # Generate evidence ID
            evidence_id = str(uuid.uuid4())
            
            # Calculate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Create evidence metadata
            metadata = EvidenceMetadata(
                filename=filename,
                file_size=len(file_data),
                content_type=mime_type,
                checksum=file_hash,
                uploaded_at=datetime.utcnow(),
                description=description or "",
                tags=tags or {}
            )
            
            # Create evidence model
            evidence = Evidence(
                id=evidence_id,
                evidence_type=evidence_type,
                metadata=metadata,
                status=EvidenceStatus.UPLOADED,
                case_id=case_id
            )
            
            # Add initial custody entry
            evidence.add_custody_entry("UPLOADED", uploaded_by)
            
            # Store file in storage
            storage_metadata = {
                "content_type": mime_type,
                "filename": filename,
                "evidence_type": evidence_type.value,
                "case_id": case_id,
                "uploaded_by": uploaded_by,
                "tags": tags or {}
            }
            
            storage_id = await self.storage.store_evidence(
                file_data, 
                storage_metadata, 
                evidence_id
            )
            evidence.storage_id = storage_id
            
            # Save to database
            db_evidence = await self.db_service.create_evidence(
                case_id=case_id,
                filename=filename,
                file_path=storage_id,
                file_size=len(file_data),
                mime_type=mime_type,
                file_hash=file_hash,
                uploaded_by=uploaded_by,
                case_metadata={
                    "evidence_type": evidence_type.value,
                    "description": description or "",
                    "tags": tags or {},
                    "chain_of_custody": evidence.chain_of_custody
                }
            )
            
            # Update evidence with database ID
            evidence.id = str(db_evidence.id)
            
            logger.info(f"Stored evidence {evidence.id} for case {case_id}")
            return evidence
            
        except Exception as e:
            logger.error(f"Failed to store evidence: {e}")
            raise
    
    async def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        try:
            db_evidence = await self.db_service.get_evidence(evidence_id)
            if not db_evidence:
                return None
            
            # Convert database model to Evidence
            case_metadata = db_evidence.case_metadata or {}
            processing_results = db_evidence.processing_results or {}
            
            evidence = Evidence(
                id=str(db_evidence.id),
                evidence_type=EvidenceType(case_metadata.get("evidence_type", "document")),
                metadata=EvidenceMetadata(
                    filename=db_evidence.filename,
                    file_size=db_evidence.file_size,
                    content_type=db_evidence.mime_type,
                    checksum=db_evidence.file_hash,
                    uploaded_at=db_evidence.uploaded_at,
                    description=case_metadata.get("description", ""),
                    tags=case_metadata.get("tags", {})
                ),
                status=EvidenceStatus(db_evidence.status),
                storage_id=db_evidence.file_path,
                case_id=str(db_evidence.case_id),
                chain_of_custody=case_metadata.get("chain_of_custody", []),
                worm_locked=case_metadata.get("worm_locked", False),
                processing_result=ProcessingResult(**processing_results) if processing_results else None
            )
            
            return evidence
            
        except Exception as e:
            logger.error(f"Failed to get evidence {evidence_id}: {e}")
            return None
    
    async def list_evidence(
        self,
        case_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[EvidenceStatus] = None
    ) -> List[Evidence]:
        """List evidence with optional filtering."""
        try:
            db_evidence_list = await self.db_service.list_evidence(
                case_id=case_id,
                skip=skip,
                limit=limit,
                status_filter=status_filter.value if status_filter else None
            )
            
            evidence_list = []
            for db_evidence in db_evidence_list:
                case_metadata = db_evidence.case_metadata or {}
                processing_results = db_evidence.processing_results or {}
                
                evidence = Evidence(
                    id=str(db_evidence.id),
                    evidence_type=EvidenceType(case_metadata.get("evidence_type", "document")),
                    metadata=EvidenceMetadata(
                        filename=db_evidence.filename,
                        file_size=db_evidence.file_size,
                        content_type=db_evidence.mime_type,
                        checksum=db_evidence.file_hash,
                        uploaded_at=db_evidence.uploaded_at,
                        description=case_metadata.get("description", ""),
                        tags=case_metadata.get("tags", {})
                    ),
                    status=EvidenceStatus(db_evidence.status),
                    storage_id=db_evidence.file_path,
                    case_id=str(db_evidence.case_id),
                    chain_of_custody=case_metadata.get("chain_of_custody", []),
                    worm_locked=case_metadata.get("worm_locked", False),
                    processing_result=ProcessingResult(**processing_results) if processing_results else None
                )
                evidence_list.append(evidence)
            
            return evidence_list
            
        except Exception as e:
            logger.error(f"Failed to list evidence: {e}")
            return []
    
    async def update_evidence(self, evidence_id: str, **kwargs) -> Optional[Evidence]:
        """Update evidence."""
        try:
            # Update database
            updated_evidence = await self.db_service.update_evidence(evidence_id, **kwargs)
            if not updated_evidence:
                return None
            
            # Get updated evidence
            return await self.get_evidence(evidence_id)
            
        except Exception as e:
            logger.error(f"Failed to update evidence {evidence_id}: {e}")
            return None
    
    async def delete_evidence(self, evidence_id: str) -> bool:
        """Delete evidence."""
        try:
            # Get evidence first to get storage ID
            evidence = await self.get_evidence(evidence_id)
            if not evidence:
                return False
            
            # Delete from storage
            try:
                await self.storage.delete_evidence(evidence.storage_id)
            except Exception as e:
                logger.warning(f"Failed to delete evidence from storage: {e}")
            
            # Delete from database
            success = await self.db_service.delete_evidence(evidence_id)
            
            logger.info(f"Deleted evidence {evidence_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete evidence {evidence_id}: {e}")
            return False
    
    async def download_evidence(self, evidence_id: str) -> Optional[bytes]:
        """Download evidence file."""
        try:
            evidence = await self.get_evidence(evidence_id)
            if not evidence:
                return None
            
            # Get file from storage
            file_data = await self.storage.get_evidence(evidence.storage_id)
            
            # Add custody entry
            evidence.add_custody_entry("DOWNLOADED", "system")
            await self.update_evidence(
                evidence_id,
                case_metadata={
                    **evidence.to_dict().get("case_metadata", {}),
                    "chain_of_custody": evidence.chain_of_custody
                }
            )
            
            return file_data
            
        except Exception as e:
            logger.error(f"Failed to download evidence {evidence_id}: {e}")
            return None
    
    async def process_evidence(self, evidence_id: str) -> bool:
        """Process evidence (OCR, ASR, etc.)."""
        try:
            evidence = await self.get_evidence(evidence_id)
            if not evidence:
                return False
            
            # Update status to processing
            await self.update_evidence(
                evidence_id,
                status="processing",
                case_metadata={
                    **evidence.to_dict().get("case_metadata", {}),
                    "processing_started_at": datetime.utcnow().isoformat()
                }
            )
            
            # TODO: Integrate with evidence processor service
            # This would typically involve:
            # 1. Sending evidence to processing queue
            # 2. Processing service handles OCR/ASR/etc.
            # 3. Results are stored back in processing_results
            
            # For now, simulate processing
            processing_result = ProcessingResult(
                confidence_scores={"overall": 0.95},
                extracted_text="Sample extracted text",
                processing_time_ms=1500,
                engine_used="mock_processor"
            )
            
            evidence.mark_processed(processing_result)
            
            # Update database with results
            await self.update_evidence(
                evidence_id,
                status="processed",
                processing_results=processing_result.to_dict(),
                case_metadata={
                    **evidence.to_dict().get("case_metadata", {}),
                    "processing_completed_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Processed evidence {evidence_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process evidence {evidence_id}: {e}")
            # Mark as failed
            await self.update_evidence(
                evidence_id,
                status="failed",
                case_metadata={
                    **evidence.to_dict().get("case_metadata", {}),
                    "processing_error": str(e),
                    "processing_failed_at": datetime.utcnow().isoformat()
                }
            )
            return False
    
    async def apply_worm_lock(self, evidence_id: str) -> bool:
        """Apply WORM lock to evidence."""
        try:
            evidence = await self.get_evidence(evidence_id)
            if not evidence:
                return False
            
            # Apply WORM lock in storage
            success = await self.storage.ensure_worm_lock(evidence.storage_id)
            if not success:
                return False
            
            # Update evidence
            evidence.apply_worm_lock()
            
            await self.update_evidence(
                evidence_id,
                case_metadata={
                    **evidence.to_dict().get("case_metadata", {}),
                    "worm_locked": True,
                    "chain_of_custody": evidence.chain_of_custody
                }
            )
            
            logger.info(f"Applied WORM lock to evidence {evidence_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply WORM lock to evidence {evidence_id}: {e}")
            return False
