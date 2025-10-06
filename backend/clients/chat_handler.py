import json
import json
from typing import Dict, List, Any, Optional
from .opensearch_client import get_opensearch_client
from .claude_client import ClaudeClient

class ChatHandler:
    def __init__(self):
        self.opensearch_client = get_opensearch_client()
        self.claude_client = ClaudeClient()
    
    def handle_chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle a chat message using all structured data in a large prompt."""
        try:
            # Get ALL documents in the session
            session_documents = self.opensearch_client.get_session_documents(session_id)
            
            # Check if we found any documents
            if not session_documents:
                return {
                    'success': True,
                    'response': "I don't have any documents uploaded yet. Please upload some invoices first and I'll be happy to help analyze them!",
                    'session_id': session_id
                }
            
            # Build comprehensive structured data context
            structured_data_context = []
            for doc in session_documents:
                if doc.get('structured_data'):
                    structured_data_context.append({
                        'filename': doc['filename'],
                        'data': doc['structured_data']
                    })
            
            # Create prompt with all structured data
            prompt = f"""You are analyzing invoice data. Answer the user's question based on this structured data:

{json.dumps(structured_data_context, indent=2)}

User question: {message}

Provide a clear, conversational answer based on the data above."""
            
            # Use Claude for response
            claude_response = self.claude_client.chat_with_streaming(prompt)
            
            if claude_response.get('success'):
                return {
                    'success': True,
                    'response': claude_response['response'],
                    'sources': [{'filename': doc['filename']} for doc in session_documents],
                    'session_id': session_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to generate response',
                    'session_id': session_id
                }
            
        except Exception as e:
            print(f"Chat error: {e}")
            return {
                'success': False,
                'error': f"Chat processing failed: {str(e)}",
                'session_id': session_id
            }
    
    def handle_aggregation_query(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle queries that require aggregation across documents."""
        try:
            message_lower = message.lower()
            
            # Determine what to aggregate
            if 'total' in message_lower and ('amount' in message_lower or 'cost' in message_lower or 'spent' in message_lower):
                result = self.opensearch_client.aggregate_data(session_id, 'total_amount', 'sum')
                if result['success']:
                    return {
                        'success': True,
                        'response': f"The total amount across all invoices is ${result['result']:,.2f} from {result['document_count']} document(s).",
                        'session_id': session_id
                    }
            
            elif 'vendor' in message_lower and ('count' in message_lower or 'how many' in message_lower):
                result = self.opensearch_client.aggregate_data(session_id, 'vendor_name', 'count')
                if result['success']:
                    vendor_list = ', '.join(result['result'].keys())
                    return {
                        'success': True,
                        'response': f"I found {len(result['result'])} unique vendors: {vendor_list}",
                        'session_id': session_id
                    }
            
            # Fall back to regular search
            return self.handle_chat(message, session_id)
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Aggregation query failed: {str(e)}",
                'session_id': session_id
            }