#!/usr/bin/env python3
"""Test script for evidence integration."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any

from services.shared.services.database_service import DatabaseService
from services.shared.services.evidence_service import EvidenceService
from services.shared.models.evidence import EvidenceType


async def test_evidence_service():
    """Test the evidence service functionality."""
    print("Testing Evidence Service Integration...")
    
    # Initialize services
    db_service = DatabaseService()
    evidence_service = EvidenceService(db_service)
    
    # Test data
    case_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    print(f"Test case ID: {case_id}")
    print(f"Test user ID: {user_id}")
    
    try:
        # Test 1: Store evidence
        print("\n1. Testing store evidence...")
        test_file_data = b"This is a test document content for evidence upload."
        
        evidence = await evidence_service.store_evidence(
            file_data=test_file_data,
            filename="test_document.txt",
            mime_type="text/plain",
            evidence_type=EvidenceType.DOCUMENT,
            case_id=case_id,
            uploaded_by=user_id,
            description="Test evidence document",
            tags={"test": True, "category": "sample"}
        )
        print(f"✅ Stored evidence: {evidence.id}")
        print(f"   Status: {evidence.status.value}")
        print(f"   Case ID: {evidence.case_id}")
        print(f"   Storage ID: {evidence.storage_id}")
        print(f"   Chain of custody entries: {len(evidence.chain_of_custody)}")
        
        # Test 2: Get evidence
        print("\n2. Testing get evidence...")
        retrieved_evidence = await evidence_service.get_evidence(evidence.id)
        if retrieved_evidence:
            print(f"✅ Retrieved evidence: {retrieved_evidence.id}")
            print(f"   Filename: {retrieved_evidence.metadata.filename}")
            print(f"   File size: {retrieved_evidence.metadata.file_size} bytes")
            print(f"   Checksum: {retrieved_evidence.metadata.checksum}")
        else:
            print("❌ Failed to retrieve evidence")
            return
        
        # Test 3: List evidence
        print("\n3. Testing list evidence...")
        evidence_list = await evidence_service.list_evidence(case_id=case_id)
        print(f"✅ Found {len(evidence_list)} evidence items for case")
        for ev in evidence_list:
            print(f"   - {ev.id}: {ev.metadata.filename} ({ev.status.value})")
        
        # Test 4: Download evidence
        print("\n4. Testing download evidence...")
        downloaded_data = await evidence_service.download_evidence(evidence.id)
        if downloaded_data:
            print(f"✅ Downloaded evidence: {len(downloaded_data)} bytes")
            print(f"   Content matches: {downloaded_data == test_file_data}")
            
            # Check chain of custody was updated
            updated_evidence = await evidence_service.get_evidence(evidence.id)
            print(f"   Chain of custody entries: {len(updated_evidence.chain_of_custody)}")
        else:
            print("❌ Failed to download evidence")
        
        # Test 5: Update evidence
        print("\n5. Testing update evidence...")
        updated_evidence = await evidence_service.update_evidence(
            evidence.id,
            case_metadata={
                "description": "Updated test evidence",
                "tags": {"test": True, "category": "sample", "updated": True}
            }
        )
        if updated_evidence:
            print(f"✅ Updated evidence: {updated_evidence.id}")
            print(f"   Description: {updated_evidence.metadata.description}")
        else:
            print("❌ Failed to update evidence")
        
        # Test 6: Process evidence
        print("\n6. Testing process evidence...")
        processing_success = await evidence_service.process_evidence(evidence.id)
        if processing_success:
            print(f"✅ Processed evidence: {evidence.id}")
            
            # Check processing results
            processed_evidence = await evidence_service.get_evidence(evidence.id)
            if processed_evidence and processed_evidence.processing_result:
                print(f"   Processing confidence: {processed_evidence.processing_result.confidence_scores}")
                print(f"   Extracted text: {processed_evidence.processing_result.extracted_text[:50]}...")
        else:
            print("❌ Failed to process evidence")
        
        # Test 7: Apply WORM lock
        print("\n7. Testing apply WORM lock...")
        worm_success = await evidence_service.apply_worm_lock(evidence.id)
        if worm_success:
            print(f"✅ Applied WORM lock to evidence: {evidence.id}")
            
            # Check WORM lock status
            locked_evidence = await evidence_service.get_evidence(evidence.id)
            print(f"   WORM locked: {locked_evidence.worm_locked}")
            print(f"   Chain of custody entries: {len(locked_evidence.chain_of_custody)}")
        else:
            print("❌ Failed to apply WORM lock")
        
        # Test 8: Delete evidence
        print("\n8. Testing delete evidence...")
        delete_success = await evidence_service.delete_evidence(evidence.id)
        if delete_success:
            print(f"✅ Deleted evidence: {evidence.id}")
            
            # Verify deletion
            deleted_evidence = await evidence_service.get_evidence(evidence.id)
            if not deleted_evidence:
                print("   Evidence successfully removed from database")
            else:
                print("❌ Evidence still exists after deletion")
        else:
            print("❌ Failed to delete evidence")
        
        print("\n✅ All evidence service tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_api_endpoints():
    """Test the evidence API endpoints."""
    print("\nTesting Evidence API Endpoints...")
    
    import httpx
    
    base_url = "http://localhost:8000/api/v1/evidence"
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Health check
            print("\n1. Testing API health...")
            try:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print("✅ API Gateway is healthy")
                else:
                    print(f"❌ API Gateway health check failed: {response.status_code}")
                    return
            except Exception as e:
                print(f"❌ Cannot connect to API Gateway: {e}")
                return
            
            # Test 2: List evidence
            print("\n2. Testing list evidence endpoint...")
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                evidence_list = response.json()
                print(f"✅ Listed {len(evidence_list)} evidence items")
            else:
                print(f"❌ List evidence failed: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Test 3: Upload evidence (simulated)
            print("\n3. Testing upload evidence endpoint...")
            test_file_content = b"This is a test file for evidence upload."
            files = {"file": ("test.txt", test_file_content, "text/plain")}
            data = {
                "evidence_type": "document",
                "case_id": str(uuid.uuid4()),
                "description": "Test evidence upload",
                "tags": '{"test": true}'
            }
            
            response = await client.post(
                f"{base_url}/upload",
                files=files,
                data=data
            )
            
            if response.status_code == 201:
                evidence_data = response.json()
                print(f"✅ Uploaded evidence: {evidence_data['id']}")
                print(f"   Status: {evidence_data['status']}")
                print(f"   Case ID: {evidence_data['case_id']}")
            else:
                print(f"❌ Upload evidence failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        print("\n✅ Evidence API endpoint tests completed!")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("EVIDENCE INTEGRATION TEST")
    print("=" * 60)
    
    # Test evidence service
    await test_evidence_service()
    
    # Test API endpoints
    await test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
