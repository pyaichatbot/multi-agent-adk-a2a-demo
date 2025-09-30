#!/usr/bin/env python3
"""
SageAI Integration Tests
Test SageAI agent and tool calls without running the MCP server
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.policy_engine import policy_engine
from core.policy_enforcement import policy_enforcement
from core.sageai_auth import sageai_auth
from core.sageai_observability import sageai_observability
from sageai.agents.agent_client import sageai_agent_client
from sageai.tools.tool_client import sageai_tool_client
from sageai.agents.sageai_agent_tools import SageAIAgentTools
from sageai.tools.sageai_tool_tools import SageAIToolTools

class SageAIIntegrationTester:
    """Test SageAI integration without MCP server"""
    
    def __init__(self):
        self.test_results = []
        self.mock_token = "test_sageai_token_12345"
        self.mock_user_info = {
            "user_id": "test_user_001",
            "role": "admin",
            "permissions": ["can_invoke_agents", "can_execute_tools"]
        }
        
    async def setup_test_environment(self):
        """Setup test environment with mock data"""
        print("🔧 Setting up test environment...")
        
        # Initialize policy engine
        await policy_engine.initialize()
        
        # Mock SageAI auth responses
        sageai_auth.validate_token = self.mock_validate_token
        sageai_auth.get_user_permissions = self.mock_get_user_permissions
        
        # Mock SageAI client responses
        sageai_agent_client.list_agents = self.mock_list_agents
        sageai_agent_client.get_agent_details = self.mock_get_agent_details
        sageai_agent_client.invoke_agent = self.mock_invoke_agent
        
        sageai_tool_client.list_tools = self.mock_list_tools
        sageai_tool_client.get_tool_details = self.mock_get_tool_details
        sageai_tool_client.execute_tool = self.mock_execute_tool
        
        print("✅ Test environment setup complete")
    
    # Mock functions for testing
    async def mock_validate_token(self, token: str) -> Dict[str, Any]:
        """Mock token validation"""
        if token == self.mock_token:
            return self.mock_user_info
        return None
    
    async def mock_get_user_permissions(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Mock user permissions"""
        return {
            "can_invoke_agents": True,
            "can_execute_tools": True,
            "agents": ["agent_001", "agent_003", "agent_005"],
            "tools": ["tool_analytics", "tool_database"]
        }
    
    async def mock_list_agents(self, token: str) -> List[Dict[str, Any]]:
        """Mock list agents response"""
        return [
            {
                "id": "agent_001",
                "name": "Data Analysis Agent",
                "status": "active",
                "description": "Analyzes data and generates insights"
            },
            {
                "id": "agent_003", 
                "name": "Report Generator Agent",
                "status": "active",
                "description": "Generates comprehensive reports"
            },
            {
                "id": "agent_005",
                "name": "Query Processing Agent", 
                "status": "active",
                "description": "Processes natural language queries"
            }
        ]
    
    async def mock_get_agent_details(self, agent_id: str, token: str) -> Dict[str, Any]:
        """Mock get agent details response"""
        agents = {
            "agent_001": {
                "id": "agent_001",
                "name": "Data Analysis Agent",
                "description": "Analyzes data and generates insights",
                "status": "active",
                "capabilities": ["data_analysis", "insight_generation"],
                "parameters": ["data_source", "analysis_type", "output_format"]
            },
            "agent_003": {
                "id": "agent_003",
                "name": "Report Generator Agent", 
                "description": "Generates comprehensive reports",
                "status": "active",
                "capabilities": ["report_generation", "formatting"],
                "parameters": ["report_type", "template", "output_format"]
            }
        }
        return agents.get(agent_id)
    
    async def mock_invoke_agent(self, agent_id: str, input_data: Dict[str, Any], 
                               parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Mock invoke agent response"""
        return {
            "success": True,
            "output": f"Agent {agent_id} executed successfully with input: {input_data}",
            "execution_time": 1.5,
            "status": "completed",
            "result": {
                "analysis": "Mock analysis result",
                "insights": ["Mock insight 1", "Mock insight 2"],
                "confidence": 0.95
            }
        }
    
    async def mock_list_tools(self, token: str) -> List[Dict[str, Any]]:
        """Mock list tools response"""
        return [
            {
                "id": "tool_analytics",
                "name": "Analytics Tool",
                "description": "Performs data analytics operations",
                "status": "active"
            },
            {
                "id": "tool_database",
                "name": "Database Tool", 
                "description": "Executes database queries",
                "status": "active"
            }
        ]
    
    async def mock_get_tool_details(self, tool_id: str, token: str) -> Dict[str, Any]:
        """Mock get tool details response"""
        tools = {
            "tool_analytics": {
                "id": "tool_analytics",
                "name": "Analytics Tool",
                "description": "Performs data analytics operations",
                "status": "active",
                "parameters": ["data_source", "analysis_type", "output_format"]
            },
            "tool_database": {
                "id": "tool_database",
                "name": "Database Tool",
                "description": "Executes database queries", 
                "status": "active",
                "parameters": ["query", "database", "limit"]
            }
        }
        return tools.get(tool_id)
    
    async def mock_execute_tool(self, tool_id: str, parameters: Dict[str, Any], 
                               token: str) -> Dict[str, Any]:
        """Mock execute tool response"""
        return {
            "success": True,
            "output": f"Tool {tool_id} executed successfully with parameters: {parameters}",
            "execution_time": 0.8,
            "result": {
                "data": "Mock tool result data",
                "status": "completed",
                "rows_affected": 42
            }
        }
    
    async def test_policy_engine(self):
        """Test policy engine functionality"""
        print("\n🔐 Testing Policy Engine...")
        
        # Test policy evaluation
        test_cases = [
            {
                "user_id": "test_user_001",
                "user_role": "admin",
                "resource_type": "agent",
                "resource_id": "agent_001",
                "action": "execute",
                "parameters": {"format": "json", "output_type": "detailed"}
            },
            {
                "user_id": "test_user_002", 
                "user_role": "agent_user",
                "resource_type": "agent",
                "resource_id": "agent_003",
                "action": "execute",
                "parameters": {"format": "json"}
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"   Test Case {i}: {test_case['user_role']} accessing {test_case['resource_type']}/{test_case['resource_id']}")
            
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
            
            self.test_results.append({
                "test": f"policy_evaluation_{i}",
                "status": "PASS" if decision.allowed else "FAIL",
                "details": decision.reason
            })
    
    async def test_sageai_agent_tools(self):
        """Test SageAI agent tools"""
        print("\n🤖 Testing SageAI Agent Tools...")
        
        # Test list_sageai_agents
        print("   Testing list_sageai_agents...")
        try:
            result = await SageAIAgentTools.list_sageai_agents(self.mock_token)
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "list_sageai_agents",
                "status": "PASS",
                "details": "Successfully listed SageAI agents"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "list_sageai_agents", 
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test get_sageai_agent_details
        print("   Testing get_sageai_agent_details...")
        try:
            result = await SageAIAgentTools.get_sageai_agent_details("agent_001", self.mock_token)
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "get_sageai_agent_details",
                "status": "PASS", 
                "details": "Successfully retrieved agent details"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "get_sageai_agent_details",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test invoke_sageai_agent
        print("   Testing invoke_sageai_agent...")
        try:
            input_data = {"query": "Analyze sales data for Q1 2024"}
            parameters = {"format": "json", "output_type": "detailed"}
            result = await SageAIAgentTools.invoke_sageai_agent(
                "agent_001", input_data, self.mock_token, parameters
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "invoke_sageai_agent",
                "status": "PASS",
                "details": "Successfully invoked SageAI agent"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "invoke_sageai_agent",
                "status": "FAIL", 
                "details": str(e)
            })
    
    async def test_sageai_tool_tools(self):
        """Test SageAI tool tools"""
        print("\n🛠️ Testing SageAI Tool Tools...")
        
        # Test list_sageai_tools
        print("   Testing list_sageai_tools...")
        try:
            result = await SageAIToolTools.list_sageai_tools(self.mock_token)
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "list_sageai_tools",
                "status": "PASS",
                "details": "Successfully listed SageAI tools"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "list_sageai_tools",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test get_sageai_tool_details
        print("   Testing get_sageai_tool_details...")
        try:
            result = await SageAIToolTools.get_sageai_tool_details("tool_analytics", self.mock_token)
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "get_sageai_tool_details",
                "status": "PASS",
                "details": "Successfully retrieved tool details"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "get_sageai_tool_details",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test execute_sageai_tool
        print("   Testing execute_sageai_tool...")
        try:
            parameters = {"data_source": "sales_db", "analysis_type": "summary"}
            result = await SageAIToolTools.execute_sageai_tool(
                "tool_analytics", parameters, self.mock_token
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "execute_sageai_tool",
                "status": "PASS",
                "details": "Successfully executed SageAI tool"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "execute_sageai_tool",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_policy_enforcement(self):
        """Test policy enforcement integration"""
        print("\n🛡️ Testing Policy Enforcement...")
        
        # Test policy enforcement for agent tools
        print("   Testing policy enforcement for agent tools...")
        try:
            decision = await policy_enforcement.enforce_policy(
                "invoke_sageai_agent", self.mock_token, {"agent_id": "agent_001"}
            )
            status = "✅ ALLOWED" if decision.allowed else "❌ DENIED"
            print(f"   Agent Policy Enforcement: {status}")
            print(f"   Reason: {decision.reason}")
            
            self.test_results.append({
                "test": "agent_policy_enforcement",
                "status": "PASS" if decision.allowed else "FAIL",
                "details": decision.reason
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "agent_policy_enforcement",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test policy enforcement for tool tools
        print("   Testing policy enforcement for tool tools...")
        try:
            decision = await policy_enforcement.enforce_policy(
                "execute_sageai_tool", self.mock_token, {"tool_id": "tool_analytics"}
            )
            status = "✅ ALLOWED" if decision.allowed else "❌ DENIED"
            print(f"   Tool Policy Enforcement: {status}")
            print(f"   Reason: {decision.reason}")
            
            self.test_results.append({
                "test": "tool_policy_enforcement",
                "status": "PASS" if decision.allowed else "FAIL",
                "details": decision.reason
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "tool_policy_enforcement",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_compliance_monitoring(self):
        """Test compliance monitoring and metrics"""
        print("\n📊 Testing Compliance Monitoring...")
        
        # Test compliance metrics
        print("   Testing compliance metrics...")
        try:
            metrics = await policy_engine.get_compliance_metrics()
            print(f"   Compliance Rate: {metrics.get('compliance_rate', 0):.1f}%")
            print(f"   Total Requests: {metrics.get('total_requests', 0)}")
            print(f"   Policy Violations: {metrics.get('policy_violations', 0)}")
            
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
        
        # Test audit trail
        print("   Testing audit trail...")
        try:
            audit_trail = await policy_engine.get_audit_trail(limit=10)
            print(f"   Audit Entries: {len(audit_trail)}")
            
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
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting SageAI Integration Tests")
        print("=" * 60)
        
        try:
            # Setup test environment
            await self.setup_test_environment()
            
            # Run all test suites
            await self.test_policy_engine()
            await self.test_sageai_agent_tools()
            await self.test_sageai_tool_tools()
            await self.test_policy_enforcement()
            await self.test_compliance_monitoring()
            
            # Generate test report
            await self.generate_test_report()
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Test Report")
        print("=" * 40)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {result['test']}: {result['details']}")
        
        # Save test report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "results": self.test_results
        }
        
        with open("test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Test report saved to: test_report.json")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! SageAI integration is working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Please check the details above.")

async def main():
    """Main test function"""
    tester = SageAIIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
