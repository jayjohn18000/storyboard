"""Video processing pipeline for evidence."""

import time
from typing import Dict, Any, List
from ..shared.interfaces.storage import StorageInterface
from ..shared.interfaces.ocr import OCRInterface, OCRConfig
from ..shared.interfaces.asr import ASRInterface, ASRConfig
from ..shared.models.evidence import Evidence, EvidenceStatus, ProcessingResult


class VideoPipeline:
    """Pipeline for processing video evidence."""
    
    def __init__(self, storage_service: StorageInterface, ocr_service: OCRInterface, asr_service: ASRInterface):
        self.storage_service = storage_service
        self.ocr_service = ocr_service
        self.asr_service = asr_service
    
    async def process_video(self, evidence_id: str) -> Dict[str, Any]:
        """Process video evidence."""
        try:
            # Get evidence from storage
            video_data = await self.storage_service.get_evidence(evidence_id)
            
            # Detect video format
            video_format = self._detect_video_format(video_data)
            
            # Process video
            result = await self._process_video_data(video_data, video_format)
            
            # Create processing result
            processing_result = ProcessingResult(
                ocr_text=result.get("ocr_text", ""),
                asr_transcript=result.get("asr_transcript", ""),
                extracted_entities=result.get("entities", []),
                confidence_scores=result.get("confidence", {}),
                processing_time_ms=result.get("processing_time_ms", 0),
                engine_used=result.get("engine_used", "unknown")
            )
            
            return {
                "evidence_id": evidence_id,
                "status": "processed",
                "processing_result": processing_result.to_dict(),
                "video_format": video_format,
                "processing_time_ms": processing_result.processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Video processing failed: {str(e)}")
    
    def _detect_video_format(self, data: bytes) -> str:
        """Detect video format from data."""
        # Simple detection based on file headers
        if data.startswith(b'\x00\x00\x00\x20ftypmp41'):
            return "mp4"
        elif data.startswith(b'RIFF') and b'AVI ' in data[:12]:
            return "avi"
        elif data.startswith(b'\x00\x00\x00\x14ftypqt'):
            return "mov"
        elif data.startswith(b'\x1a\x45\xdf\xa3'):
            return "mkv"
        elif data.startswith(b'\x00\x00\x00\x20ftypisom'):
            return "mp4"
        else:
            return "unknown"
    
    async def _process_video_data(self, video_data: bytes, video_format: str) -> Dict[str, Any]:
        """Process video data."""
        start_time = time.time()
        
        try:
            # Extract audio and video frames
            audio_data, video_frames = await self._extract_audio_and_frames(video_data)
            
            # Process audio
            asr_result = await self._process_audio(audio_data)
            
            # Process video frames
            ocr_result = await self._process_video_frames(video_frames)
            
            # Combine results
            combined_text = f"{asr_result.get('transcript', '')}\n{ocr_result.get('text', '')}"
            
            # Extract entities from combined text
            entities = self._extract_entities(combined_text)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "ocr_text": ocr_result.get("text", ""),
                "asr_transcript": asr_result.get("transcript", ""),
                "entities": entities,
                "confidence": {
                    "ocr": ocr_result.get("confidence", {}).get("ocr", 0.0),
                    "asr": asr_result.get("confidence", {}).get("asr", 0.0)
                },
                "processing_time_ms": processing_time_ms,
                "engine_used": "whisperx_local+tesseract_local",
                "frames_processed": ocr_result.get("frames_processed", 0),
                "audio_segments": asr_result.get("segments_count", 0)
            }
            
        except Exception as e:
            raise Exception(f"Video processing failed: {str(e)}")
    
    async def _extract_audio_and_frames(self, video_data: bytes) -> tuple[bytes, List[bytes]]:
        """Extract audio and video frames from video data."""
        # This is a simplified implementation
        # In production, you would use FFmpeg or similar tools
        
        # For now, return mock data
        # In reality, you would:
        # 1. Use FFmpeg to extract audio track
        # 2. Extract video frames at regular intervals
        # 3. Convert frames to images for OCR processing
        
        audio_data = b""  # Extracted audio
        video_frames = []  # Extracted frames
        
        return audio_data, video_frames
    
    async def _process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Process audio from video."""
        try:
            # Configure ASR
            asr_config = ASRConfig(
                language="en",
                model_size="base",
                diarization=False,
                confidence_threshold=0.7
            )
            
            # Transcribe audio
            asr_results = await self.asr_service.transcribe_audio(audio_data, asr_config)
            
            # Combine transcript from all segments
            full_transcript = " ".join([result.text for result in asr_results])
            
            # Calculate average confidence
            avg_confidence = sum(result.confidence for result in asr_results) / len(asr_results) if asr_results else 0.0
            
            return {
                "transcript": full_transcript,
                "confidence": {"asr": avg_confidence},
                "segments_count": len(asr_results)
            }
            
        except Exception as e:
            return {
                "transcript": "",
                "confidence": {"asr": 0.0},
                "segments_count": 0
            }
    
    async def _process_video_frames(self, video_frames: List[bytes]) -> Dict[str, Any]:
        """Process video frames for OCR."""
        try:
            if not video_frames:
                return {
                    "text": "",
                    "confidence": {"ocr": 0.0},
                    "frames_processed": 0
                }
            
            # Configure OCR
            ocr_config = OCRConfig(
                language="eng",
                confidence_threshold=0.7,
                preprocess=True,
                deskew=True,
                denoise=True
            )
            
            # Process each frame
            all_text = []
            all_confidence = []
            
            for frame in video_frames:
                try:
                    ocr_result = await self.ocr_service.extract_text(frame, ocr_config)
                    if ocr_result.text.strip():
                        all_text.append(ocr_result.text)
                        all_confidence.append(ocr_result.confidence)
                except Exception:
                    continue
            
            # Combine text from all frames
            combined_text = "\n".join(all_text)
            
            # Calculate average confidence
            avg_confidence = sum(all_confidence) / len(all_confidence) if all_confidence else 0.0
            
            return {
                "text": combined_text,
                "confidence": {"ocr": avg_confidence},
                "frames_processed": len(video_frames)
            }
            
        except Exception as e:
            return {
                "text": "",
                "confidence": {"ocr": 0.0},
                "frames_processed": 0
            }
    
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
        
        # Extract names (simple pattern)
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        for name in names:
            entities.append({
                "type": "PERSON",
                "value": name,
                "confidence": 0.7
            })
        
        return entities
