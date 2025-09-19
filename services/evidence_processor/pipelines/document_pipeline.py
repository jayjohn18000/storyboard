"""Document processing pipeline for evidence."""

import time
from typing import Dict, Any, Optional, List
from ...shared.interfaces.storage import StorageInterface
from ...shared.interfaces.ocr import OCRInterface, OCRConfig
from ...shared.models.evidence import Evidence, EvidenceStatus, ProcessingResult
from ...shared.utils.crypto import CryptoUtils


class DocumentPipeline:
    """Pipeline for processing document evidence."""
    
    def __init__(self, storage_service: StorageInterface, ocr_service: OCRInterface):
        self.storage_service = storage_service
        self.ocr_service = ocr_service
    
    async def process_document(self, evidence_id: str) -> Dict[str, Any]:
        """Process document evidence."""
        try:
            # Get evidence from storage
            evidence_data = await self.storage_service.get_evidence(evidence_id)
            
            # Determine document type and processing strategy
            document_type = self._detect_document_type(evidence_data)
            
            # Process based on type
            if document_type == "pdf":
                result = await self._process_pdf(evidence_data)
            elif document_type in ["image"]:
                result = await self._process_image(evidence_data)
            else:
                result = await self._process_text(evidence_data)
            
            # Create processing result
            processing_result = ProcessingResult(
                ocr_text=result.get("text", ""),
                extracted_entities=result.get("entities", []),
                confidence_scores=result.get("confidence", {}),
                processing_time_ms=result.get("processing_time_ms", 0),
                engine_used=result.get("engine_used", "unknown")
            )
            
            return {
                "evidence_id": evidence_id,
                "status": "processed",
                "processing_result": processing_result.to_dict(),
                "document_type": document_type,
                "processing_time_ms": processing_result.processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Document processing failed: {str(e)}")
    
    def _detect_document_type(self, data: bytes) -> str:
        """Detect document type from data."""
        # Simple detection based on file headers
        if data.startswith(b'%PDF'):
            return "pdf"
        elif data.startswith(b'\xff\xd8\xff'):
            return "image"  # JPEG
        elif data.startswith(b'\x89PNG'):
            return "image"  # PNG
        elif data.startswith(b'BM'):
            return "image"  # BMP
        elif data.startswith(b'GIF'):
            return "image"  # GIF
        else:
            return "text"
    
    async def _process_pdf(self, pdf_data: bytes) -> Dict[str, Any]:
        """Process PDF document."""
        start_time = time.time()
        
        try:
            # Configure OCR
            ocr_config = OCRConfig(
                language="eng",
                confidence_threshold=0.7,
                preprocess=True,
                deskew=True,
                denoise=True
            )
            
            # Extract text from PDF
            ocr_results = await self.ocr_service.extract_text_from_pdf(pdf_data, ocr_config)
            
            # Combine text from all pages
            full_text = "\n".join([result.text for result in ocr_results])
            
            # Calculate average confidence
            avg_confidence = sum(result.confidence for result in ocr_results) / len(ocr_results) if ocr_results else 0.0
            
            # Extract entities (simplified)
            entities = self._extract_entities(full_text)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "text": full_text,
                "entities": entities,
                "confidence": {"ocr": avg_confidence},
                "processing_time_ms": processing_time_ms,
                "engine_used": "tesseract_local",
                "pages_processed": len(ocr_results)
            }
            
        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")
    
    async def _process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Process image document."""
        start_time = time.time()
        
        try:
            # Configure OCR
            ocr_config = OCRConfig(
                language="eng",
                confidence_threshold=0.7,
                preprocess=True,
                deskew=True,
                denoise=True
            )
            
            # Extract text from image
            ocr_result = await self.ocr_service.extract_text(image_data, ocr_config)
            
            # Extract entities (simplified)
            entities = self._extract_entities(ocr_result.text)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "text": ocr_result.text,
                "entities": entities,
                "confidence": {"ocr": ocr_result.confidence},
                "processing_time_ms": processing_time_ms,
                "engine_used": "tesseract_local"
            }
            
        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")
    
    async def _process_text(self, text_data: bytes) -> Dict[str, Any]:
        """Process text document."""
        start_time = time.time()
        
        try:
            # Decode text
            text = text_data.decode('utf-8', errors='ignore')
            
            # Extract entities (simplified)
            entities = self._extract_entities(text)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "text": text,
                "entities": entities,
                "confidence": {"text": 1.0},
                "processing_time_ms": processing_time_ms,
                "engine_used": "text_parser"
            }
            
        except Exception as e:
            raise Exception(f"Text processing failed: {str(e)}")
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text (simplified implementation)."""
        entities = []
        
        # Simple entity extraction
        # In production, you would use more sophisticated NLP libraries
        
        # Extract dates (simple pattern)
        import re
        date_pattern = r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b'
        dates = re.findall(date_pattern, text)
        for date in dates:
            entities.append({
                "type": "DATE",
                "value": date,
                "confidence": 0.8
            })
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email in emails:
            entities.append({
                "type": "EMAIL",
                "value": email,
                "confidence": 0.9
            })
        
        # Extract phone numbers
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b'
        phones = re.findall(phone_pattern, text)
        for phone in phones:
            entities.append({
                "type": "PHONE",
                "value": phone,
                "confidence": 0.8
            })
        
        return entities
