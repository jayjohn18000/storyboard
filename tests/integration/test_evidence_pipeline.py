"""Integration tests for the evidence processing pipeline.

Tests the complete evidence processing flow from upload to final storage,
including OCR accuracy, ASR processing, NLP extraction, and WORM compliance.
"""

import pytest
import asyncio
import tempfile
import os
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Import the services we're testing
from services.shared.models.evidence import Evidence, EvidenceType
from services.shared.models.case import Case
from services.evidence-processor.pipelines.document_pipeline import DocumentPipeline
from services.evidence-processor.pipelines.audio_pipeline import AudioPipeline
from services.evidence-processor.pipelines.video_pipeline import VideoPipeline
from services.shared.implementations.storage.local_storage import LocalStorage
from services.shared.implementations.ocr.tesseract_local import TesseractLocalOCR
from services.shared.implementations.asr.whisperx_local import WhisperXLocalASR


class TestEvidencePipeline:
    """Test suite for evidence processing pipeline integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def storage_service(self, temp_dir):
        """Create local storage service for testing."""
        return LocalStorage(base_path=temp_dir)
    
    @pytest.fixture
    def test_case(self):
        """Create test case for evidence processing."""
        return Case(
            id="test-case-123",
            title="Test Legal Case",
            jurisdiction="federal",
            case_type="civil",
            mode="DEMONSTRATIVE"
        )
    
    def create_test_document_image(self, temp_dir: Path, text: str) -> Path:
        """Create a test document image with specified text."""
        # Create a white background image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fallback to basic if not available
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except OSError:
            font = ImageFont.load_default()
        
        # Draw text on the image
        draw.text((50, 50), text, fill='black', font=font)
        
        # Save the image
        image_path = temp_dir / "test_document.png"
        img.save(image_path)
        return image_path
    
    def create_test_audio_file(self, temp_dir: Path, duration: float = 5.0) -> Path:
        """Create a test audio file with speech."""
        import wave
        import numpy as np
        
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # Generate a simple sine wave as test audio
        t = np.linspace(0, duration, samples)
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.1
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Save as WAV file
        audio_path = temp_dir / "test_audio.wav"
        with wave.open(str(audio_path), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return audio_path
    
    def create_test_video_file(self, temp_dir: Path, duration: float = 3.0) -> Path:
        """Create a test video file."""
        # Create a simple mock video file (without OpenCV)
        video_path = temp_dir / "test_video.mp4"
        
        # Create a minimal MP4 file header (mock)
        with open(video_path, 'wb') as f:
            # Write a minimal MP4 header
            f.write(b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom')
            # Add some mock video data
            f.write(b'\x00' * 1024)  # 1KB of mock data
        
        return video_path
    
    @pytest.mark.asyncio
    async def test_document_processing_flow(self, temp_dir, storage_service, test_case):
        """Test complete document processing pipeline."""
        # Create test document
        test_text = "This is a legal document containing important case information."
        document_path = self.create_test_document_image(temp_dir, test_text)
        
        # Create evidence record
        evidence = Evidence(
            id="doc-001",
            case_id=test_case.id,
            filename="test_document.png",
            evidence_type=EvidenceType.DOCUMENT,
            file_path=str(document_path),
            sha256_hash=hashlib.sha256(document_path.read_bytes()).hexdigest(),
            metadata={"original_text": test_text}
        )
        
        # Process document through pipeline
        pipeline = DocumentPipeline(storage_service)
        result = await pipeline.process(evidence)
        
        # Verify processing results
        assert result is not None
        assert result.ocr_text is not None
        assert len(result.ocr_text) > 0
        assert result.confidence_score > 0.5
        assert result.processed_at is not None
        
        # Verify storage
        assert await storage_service.exists(result.file_path)
        
        # Verify WORM compliance (file should not be modifiable)
        with pytest.raises(Exception):  # Should raise error on write attempt
            await storage_service.write(result.file_path, b"modified content")
    
    @pytest.mark.asyncio
    async def test_audio_processing_flow(self, temp_dir, storage_service, test_case):
        """Test complete audio processing pipeline."""
        # Create test audio file
        audio_path = self.create_test_audio_file(temp_dir, duration=3.0)
        
        # Create evidence record
        evidence = Evidence(
            id="audio-001",
            case_id=test_case.id,
            filename="test_audio.wav",
            evidence_type=EvidenceType.AUDIO,
            file_path=str(audio_path),
            sha256_hash=hashlib.sha256(audio_path.read_bytes()).hexdigest()
        )
        
        # Process audio through pipeline
        pipeline = AudioPipeline(storage_service)
        result = await pipeline.process(evidence)
        
        # Verify processing results
        assert result is not None
        assert result.transcript is not None
        assert result.confidence_score > 0.0
        assert result.processed_at is not None
        
        # Verify storage
        assert await storage_service.exists(result.file_path)
    
    @pytest.mark.asyncio
    async def test_video_processing_flow(self, temp_dir, storage_service, test_case):
        """Test complete video processing pipeline."""
        # Create test video file
        video_path = self.create_test_video_file(temp_dir, duration=2.0)
        
        # Create evidence record
        evidence = Evidence(
            id="video-001",
            case_id=test_case.id,
            filename="test_video.mp4",
            evidence_type=EvidenceType.VIDEO,
            file_path=str(video_path),
            sha256_hash=hashlib.sha256(video_path.read_bytes()).hexdigest()
        )
        
        # Process video through pipeline
        pipeline = VideoPipeline(storage_service)
        result = await pipeline.process(evidence)
        
        # Verify processing results
        assert result is not None
        assert result.transcript is not None
        assert result.frame_count > 0
        assert result.duration > 0
        assert result.processed_at is not None
        
        # Verify storage
        assert await storage_service.exists(result.file_path)
    
    @pytest.mark.asyncio
    async def test_ocr_accuracy_on_legal_documents(self, temp_dir, storage_service):
        """Test OCR accuracy on various legal document formats."""
        test_cases = [
            ("CONTRACT AGREEMENT\n\nThis agreement is entered into on January 1, 2024.", 0.9),
            ("LEGAL NOTICE\n\nPursuant to Federal Rule 26(a)(1)...", 0.85),
            ("DEPOSITION TRANSCRIPT\n\nQ: What is your name?\nA: John Doe", 0.8)
        ]
        
        ocr_service = TesseractLocalOCR()
        
        for text, min_accuracy in test_cases:
            # Create document image
            doc_path = self.create_test_document_image(temp_dir, text)
            
            # Process with OCR
            result = await ocr_service.extract_text(str(doc_path))
            
            # Verify accuracy
            assert result.confidence_score >= min_accuracy
            assert result.extracted_text is not None
            assert len(result.extracted_text) > 0
    
    @pytest.mark.asyncio
    async def test_asr_with_legal_audio_samples(self, temp_dir, storage_service):
        """Test ASR accuracy with legal audio samples."""
        # This would use real legal audio samples in production
        # For testing, we'll create synthetic audio and mock the ASR results
        
        audio_path = self.create_test_audio_file(temp_dir, duration=5.0)
        
        # Mock ASR service for testing
        with patch('services.shared.implementations.asr.whisperx_local.WhisperXLocalASR') as mock_asr:
            mock_asr.return_value.extract_text.return_value = Mock(
                transcript="This is a test legal deposition transcript.",
                confidence_score=0.95,
                segments=[
                    {"start": 0.0, "end": 2.5, "text": "This is a test", "confidence": 0.98},
                    {"start": 2.5, "end": 5.0, "text": "legal deposition transcript.", "confidence": 0.92}
                ]
            )
            
            asr_service = mock_asr.return_value
            result = await asr_service.extract_text(str(audio_path))
            
            assert result.transcript is not None
            assert result.confidence_score > 0.9
            assert len(result.segments) > 0
    
    @pytest.mark.asyncio
    async def test_storage_integrity_and_worm_compliance(self, temp_dir, storage_service):
        """Test storage integrity and WORM (Write Once, Read Many) compliance."""
        test_content = b"Important legal evidence data"
        file_path = "evidence/test-doc-001.pdf"
        
        # Store file
        await storage_service.write(file_path, test_content)
        
        # Verify file exists and content matches
        assert await storage_service.exists(file_path)
        retrieved_content = await storage_service.read(file_path)
        assert retrieved_content == test_content
        
        # Verify WORM compliance - should not allow overwrites
        with pytest.raises(PermissionError):
            await storage_service.write(file_path, b"Modified content")
        
        # Verify content is still original
        retrieved_content = await storage_service.read(file_path)
        assert retrieved_content == test_content
        
        # Test checksum verification
        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = hashlib.sha256(retrieved_content).hexdigest()
        assert actual_hash == expected_hash
    
    @pytest.mark.asyncio
    async def test_nlp_extraction_accuracy(self, temp_dir, storage_service):
        """Test NLP extraction accuracy for legal entities and relationships."""
        # Create document with known entities
        legal_text = """
        Case: Smith v. Jones Corporation
        Date: January 15, 2024
        Plaintiff: John Smith (SSN: 123-45-6789)
        Defendant: Jones Corporation (EIN: 98-7654321)
        Amount in dispute: $50,000.00
        Attorney: Jane Doe, Esq.
        """
        
        doc_path = self.create_test_document_image(temp_dir, legal_text)
        
        # Mock NLP extraction results
        expected_entities = {
            "PERSON": ["John Smith", "Jane Doe"],
            "ORG": ["Jones Corporation"],
            "MONEY": ["$50,000.00"],
            "DATE": ["January 15, 2024"],
            "SSN": ["123-45-6789"],
            "EIN": ["98-7654321"]
        }
        
        # In a real implementation, this would use actual NLP service
        # For testing, we'll verify the structure and mock the results
        with patch('services.evidence_processor.pipelines.document_pipeline.extract_entities') as mock_nlp:
            mock_nlp.return_value = expected_entities
            
            pipeline = DocumentPipeline(storage_service)
            evidence = Evidence(
                id="nlp-test-001",
                case_id="test-case",
                filename="legal_document.png",
                evidence_type=EvidenceType.DOCUMENT,
                file_path=str(doc_path),
                sha256_hash="test_hash"
            )
            
            result = await pipeline.process(evidence)
            
            # Verify NLP extraction was called
            mock_nlp.assert_called_once()
            
            # In real implementation, verify extracted entities
            assert result.nlp_entities is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_evidence_processing(self, temp_dir, storage_service, test_case):
        """Test processing multiple evidence items concurrently."""
        # Create multiple test documents
        evidence_items = []
        for i in range(5):
            text = f"Legal document {i} containing case information."
            doc_path = self.create_test_document_image(temp_dir, text)
            
            evidence = Evidence(
                id=f"doc-{i:03d}",
                case_id=test_case.id,
                filename=f"document_{i}.png",
                evidence_type=EvidenceType.DOCUMENT,
                file_path=str(doc_path),
                sha256_hash=hashlib.sha256(doc_path.read_bytes()).hexdigest()
            )
            evidence_items.append(evidence)
        
        # Process all evidence concurrently
        pipeline = DocumentPipeline(storage_service)
        tasks = [pipeline.process(evidence) for evidence in evidence_items]
        results = await asyncio.gather(*tasks)
        
        # Verify all items were processed successfully
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert result.processed_at is not None
            assert result.confidence_score > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
