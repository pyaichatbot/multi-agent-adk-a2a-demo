#!/usr/bin/env python3
"""
Test script for SageAI Policy Engine
Demonstrates policy enforcement, compliance monitoring, and governance features
"""

import asyncio
import json
from datetime import datetime
from src.core.policy_engine import policy_engine
from src.core.policy_enforcement import policy_enforcement

async def test_policy_engine():
    """Test policy engine functionality"""
    print("🎯 Testing SageAI Policy Engine")
    print("=" * 50)
    
    # Initialize policy engine
    print("1. Initializing Policy Engine...")
    await policy_engine.initialize()
    print("✅ Policy engine initialized")
    
    # Test policy evaluation
    print("\n2. Testing Policy Evaluation...")
    
    # Test cases
    test_cases = [
        {
            "user_id": "admin_user",
            "user_role": "admin",
            "resource_type": "agent",
            "resource_id": "agent_001",
            "action": "execute",
            "parameters": {"format": "json", "output_type": "detailed"}
        },
        {
            "user_id": "agent_user",
            "user_role": "agent_user", 
            "resource_type": "agent",
            "resource_id": "agent_001",
            "action": "execute",
            "parameters": {"format": "json"}
        },
        {
            "user_id": "tool_user",
            "user_role": "tool_user",
            "resource_type": "tool", 
            "resource_id": "tool_analytics",
            "action": "execute",
            "parameters": {"data_source": "database", "analysis_type": "summary"}
        },
        {
            "user_id": "restricted_user",
            "user_role": "restricted",
            "resource_type": "agent",
            "resource_id": "agent_002",  # This should be denied
            "action": "execute",
            "parameters": {}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test Case {i}: {test_case['user_role']} accessing {test_case['resource_type']}/{test_case['resource_id']}")
        
        decision = await policy_engine.evaluate_policy(
            user_id=test_case["user_id"],
            user_role=test_case["user_role"],
            resource_type=test_case["resource_type"],
            resource_id=test_case["resource_id"],
            action=test_case["action"],
            parameters=test_case.get("parameters")
        )
        
        status = "✅ ALLOWED" if decision.allowed else "❌ DENIED"
        print(f"   Result: {status}")
        print(f"   Reason: {decision.reason}")
        if decision.restrictions:
            print(f"   Restrictions: {decision.restrictions}")
    
    # Test compliance metrics
    print("\n3. Testing Compliance Metrics...")
    metrics = await policy_engine.get_compliance_metrics()
    print(f"   Total Requests: {metrics.get('total_requests', 0)}")
    print(f"   Allowed Requests: {metrics.get('allowed_requests', 0)}")
    print(f"   Denied Requests: {metrics.get('denied_requests', 0)}")
    print(f"   Compliance Rate: {metrics.get('compliance_rate', 0):.1f}%")
    print(f"   Policy Violations: {metrics.get('policy_violations', 0)}")
    
    # Test audit trail
    print("\n4. Testing Audit Trail...")
    audit_trail = await policy_engine.get_audit_trail(limit=10)
    print(f"   Audit Entries: {len(audit_trail)}")
    for entry in audit_trail[:3]:  # Show first 3 entries
        print(f"   - {entry['timestamp']}: {entry['type']} - {entry['user_id']} - {entry['resource_type']}/{entry['resource_id']}")
    
    # Test policy enforcement
    print("\n5. Testing Policy Enforcement...")
    enforcement_result = await policy_enforcement.enforce_policy(
        tool_name="invoke_sageai_agent",
        user_token="test_token_admin",
        parameters={"agent_id": "agent_001", "format": "json"}
    )
    print(f"   Enforcement Result: {'✅ ALLOWED' if enforcement_result.allowed else '❌ DENIED'}")
    print(f"   Reason: {enforcement_result.reason}")
    
    # Test user accessible tools
    print("\n6. Testing User Accessible Tools...")
    accessible_tools = await policy_enforcement.get_user_accessible_tools("test_token_admin")
    print(f"   Accessible Tools: {len(accessible_tools)}")
    for tool in accessible_tools[:5]:  # Show first 5 tools
        print(f"   - {tool}")
    
    # Test compliance report
    print("\n7. Testing Compliance Report...")
    compliance_report = await policy_enforcement.get_compliance_report()
    print(f"   Report Generated: {bool(compliance_report)}")
    if compliance_report:
        print(f"   Policy Metrics Available: {bool(compliance_report.get('policy_metrics'))}")
        print(f"   Audit Trail Available: {bool(compliance_report.get('audit_trail'))}")
        print(f"   Enforcement Stats Available: {bool(compliance_report.get('enforcement_stats'))}")
    
    print("\n🎯 Policy Engine Test Complete!")
    print("=" * 50)

async def test_policy_configuration():
    """Test policy configuration loading"""
    print("\n🔧 Testing Policy Configuration...")
    
    # Test YAML loading
    policies = await policy_engine.load_policies_from_yaml()
    print(f"   YAML Policies Loaded: {bool(policies)}")
    print(f"   Policy Count: {len(policies)}")
    
    # Test database loading (should return False for now)
    db_available = await policy_engine.load_policies_from_database()
    print(f"   Database Available: {db_available}")
    
    # Test policy reload
    print("   Reloading policies...")
    await policy_engine.reload_policies()
    print("   ✅ Policies reloaded successfully")

async def main():
    """Main test function"""
    print("🚀 SageAI Policy Engine Test Suite")
    print("=" * 60)
    
    try:
        # Test policy configuration
        await test_policy_configuration()
        
        # Test policy engine
        await test_policy_engine()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
