import json
from typing import Dict, List, Any, Optional
from .opensearch_client import OpenSearchClient
from .claude_client import ClaudeClient

class ChatHandler:
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.claude_client = ClaudeClient()
    
    def handle_chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle a chat message using OpenSearch semantic search."""
        try:
            print(f"DEBUG: Searching for '{message}' in session '{session_id}'")
            print(f"DEBUG: Total documents in store: {len(self.opensearch_client.documents)}")
            
            # Perform semantic search
            search_result = self.opensearch_client.semantic_search(message, session_id, limit=3)
            
            if not search_result['success']:
                return {
                    'success': False,
                    'error': search_result['error'],
                    'session_id': session_id
                }
            
            # Check if we found relevant documents
            if not search_result['results']:
                return {
                    'success': True,
                    'response': "I don't have any documents uploaded yet. Please upload some invoices first and I'll be happy to help analyze them!",
                    'session_id': session_id
                }
            
            # Build concise context from search results
            context_parts = []
            for result in search_result['results']:
                if result['structured_data']:
                    vendor = result['structured_data'].get('vendor_name', 'Unknown vendor')
                    amount = result['structured_data'].get('total_amount', 'Unknown amount')
                    invoice_num = result['structured_data'].get('invoice_number', '')
                    date = result['structured_data'].get('date', '')
                    line_items = result['structured_data'].get('line_items', [])
                    
                    doc_info = f"Document: {result['filename']} - Vendor: {vendor}, Amount: ${amount}"
                    if invoice_num:
                        doc_info += f", Invoice: {invoice_num}"
                    if date:
                        doc_info += f", Date: {date}"
                    
                    # Add detailed line items if available
                    if line_items and isinstance(line_items, list):
                        doc_info += f"\nLine Items ({len(line_items)} items):"
                        for i, item in enumerate(line_items):
                            if isinstance(item, dict):
                                desc = item.get('description', 'Unknown')
                                qty = item.get('quantity', '')
                                rate = item.get('rate', '')
                                item_amount = item.get('amount', '')
                                
                                line_detail = f"\n  {i+1}. {desc}"
                                if qty: line_detail += f" - Quantity: {qty}"
                                if rate: line_detail += f" - Rate: ${rate}"
                                if item_amount: line_detail += f" - Amount: ${item_amount}"
                                
                                doc_info += line_detail
                    
                    context_parts.append(doc_info)
            
            context = "Invoice data:\n" + "\n".join(context_parts)
            
            # Create a natural conversation prompt
            conversation_prompt = f"""You are a helpful assistant analyzing invoices. Based on the invoice data below, answer the user's question naturally and conversationally. Be brief and direct - no numbered lists or formal structure. Just answer like you're having a conversation.

{context}

User question: {message}

Provide a natural, conversational response. If asked about "who charged the most" or similar, just say the vendor name and amount directly."""

            # Use Claude for natural conversation
            claude_response = self.claude_client.chat_with_streaming(conversation_prompt)
            
            if claude_response.get('success'):
                return {
                    'success': True,
                    'response': claude_response['response'],
                    'sources': [{'filename': r['filename'], 'similarity': r['similarity_score']} for r in search_result['results']],
                    'session_id': session_id
                }
            else:
                # Simple fallback based on the question
                if 'vendor' in message.lower() and ('most' in message.lower() or 'highest' in message.lower() or 'charged' in message.lower()):
                    # Find the highest amount
                    highest_amount = 0
                    highest_vendor = "Unknown"
                    
                    for result in search_result['results']:
                        amount = result['structured_data'].get('total_amount', 0)
                        vendor = result['structured_data'].get('vendor_name', 'Unknown')
                        if isinstance(amount, (int, float)) and amount > highest_amount:
                            highest_amount = amount
                            highest_vendor = vendor
                    
                    if highest_amount > 0:
                        response = f"{highest_vendor} charged the most at ${highest_amount:,.2f}."
                    else:
                        response = "I couldn't determine which vendor charged the most from the available data."
                    
                    return {
                        'success': True,
                        'response': response,
                        'sources': [{'filename': r['filename'], 'similarity': r['similarity_score']} for r in search_result['results']],
                        'session_id': session_id
                    }
                
                # Generic response with basic info
                if search_result['results']:
                    result = search_result['results'][0]
                    vendor = result['structured_data'].get('vendor_name', 'Unknown vendor')
                    amount = result['structured_data'].get('total_amount', 'Unknown amount')
                    response = f"I found an invoice from {vendor} for ${amount}."
                else:
                    response = "I found some documents but couldn't extract the specific information you're looking for."
                
                return {
                    'success': True,
                    'response': response,
                    'sources': [{'filename': r['filename'], 'similarity': r['similarity_score']} for r in search_result['results']],
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