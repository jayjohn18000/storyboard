#!/usr/bin/env python3
"""
Test script for Evidence API integration.
Tests the complete flow from API Gateway to Evidence Service.
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any


class EvidenceAPITester:
    def __init__(self):
        self.api_gateway_url = "http://localhost:8000"
        self.evidence_service_url = "http://localhost:8001"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_api_gateway_health(self) -> bool:
        """Test API Gateway health endpoint."""
        try:
            async with self.session.get(f"{self.api_gateway_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API Gateway health: {data}")
                    return True
                else:
                    print(f"❌ API Gateway health failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API Gateway health error: {e}")
            return False
    
    async def test_evidence_service_health(self) -> bool:
        """Test Evidence Service health endpoint."""
        try:
            async with self.session.get(f"{self.evidence_service_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Evidence Service health: {data}")
                    return True
                else:
                    print(f"❌ Evidence Service health failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Evidence Service health error: {e}")
            return False
    
    async def test_evidence_list(self) -> bool:
        """Test listing evidence through API Gateway."""
        try:
            async with self.session.get(f"{self.api_gateway_url}/api/v1/evidence") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Evidence list: {len(data)} items")
                    return True
                else:
                    print(f"❌ Evidence list failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Evidence list error: {e}")
            return False
    
    async def test_evidence_service_list(self) -> bool:
        """Test listing evidence directly from Evidence Service."""
        try:
            async with self.session.get(f"{self.evidence_service_url}/evidence") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Evidence Service list: {data.get('total_count', 0)} items")
                    return True
                else:
                    print(f"❌ Evidence Service list failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Evidence Service list error: {e}")
            return False
    
    async def test_evidence_upload(self) -> str:
        """Test evidence upload through API Gateway."""
        try:
            # Create a test file content
            test_content = b"Test evidence file content for integration testing"
            
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('file', test_content, filename='test_evidence.txt', content_type='text/plain')
            data.add_field('evidence_type', 'document')
            data.add_field('description', 'Test evidence for integration testing')
            data.add_field('tags', '{"test": true}')
            
            async with self.session.post(
                f"{self.api_gateway_url}/api/v1/evidence/upload",
                data=data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    evidence_id = data.get('id')
                    print(f"✅ Evidence upload successful: {evidence_id}")
                    return evidence_id
                else:
                    error_text = await response.text()
                    print(f"❌ Evidence upload failed: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Evidence upload error: {e}")
            return None
    
    async def test_evidence_get(self, evidence_id: str) -> bool:
        """Test getting evidence by ID through API Gateway."""
        try:
            async with self.session.get(f"{self.api_gateway_url}/api/v1/evidence/{evidence_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Evidence get successful: {data.get('id')}")
                    return True
                else:
                    print(f"❌ Evidence get failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Evidence get error: {e}")
            return False
    
    async def test_evidence_commit(self, evidence_id: str) -> bool:
        """Test committing evidence through API Gateway."""
        try:
            async with self.session.post(f"{self.api_gateway_url}/api/v1/evidence/{evidence_id}/commit") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Evidence commit successful: {data.get('status')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Evidence commit failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Evidence commit error: {e}")
            return False
    
    async def test_evidence_chain_of_custody(self, evidence_id: str) -> bool:
        """Test getting chain of custody through API Gateway."""
        try:
            async with self.session.get(f"{self.api_gateway_url}/api/v1/evidence/{evidence_id}/chain-of-custody") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Chain of custody: {len(data)} entries")
                    return True
                else:
                    print(f"❌ Chain of custody failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Chain of custody error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all evidence API integration tests."""
        print("🧪 Starting Evidence API Integration Tests")
        print("=" * 50)
        
        # Test service health
        api_gateway_healthy = await self.test_api_gateway_health()
        evidence_service_healthy = await self.test_evidence_service_health()
        
        if not api_gateway_healthy or not evidence_service_healthy:
            print("❌ Services are not healthy, skipping further tests")
            return False
        
        # Test evidence listing
        await self.test_evidence_list()
        await self.test_evidence_service_list()
        
        # Test evidence upload
        evidence_id = await self.test_evidence_upload()
        if not evidence_id:
            print("❌ Evidence upload failed, skipping further tests")
            return False
        
        # Test evidence operations
        await self.test_evidence_get(evidence_id)
        await self.test_evidence_commit(evidence_id)
        await self.test_evidence_chain_of_custody(evidence_id)
        
        print("=" * 50)
        print("✅ Evidence API Integration Tests Complete")
        return True


async def main():
    """Main test runner."""
    async with EvidenceAPITester() as tester:
        success = await tester.run_all_tests()
        return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
