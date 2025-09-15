"""OCRMyPDF adapter implementation."""

import asyncio
import time
import tempfile
import os
import subprocess
from typing import List, Dict, Any

from ...interfaces.ocr import OCRInterface, OCRResult, OCRConfig, OCRError, UnsupportedFormatError


class OCRMyPDFAdapter(OCRInterface):
    """OCRMyPDF adapter implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OCRMyPDF adapter."""
        self.ocrmypdf_path = config.get("ocrmypdf_path", "ocrmypdf")
        self.language = config.get("language", "eng")
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.max_image_size = config.get("max_image_size", 10000000)
        
        # Verify ocrmypdf installation
        asyncio.create_task(self._verify_installation())
    
    async def _verify_installation(self) -> None:
        """Verify OCRMyPDF installation."""
        try:
            # Test ocrmypdf command
            result = subprocess.run(
                [self.ocrmypdf_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise OCRError(f"OCRMyPDF not found at {self.ocrmypdf_path}")
                
        except subprocess.TimeoutExpired:
            raise OCRError(f"OCRMyPDF command timeout")
        except FileNotFoundError:
            raise OCRError(f"OCRMyPDF not found at {self.ocrmypdf_path}")
    
    async def extract_text(
        self, 
        image_data: bytes, 
        config: OCRConfig
    ) -> OCRResult:
        """Extract text from image data."""
        # OCRMyPDF is primarily for PDF processing
        # For images, we would need to convert to PDF first
        raise OCRError("OCRMyPDF adapter requires PDF input for image processing")
    
    async def extract_text_from_pdf(
        self, 
        pdf_data: bytes, 
        config: OCRConfig
    ) -> List[OCRResult]:
        """Extract text from PDF document."""
        try:
            start_time = time.time()
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as input_file:
                input_file.write(pdf_data)
                input_file_path = input_file.name
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as output_file:
                output_file_path = output_file.name
            
            try:
                # Run OCRMyPDF
                cmd = [
                    self.ocrmypdf_path,
                    "--language", config.language or self.language,
                    "--max-image-mpixels", str(self.max_image_size),
                    "--force-ocr",
                    "--output-type", "pdf",
                    input_file_path,
                    output_file_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                if result.returncode != 0:
                    raise OCRError(f"OCRMyPDF failed: {result.stderr}")
                
                # Read the OCR'd PDF
                with open(output_file_path, 'rb') as f:
                    ocr_pdf_data = f.read()
                
                # Extract text from OCR'd PDF
                results = await self._extract_text_from_ocr_pdf(ocr_pdf_data, config)
                
                # Update processing time
                processing_time = int((time.time() - start_time) * 1000)
                for result in results:
                    result.processing_time_ms = processing_time
                    result.engine_used = "ocrmypdf"
                
                return results
                
            finally:
                # Clean up temporary files
                if os.path.exists(input_file_path):
                    os.unlink(input_file_path)
                if os.path.exists(output_file_path):
                    os.unlink(output_file_path)
            
        except Exception as e:
            raise OCRError(f"OCRMyPDF extraction failed: {e}")
    
    async def _extract_text_from_ocr_pdf(self, pdf_data: bytes, config: OCRConfig) -> List[OCRResult]:
        """Extract text from OCR'd PDF."""
        try:
            import fitz  # PyMuPDF
            
            # Open PDF
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            results = []
            
            for page_num in range(pdf_document.page_count):
                # Get page
                page = pdf_document[page_num]
                
                # Extract text
                text = page.get_text()
                
                # Get text blocks with positions
                blocks = page.get_text("dict")
                
                bounding_boxes = []
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                bbox = span["bbox"]
                                bounding_boxes.append({
                                    'x': int(bbox[0]),
                                    'y': int(bbox[1]),
                                    'width': int(bbox[2] - bbox[0]),
                                    'height': int(bbox[3] - bbox[1]),
                                    'text': span["text"]
                                })
                
                results.append(OCRResult(
                    text=text,
                    confidence=1.0,  # OCRMyPDF doesn't provide confidence scores
                    bounding_boxes=bounding_boxes,
                    page_number=page_num + 1,
                    language=config.language or self.language,
                    processing_time_ms=0,  # Will be updated by caller
                    engine_used="ocrmypdf"
                ))
            
            pdf_document.close()
            return results
            
        except ImportError:
            raise OCRError("PyMuPDF not installed for PDF text extraction")
        except Exception as e:
            raise OCRError(f"PDF text extraction failed: {e}")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        try:
            # Get available languages from tesseract (OCRMyPDF uses tesseract)
            result = subprocess.run(
                ["tesseract", "--list-langs"],
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
