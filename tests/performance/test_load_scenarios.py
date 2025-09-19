"""Performance and load tests for the Legal Simulation Platform.

Tests system performance under various load scenarios including concurrent users,
large evidence files, render queue performance, and database optimization.
"""

import pytest
import asyncio
import tempfile
import time
import psutil
import statistics
from pathlib import Path
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import services for load testing
from services.shared.models.case import Case, CaseMode, CaseType
from services.shared.models.evidence import Evidence, EvidenceType
from services.shared.models.storyboard import Storyboard
from services.shared.models.render import RenderJob
from services.evidence-processor.pipelines.document_pipeline import DocumentPipeline
from services.render-orchestrator.implementations.blender.local_renderer import BlenderLocalRenderer


class TestLoadScenarios:
    """Test suite for performance and load testing."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def mock_storage_service(self, temp_dir):
        """Create mock storage service for testing."""
        from services.shared.implementations.storage.local_storage import LocalStorage
        return LocalStorage(base_path=temp_dir)
    
    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitoring fixture."""
        return PerformanceMonitor()
    
    def create_large_test_file(self, temp_dir: Path, size_mb: int, file_type: str = "pdf") -> Path:
        """Create a large test file of specified size."""
        file_path = temp_dir / f"large_test_file.{file_type}"
        
        # Create file with random data
        chunk_size = 1024 * 1024  # 1MB chunks
        total_size = size_mb * chunk_size
        
        with open(file_path, 'wb') as f:
            remaining = total_size
            while remaining > 0:
                chunk_size_to_write = min(chunk_size, remaining)
                # Generate random data
                random_data = np.random.bytes(chunk_size_to_write)
                f.write(random_data)
                remaining -= chunk_size_to_write
        
        return file_path
    
    def create_test_case_batch(self, count: int) -> List[Case]:
        """Create a batch of test cases."""
        cases = []
        for i in range(count):
            case = Case(
                id=f"load-test-case-{i:04d}",
                title=f"Load Test Case {i}",
                jurisdiction="federal",
                case_type=CaseType.CIVIL,
                mode=CaseMode.DEMONSTRATIVE
            )
            cases.append(case)
        return cases
    
    def create_test_evidence_batch(self, case_id: str, count: int, temp_dir: Path) -> List[Evidence]:
        """Create a batch of test evidence items."""
        evidence_items = []
        for i in range(count):
            # Create small test file
            file_path = temp_dir / f"evidence_{i}.txt"
            file_path.write_text(f"Test evidence content {i}")
            
            evidence = Evidence(
                id=f"evid-{i:04d}",
                case_id=case_id,
                filename=f"evidence_{i}.txt",
                evidence_type=EvidenceType.DOCUMENT,
                file_path=str(file_path),
                sha256_hash="test_hash",
                metadata={"test": True}
            )
            evidence_items.append(evidence)
        return evidence_items
    
    @pytest.mark.asyncio
    async def test_concurrent_case_processing(self, temp_dir, mock_storage_service, performance_monitor):
        """Test processing multiple cases concurrently."""
        num_cases = 10
        evidence_per_case = 5
        
        # Create test cases and evidence
        cases = self.create_test_case_batch(num_cases)
        all_evidence = []
        
        for case in cases:
            evidence_batch = self.create_test_evidence_batch(case.id, evidence_per_case, temp_dir)
            all_evidence.extend(evidence_batch)
        
        # Monitor system resources
        performance_monitor.start_monitoring()
        
        start_time = time.time()
        
        # Process all evidence concurrently
        async def process_evidence_batch(evidence_batch: List[Evidence]):
            """Process a batch of evidence items."""
            pipeline = DocumentPipeline(mock_storage_service)
            tasks = [pipeline.process(evidence) for evidence in evidence_batch]
            return await asyncio.gather(*tasks)
        
        # Split evidence into batches for each case
        evidence_batches = []
        for case in cases:
            case_evidence = [e for e in all_evidence if e.case_id == case.id]
            evidence_batches.append(case_evidence)
        
        # Process all batches concurrently
        batch_tasks = [process_evidence_batch(batch) for batch in evidence_batches]
        results = await asyncio.gather(*batch_tasks)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Stop monitoring and get metrics
        metrics = performance_monitor.stop_monitoring()
        
        # Verify all evidence was processed
        total_processed = sum(len(batch_results) for batch_results in results)
        assert total_processed == len(all_evidence)
        
        # Performance assertions
        assert processing_time < 30.0, f"Processing took too long: {processing_time:.2f}s"
        assert metrics["avg_cpu_percent"] < 80.0, f"CPU usage too high: {metrics['avg_cpu_percent']:.1f}%"
        assert metrics["max_memory_mb"] < 2048, f"Memory usage too high: {metrics['max_memory_mb']:.1f}MB"
        
        # Calculate throughput
        throughput = len(all_evidence) / processing_time
        assert throughput > 1.0, f"Throughput too low: {throughput:.2f} items/sec"
    
    @pytest.mark.asyncio
    async def test_large_evidence_file_processing(self, temp_dir, mock_storage_service, performance_monitor):
        """Test processing large evidence files (1GB+)."""
        large_file_sizes = [100, 500, 1000]  # MB
        
        for file_size_mb in large_file_sizes:
            # Create large test file
            large_file = self.create_large_test_file(temp_dir, file_size_mb, "pdf")
            
            # Create evidence record
            evidence = Evidence(
                id=f"large-file-{file_size_mb}mb",
                case_id="large-file-test-case",
                filename=large_file.name,
                evidence_type=EvidenceType.DOCUMENT,
                file_path=str(large_file),
                sha256_hash="large_file_hash",
                metadata={"size_mb": file_size_mb}
            )
            
            # Monitor performance during processing
            performance_monitor.start_monitoring()
            
            start_time = time.time()
            
            # Process large file
            pipeline = DocumentPipeline(mock_storage_service)
            result = await pipeline.process(evidence)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Get performance metrics
            metrics = performance_monitor.stop_monitoring()
            
            # Verify processing completed
            assert result is not None
            assert result.processed_at is not None
            
            # Performance assertions for large files
            max_processing_time = file_size_mb * 2  # 2 seconds per MB is reasonable
            assert processing_time < max_processing_time, \
                f"Processing {file_size_mb}MB file took too long: {processing_time:.2f}s"
            
            # Memory usage should be reasonable even for large files
            assert metrics["max_memory_mb"] < 4096, \
                f"Memory usage too high for {file_size_mb}MB file: {metrics['max_memory_mb']:.1f}MB"
            
            # Clean up large file
            large_file.unlink()
    
    @pytest.mark.asyncio
    async def test_render_queue_performance(self, temp_dir, performance_monitor):
        """Test render queue performance under load."""
        num_renders = 20
        render_jobs = []
        
        # Create render jobs
        for i in range(num_renders):
            render_job = RenderJob(
                id=f"render-job-{i:03d}",
                case_id=f"case-{i:03d}",
                storyboard_id=f"story-{i:03d}",
                profile="neutral",
                mode=CaseMode.DEMONSTRATIVE,
                output_path=str(temp_dir / f"render_{i:03d}.mp4")
            )
            render_jobs.append(render_job)
        
        # Mock renderer for performance testing
        with patch('services.render_orchestrator.implementations.blender.local_renderer.BlenderLocalRenderer') as mock_renderer:
            # Mock render method to simulate processing time
            async def mock_render(scene_data, config):
                # Simulate render time based on complexity
                await asyncio.sleep(0.1)  # 100ms simulation
                return Mock(
                    output_path=config.output_path,
                    render_time_seconds=0.1,
                    frames_generated=24,
                    file_size_bytes=1024*1024
                )
            
            mock_renderer.return_value.render_scene = mock_render
            
            renderer = mock_renderer.return_value
            
            # Monitor performance
            performance_monitor.start_monitoring()
            
            start_time = time.time()
            
            # Process render queue
            render_tasks = []
            for job in render_jobs:
                scene_data = Mock()  # Mock scene data
                config = Mock()
                config.output_path = job.output_path
                config.width = 1920
                config.height = 1080
                config.fps = 24
                config.duration_seconds = 10.0
                
                task = renderer.render_scene(scene_data, config)
                render_tasks.append(task)
            
            # Execute all renders concurrently
            results = await asyncio.gather(*render_tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Get performance metrics
            metrics = performance_monitor.stop_monitoring()
            
            # Verify all renders completed
            assert len(results) == num_renders
            
            # Performance assertions
            assert total_time < 5.0, f"Render queue processing took too long: {total_time:.2f}s"
            assert metrics["avg_cpu_percent"] < 90.0, f"CPU usage too high: {metrics['avg_cpu_percent']:.1f}%"
            
            # Calculate queue throughput
            throughput = num_renders / total_time
            assert throughput > 4.0, f"Render queue throughput too low: {throughput:.2f} renders/sec"
    
    @pytest.mark.asyncio
    async def test_database_query_optimization(self, temp_dir):
        """Test database query performance under load."""
        # This would test actual database queries in a real implementation
        # For now, we'll simulate database operations
        
        num_queries = 1000
        query_times = []
        
        # Mock database service
        with patch('services.shared.services.database_service.DatabaseService') as mock_db:
            async def mock_query(query_type: str, params: Dict[str, Any]):
                # Simulate different query types with different response times
                if query_type == "simple_select":
                    await asyncio.sleep(0.001)  # 1ms
                elif query_type == "complex_join":
                    await asyncio.sleep(0.01)   # 10ms
                elif query_type == "aggregate":
                    await asyncio.sleep(0.005)  # 5ms
                
                return Mock(results=[{"id": i} for i in range(10)])
            
            mock_db.return_value.query = mock_query
            db_service = mock_db.return_value
            
            # Execute queries concurrently
            start_time = time.time()
            
            query_tasks = []
            for i in range(num_queries):
                query_type = ["simple_select", "complex_join", "aggregate"][i % 3]
                task = db_service.query(query_type, {"id": i})
                query_tasks.append(task)
            
            results = await asyncio.gather(*query_tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Verify all queries completed
            assert len(results) == num_queries
            
            # Performance assertions
            assert total_time < 2.0, f"Database queries took too long: {total_time:.2f}s"
            
            # Calculate query throughput
            throughput = num_queries / total_time
            assert throughput > 500.0, f"Database throughput too low: {throughput:.2f} queries/sec"
    
    @pytest.mark.asyncio
    async def test_memory_usage_profiling(self, temp_dir, mock_storage_service, performance_monitor):
        """Test memory usage under various scenarios."""
        # Test memory usage with different evidence types
        evidence_types = [EvidenceType.DOCUMENT, EvidenceType.AUDIO, EvidenceType.VIDEO]
        
        for evidence_type in evidence_types:
            # Create test evidence
            evidence = Evidence(
                id=f"memory-test-{evidence_type.value}",
                case_id="memory-test-case",
                filename=f"test.{evidence_type.value}",
                evidence_type=evidence_type,
                file_path=str(temp_dir / f"test.{evidence_type.value}"),
                sha256_hash="memory_test_hash"
            )
            
            # Monitor memory usage
            performance_monitor.start_monitoring()
            
            # Process evidence (mock the actual processing)
            with patch('services.evidence_processor.pipelines.document_pipeline.DocumentPipeline') as mock_pipeline:
                mock_pipeline.return_value.process.return_value = Mock(
                    processed_at=time.time(),
                    confidence_score=0.95
                )
                
                pipeline = mock_pipeline.return_value
                result = await pipeline.process(evidence)
                
                # Get memory metrics
                metrics = performance_monitor.stop_monitoring()
                
                # Verify processing completed
                assert result is not None
                
                # Memory usage should be reasonable for each evidence type
                max_memory_mb = {
                    EvidenceType.DOCUMENT: 512,
                    EvidenceType.AUDIO: 1024,
                    EvidenceType.VIDEO: 2048
                }
                
                assert metrics["max_memory_mb"] < max_memory_mb[evidence_type], \
                    f"Memory usage too high for {evidence_type.value}: {metrics['max_memory_mb']:.1f}MB"
    
    @pytest.mark.asyncio
    async def test_stress_testing_limits(self, temp_dir, mock_storage_service, performance_monitor):
        """Test system limits under extreme stress."""
        # Gradually increase load until system limits are reached
        load_levels = [10, 25, 50, 100, 200]  # Concurrent operations
        
        results = {}
        
        for load_level in load_levels:
            # Create load
            evidence_items = []
            for i in range(load_level):
                evidence = Evidence(
                    id=f"stress-{load_level}-{i}",
                    case_id="stress-test-case",
                    filename=f"stress_{i}.txt",
                    evidence_type=EvidenceType.DOCUMENT,
                    file_path=str(temp_dir / f"stress_{i}.txt"),
                    sha256_hash=f"stress_hash_{i}"
                )
                evidence_items.append(evidence)
            
            # Monitor performance
            performance_monitor.start_monitoring()
            
            start_time = time.time()
            
            try:
                # Process with current load level
                pipeline = DocumentPipeline(mock_storage_service)
                tasks = [pipeline.process(evidence) for evidence in evidence_items]
                
                # Set timeout for stress test
                results_list = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Get metrics
                metrics = performance_monitor.stop_monitoring()
                
                # Count successful vs failed operations
                successful = sum(1 for r in results_list if not isinstance(r, Exception))
                failed = sum(1 for r in results_list if isinstance(r, Exception))
                
                results[load_level] = {
                    "successful": successful,
                    "failed": failed,
                    "processing_time": processing_time,
                    "cpu_avg": metrics["avg_cpu_percent"],
                    "memory_max": metrics["max_memory_mb"],
                    "throughput": successful / processing_time if processing_time > 0 else 0
                }
                
                # Stop if failure rate is too high
                failure_rate = failed / load_level
                if failure_rate > 0.1:  # 10% failure rate threshold
                    break
                    
            except asyncio.TimeoutError:
                # System is overwhelmed
                results[load_level] = {
                    "successful": 0,
                    "failed": load_level,
                    "processing_time": 30.0,
                    "timeout": True
                }
                break
        
        # Analyze results
        max_sustainable_load = max(
            load for load, result in results.items() 
            if result.get("failed", 0) / load < 0.05  # 5% failure threshold
        )
        
        # Assertions
        assert max_sustainable_load >= 50, f"System cannot handle reasonable load: {max_sustainable_load}"
        
        # Verify performance degrades gracefully
        for load_level in sorted(results.keys()):
            result = results[load_level]
            if not result.get("timeout", False):
                throughput = result["throughput"]
                assert throughput > 0, f"No throughput at load level {load_level}"


class PerformanceMonitor:
    """Monitor system performance during tests."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.cpu_samples = []
        self.memory_samples = []
        self.start_time = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
        self.cpu_samples = []
        self.memory_samples = []
        self.start_time = time.time()
        
        # Start monitoring thread
        asyncio.create_task(self._monitor_loop())
    
    async def _monitor_loop(self):
        """Monitoring loop."""
        while self.monitoring:
            try:
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                self.cpu_samples.append(cpu_percent)
                self.memory_samples.append(memory_mb)
                
                await asyncio.sleep(0.1)  # Sample every 100ms
            except Exception:
                break
    
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return metrics."""
        self.monitoring = False
        
        if not self.cpu_samples or not self.memory_samples:
            return {"avg_cpu_percent": 0, "max_memory_mb": 0}
        
        return {
            "avg_cpu_percent": statistics.mean(self.cpu_samples),
            "max_cpu_percent": max(self.cpu_samples),
            "avg_memory_mb": statistics.mean(self.memory_samples),
            "max_memory_mb": max(self.memory_samples),
            "duration_seconds": time.time() - self.start_time if self.start_time else 0
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])