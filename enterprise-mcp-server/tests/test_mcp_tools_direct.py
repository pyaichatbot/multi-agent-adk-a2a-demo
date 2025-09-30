#!/usr/bin/env python3
"""
Direct MCP Tools Tests
Test MCP tools directly without running the MCP server
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.database_tools import DatabaseTools
from tools.analytics_tools import AnalyticsTools
from tools.document_tools import DocumentTools
from tools.system_tools import SystemTools
from sageai.agents.sageai_agent_tools import SageAIAgentTools
from sageai.tools.sageai_tool_tools import SageAIToolTools

class MCPToolsDirectTester:
    """Test MCP tools directly without server"""
    
    def __init__(self):
        self.test_results = []
        self.mock_token = "test_sageai_token_12345"
        
    async def setup_test_environment(self):
        """Setup test environment"""
        print("🔧 Setting up MCP Tools test environment...")
        
        # Import and mock SageAI auth responses
        from src.core.sageai_auth import sageai_auth
        sageai_auth.validate_token = self.mock_validate_token
        sageai_auth.get_user_permissions = self.mock_get_user_permissions
        
        # Import and mock SageAI client responses
        from src.sageai.agents.agent_client import sageai_agent_client
        from src.sageai.tools.tool_client import sageai_tool_client
        
        sageai_agent_client.list_agents = self.mock_list_agents
        sageai_agent_client.get_agent_details = self.mock_get_agent_details
        sageai_agent_client.invoke_agent = self.mock_invoke_agent
        
        sageai_tool_client.list_tools = self.mock_list_tools
        sageai_tool_client.get_tool_details = self.mock_get_tool_details
        sageai_tool_client.execute_tool = self.mock_execute_tool
        
        print("✅ MCP Tools test environment setup complete")
    
    # Mock functions
    async def mock_validate_token(self, token: str) -> Dict[str, Any]:
        """Mock token validation"""
        if token == self.mock_token:
            return {
                "user_id": "test_user_001",
                "role": "admin",
                "permissions": ["can_invoke_agents", "can_execute_tools"]
            }
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
            }
        ]
    
    async def mock_get_agent_details(self, agent_id: str, token: str) -> Dict[str, Any]:
        """Mock get agent details response"""
        return {
            "id": agent_id,
            "name": f"Agent {agent_id}",
            "description": f"Mock agent {agent_id} description",
            "status": "active",
            "capabilities": ["data_analysis", "insight_generation"]
        }
    
    async def mock_invoke_agent(self, agent_id: str, input_data: Dict[str, Any], 
                               parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Mock invoke agent response"""
        return {
            "success": True,
            "output": f"Agent {agent_id} executed successfully",
            "execution_time": 1.5,
            "status": "completed"
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
        return {
            "id": tool_id,
            "name": f"Tool {tool_id}",
            "description": f"Mock tool {tool_id} description",
            "status": "active",
            "parameters": ["param1", "param2"]
        }
    
    async def mock_execute_tool(self, tool_id: str, parameters: Dict[str, Any], 
                               token: str) -> Dict[str, Any]:
        """Mock execute tool response"""
        return {
            "success": True,
            "output": f"Tool {tool_id} executed successfully",
            "execution_time": 0.8,
            "status": "completed"
        }
    
    async def test_database_tools(self):
        """Test database tools"""
        print("\n🗄️ Testing Database Tools...")
        
        # Test search_database
        print("   Testing search_database...")
        try:
            result = await DatabaseTools.search_database(
                query="SELECT * FROM users WHERE active = true",
                database="test_db",
                limit=100
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "search_database",
                "status": "PASS",
                "details": "Database search executed successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "search_database",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test get_table_schema
        print("   Testing get_table_schema...")
        try:
            result = await DatabaseTools.get_table_schema("users", "test_db")
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "get_table_schema",
                "status": "PASS",
                "details": "Table schema retrieved successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "get_table_schema",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test execute_query
        print("   Testing execute_query...")
        try:
            result = await DatabaseTools.execute_query(
                "SELECT COUNT(*) FROM users",
                "test_db"
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "execute_query",
                "status": "PASS",
                "details": "Query executed successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "execute_query",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_analytics_tools(self):
        """Test analytics tools"""
        print("\n📊 Testing Analytics Tools...")
        
        # Test analyze_data
        print("   Testing analyze_data...")
        try:
            result = await AnalyticsTools.analyze_data(
                data_source="sales_data",
                analysis_type="summary",
                parameters={"group_by": "region", "metrics": ["revenue", "profit"]}
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "analyze_data",
                "status": "PASS",
                "details": "Data analysis executed successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "analyze_data",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test generate_report
        print("   Testing generate_report...")
        try:
            result = await AnalyticsTools.generate_report(
                report_type="sales_summary",
                parameters={"date_range": "2024-01-01 to 2024-12-31"},
                data_filters={"date_range": "2024-01-01 to 2024-12-31"},
                format="pdf"
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "generate_report",
                "status": "PASS",
                "details": "Report generated successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "generate_report",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_document_tools(self):
        """Test document tools"""
        print("\n📄 Testing Document Tools...")
        
        # Test process_document
        print("   Testing process_document...")
        try:
            result = await DocumentTools.process_document(
                document_path="/path/to/test.pdf",
                operation="extract_text",
                parameters={"language": "en", "format": "plain_text"}
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "process_document",
                "status": "PASS",
                "details": "Document processed successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "process_document",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test search_documents
        print("   Testing search_documents...")
        try:
            result = await DocumentTools.search_documents(
                query="machine learning algorithms",
                filters={"document_type": "pdf", "date_range": "2024-01-01 to 2024-12-31"},
                limit=10
            )
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "search_documents",
                "status": "PASS",
                "details": "Document search executed successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "search_documents",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_system_tools(self):
        """Test system tools"""
        print("\n⚙️ Testing System Tools...")
        
        # Test get_system_info
        print("   Testing get_system_info...")
        try:
            result = await SystemTools.get_system_info()
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "get_system_info",
                "status": "PASS",
                "details": "System info retrieved successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "get_system_info",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test check_system_health
        print("   Testing check_system_health...")
        try:
            result = await SystemTools.check_system_health()
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "check_system_health",
                "status": "PASS",
                "details": "System health checked successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "check_system_health",
                "status": "FAIL",
                "details": str(e)
            })
        
        # Test list_tools
        print("   Testing list_tools...")
        try:
            result = await SystemTools.list_tools()
            print(f"   Result: {result[:100]}...")
            self.test_results.append({
                "test": "list_tools",
                "status": "PASS",
                "details": "Tools listed successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "list_tools",
                "status": "FAIL",
                "details": str(e)
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
                "details": "SageAI agents listed successfully"
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
                "details": "SageAI agent details retrieved successfully"
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
                "details": "SageAI agent invoked successfully"
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
                "details": "SageAI tools listed successfully"
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
                "details": "SageAI tool details retrieved successfully"
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
                "details": "SageAI tool executed successfully"
            })
        except Exception as e:
            print(f"   Error: {str(e)}")
            self.test_results.append({
                "test": "execute_sageai_tool",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def run_all_tests(self):
        """Run all MCP tools tests"""
        print("🚀 Starting MCP Tools Direct Tests")
        print("=" * 60)
        
        try:
            # Setup test environment
            await self.setup_test_environment()
            
            # Run all test suites
            await self.test_database_tools()
            await self.test_analytics_tools()
            await self.test_document_tools()
            await self.test_system_tools()
            await self.test_sageai_agent_tools()
            await self.test_sageai_tool_tools()
            
            # Generate test report
            await self.generate_test_report()
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 MCP Tools Test Report")
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
            "test_suite": "mcp_tools_direct",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "results": self.test_results
        }
        
        with open("mcp_tools_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Test report saved to: mcp_tools_test_report.json")
        
        if failed_tests == 0:
            print("\n🎉 All MCP tools tests passed! All tools are working correctly.")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Please check the details above.")

async def main():
    """Main test function"""
    tester = MCPToolsDirectTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
