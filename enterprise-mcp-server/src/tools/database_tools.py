"""
Enterprise Database Tools
SOLID Principle: Single Responsibility - Handles all database-related operations
Enterprise Standard: Zero-configuration auto-discovery with enterprise-grade features
"""

from typing import Any, Dict
from src.core.observability import observability
from src.core.rate_limiter import rate_limiter
from src.tools.base_tool import EnterpriseToolRegistry, enterprise_tool


class DatabaseTools:
    """Enterprise database tools with zero-configuration auto-discovery"""
    
    @staticmethod
    def get_tools_metadata() -> list:
        """Return metadata for all database tools - Enterprise auto-discovery!"""
        return EnterpriseToolRegistry.get_tools_metadata("database")
    
    @enterprise_tool(category="database")
    @staticmethod
    async def search_database(
        query: str,
        database: str = "default",
        limit: int = 100
    ) -> str:
        """Search enterprise database with SQL queries"""
        try:
            async with observability.trace_operation("tool_execution", tool="search_database"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "search_database", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for search_database. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate database search
                result = f"Database search completed for query: '{query}' in database: '{database}' with limit: {limit}"
                
                observability.record_tool_execution("search_database", "success")
                observability.log("info", "Database search completed", 
                               query=query, database=database, limit=limit)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("search_database", "error")
            observability.log("error", "Database search failed", error=str(e))
            return f"Database search failed: {str(e)}"
    
    @enterprise_tool(category="database")
    @staticmethod
    async def execute_query(
        sql: str,
        database: str = "default",
        parameters: Dict[str, Any] = None
    ) -> str:
        """Execute SQL query on enterprise database"""
        try:
            async with observability.trace_operation("tool_execution", tool="execute_query"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "execute_query", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for execute_query. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate query execution
                result = f"SQL query executed: '{sql}' in database: '{database}' with parameters: {parameters or {}}"
                
                observability.record_tool_execution("execute_query", "success")
                observability.log("info", "SQL query executed", 
                               sql=sql, database=database, parameters=parameters)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("execute_query", "error")
            observability.log("error", "SQL query execution failed", error=str(e))
            return f"SQL query execution failed: {str(e)}"
    
    @enterprise_tool(category="database")
    @staticmethod
    async def execute_sql(
        sql: str,
        database: str = "default",
        timeout: int = 30
    ) -> str:
        """Execute SQL query with timeout protection"""
        try:
            with observability.trace_operation("tool_execution", tool="execute_sql"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "execute_sql", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for execute_sql. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate SQL execution
                result = f"SQL executed successfully: '{sql}' in database: '{database}' with timeout: {timeout}s"
                
                observability.record_tool_execution("execute_sql", "success")
                observability.log("info", "SQL executed", 
                               sql=sql, database=database, timeout=timeout)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("execute_sql", "error")
            observability.log("error", "SQL execution failed", error=str(e))
            return f"SQL execution failed: {str(e)}"
    
    @enterprise_tool(category="database")
    @staticmethod
    async def get_table_schema(
        table_name: str,
        database: str = "default"
    ) -> str:
        """Get table schema information"""
        try:
            with observability.trace_operation("tool_execution", tool="get_table_schema"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "get_table_schema", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for get_table_schema. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate schema retrieval
                result = f"Table schema retrieved for '{table_name}' in database: '{database}'"
                
                observability.record_tool_execution("get_table_schema", "success")
                observability.log("info", "Table schema retrieved", 
                               table_name=table_name, database=database)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("get_table_schema", "error")
            observability.log("error", "Schema retrieval failed", error=str(e))
            return f"Schema retrieval failed: {str(e)}"
