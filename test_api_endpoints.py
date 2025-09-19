#!/usr/bin/env python3
"""
Test script to verify all API endpoints are working correctly.
This will help identify frontend-to-backend pipeline issues.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, List


class APITester:
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
    
    async def test_endpoint(self, method: str, url: str, expected_status: int = 200, **kwargs) -> Dict[str, Any]:
        """Test a single endpoint and return results."""
        try:
            async with self.session.request(method, url, **kwargs) as response:
                try:
                    data = await response.json()
                except:
                    data = await response.text()
                
                return {
                    "url": url,
                    "method": method,
                    "status": response.status,
                    "expected_status": expected_status,
                    "success": response.status == expected_status,
                    "data": data,
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {
                "url": url,
                "method": method,
                "status": "ERROR",
                "expected_status": expected_status,
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def test_all_endpoints(self):
        """Test all API endpoints that the frontend uses."""
        results = []
        
        print("🧪 Testing API Endpoints")
        print("=" * 50)
        
        # Test API Gateway health
        print("\n1. Testing API Gateway Health...")
        result = await self.test_endpoint("GET", f"{self.api_gateway_url}/health")
        results.append(result)
        self.print_result(result)
        
        # Test Evidence Service health
        print("\n2. Testing Evidence Service Health...")
        result = await self.test_endpoint("GET", f"{self.evidence_service_url}/health")
        results.append(result)
        self.print_result(result)
        
        # Test Cases API
        print("\n3. Testing Cases API...")
        result = await self.test_endpoint("GET", f"{self.api_gateway_url}/api/v1/cases")
        results.append(result)
        self.print_result(result)
        
        # Test Evidence API (used by docs page)
        print("\n4. Testing Evidence API...")
        result = await self.test_endpoint("GET", f"{self.api_gateway_url}/api/v1/evidence")
        results.append(result)
        self.print_result(result)
        
        # Test Storyboards API
        print("\n5. Testing Storyboards API...")
        result = await self.test_endpoint("GET", f"{self.api_gateway_url}/api/v1/storyboards")
        results.append(result)
        self.print_result(result)
        
        # Test Renders API (used by renders page)
        print("\n6. Testing Renders API...")
        result = await self.test_endpoint("GET", f"{self.api_gateway_url}/api/v1/renders")
        results.append(result)
        self.print_result(result)
        
        # Test Evidence Service directly
        print("\n7. Testing Evidence Service Direct...")
        result = await self.test_endpoint("GET", f"{self.evidence_service_url}/evidence")
        results.append(result)
        self.print_result(result)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {total - successful}/{total}")
        
        if successful < total:
            print("\n🔍 FAILED ENDPOINTS:")
            for result in results:
                if not result["success"]:
                    print(f"  ❌ {result['method']} {result['url']}")
                    if "error" in result:
                        print(f"     Error: {result['error']}")
                    elif result["status"] != result["expected_status"]:
                        print(f"     Status: {result['status']} (expected {result['expected_status']})")
        
        return results
    
    def print_result(self, result: Dict[str, Any]):
        """Print a single test result."""
        if result["success"]:
            print(f"  ✅ {result['method']} {result['url']} - {result['status']}")
        else:
            print(f"  ❌ {result['method']} {result['url']} - {result.get('status', 'ERROR')}")
            if "error" in result:
                print(f"     Error: {result['error']}")
            elif result.get("status") != result.get("expected_status"):
                print(f"     Expected: {result.get('expected_status')}, Got: {result.get('status')}")


async def main():
    """Main test runner."""
    async with APITester() as tester:
        results = await tester.test_all_endpoints()
        
        # Check if any critical endpoints failed
        critical_endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/api/v1/evidence",
            "http://localhost:8000/api/v1/renders"
        ]
        
        critical_failures = []
        for result in results:
            if result["url"] in critical_endpoints and not result["success"]:
                critical_failures.append(result)
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES FOUND!")
            print("These endpoints are required for the frontend to work:")
            for failure in critical_failures:
                print(f"  ❌ {failure['url']}")
            return False
        else:
            print(f"\n🎉 All critical endpoints are working!")
            return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
