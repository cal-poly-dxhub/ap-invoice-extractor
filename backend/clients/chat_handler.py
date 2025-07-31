import json
from typing import Dict, List, Any, Optional
from .claude_client import ClaudeClient
from .invoice_tools import InvoiceTools, INVOICE_TOOLS

class ChatHandler:
    def __init__(self):
        self.claude = ClaudeClient()
    
    def handle_chat(self, message: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a chat message about the session's invoices."""
        try:
            # Initialize tools for this session
            tools = InvoiceTools(session_data)
            
            # Create context about the session
            invoice_count = len(session_data.get("invoices", []))
            context = f"""You are analyzing {invoice_count} invoices for the user. 
            You have access to tools to search, filter, and aggregate invoice data.
            Be helpful and provide specific, actionable insights.
            Always use tools when the user asks for specific data or analysis.

            Available invoice data includes vendor names, amounts, dates, and invoice numbers.
            You can help with analysis, summarization, filtering, and answering questions about the invoices.
            
            Just give the answer to the user. Do not explain what you are going to do or what tools you used. 
            """

            # Use streaming chat for better user experience
            response = self.claude.chat_with_streaming(message, context)
            
            if response.get("success"):
                return {
                    "success": True,
                    "response": response["response"],
                    "session_id": session_data.get("id"),
                    "streaming": True
                }
            else:
                # Fallback to tool-based chat if streaming fails
                return self._fallback_tool_chat(message, context, tools, session_data)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Chat error: {str(e)}"
            }
    
    def _fallback_tool_chat(self, message: str, context: str, tools: InvoiceTools, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to tool-based chat if streaming fails."""
        try:
            # Call Claude with tools
            response = self._call_claude_with_tools(message, context, tools)
            
            return {
                "success": True,
                "response": response,
                "session_id": session_data.get("id"),
                "streaming": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback chat error: {str(e)}"
            }
    
    def _call_claude_with_tools(self, message: str, context: str, tools: InvoiceTools) -> str:
        """Call Claude with tool calling capabilities."""
        
        # Prepare the conversation
        conversation = [
            {
                "role": "user", 
                "content": f"{context}\n\nUser question: {message}"
            }
        ]
        
        max_tool_calls = 3  # Prevent infinite loops
        tool_call_count = 0
        
        while tool_call_count < max_tool_calls:
            # Call Claude
            response = self.claude._call_claude_with_tools(
                conversation, 
                INVOICE_TOOLS
            )
            
            if not response.get("content"):
                break
                
            # Check if Claude wants to use tools
            if response.get("stop_reason") == "tool_use":
                tool_call_count += 1
                
                # Process tool calls
                tool_results = []
                for content_block in response["content"]:
                    if content_block.get("type") == "tool_use":
                        tool_result = self._execute_tool(content_block, tools)
                        tool_results.append(tool_result)
                
                # Add tool results to conversation
                conversation.append({
                    "role": "assistant",
                    "content": response["content"]
                })
                
                conversation.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                # Claude provided a final response
                for content_block in response["content"]:
                    if content_block.get("type") == "text":
                        return content_block["text"]
                break
        
        return "I encountered an issue processing your request. Please try rephrasing your question."
    
    def _execute_tool(self, tool_call: Dict, tools: InvoiceTools) -> Dict[str, Any]:
        """Execute a tool call and return the result."""
        tool_name = tool_call.get("name")
        tool_input = tool_call.get("input", {})
        tool_id = tool_call.get("id")
        
        try:
            if tool_name == "search_similar_invoices":
                result = tools.search_similar_invoices(
                    query=tool_input.get("query", ""),
                    limit=tool_input.get("limit", 5)
                )
            elif tool_name == "aggregate_amounts":
                result = tools.aggregate_amounts(
                    group_by=tool_input.get("group_by", "vendor"),
                    operation=tool_input.get("operation", "sum")
                )
            elif tool_name == "filter_invoices":
                result = tools.filter_invoices(
                    vendor=tool_input.get("vendor"),
                    amount_min=tool_input.get("amount_min"),
                    amount_max=tool_input.get("amount_max"),
                    date_start=tool_input.get("date_start"),
                    date_end=tool_input.get("date_end"),
                    payment_terms=tool_input.get("payment_terms")
                )
            elif tool_name == "get_session_summary":
                result = tools.get_session_summary()
            elif tool_name == "get_vendor_summary":
                result = tools.get_vendor_summary()
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(result, default=str)
            }
            
        except Exception as e:
            return {
                "type": "tool_result", 
                "tool_use_id": tool_id,
                "content": json.dumps({"error": str(e)})
            } 