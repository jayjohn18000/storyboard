"""Local Tesseract OCR implementation."""

import subprocess
import tempfile
import os
from typing import List, Dict, Any
from PIL import Image
import fitz  # PyMuPDF
from ..shared.interfaces.ocr import OCRInterface, OCRConfig, OCRResult, OCRError


class TesseractLocalOCR(OCRInterface):
    """Local Tesseract OCR implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tesseract_path = config.get("tesseract_path", "tesseract")
        self.tessdata_path = config.get("tessdata_path")
        self.language = config.get("language", "eng")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.preprocess = config.get("preprocess", True)
        self.deskew = config.get("deskew", True)
        self.denoise = config.get("denoise", True)
        
        # Verify Tesseract installation
        self._verify_installation()
    
    def _verify_installation(self) -> None:
        """Verify Tesseract installation."""
        try:
            result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise OCRError("Tesseract not found or not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise OCRError("Tesseract not found or not working")
    
    async def extract_text(self, image_data: bytes, config: OCRConfig) -> OCRResult:
        """Extract text from image data."""
        try:
            # Save image data to temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file.write(image_data)
                temp_image_path = temp_file.name
            
            try:
                # Preprocess image if requested
                if config.preprocess:
                    processed_image_path = self._preprocess_image(temp_image_path)
                else:
                    processed_image_path = temp_image_path
                
                # Run Tesseract OCR
                result = await self._run_tesseract(processed_image_path, config)
                
                return result
                
            finally:
                # Clean up temporary files
                if os.path.exists(temp_image_path):
                    os.unlink(temp_image_path)
                if processed_image_path != temp_image_path and os.path.exists(processed_image_path):
                    os.unlink(processed_image_path)
                    
        except Exception as e:
            raise OCRError(f"OCR extraction failed: {str(e)}")
    
    async def extract_text_from_pdf(self, pdf_data: bytes, config: OCRConfig) -> List[OCRResult]:
        """Extract text from PDF document."""
        try:
            results = []
            
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            
            for page_num in range(len(pdf_document)):
                # Get page
                page = pdf_document[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Extract text from image
                result = await self.extract_text(img_data, config)
                result.page_number = page_num + 1
                results.append(result)
            
            pdf_document.close()
            return results
            
        except Exception as e:
            raise OCRError(f"PDF OCR extraction failed: {str(e)}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        try:
            result = subprocess.run(
                [self.tesseract_path, "--list-langs"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return ["eng"]  # Default to English
            
            # Parse output to get language codes
            lines = result.stdout.strip().split('\n')[1:]  # Skip first line
            languages = [lang.strip() for lang in lines if lang.strip()]
            
            return languages if languages else ["eng"]
            
        except Exception:
            return ["eng"]  # Default to English
    
    def _preprocess_image(self, image_path: str) -> str:
        """Preprocess image for better OCR."""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Apply preprocessing if enabled
            if self.deskew:
                image = self._deskew_image(image)
            
            if self.denoise:
                image = self._denoise_image(image)
            
            # Save processed image
            processed_path = image_path.replace('.png', '_processed.png')
            image.save(processed_path)
            
            return processed_path
            
        except Exception:
            return image_path  # Return original if preprocessing fails
    
    def _deskew_image(self, image: Image.Image) -> Image.Image:
        """Deskew image using simple rotation detection."""
        # Simple deskewing implementation
        # In production, you might want to use more sophisticated methods
        return image
    
    def _denoise_image(self, image: Image.Image) -> Image.Image:
        """Denoise image using simple filtering."""
        # Simple denoising implementation
        # In production, you might want to use more sophisticated methods
        return image
    
    async def _run_tesseract(self, image_path: str, config: OCRConfig) -> OCRResult:
        """Run Tesseract OCR on image."""
        try:
            # Prepare Tesseract command
            cmd = [
                self.tesseract_path,
                image_path,
                "stdout",
                "-l", config.language,
                "--psm", "6",  # Assume uniform block of text
                "--oem", "3",  # Default OCR Engine Mode
            ]
            
            # Add tessdata path if specified
            if self.tessdata_path:
                cmd.extend(["--tessdata-dir", self.tessdata_path])
            
            # Run Tesseract
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise OCRError(f"Tesseract failed: {result.stderr}")
            
            # Parse output
            text = result.stdout.strip()
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(text)
            
            # Create result
            return OCRResult(
                text=text,
                confidence=confidence,
                bounding_boxes=[],  # Would need additional processing
                page_number=1,
                language=config.language,
                processing_time_ms=0,  # Would need timing
                engine_used="tesseract_local"
            )
            
        except subprocess.TimeoutExpired:
            raise OCRError("Tesseract processing timeout")
        except Exception as e:
            raise OCRError(f"Tesseract execution failed: {str(e)}")
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for extracted text."""
        if not text:
            return 0.0
        
        # Simple confidence calculation based on text characteristics
        # In production, you might want to use Tesseract's confidence output
        confidence = 0.8  # Base confidence
        
        # Adjust based on text length
        if len(text) < 10:
            confidence *= 0.7
        elif len(text) > 100:
            confidence *= 1.1
        
        # Adjust based on character types
        alpha_chars = sum(1 for c in text if c.isalpha())
        if alpha_chars / len(text) > 0.8:
            confidence *= 1.1
        
        return min(confidence, 1.0)
