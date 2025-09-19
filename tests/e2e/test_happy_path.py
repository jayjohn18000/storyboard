"""End-to-end happy path test for the complete Legal Simulation Platform workflow.

This test implements the full upload→process→storyboard→timeline→render flow
by making actual HTTP calls to the running services.
"""

import pytest
import asyncio
import httpx
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import uuid


class PollingHelper:
    """Helper class for polling operations with timeout."""
    
    def __init__(self, timeout: float = 60.0, interval: float = 2.0):
        self.timeout = timeout
        self.interval = interval
    
    async def poll_until(self, check_func, *args, **kwargs) -> Any:
        """
        Poll until check_func returns a truthy value or timeout is reached.
        
        Args:
            check_func: Function to call for checking condition
            *args, **kwargs: Arguments to pass to check_func
            
        Returns:
            Result of check_func when condition is met
            
        Raises:
            TimeoutError: If timeout is reached without condition being met
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                result = await check_func(*args, **kwargs)
                if result:
                    return result
            except Exception as e:
                print(f"Polling check failed: {e}")
            
            await asyncio.sleep(self.interval)
        
        raise TimeoutError(f"Polling timeout after {self.timeout} seconds")


class E2EHappyPathTest:
    """End-to-end happy path test implementation."""
    
    def __init__(self):
        self.base_urls = {
            "api_gateway": "http://localhost:8000",
            "evidence_processor": "http://localhost:8001",
            "storyboard_service": "http://localhost:8002", 
            "timeline_compiler": "http://localhost:8003",
            "render_orchestrator": "http://localhost:8004"
        }
        self.polling_helper = PollingHelper(timeout=120.0, interval=3.0)
        self.test_data = {}
    
    async def check_service_health(self, service_name: str, base_url: str) -> bool:
        """Check if a service is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def wait_for_services(self) -> bool:
        """Wait for all services to be healthy."""
        print("🔍 Waiting for services to be healthy...")
        
        for service_name, base_url in self.base_urls.items():
            try:
                result = await self.polling_helper.poll_until(
                    self.check_service_health, service_name, base_url
                )
                print(f"✅ {service_name}: Healthy")
            except TimeoutError:
                print(f"❌ {service_name}: Not responding")
                return False
        
        return True
    
    async def create_test_case(self) -> str:
        """Create a test case via API Gateway."""
        print("📝 Creating test case...")
        
        case_data = {
            "case_number": "E2E-TEST-001",
            "title": "E2E Happy Path Test Case",
            "case_type": "civil",
            "jurisdiction": "federal",
            "court": "US District Court",
            "filing_date": "2024-01-01",
            "parties": {
                "plaintiff": "Test Plaintiff Corp.",
                "defendant": "Test Defendant LLC"
            },
            "attorneys": {
                "plaintiff": "Jane Smith, Esq.",
                "defendant": "John Doe, Esq."
            }
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_urls['api_gateway']}/api/v1/cases",
                json=case_data
            )
            
            if response.status_code == 201:
                case_result = response.json()
                case_id = case_result.get("id")
                print(f"✅ Case created: {case_id}")
                self.test_data["case_id"] = case_id
                return case_id
            else:
                print(f"❌ Case creation failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create case: {response.text}")
    
    async def upload_test_evidence(self, case_id: str) -> str:
        """Upload test evidence via API Gateway."""
        print("📤 Uploading test evidence...")
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            TEST EVIDENCE DOCUMENT
            
            This is a test document for the E2E happy path test.
            
            Key facts:
            1. Contract signed on January 1, 2024
            2. Payment of $50,000.00 due
            3. Delivery deadline: March 1, 2024
            4. Warranty period: 1 year
            
            This document is used to test the complete workflow
            from evidence upload to final render output.
            """)
            temp_file_path = f.name
        
        try:
            # Upload the file
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("test_evidence.txt", f, "text/plain")}
                data = {"case_id": case_id, "description": "E2E test evidence document"}
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_urls['api_gateway']}/api/v1/evidence/upload",
                        files=files,
                        data=data
                    )
            
            if response.status_code == 201:
                evidence_result = response.json()
                evidence_id = evidence_result.get("id")
                print(f"✅ Evidence uploaded: {evidence_id}")
                self.test_data["evidence_id"] = evidence_id
                return evidence_id
            else:
                print(f"❌ Evidence upload failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to upload evidence: {response.text}")
        
        finally:
            # Clean up temp file
            Path(temp_file_path).unlink(missing_ok=True)
    
    async def wait_for_evidence_processing(self, evidence_id: str) -> Dict[str, Any]:
        """Wait for evidence to be processed."""
        print("⏳ Waiting for evidence processing...")
        
        async def check_processing_status():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['api_gateway']}/api/v1/evidence/{evidence_id}"
                )
                
                if response.status_code == 200:
                    evidence_data = response.json()
                    status = evidence_data.get("status")
                    
                    if status == "processed":
                        print(f"✅ Evidence processed: {evidence_id}")
                        return evidence_data
                    elif status == "failed":
                        print(f"❌ Evidence processing failed: {evidence_id}")
                        raise Exception("Evidence processing failed")
                    else:
                        print(f"⏳ Evidence status: {status}")
                        return None
                else:
                    print(f"❌ Failed to check evidence status: {response.status_code}")
                    return None
        
        try:
            result = await self.polling_helper.poll_until(check_processing_status)
            return result
        except TimeoutError:
            raise Exception("Evidence processing timeout")
    
    async def create_storyboard(self, case_id: str, evidence_id: str) -> str:
        """Create a storyboard via API Gateway."""
        print("📋 Creating storyboard...")
        
        storyboard_data = {
            "case_id": case_id,
            "title": "E2E Test Storyboard",
            "content": """
            # E2E Test Storyboard
            
            ## Scene 1: Evidence Overview (0:00 - 0:30)
            - Present the uploaded evidence document
            - Highlight key facts and terms
            - Show document metadata and chain of custody
            
            ## Scene 2: Key Facts Presentation (0:30 - 1:00)
            - Display contract terms
            - Show payment information
            - Present delivery timeline
            
            ## Scene 3: Conclusion (1:00 - 1:30)
            - Summarize key points
            - Present evidence summary
            - Show final conclusions
            """,
            "scenes": [
                {
                    "scene_id": "scene-001",
                    "title": "Evidence Overview",
                    "duration_seconds": 30.0,
                    "evidence_anchors": [
                        {
                            "evidence_id": evidence_id,
                            "timestamp": 5.0,
                            "confidence": 0.95,
                            "description": "Evidence document presentation"
                        }
                    ]
                },
                {
                    "scene_id": "scene-002", 
                    "title": "Key Facts Presentation",
                    "duration_seconds": 30.0,
                    "evidence_anchors": [
                        {
                            "evidence_id": evidence_id,
                            "timestamp": 10.0,
                            "confidence": 0.90,
                            "description": "Contract terms highlight"
                        }
                    ]
                },
                {
                    "scene_id": "scene-003",
                    "title": "Conclusion",
                    "duration_seconds": 30.0,
                    "evidence_anchors": []
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_urls['api_gateway']}/api/v1/storyboards",
                json=storyboard_data
            )
            
            if response.status_code == 201:
                storyboard_result = response.json()
                storyboard_id = storyboard_result.get("id")
                print(f"✅ Storyboard created: {storyboard_id}")
                self.test_data["storyboard_id"] = storyboard_id
                return storyboard_id
            else:
                print(f"❌ Storyboard creation failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create storyboard: {response.text}")
    
    async def compile_timeline(self, storyboard_id: str) -> str:
        """Compile timeline via API Gateway."""
        print("⏱️ Compiling timeline...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_urls['api_gateway']}/api/v1/storyboards/{storyboard_id}/compile"
            )
            
            if response.status_code == 202:
                timeline_result = response.json()
                timeline_id = timeline_result.get("timeline_id")
                print(f"✅ Timeline compilation started: {timeline_id}")
                self.test_data["timeline_id"] = timeline_id
                return timeline_id
            else:
                print(f"❌ Timeline compilation failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to compile timeline: {response.text}")
    
    async def wait_for_timeline_compilation(self, timeline_id: str) -> Dict[str, Any]:
        """Wait for timeline compilation to complete."""
        print("⏳ Waiting for timeline compilation...")
        
        async def check_timeline_status():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['timeline_compiler']}/timeline/{timeline_id}"
                )
                
                if response.status_code == 200:
                    timeline_data = response.json()
                    status = timeline_data.get("status")
                    
                    if status == "completed":
                        print(f"✅ Timeline compiled: {timeline_id}")
                        return timeline_data
                    elif status == "failed":
                        print(f"❌ Timeline compilation failed: {timeline_id}")
                        raise Exception("Timeline compilation failed")
                    else:
                        print(f"⏳ Timeline status: {status}")
                        return None
                else:
                    print(f"❌ Failed to check timeline status: {response.status_code}")
                    return None
        
        try:
            result = await self.polling_helper.poll_until(check_timeline_status)
            return result
        except TimeoutError:
            raise Exception("Timeline compilation timeout")
    
    async def start_render(self, timeline_id: str) -> str:
        """Start render job via API Gateway."""
        print("🎬 Starting render job...")
        
        render_data = {
            "timeline_id": timeline_id,
            "config": {
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "duration_seconds": 90.0,
                "profile": "neutral",
                "deterministic": True,
                "seed": 42,
                "output_format": "mp4",
                "quality": "high"
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_urls['api_gateway']}/api/v1/renders",
                json=render_data
            )
            
            if response.status_code == 202:
                render_result = response.json()
                render_id = render_result.get("id")
                print(f"✅ Render job started: {render_id}")
                self.test_data["render_id"] = render_id
                return render_id
            else:
                print(f"❌ Render job start failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to start render: {response.text}")
    
    async def wait_for_render_completion(self, render_id: str) -> Dict[str, Any]:
        """Wait for render job to complete."""
        print("⏳ Waiting for render completion...")
        
        async def check_render_status():
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['api_gateway']}/api/v1/renders/{render_id}"
                )
                
                if response.status_code == 200:
                    render_data = response.json()
                    status = render_data.get("status")
                    
                    if status == "completed":
                        print(f"✅ Render completed: {render_id}")
                        return render_data
                    elif status == "failed":
                        print(f"❌ Render failed: {render_id}")
                        raise Exception("Render job failed")
                    else:
                        print(f"⏳ Render status: {status}")
                        return None
                else:
                    print(f"❌ Failed to check render status: {response.status_code}")
                    return None
        
        try:
            result = await self.polling_helper.poll_until(check_render_status)
            return result
        except TimeoutError:
            raise Exception("Render completion timeout")
    
    async def verify_database_rows(self) -> Dict[str, Any]:
        """Verify that database rows were created in each service."""
        print("🔍 Verifying database rows...")
        
        verification_results = {}
        
        # Check case in API Gateway
        if "case_id" in self.test_data:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['api_gateway']}/api/v1/cases/{self.test_data['case_id']}"
                )
                verification_results["case"] = response.status_code == 200
        
        # Check evidence in API Gateway
        if "evidence_id" in self.test_data:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['api_gateway']}/api/v1/evidence/{self.test_data['evidence_id']}"
                )
                verification_results["evidence"] = response.status_code == 200
        
        # Check storyboard in Storyboard Service
        if "storyboard_id" in self.test_data:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['storyboard_service']}/storyboards/{self.test_data['storyboard_id']}"
                )
                verification_results["storyboard"] = response.status_code == 200
        
        # Check timeline in Timeline Compiler
        if "timeline_id" in self.test_data:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['timeline_compiler']}/timeline/{self.test_data['timeline_id']}"
                )
                verification_results["timeline"] = response.status_code == 200
        
        # Check render in Render Orchestrator
        if "render_id" in self.test_data:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_urls['render_orchestrator']}/renders/{self.test_data['render_id']}"
                )
                verification_results["render"] = response.status_code == 200
        
        print(f"✅ Database verification: {verification_results}")
        return verification_results
    
    async def verify_custody_and_worm(self, evidence_id: str) -> Dict[str, Any]:
        """Verify chain of custody and WORM lock were recorded."""
        print("🔒 Verifying chain of custody and WORM lock...")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check chain of custody
            custody_response = await client.get(
                f"{self.base_urls['api_gateway']}/api/v1/evidence/{evidence_id}/custody"
            )
            
            # Check WORM lock status
            lock_response = await client.get(
                f"{self.base_urls['api_gateway']}/api/v1/evidence/{evidence_id}/lock"
            )
            
            custody_recorded = custody_response.status_code == 200
            worm_locked = lock_response.status_code == 200
            
            print(f"✅ Custody recorded: {custody_recorded}")
            print(f"✅ WORM locked: {worm_locked}")
            
            return {
                "custody_recorded": custody_recorded,
                "worm_locked": worm_locked
            }
    
    async def run_happy_path_test(self) -> Dict[str, Any]:
        """Run the complete happy path test."""
        print("🚀 Starting E2E Happy Path Test")
        print("=" * 50)
        
        try:
            # Step 1: Wait for services to be healthy
            if not await self.wait_for_services():
                raise Exception("Services are not healthy")
            
            # Step 2: Create test case
            case_id = await self.create_test_case()
            
            # Step 3: Upload evidence
            evidence_id = await self.upload_test_evidence(case_id)
            
            # Step 4: Wait for evidence processing
            await self.wait_for_evidence_processing(evidence_id)
            
            # Step 5: Create storyboard
            storyboard_id = await self.create_storyboard(case_id, evidence_id)
            
            # Step 6: Compile timeline
            timeline_id = await self.compile_timeline(storyboard_id)
            
            # Step 7: Wait for timeline compilation
            await self.wait_for_timeline_compilation(timeline_id)
            
            # Step 8: Start render
            render_id = await self.start_render(timeline_id)
            
            # Step 9: Wait for render completion
            render_result = await self.wait_for_render_completion(render_id)
            
            # Step 10: Verify database rows
            db_verification = await self.verify_database_rows()
            
            # Step 11: Verify custody and WORM lock
            custody_verification = await self.verify_custody_and_worm(evidence_id)
            
            # Test summary
            test_summary = {
                "success": True,
                "case_id": case_id,
                "evidence_id": evidence_id,
                "storyboard_id": storyboard_id,
                "timeline_id": timeline_id,
                "render_id": render_id,
                "database_verification": db_verification,
                "custody_verification": custody_verification,
                "render_output": render_result.get("output_path") if render_result else None
            }
            
            print("\n🎉 E2E Happy Path Test Completed Successfully!")
            print("=" * 50)
            print(f"Case ID: {case_id}")
            print(f"Evidence ID: {evidence_id}")
            print(f"Storyboard ID: {storyboard_id}")
            print(f"Timeline ID: {timeline_id}")
            print(f"Render ID: {render_id}")
            print(f"Database verification: {db_verification}")
            print(f"Custody verification: {custody_verification}")
            
            return test_summary
            
        except Exception as e:
            print(f"\n❌ E2E Happy Path Test Failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_data": self.test_data
            }


@pytest.mark.asyncio
async def test_happy_path():
    """Main E2E happy path test."""
    test_runner = E2EHappyPathTest()
    result = await test_runner.run_happy_path_test()
    
    assert result["success"], f"E2E test failed: {result.get('error', 'Unknown error')}"
    
    # Verify all steps completed
    assert "case_id" in result
    assert "evidence_id" in result
    assert "storyboard_id" in result
    assert "timeline_id" in result
    assert "render_id" in result
    
    # Verify database rows were created
    db_verification = result["database_verification"]
    assert db_verification.get("case", False), "Case not found in database"
    assert db_verification.get("evidence", False), "Evidence not found in database"
    assert db_verification.get("storyboard", False), "Storyboard not found in database"
    assert db_verification.get("timeline", False), "Timeline not found in database"
    assert db_verification.get("render", False), "Render not found in database"
    
    # Verify custody and WORM lock
    custody_verification = result["custody_verification"]
    assert custody_verification.get("custody_recorded", False), "Chain of custody not recorded"
    assert custody_verification.get("worm_locked", False), "WORM lock not applied"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
