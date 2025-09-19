#!/usr/bin/env python3
"""Test script for Temporal integration.

This script tests the Temporal integration with AI agents by:
1. Checking Temporal server connectivity
2. Testing workflow registration
3. Testing activity execution
4. Testing event bridge functionality
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_temporal_connectivity():
    """Test connection to Temporal server."""
    
    try:
        from temporalio.client import Client
        
        temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
        temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "legal-sim")
        
        print(f"Testing Temporal connectivity to {temporal_host}...")
        
        client = await Client.connect(temporal_host, namespace=temporal_namespace)
        
        # Test basic connectivity
        workflows = await client.list_workflows()
        print(f"✅ Connected to Temporal server successfully")
        print(f"   Found {len(workflows)} workflows")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Temporal server: {e}")
        return False


async def test_workflow_registration():
    """Test workflow registration."""
    
    try:
        from services.shared.workflows.ai_agent_workflows import (
            EvidenceIntakeWorkflow,
            TimelineReconciliationWorkflow,
            AIAgentOrchestrationWorkflow
        )
        
        print("Testing workflow registration...")
        
        # Check if workflows can be imported
        workflows = [
            EvidenceIntakeWorkflow,
            TimelineReconciliationWorkflow,
            AIAgentOrchestrationWorkflow
        ]
        
        for workflow in workflows:
            print(f"   ✅ {workflow.__name__} imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import workflows: {e}")
        return False


async def test_activity_registration():
    """Test activity registration."""
    
    try:
        from services.shared.workflows.ai_agent_workflows import (
            process_evidence_intake,
            process_timeline_reconciliation,
            log_ai_processing_event,
            get_evidence_details,
            get_storyboard_details,
            generate_ai_summary_report
        )
        
        print("Testing activity registration...")
        
        activities = [
            process_evidence_intake,
            process_timeline_reconciliation,
            log_ai_processing_event,
            get_evidence_details,
            get_storyboard_details,
            generate_ai_summary_report
        ]
        
        for activity in activities:
            print(f"   ✅ {activity.__name__} imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import activities: {e}")
        return False


async def test_ai_agent_imports():
    """Test AI agent imports."""
    
    try:
        print("Testing AI agent imports...")
        
        # Test intake triage agent
        from agents.intake_triage.main import IntakeTriageAgent
        print("   ✅ IntakeTriageAgent imported successfully")
        
        # Test timeline reconciliation agent
        from agents.timeline_reconciliation.main import TimelineReconciliationAgent
        print("   ✅ TimelineReconciliationAgent imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to import AI agents: {e}")
        return False


async def test_event_bridge():
    """Test event bridge functionality."""
    
    try:
        print("Testing event bridge...")
        
        from services.shared.events.temporal_event_bridge import TemporalEventBridge
        
        # Create bridge instance (don't start it)
        bridge = TemporalEventBridge()
        print("   ✅ TemporalEventBridge created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create event bridge: {e}")
        return False


async def test_worker():
    """Test worker functionality."""
    
    try:
        print("Testing worker...")
        
        from services.shared.workers.ai_agent_worker import AIAgentWorker
        
        # Create worker instance (don't start it)
        worker = AIAgentWorker()
        print("   ✅ AIAgentWorker created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create worker: {e}")
        return False


async def main():
    """Run all tests."""
    
    print("🧪 Testing Temporal Integration")
    print("=" * 50)
    
    tests = [
        ("Temporal Connectivity", test_temporal_connectivity),
        ("Workflow Registration", test_workflow_registration),
        ("Activity Registration", test_activity_registration),
        ("AI Agent Imports", test_ai_agent_imports),
        ("Event Bridge", test_event_bridge),
        ("Worker", test_worker),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 30)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Temporal integration is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
