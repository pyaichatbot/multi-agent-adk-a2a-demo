#!/usr/bin/env python3
"""
Comprehensive Test Runner
Run all tests for SageAI MCP Server without Docker or server
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class ComprehensiveTestRunner:
    """Run all tests comprehensively"""
    
    def __init__(self):
        self.all_test_results = []
        self.test_suites = [
            "policy_engine_standalone",
            "mcp_tools_direct", 
            "sageai_integration"
        ]
        
    async def run_policy_engine_tests(self):
        """Run policy engine standalone tests"""
        print("\n" + "="*60)
        print("🔐 RUNNING POLICY ENGINE TESTS")
        print("="*60)
        
        try:
            from test_policy_engine_standalone import PolicyEngineStandaloneTester
            tester = PolicyEngineStandaloneTester()
            await tester.run_all_tests()
            
            # Collect results
            self.all_test_results.extend(tester.test_results)
            return True
            
        except Exception as e:
            print(f"❌ Policy Engine tests failed: {str(e)}")
            return False
    
    async def run_mcp_tools_tests(self):
        """Run MCP tools direct tests"""
        print("\n" + "="*60)
        print("🛠️ RUNNING MCP TOOLS TESTS")
        print("="*60)
        
        try:
            from test_mcp_tools_direct import MCPToolsDirectTester
            tester = MCPToolsDirectTester()
            await tester.run_all_tests()
            
            # Collect results
            self.all_test_results.extend(tester.test_results)
            return True
            
        except Exception as e:
            print(f"❌ MCP Tools tests failed: {str(e)}")
            return False
    
    async def run_sageai_integration_tests(self):
        """Run SageAI integration tests"""
        print("\n" + "="*60)
        print("🤖 RUNNING SAGEAI INTEGRATION TESTS")
        print("="*60)
        
        try:
            from test_sageai_integration import SageAIIntegrationTester
            tester = SageAIIntegrationTester()
            await tester.run_all_tests()
            
            # Collect results
            self.all_test_results.extend(tester.test_results)
            return True
            
        except Exception as e:
            print(f"❌ SageAI Integration tests failed: {str(e)}")
            return False
    
    async def run_all_test_suites(self):
        """Run all test suites"""
        print("🚀 COMPREHENSIVE SAGEAI MCP SERVER TEST SUITE")
        print("="*80)
        print("Testing without Docker or MCP server")
        print("="*80)
        
        start_time = datetime.now()
        suite_results = {}
        
        # Run Policy Engine Tests
        print("\n1️⃣ Policy Engine Tests")
        suite_results["policy_engine"] = await self.run_policy_engine_tests()
        
        # Run MCP Tools Tests
        print("\n2️⃣ MCP Tools Tests")
        suite_results["mcp_tools"] = await self.run_mcp_tools_tests()
        
        # Run SageAI Integration Tests
        print("\n3️⃣ SageAI Integration Tests")
        suite_results["sageai_integration"] = await self.run_sageai_integration_tests()
        
        # Generate comprehensive report
        await self.generate_comprehensive_report(suite_results, start_time)
    
    async def generate_comprehensive_report(self, suite_results: Dict[str, bool], start_time: datetime):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        # Calculate overall statistics
        total_tests = len(self.all_test_results)
        passed_tests = len([r for r in self.all_test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.all_test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.all_test_results if r["status"] == "ERROR"])
        
        print(f"⏱️  Test Duration: {duration:.2f} seconds")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Errors: {error_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Test suite results
        print(f"\n🏆 Test Suite Results:")
        for suite, success in suite_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} {suite.replace('_', ' ').title()}")
        
        # Detailed results by category
        print(f"\n📋 Detailed Results by Category:")
        categories = {}
        for result in self.all_test_results:
            category = result["test"].split("_")[0]
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0, "errors": 0}
            
            categories[category]["total"] += 1
            if result["status"] == "PASS":
                categories[category]["passed"] += 1
            elif result["status"] == "FAIL":
                categories[category]["failed"] += 1
            else:
                categories[category]["errors"] += 1
        
        for category, stats in categories.items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   📁 {category.title()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Failed tests details
        if failed_tests > 0 or error_tests > 0:
            print(f"\n❌ Failed/Error Tests:")
            for result in self.all_test_results:
                if result["status"] in ["FAIL", "ERROR"]:
                    status_icon = "❌" if result["status"] == "FAIL" else "⚠️"
                    print(f"   {status_icon} {result['test']}: {result.get('details', result.get('error', 'N/A'))}")
        
        # Save comprehensive report
        comprehensive_report = {
            "timestamp": end_time.isoformat(),
            "test_duration_seconds": duration,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": passed_tests/total_tests*100,
            "suite_results": suite_results,
            "category_breakdown": categories,
            "all_results": self.all_test_results
        }
        
        with open("comprehensive_test_report.json", "w") as f:
            json.dump(comprehensive_report, f, indent=2)
        
        print(f"\n📄 Comprehensive report saved to: comprehensive_test_report.json")
        
        # Final status
        if failed_tests == 0 and error_tests == 0:
            print(f"\n🎉 ALL TESTS PASSED! 🎉")
            print(f"SageAI MCP Server is ready for production deployment!")
            print(f"✅ Policy Engine: Working correctly")
            print(f"✅ MCP Tools: All tools functional")
            print(f"✅ SageAI Integration: Platform integration working")
            print(f"✅ Governance: Policy enforcement operational")
        else:
            print(f"\n⚠️  {failed_tests + error_tests} tests failed.")
            print(f"Please review the failed tests above before deployment.")
    
    async def run_quick_smoke_tests(self):
        """Run quick smoke tests for basic functionality"""
        print("💨 QUICK SMOKE TESTS")
        print("="*40)
        
        try:
            # Test policy engine initialization
            from core.policy_engine import policy_engine
            await policy_engine.initialize()
            print("✅ Policy Engine: Initialized")
            
            # Test policy evaluation
            decision = await policy_engine.evaluate_policy(
                "test_user", "admin", "agent", "agent_001", "execute"
            )
            print(f"✅ Policy Evaluation: {'ALLOWED' if decision.allowed else 'DENIED'}")
            
            # Test compliance metrics
            metrics = await policy_engine.get_compliance_metrics()
            print(f"✅ Compliance Metrics: {metrics.get('total_requests', 0)} requests")
            
            print("\n🎉 Quick smoke tests passed! Core functionality is working.")
            return True
            
        except Exception as e:
            print(f"❌ Quick smoke tests failed: {str(e)}")
            return False

async def main():
    """Main test runner function"""
    runner = ComprehensiveTestRunner()
    
    # Check if quick smoke test is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("🚀 Running Quick Smoke Tests...")
        success = await runner.run_quick_smoke_tests()
        sys.exit(0 if success else 1)
    else:
        print("🚀 Running Comprehensive Test Suite...")
        await runner.run_all_test_suites()

if __name__ == "__main__":
    asyncio.run(main())
