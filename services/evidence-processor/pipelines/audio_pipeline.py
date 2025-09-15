"""Audio processing pipeline for evidence."""

import time
from typing import Dict, Any, List
from ..shared.interfaces.storage import StorageInterface
from ..shared.interfaces.asr import ASRInterface, ASRConfig
from ..shared.models.evidence import Evidence, EvidenceStatus, ProcessingResult


class AudioPipeline:
    """Pipeline for processing audio evidence."""
    
    def __init__(self, storage_service: StorageInterface, asr_service: ASRInterface):
        self.storage_service = storage_service
        self.asr_service = asr_service
    
    async def process_audio(self, evidence_id: str) -> Dict[str, Any]:
        """Process audio evidence."""
        try:
            # Get evidence from storage
            audio_data = await self.storage_service.get_evidence(evidence_id)
            
            # Detect audio format
            audio_format = self._detect_audio_format(audio_data)
            
            # Process audio
            result = await self._process_audio_data(audio_data, audio_format)
            
            # Create processing result
            processing_result = ProcessingResult(
                asr_transcript=result.get("transcript", ""),
                extracted_entities=result.get("entities", []),
                confidence_scores=result.get("confidence", {}),
                processing_time_ms=result.get("processing_time_ms", 0),
                engine_used=result.get("engine_used", "unknown")
            )
            
            return {
                "evidence_id": evidence_id,
                "status": "processed",
                "processing_result": processing_result.to_dict(),
                "audio_format": audio_format,
                "processing_time_ms": processing_result.processing_time_ms,
            }
            
        except Exception as e:
            raise Exception(f"Audio processing failed: {str(e)}")
    
    def _detect_audio_format(self, data: bytes) -> str:
        """Detect audio format from data."""
        # Simple detection based on file headers
        if data.startswith(b'RIFF') and b'WAVE' in data[:12]:
            return "wav"
        elif data.startswith(b'ID3') or data[1:4] == b'\xff\xfb':
            return "mp3"
        elif data.startswith(b'fLaC'):
            return "flac"
        elif data.startswith(b'OggS'):
            return "ogg"
        elif data.startswith(b'\x00\x00\x00\x20ftypM4A'):
            return "m4a"
        else:
            return "unknown"
    
    async def _process_audio_data(self, audio_data: bytes, audio_format: str) -> Dict[str, Any]:
        """Process audio data."""
        start_time = time.time()
        
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
            
            # Extract entities from transcript
            entities = self._extract_entities(full_transcript)
            
            # Calculate total duration
            total_duration = max(result.end_time for result in asr_results) if asr_results else 0.0
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "transcript": full_transcript,
                "entities": entities,
                "confidence": {"asr": avg_confidence},
                "processing_time_ms": processing_time_ms,
                "engine_used": "whisperx_local",
                "segments_count": len(asr_results),
                "total_duration": total_duration
            }
            
        except Exception as e:
            raise Exception(f"Audio transcription failed: {str(e)}")
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from transcript (simplified implementation)."""
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
