"""PaddleOCR adapter implementation."""

import asyncio
import time
from typing import List, Dict, Any
import cv2
import numpy as np
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

from ...interfaces.ocr import OCRInterface, OCRResult, OCRConfig, OCRError, UnsupportedFormatError


class PaddleOCRAdapter(OCRInterface):
    """PaddleOCR adapter implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize PaddleOCR adapter."""
        if not PADDLEOCR_AVAILABLE:
            raise OCRError("PaddleOCR is not available. Please install paddleocr.")
        
        self.language = config.get("language", "en")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.use_gpu = config.get("use_gpu", False)
        self.use_angle_cls = config.get("use_angle_cls", True)
        self.use_text_detection = config.get("use_text_detection", True)
        
        # Initialize PaddleOCR
        asyncio.create_task(self._initialize_ocr())
    
    async def _initialize_ocr(self) -> None:
        """Initialize PaddleOCR."""
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=self.use_angle_cls,
                lang=self.language,
                use_gpu=self.use_gpu,
                show_log=False
            )
        except Exception as e:
            raise OCRError(f"Failed to initialize PaddleOCR: {e}")
    
    async def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    
    async def extract_text(
        self, 
        image_data: bytes, 
        config: OCRConfig
    ) -> OCRResult:
        """Extract text from image data."""
        try:
            start_time = time.time()
            
            # Load image
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise UnsupportedFormatError("Invalid image format")
            
            # Preprocess image
            processed_image = await self._preprocess_image(image)
            
            # Run OCR
            results = self.ocr.ocr(processed_image, cls=self.use_angle_cls)
            
            # Process results
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            if results and results[0]:
                for line in results[0]:
                    if line:
                        # Extract text and confidence
                        text_info = line[1]
                        text = text_info[0]
                        confidence = text_info[1]
                        
                        # Extract bounding box
                        bbox = line[0]
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]
                        
                        x_min, x_max = min(x_coords), max(x_coords)
                        y_min, y_max = min(y_coords), max(y_coords)
                        
                        if confidence >= self.confidence_threshold:
                            text_parts.append(text)
                            confidences.append(confidence)
                            bounding_boxes.append({
                                'x': int(x_min),
                                'y': int(y_min),
                                'width': int(x_max - x_min),
                                'height': int(y_max - y_min),
                                'text': text
                            })
            
            # Combine text
            full_text = ' '.join(text_parts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                page_number=1,
                language=config.language or self.language,
                processing_time_ms=int((time.time() - start_time) * 1000),
                engine_used="paddleocr"
            )
            
        except Exception as e:
            raise OCRError(f"PaddleOCR extraction failed: {e}")
    
    async def extract_text_from_pdf(
        self, 
        pdf_data: bytes, 
        config: OCRConfig
    ) -> List[OCRResult]:
        """Extract text from PDF document."""
        try:
            import fitz  # PyMuPDF
            
            # Open PDF
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            results = []
            
            for page_num in range(pdf_document.page_count):
                start_time = time.time()
                
                # Get page
                page = pdf_document[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Extract text from image
                result = await self.extract_text(img_data, config)
                
                # Update page number
                result.page_number = page_num + 1
                result.processing_time_ms = int((time.time() - start_time) * 1000)
                
                results.append(result)
            
            pdf_document.close()
            return results
            
        except ImportError:
            raise OCRError("PyMuPDF not installed for PDF processing")
        except Exception as e:
            raise OCRError(f"PDF OCR extraction failed: {e}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "en", "ch", "ta", "te", "ka", "ja", "ko", "hi", "mr", "ne",
            "ur", "fa", "ar", "uk", "be", "te", "kn", "ml", "th", "my",
            "km", "lo", "vi", "ms", "tl", "id", "bn", "gu", "pa", "or",
            "as", "si", "my", "km", "lo", "vi", "ms", "tl", "id", "bn"
        ]
