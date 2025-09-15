"""Tesseract distributed OCR implementation."""

import asyncio
import time
import json
from typing import List, Dict, Any
from urllib.parse import urljoin

from ...interfaces.ocr import OCRInterface, OCRResult, OCRConfig, OCRError, TranscriptionError
from ...http_client import get_http_client


class TesseractDistributedOCR(OCRInterface):
    """Tesseract distributed OCR implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Tesseract distributed OCR."""
        self.worker_endpoints = config.get("worker_endpoints", [])
        self.timeout = config.get("timeout", 300)
        self.language = config.get("language", "eng")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.preprocess = config.get("preprocess", True)
        self.deskew = config.get("deskew", True)
        self.denoise = config.get("denoise", True)
        
        if not self.worker_endpoints:
            raise OCRError("No worker endpoints provided")
        
        # Current worker index for round-robin
        self.current_worker = 0
        
        # Get shared HTTP client
        self.client = get_http_client()
    
    def _get_next_worker(self) -> str:
        """Get next worker endpoint based on round-robin."""
        worker = self.worker_endpoints[self.current_worker]
        self.current_worker = (self.current_worker + 1) % len(self.worker_endpoints)
        return worker
    
    async def _call_worker(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call worker endpoint."""
        try:
            response = await self.client.post(
                urljoin(endpoint, "/ocr"),
                json=data,
                timeout=self.timeout
            )
            return response
            
        except Exception as e:
            raise OCRError(f"Worker call failed: {e}")
    
    async def extract_text(
        self, 
        image_data: bytes, 
        config: OCRConfig
    ) -> OCRResult:
        """Extract text from image data."""
        try:
            start_time = time.time()
            
            # Prepare request data
            import base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            request_data = {
                "image_data": image_b64,
                "language": config.language or self.language,
                "confidence_threshold": self.confidence_threshold,
                "preprocess": self.preprocess,
                "deskew": self.deskew,
                "denoise": self.denoise
            }
            
            # Call worker
            worker_endpoint = self._get_next_worker()
            result = await self._call_worker(worker_endpoint, request_data)
            
            return OCRResult(
                text=result.get("text", ""),
                confidence=result.get("confidence", 0.0),
                bounding_boxes=result.get("bounding_boxes", []),
                page_number=1,
                language=config.language or self.language,
                processing_time_ms=int((time.time() - start_time) * 1000),
                engine_used="tesseract_distributed"
            )
            
        except Exception as e:
            raise OCRError(f"Distributed OCR extraction failed: {e}")
    
    async def extract_text_from_pdf(
        self, 
        pdf_data: bytes, 
        config: OCRConfig
    ) -> List[OCRResult]:
        """Extract text from PDF document."""
        try:
            start_time = time.time()
            
            # Prepare request data
            import base64
            pdf_b64 = base64.b64encode(pdf_data).decode('utf-8')
            
            request_data = {
                "pdf_data": pdf_b64,
                "language": config.language or self.language,
                "confidence_threshold": self.confidence_threshold,
                "preprocess": self.preprocess,
                "deskew": self.deskew,
                "denoise": self.denoise
            }
            
            # Call worker
            worker_endpoint = self._get_next_worker()
            result = await self._call_worker(worker_endpoint, request_data)
            
            # Convert results
            results = []
            for page_result in result.get("pages", []):
                results.append(OCRResult(
                    text=page_result.get("text", ""),
                    confidence=page_result.get("confidence", 0.0),
                    bounding_boxes=page_result.get("bounding_boxes", []),
                    page_number=page_result.get("page_number", 1),
                    language=config.language or self.language,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    engine_used="tesseract_distributed"
                ))
            
            return results
            
        except Exception as e:
            raise OCRError(f"Distributed PDF OCR extraction failed: {e}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        try:
            # Try to get from first worker
            worker_endpoint = self.worker_endpoints[0]
            response = await self.client.get(
                urljoin(worker_endpoint, "/languages"),
                timeout=30
            )
            return response.get("languages", [])
            
        except Exception:
            # Fallback to common languages
            return ["eng", "spa", "fra", "deu", "ita", "por", "rus", "jpn", "kor", "chi_sim"]
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Shared HTTP client doesn't need to be closed here
        pass
