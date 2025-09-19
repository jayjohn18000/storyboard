#!/usr/bin/env python3
"""Test script for renders integration."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any

from services.shared.services.database_service import DatabaseService
from services.shared.services.render_service import RenderService


async def test_render_service():
    """Test the render service functionality."""
    print("Testing Render Service Integration...")
    
    # Initialize services
    db_service = DatabaseService()
    render_service = RenderService(db_service)
    
    # Test data
    case_id = str(uuid.uuid4())
    storyboard_id = str(uuid.uuid4())
    timeline_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    print(f"Test case ID: {case_id}")
    print(f"Test storyboard ID: {storyboard_id}")
    print(f"Test timeline ID: {timeline_id}")
    
    try:
        # Test 1: Create render job
        print("\n1. Testing create render job...")
        render_job = await render_service.create_render_job(
            case_id=case_id,
            storyboard_id=storyboard_id,
            timeline_id=timeline_id,
            created_by=user_id,
            render_config={
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "quality": "standard",
                "profile": "neutral",
                "deterministic": True,
                "seed": 42,
                "output_format": "mp4",
                "priority": 0,
            }
        )
        print(f"✅ Created render job: {render_job.id}")
        print(f"   Status: {render_job.status.value}")
        print(f"   Case ID: {render_job.case_id}")
        
        # Test 2: Get render job
        print("\n2. Testing get render job...")
        retrieved_job = await render_service.get_render_job(render_job.id)
        if retrieved_job:
            print(f"✅ Retrieved render job: {retrieved_job.id}")
            print(f"   Status: {retrieved_job.status.value}")
        else:
            print("❌ Failed to retrieve render job")
            return
        
        # Test 3: List render jobs
        print("\n3. Testing list render jobs...")
        renders = await render_service.list_render_jobs(case_id=case_id)
        print(f"✅ Found {len(renders)} render jobs for case")
        for render in renders:
            print(f"   - {render.id}: {render.status.value}")
        
        # Test 4: Update render job
        print("\n4. Testing update render job...")
        updated_job = await render_service.update_render_job(
            render_job.id, 
            priority=1
        )
        if updated_job and updated_job.priority == 1:
            print(f"✅ Updated render job priority to {updated_job.priority}")
        else:
            print("❌ Failed to update render job")
        
        # Test 5: Get render status
        print("\n5. Testing get render status...")
        status = await render_service.get_render_status(render_job.id)
        if status:
            print(f"✅ Retrieved render status:")
            print(f"   Status: {status['status']}")
            print(f"   Progress: {status['progress_percentage']}%")
        else:
            print("❌ Failed to get render status")
        
        # Test 6: Get queue stats
        print("\n6. Testing get queue stats...")
        stats = await render_service.get_queue_stats()
        print(f"✅ Retrieved queue stats:")
        print(f"   Total jobs: {stats['total_jobs']}")
        print(f"   Queued: {stats['queued']}")
        print(f"   Processing: {stats['processing']}")
        print(f"   Completed: {stats['completed']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Cancelled: {stats['cancelled']}")
        
        # Test 7: Cancel render job
        print("\n7. Testing cancel render job...")
        success = await render_service.cancel_render_job(render_job.id)
        if success:
            print(f"✅ Cancelled render job: {render_job.id}")
            
            # Verify status updated
            cancelled_job = await render_service.get_render_job(render_job.id)
            if cancelled_job and cancelled_job.status.value == "cancelled":
                print(f"   Status confirmed: {cancelled_job.status.value}")
            else:
                print("❌ Status not updated to cancelled")
        else:
            print("❌ Failed to cancel render job")
        
        print("\n✅ All render service tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_api_endpoints():
    """Test the API endpoints."""
    print("\nTesting API Endpoints...")
    
    import httpx
    
    base_url = "http://localhost:8000/api/v1/renders"
    
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
            
            # Test 2: List renders
            print("\n2. Testing list renders endpoint...")
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                renders = response.json()
                print(f"✅ Listed {len(renders)} renders")
            else:
                print(f"❌ List renders failed: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Test 3: Get queue stats
            print("\n3. Testing queue stats endpoint...")
            response = await client.get(f"{base_url}/queue/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Retrieved queue stats: {stats}")
            else:
                print(f"❌ Queue stats failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        print("\n✅ API endpoint tests completed!")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("RENDERS INTEGRATION TEST")
    print("=" * 60)
    
    # Test render service
    await test_render_service()
    
    # Test API endpoints
    await test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
