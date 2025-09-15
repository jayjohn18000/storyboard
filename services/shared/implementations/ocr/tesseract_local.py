"""Tesseract local OCR implementation."""

import asyncio
import time
import tempfile
import os
import subprocess
from typing import List, Dict, Any
import cv2
import numpy as np
from PIL import Image
import pytesseract

from ...interfaces.ocr import OCRInterface, OCRResult, OCRConfig, OCRError, UnsupportedFormatError, LanguageNotSupportedError


class TesseractLocalOCR(OCRInterface):
    """Tesseract local OCR implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Tesseract local OCR."""
        self.tesseract_path = config.get("tesseract_path", "tesseract")
        self.tessdata_path = config.get("tessdata_path")
        self.language = config.get("language", "eng")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.preprocess = config.get("preprocess", True)
        self.deskew = config.get("deskew", True)
        self.denoise = config.get("denoise", True)
        
        # Set tesseract path if provided
        if self.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # Set tessdata path if provided
        if self.tessdata_path:
            os.environ['TESSDATA_PREFIX'] = self.tessdata_path
        
        # Verify tesseract installation
        asyncio.create_task(self._verify_installation())
    
    async def _verify_installation(self) -> None:
        """Verify Tesseract installation."""
        try:
            # Test tesseract command
            result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise OCRError(f"Tesseract not found at {self.tesseract_path}")
                
        except subprocess.TimeoutExpired:
            raise OCRError(f"Tesseract command timeout")
        except FileNotFoundError:
            raise OCRError(f"Tesseract not found at {self.tesseract_path}")
    
    async def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        if not self.preprocess:
            return image
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise if enabled
        if self.denoise:
            gray = cv2.medianBlur(gray, 3)
        
        # Deskew if enabled
        if self.deskew:
            gray = self._deskew_image(gray)
        
        # Enhance contrast
        gray = cv2.equalizeHist(gray)
        
        # Apply threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image using Hough transform."""
        try:
            # Find edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Find lines
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Calculate average angle
                angles = []
                for line in lines:
                    rho, theta = line[0]
                    angle = theta * 180 / np.pi
                    if angle > 90:
                        angle -= 180
                    angles.append(angle)
                
                if angles:
                    avg_angle = np.mean(angles)
                    
                    # Rotate image
                    if abs(avg_angle) > 0.5:  # Only rotate if significant skew
                        h, w = image.shape
                        center = (w // 2, h // 2)
                        rotation_matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                        image = cv2.warpAffine(image, rotation_matrix, (w, h))
            
            return image
            
        except Exception:
            # If deskewing fails, return original image
            return image
    
    async def _image_to_bytes(self, image: np.ndarray) -> bytes:
        """Convert image array to bytes."""
        # Convert to PIL Image
        if len(image.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image)
        
        # Convert to bytes
        import io
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
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
            
            # Convert to PIL Image for tesseract
            pil_image = Image.fromarray(processed_image)
            
            # Configure tesseract
            tesseract_config = f'--oem 3 --psm 6 -l {config.language or self.language}'
            
            # Extract text with confidence
            data = pytesseract.image_to_data(
                pil_image,
                config=tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Process results
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # Valid text
                    text = data['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(int(data['conf'][i]) / 100.0)
                        bounding_boxes.append({
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i],
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
                engine_used="tesseract_local"
            )
            
        except Exception as e:
            raise OCRError(f"OCR extraction failed: {e}")
    
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
        try:
            # Get available languages from tesseract
            result = subprocess.run(
                [self.tesseract_path, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip first line
                return [lang.strip() for lang in lines if lang.strip()]
            else:
                # Fallback to common languages
                return ["eng", "spa", "fra", "deu", "ita", "por", "rus", "jpn", "kor", "chi_sim"]
                
        except Exception:
            # Fallback to common languages
            return ["eng", "spa", "fra", "deu", "ita", "por", "rus", "jpn", "kor", "chi_sim"]
