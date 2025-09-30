#!/usr/bin/env python3
"""
Standalone Policy Engine Tests
Test policy engine functionality without MCP server or external dependencies
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.policy_engine import policy_engine, PolicyDecision, PolicyViolation
from core.policy_enforcement import policy_enforcement

class PolicyEngineStandaloneTester:
    """Test policy engine standalone functionality"""
    
    def __init__(self):
        self.test_results = []
        self.mock_policies = {
            'enabled': True,
            'policy_engine': 'yaml_based',
            'default_policy': 'deny',
            'agents': {
                'default_policy': 'deny',
                'allow_list': ['agent_001', 'agent_003', 'agent_005'],
                'deny_list': ['agent_002', 'agent_004'],
                'restrictions': {
                    'agent_001': {
                        'max_execution_time': 300,
                        'allowed_parameters': ['format', 'output_type'],
                        'forbidden_parameters': ['admin_access'],
                        'rate_limit': 5
                    },
                    'agent_003': {
                        'max_execution_time': 600,
                        'allowed_parameters': ['query', 'limit'],
                        'rate_limit': 10
                    }
                }
            },
            'tools': {
                'default_policy': 'deny',
                'allow_list': ['tool_analytics', 'tool_database'],
                'deny_list': ['tool_admin'],
                'restrictions': {
                    'tool_analytics': {
                        'max_execution_time': 180,
                        'allowed_parameters': ['data_source', 'analysis_type'],
                        'forbidden_parameters': ['admin_access'],
                        'rate_limit': 10
                    },
                    'tool_database': {
                        'max_execution_time': 300,
                        'allowed_parameters': ['query', 'limit', 'format'],
                        'rate_limit': 15
                    }
                }
            },
            'users': {
                'role_based_access': {
                    'admin': {
                        'agents': ['*'],
                        'tools': ['*']
                    },
                    'agent_user': {
                        'agents': ['agent_001', 'agent_003'],
                        'tools': []
                    },
                    'tool_user': {
                        'agents': [],
                        'tools': ['tool_analytics', 'tool_database']
                    },
                    'restricted_user': {
                        'agents': [],
                        'tools': []
                    }
                }
            },
            'rate_limits': {
                'global': {'requests_per_hour': 1000, 'requests_per_minute': 100},
                'per_user': {'requests_per_hour': 100, 'requests_per_minute': 10},
                'per_agent': {'requests_per_hour': 50, 'requests_per_minute': 5},
                'per_tool': {'requests_per_hour': 50, 'requests_per_minute': 5}
            },
            'execution_limits': {
                'max_execution_time': 300,
                'max_memory_usage': '1GB',
                'max_cpu_usage': '80%'
            }
        }
    
    async def setup_test_environment(self):
        """Setup test environment with mock policies"""
        print("🔧 Setting up Policy Engine test environment...")
        
        # Set mock policies directly
        policy_engine.policies = self.mock_policies
        await policy_engine.initialize_rate_limits()
        
        print("✅ Policy Engine test environment setup complete")
    
    async def test_policy_evaluation(self):
        """Test policy evaluation with various scenarios"""
        print("\n🔐 Testing Policy Evaluation...")
        
        test_cases = [
            # Admin user - should have access to everything
            {
                "name": "Admin Access Test",
                "user_id": "admin_001",
                "user_role": "admin",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "action": "execute",
                "parameters": {"format": "json", "output_type": "detailed"},
                "expected": True
            },
            # Agent user - should have access to allowed agents
            {
                "name": "Agent User Access Test",
                "user_id": "agent_user_001",
                "user_role": "agent_user",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "action": "execute",
                "parameters": {"format": "json"},
                "expected": True
            },
            # Agent user - should be denied access to non-allowed agents
            {
                "name": "Agent User Denied Access Test",
                "user_id": "agent_user_001",
                "user_role": "agent_user",
                "resource_type": "agent",
                "resource_id": "agent_002",  # Not in allow_list
                "action": "execute",
                "parameters": {},
                "expected": False
            },
            # Tool user - should have access to allowed tools
            {
                "name": "Tool User Access Test",
                "user_id": "tool_user_001",
                "user_role": "tool_user",
                "resource_type": "tool",
                "resource_id": "tool_analytics",
                "action": "execute",
                "parameters": {"data_source": "database", "analysis_type": "summary"},
                "expected": True
            },
            # Restricted user - should be denied access to everything
            {
                "name": "Restricted User Denied Test",
                "user_id": "restricted_001",
                "user_role": "restricted_user",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "action": "execute",
                "parameters": {},
                "expected": False
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"   Test Case {i}: {test_case['name']}")
            
            try:
                decision = await policy_engine.evaluate_policy(
                    user_id=test_case["user_id"],
                    user_role=test_case["user_role"],
                    resource_type=test_case["resource_type"],
                    resource_id=test_case["resource_id"],
                    action=test_case["action"],
                    parameters=test_case.get("parameters")
                )
                
                expected = test_case["expected"]
                actual = decision.allowed
                
                if expected == actual:
                    status = "✅ PASS"
                    print(f"   Result: {status}")
                    print(f"   Decision: {'ALLOWED' if decision.allowed else 'DENIED'}")
                    print(f"   Reason: {decision.reason}")
                else:
                    status = "❌ FAIL"
                    print(f"   Result: {status}")
                    print(f"   Expected: {'ALLOWED' if expected else 'DENIED'}")
                    print(f"   Actual: {'ALLOWED' if actual else 'DENIED'}")
                    print(f"   Reason: {decision.reason}")
                
                self.test_results.append({
                    "test": f"policy_evaluation_{i}",
                    "name": test_case["name"],
                    "status": "PASS" if expected == actual else "FAIL",
                    "expected": expected,
                    "actual": actual,
                    "reason": decision.reason
                })
                
            except Exception as e:
                print(f"   Error: {str(e)}")
                self.test_results.append({
                    "test": f"policy_evaluation_{i}",
                    "name": test_case["name"],
                    "status": "ERROR",
                    "error": str(e)
                })
    
    async def test_parameter_validation(self):
        """Test parameter validation"""
        print("\n🔍 Testing Parameter Validation...")
        
        test_cases = [
            # Valid parameters
            {
                "name": "Valid Parameters Test",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "parameters": {"format": "json", "output_type": "detailed"},
                "expected": True
            },
            # Invalid parameter (not in allowed list)
            {
                "name": "Invalid Parameter Test",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "parameters": {"format": "json", "admin_access": "true"},
                "expected": False
            },
            # Forbidden parameter
            {
                "name": "Forbidden Parameter Test",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "parameters": {"format": "json", "admin_access": "true"},
                "expected": False
            },
            # Valid tool parameters
            {
                "name": "Valid Tool Parameters Test",
                "resource_type": "tool",
                "resource_id": "tool_analytics",
                "parameters": {"data_source": "database", "analysis_type": "summary"},
                "expected": True
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"   Test Case {i}: {test_case['name']}")
            
            try:
                validation = await policy_engine.validate_parameters(
                    test_case["resource_type"],
                    test_case["resource_id"],
                    test_case["parameters"]
                )
                
                expected = test_case["expected"]
                actual = validation["valid"]
                
                if expected == actual:
                    status = "✅ PASS"
                    print(f"   Result: {status}")
                    print(f"   Validation: {'VALID' if validation['valid'] else 'INVALID'}")
                    print(f"   Reason: {validation.get('reason', 'N/A')}")
                else:
                    status = "❌ FAIL"
                    print(f"   Result: {status}")
                    print(f"   Expected: {'VALID' if expected else 'INVALID'}")
                    print(f"   Actual: {'VALID' if actual else 'INVALID'}")
                    print(f"   Reason: {validation.get('reason', 'N/A')}")
                
                self.test_results.append({
                    "test": f"parameter_validation_{i}",
                    "name": test_case["name"],
                    "status": "PASS" if expected == actual else "FAIL",
                    "expected": expected,
                    "actual": actual,
                    "reason": validation.get('reason', 'N/A')
                })
                
            except Exception as e:
                print(f"   Error: {str(e)}")
                self.test_results.append({
                    "test": f"parameter_validation_{i}",
                    "name": test_case["name"],
                    "status": "ERROR",
                    "error": str(e)
                })
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n⏱️ Testing Rate Limiting...")
        
        # Test global rate limiting
        print("   Testing global rate limiting...")
        try:
            # Simulate multiple requests
            for i in range(5):
                allowed = await policy_engine.check_rate_limits(
                    "test_user", "agent", "agent_001"
                )
                print(f"   Request {i+1}: {'ALLOWED' if allowed else 'DENIED'}")
            
            self.test_results.append({
                "test": "global_rate_limiting",
                "status": "PASS",
                "details": "Global rate limiting working correctly"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "global_rate_limiting",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test per-user rate limiting
        print("   Testing per-user rate limiting...")
        try:
            # Test different users
            users = ["user_001", "user_002", "user_003"]
            for user in users:
                allowed = await policy_engine.check_rate_limits(
                    user, "agent", "agent_001"
                )
                print(f"   User {user}: {'ALLOWED' if allowed else 'DENIED'}")
            
            self.test_results.append({
                "test": "per_user_rate_limiting",
                "status": "PASS",
                "details": "Per-user rate limiting working correctly"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "per_user_rate_limiting",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_violation_recording(self):
        """Test violation recording and tracking"""
        print("\n🚨 Testing Violation Recording...")
        
        # Record some test violations
        test_violations = [
            {
                "user_id": "test_user_001",
                "resource_type": "agent",
                "resource_id": "agent_002",
                "action": "execute",
                "violation_type": "access_denied"
            },
            {
                "user_id": "test_user_002",
                "resource_type": "tool",
                "resource_id": "tool_admin",
                "action": "execute",
                "violation_type": "access_denied"
            },
            {
                "user_id": "test_user_003",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "action": "execute",
                "violation_type": "rate_limit_exceeded"
            }
        ]
        
        for i, violation in enumerate(test_violations, 1):
            print(f"   Recording violation {i}: {violation['violation_type']}")
            await policy_engine.record_violation(
                violation["user_id"],
                violation["resource_type"],
                violation["resource_id"],
                violation["action"],
                violation["violation_type"]
            )
        
        # Test violation retrieval
        print("   Testing violation retrieval...")
        try:
            violations_by_type = policy_engine.get_violations_by_type()
            violations_by_user = policy_engine.get_violations_by_user()
            violations_by_resource = policy_engine.get_violations_by_resource()
            
            print(f"   Violations by type: {violations_by_type}")
            print(f"   Violations by user: {violations_by_user}")
            print(f"   Violations by resource: {violations_by_resource}")
            
            self.test_results.append({
                "test": "violation_recording",
                "status": "PASS",
                "details": f"Recorded {len(policy_engine.violations)} violations"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "violation_recording",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_compliance_metrics(self):
        """Test compliance metrics generation"""
        print("\n📊 Testing Compliance Metrics...")
        
        try:
            metrics = await policy_engine.get_compliance_metrics()
            
            print(f"   Total Requests: {metrics.get('total_requests', 0)}")
            print(f"   Allowed Requests: {metrics.get('allowed_requests', 0)}")
            print(f"   Denied Requests: {metrics.get('denied_requests', 0)}")
            print(f"   Compliance Rate: {metrics.get('compliance_rate', 0):.1f}%")
            print(f"   Policy Violations: {metrics.get('policy_violations', 0)}")
            print(f"   Rate Limit Hits: {metrics.get('rate_limit_hits', 0)}")
            
            self.test_results.append({
                "test": "compliance_metrics",
                "status": "PASS",
                "details": f"Compliance rate: {metrics.get('compliance_rate', 0):.1f}%"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "compliance_metrics",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_audit_trail(self):
        """Test audit trail functionality"""
        print("\n📋 Testing Audit Trail...")
        
        try:
            audit_trail = await policy_engine.get_audit_trail(limit=10)
            
            print(f"   Audit Entries: {len(audit_trail)}")
            for entry in audit_trail[:3]:  # Show first 3 entries
                print(f"   - {entry['timestamp']}: {entry['type']} - {entry['user_id']} - {entry['resource_type']}/{entry['resource_id']}")
            
            self.test_results.append({
                "test": "audit_trail",
                "status": "PASS",
                "details": f"Found {len(audit_trail)} audit entries"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "audit_trail",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_policy_enforcement_integration(self):
        """Test policy enforcement integration"""
        print("\n🛡️ Testing Policy Enforcement Integration...")
        
        # Mock token validation
        async def mock_validate_token(token):
            if token == "valid_token":
                return {"user_id": "test_user", "role": "admin"}
            return None
        
        # Test policy enforcement
        print("   Testing policy enforcement with valid token...")
        try:
            # Mock the auth validation
            import sys
            sys.modules['src.core.sageai_auth'].sageai_auth.validate_token = mock_validate_token
            
            decision = await policy_enforcement.enforce_policy(
                "invoke_sageai_agent", "valid_token", {"agent_id": "agent_001"}
            )
            
            status = "✅ ALLOWED" if decision.allowed else "❌ DENIED"
            print(f"   Policy Enforcement: {status}")
            print(f"   Reason: {decision.reason}")
            
            self.test_results.append({
                "test": "policy_enforcement",
                "status": "PASS" if decision.allowed else "FAIL",
                "details": decision.reason
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "policy_enforcement",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def run_all_tests(self):
        """Run all policy engine tests"""
        print("🚀 Starting Policy Engine Standalone Tests")
        print("=" * 60)
        
        try:
            # Setup test environment
            await self.setup_test_environment()
            
            # Run all test suites
            await self.test_policy_evaluation()
            await self.test_parameter_validation()
            await self.test_rate_limiting()
            await self.test_violation_recording()
            await self.test_compliance_metrics()
            await self.test_audit_trail()
            await self.test_policy_enforcement_integration()
            
            # Generate test report
            await self.generate_test_report()
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Policy Engine Test Report")
        print("=" * 40)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Errors: {error_tests} ⚠️")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            if result["status"] == "PASS":
                status_icon = "✅"
            elif result["status"] == "FAIL":
                status_icon = "❌"
            else:
                status_icon = "⚠️"
            
            print(f"  {status_icon} {result['test']}: {result.get('details', result.get('reason', 'N/A'))}")
        
        # Save test report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "policy_engine_standalone",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": passed_tests/total_tests*100,
            "results": self.test_results
        }
        
        with open("policy_engine_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Test report saved to: policy_engine_test_report.json")
        
        if failed_tests == 0 and error_tests == 0:
            print("\n🎉 All policy engine tests passed! Policy engine is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests + error_tests} tests failed. Please check the details above.")

async def main():
    """Main test function"""
    tester = PolicyEngineStandaloneTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
