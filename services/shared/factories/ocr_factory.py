"""Factory for creating OCR service implementations."""

from typing import Dict, Any, Optional
from ..interfaces.ocr import OCRInterface, OCREngine, OCRError
from ..implementations.ocr.tesseract_local import TesseractLocalOCR
from ..implementations.ocr.tesseract_distributed import TesseractDistributedOCR
from ..implementations.ocr.ocrmypdf_adapter import OCRMyPDFAdapter
from ..implementations.ocr.paddleocr_adapter import PaddleOCRAdapter


class OCRFactory:
    """Factory for creating OCR service instances."""
    
    _implementations: Dict[OCREngine, type] = {
        OCREngine.TESSERACT_LOCAL: TesseractLocalOCR,
        OCREngine.TESSERACT_DISTRIBUTED: TesseractDistributedOCR,
        OCREngine.OCRMYPDF: OCRMyPDFAdapter,
        OCREngine.PADDLEOCR: PaddleOCRAdapter,
    }
    
    @classmethod
    def create_ocr(
        cls, 
        engine: OCREngine, 
        config: Dict[str, Any]
    ) -> OCRInterface:
        """Create OCR service instance."""
        if engine not in cls._implementations:
            raise OCRError(f"Unsupported OCR engine: {engine}")
        
        implementation_class = cls._implementations[engine]
        return implementation_class(config)
    
    @classmethod
    def create_from_env(cls, env_config: Dict[str, str]) -> OCRInterface:
        """Create OCR service from environment configuration."""
        engine_str = env_config.get("OCR_ENGINE", "tesseract_local")
        
        try:
            engine = OCREngine(engine_str)
        except ValueError:
            raise OCRError(f"Invalid OCR engine: {engine_str}")
        
        config = cls._build_config(engine, env_config)
        return cls.create_ocr(engine, config)
    
    @classmethod
    def _build_config(cls, engine: OCREngine, env_config: Dict[str, str]) -> Dict[str, Any]:
        """Build configuration for OCR engine."""
        base_config = {
            "language": env_config.get("TESSERACT_LANG", "eng"),
            "confidence_threshold": float(env_config.get("OCR_CONFIDENCE_THRESHOLD", "0.7")),
            "preprocess": env_config.get("OCR_PREPROCESS", "true").lower() == "true",
            "deskew": env_config.get("OCR_DESKEW", "true").lower() == "true",
            "denoise": env_config.get("OCR_DENOISE", "true").lower() == "true",
        }
        
        if engine == OCREngine.TESSERACT_LOCAL:
            return {
                **base_config,
                "tesseract_path": env_config.get("TESSERACT_PATH", "tesseract"),
                "tessdata_path": env_config.get("TESSDATA_PATH"),
            }
        
        elif engine == OCREngine.TESSERACT_DISTRIBUTED:
            return {
                **base_config,
                "worker_endpoints": env_config.get("TESSERACT_WORKERS", "").split(","),
                "timeout": int(env_config.get("TESSERACT_TIMEOUT", "300")),
            }
        
        elif engine == OCREngine.OCRMYPDF:
            return {
                **base_config,
                "ocrmypdf_path": env_config.get("OCRMYPDF_PATH", "ocrmypdf"),
                "max_image_size": int(env_config.get("OCR_MAX_IMAGE_SIZE", "10000000")),
            }
        
        elif engine == OCREngine.PADDLEOCR:
            return {
                **base_config,
                "use_gpu": env_config.get("PADDLEOCR_USE_GPU", "false").lower() == "true",
                "use_angle_cls": env_config.get("PADDLEOCR_USE_ANGLE_CLS", "true").lower() == "true",
                "use_text_detection": env_config.get("PADDLEOCR_USE_TEXT_DETECTION", "true").lower() == "true",
            }
        
        else:
            raise OCRError(f"Configuration not implemented for {engine}")
    
    @classmethod
    def register_implementation(
        cls, 
        engine: OCREngine, 
        implementation_class: type
    ) -> None:
        """Register custom OCR implementation."""
        cls._implementations[engine] = implementation_class
