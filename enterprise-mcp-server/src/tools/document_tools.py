"""
Enterprise Document Tools
SOLID Principle: Single Responsibility - Handles all document-related operations
Enterprise Standard: Zero-configuration auto-discovery with enterprise-grade features
"""

from typing import Any, Dict
from src.core.observability import observability
from src.core.rate_limiter import rate_limiter
from src.tools.base_tool import EnterpriseToolRegistry, enterprise_tool


class DocumentTools:
    """Enterprise document tools with zero-configuration auto-discovery"""
    
    @staticmethod
    def get_tools_metadata() -> list:
        """Return metadata for all document tools - Enterprise auto-discovery!"""
        return EnterpriseToolRegistry.get_tools_metadata("document")
    
    @enterprise_tool(category="document")
    @staticmethod
    async def search_documents(
        query: str,
        document_type: str = "all",
        limit: int = 50,
        filters: Dict[str, Any] = None
    ) -> str:
        """Search enterprise documents with advanced filtering"""
        try:
            async with observability.trace_operation("tool_execution", tool="search_documents"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "search_documents", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for search_documents. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate document search
                result = f"Document search completed for query: '{query}' in type: '{document_type}' with limit: {limit}"
                
                observability.record_tool_execution("search_documents", "success")
                observability.log("info", "Document search completed", 
                               query=query, document_type=document_type, limit=limit)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("search_documents", "error")
            observability.log("error", "Document search failed", error=str(e))
            return f"Document search failed: {str(e)}"
    
    @enterprise_tool(category="document")
    @staticmethod
    async def process_document(
        document_path: str,
        operation: str = "extract",
        parameters: Dict[str, Any] = None
    ) -> str:
        """Process documents with various operations"""
        try:
            async with observability.trace_operation("tool_execution", tool="process_document"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "process_document", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for process_document. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate document processing
                result = f"Document processed: '{document_path}' with operation: '{operation}' and parameters: {parameters or {}}"
                
                observability.record_tool_execution("process_document", "success")
                observability.log("info", "Document processing completed", 
                               document_path=document_path, operation=operation)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("process_document", "error")
            observability.log("error", "Document processing failed", error=str(e))
            return f"Document processing failed: {str(e)}"
    
    @enterprise_tool(category="document")
    @staticmethod
    async def extract_text(
        document_id: str,
        format: str = "plain"
    ) -> str:
        """Extract text content from documents"""
        try:
            with observability.trace_operation("tool_execution", tool="extract_text"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "extract_text", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for extract_text. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate text extraction
                result = f"Text extracted from document {document_id} in {format} format"
                
                observability.record_tool_execution("extract_text", "success")
                observability.log("info", "Text extracted", 
                               document_id=document_id, format=format)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("extract_text", "error")
            observability.log("error", "Text extraction failed", error=str(e))
            return f"Text extraction failed: {str(e)}"
    
    @enterprise_tool(category="document")
    @staticmethod
    async def summarize_document(
        document_id: str,
        summary_length: str = "medium"
    ) -> str:
        """Generate document summary"""
        try:
            with observability.trace_operation("tool_execution", tool="summarize_document"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "summarize_document", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for summarize_document. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate document summarization
                result = f"Document summary generated for {document_id} with {summary_length} length"
                
                observability.record_tool_execution("summarize_document", "success")
                observability.log("info", "Document summarized", 
                               document_id=document_id, summary_length=summary_length)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("summarize_document", "error")
            observability.log("error", "Document summarization failed", error=str(e))
            return f"Document summarization failed: {str(e)}"
    
    @enterprise_tool(category="document")
    @staticmethod
    async def translate_document(
        document_id: str,
        target_language: str,
        source_language: str = "auto"
    ) -> str:
        """Translate document to target language"""
        try:
            with observability.trace_operation("tool_execution", tool="translate_document"):
                # Check rate limit
                is_allowed, rate_info = await rate_limiter.check_rate_limit(
                    "translate_document", "tool"
                )
                
                if not is_allowed:
                    return f"Rate limit exceeded for translate_document. Retry after {rate_info.get('window', 60)} seconds"
                
                # Simulate document translation
                result = f"Document {document_id} translated from {source_language} to {target_language}"
                
                observability.record_tool_execution("translate_document", "success")
                observability.log("info", "Document translated", 
                               document_id=document_id, target_language=target_language)
                
                return result
                
        except Exception as e:
            observability.record_tool_execution("translate_document", "error")
            observability.log("error", "Document translation failed", error=str(e))
            return f"Document translation failed: {str(e)}"