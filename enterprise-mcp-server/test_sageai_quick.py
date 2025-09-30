#!/usr/bin/env python3
"""
Quick SageAI Test Script
Test SageAI integration without running the full test suite
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_sageai_quick():
    """Quick test of SageAI integration"""
    print("🚀 Quick SageAI Integration Test")
    print("=" * 50)
    
    try:
        # Test policy engine initialization
        print("1. Testing Policy Engine...")
        from core.policy_engine import policy_engine
        await policy_engine.initialize()
        print("   ✅ Policy engine initialized")
        
        # Test policy evaluation
        decision = await policy_engine.evaluate_policy(
            "test_user", "admin", "agent", "agent_001", "execute"
        )
        print(f"   ✅ Policy evaluation: {'ALLOWED' if decision.allowed else 'DENIED'}")
        
        # Test compliance metrics
        metrics = await policy_engine.get_compliance_metrics()
        print(f"   ✅ Compliance metrics: {metrics.get('total_requests', 0)} requests")
        
        # Test SageAI agent tools (with mocks)
        print("\n2. Testing SageAI Agent Tools...")
        from sageai.agents.sageai_agent_tools import SageAIAgentTools
        
        # Mock the auth and client functions
        async def mock_validate_token(token):
            return {"user_id": "test_user", "role": "admin"}
        
        async def mock_get_user_permissions(user_info):
            return {"can_invoke_agents": True}
        
        async def mock_list_agents(token):
            return [{"id": "agent_001", "name": "Test Agent", "status": "active"}]
        
        # Apply mocks
        import sys
        sys.modules['core.sageai_auth'].sageai_auth.validate_token = mock_validate_token
        sys.modules['core.sageai_auth'].sageai_auth.get_user_permissions = mock_get_user_permissions
        sys.modules['sageai.agents.agent_client'].sageai_agent_client.list_agents = mock_list_agents
        
        # Test list agents
        result = await SageAIAgentTools.list_sageai_agents("test_token")
        print(f"   ✅ List agents: {result[:50]}...")
        
        # Test SageAI tool tools
        print("\n3. Testing SageAI Tool Tools...")
        from sageai.tools.sageai_tool_tools import SageAIToolTools
        
        async def mock_list_tools(token):
            return [{"id": "tool_001", "name": "Test Tool", "status": "active"}]
        
        sys.modules['sageai.tools.tool_client'].sageai_tool_client.list_tools = mock_list_tools
        
        # Test list tools
        result = await SageAIToolTools.list_sageai_tools("test_token")
        print(f"   ✅ List tools: {result[:50]}...")
        
        # Test policy enforcement
        print("\n4. Testing Policy Enforcement...")
        from core.policy_enforcement import policy_enforcement
        
        decision = await policy_enforcement.enforce_policy(
            "invoke_sageai_agent", "test_token", {"agent_id": "agent_001"}
        )
        print(f"   ✅ Policy enforcement: {'ALLOWED' if decision.allowed else 'DENIED'}")
        
        print("\n🎉 All quick tests passed!")
        print("✅ Policy Engine: Working")
        print("✅ SageAI Agent Tools: Working")
        print("✅ SageAI Tool Tools: Working")
        print("✅ Policy Enforcement: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Quick test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_sageai_quick()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
