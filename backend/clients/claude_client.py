import boto3
import json
import os
from typing import Dict, Any, List

class ClaudeClient:
    def __init__(self, region_name: str = "us-west-2"):
        """Initialize Claude client for chat interactions."""
        # Ensure we use the current AWS profile/credentials from environment
        session = boto3.Session()
        self.client = session.client("bedrock-runtime", region_name=region_name)
        self.chat_model_id = "anthropic.claude-3-haiku-20240307-v1:0"  # Claude for chat
        self.formatting_model_id = "us.amazon.nova-lite-v1:0"  # Nova Lite inference profile for formatting
        self.fallback_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Claude 3.5 Sonnet fallback for complex documents
    
    def format_extracted_text(self, raw_text: str, document_type: str = "invoice") -> Dict[str, Any]:
        """
        Use Nova Lite to format raw text into structured data, with Claude 3.5 Sonnet fallback.
        
        Args:
            raw_text: Raw text from text extraction
            document_type: Type of document (invoice, receipt, etc.)
            
        Returns:
            Dictionary with structured data or error information
        """
        try:
            if not raw_text or len(raw_text.strip()) < 10:
                return {"error": "Insufficient text content for processing"}
            
            # First attempt: Nova Lite (cost-effective)
            print("Attempting extraction with Nova Lite...")
            nova_result = self._try_nova_lite_extraction(raw_text, document_type)
            
            # Check if Nova Lite succeeded
            if self._is_extraction_successful(nova_result):
                print("✅ Nova Lite extraction successful")
                nova_result['model_used'] = 'nova-lite'
                return nova_result
            
            # Fallback: Claude 3.5 Sonnet (more powerful)
            print("❌ Nova Lite failed, falling back to Claude 3.5 Sonnet...")
            sonnet_result = self._try_sonnet_extraction(raw_text, document_type)
            
            if self._is_extraction_successful(sonnet_result):
                print("✅ Claude 3.5 Sonnet extraction successful")
                sonnet_result['model_used'] = 'claude-3.5-sonnet'
                return sonnet_result
            
            # If both fail, use manual fallback
            print("❌ Both models failed, using manual extraction...")
            fallback_result = self._fallback_extraction(raw_text)
            fallback_result['model_used'] = 'manual-fallback'
            return fallback_result
                
        except Exception as e:
            print(f"Extraction error: {str(e)}")
            return self._fallback_extraction(raw_text)
    
    def _try_nova_lite_extraction(self, raw_text: str, document_type: str) -> Dict[str, Any]:
        """Try extraction with Nova Lite."""
        try:
            prompt = f"""You are extracting data from a {document_type}. Follow these steps:

STEP 1: Find basic information in this text:
{raw_text}

STEP 2: Extract these required fields:
- vendor_name: Look for law firm names (containing "LLP", "LLC") or company names at the top
- invoice_number: Look for "Invoice Number:", "Matter Number:", or similar
- total_amount: Look for "Total Amount Due", "Total:", final amount (number only)
- date: Find the invoice date (format as YYYY-MM-DD)
- payment_terms: Look for "Payable in" or payment terms

STEP 3: Extract time entries/line items:
Look for patterns like:
- Date Name Description Hours
- Name Hours Rate Amount
- Service descriptions with costs

For each entry, capture:
- description: Brief description of work/service
- quantity: Hours or units (numbers only)
- rate: Hourly rate or price (numbers only)  
- amount: Line total (numbers only)
- person: Attorney/person name (if present)

STEP 4: Return ONLY this JSON structure:
{{
  "vendor_name": "firm name",
  "invoice_number": "number",
  "total_amount": 27531.83,
  "date": "2023-04-18",
  "payment_terms": "terms",
  "line_items": [
    {{
      "description": "brief description",
      "quantity": 2.5,
      "rate": 1000.00,
      "amount": 2500.00,
      "person": "Attorney Name"
    }}
  ]
}}

Extract what you can find. Return valid JSON only:"""

            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 1000,
                    "temperature": 0.1
                }
            }
            
            response = self.client.invoke_model(
                modelId=self.formatting_model_id,
                body=json.dumps(payload)
            )
            
            result = json.loads(response['body'].read())
            
            if 'output' in result and 'message' in result['output']:
                content = result['output']['message'].get('content', [])
                if content and len(content) > 0:
                    response_text = content[0].get('text', '')
                    return self._parse_json_response(response_text)
            
            return {"error": "Nova Lite: Invalid response format"}
            
        except Exception as e:
            return {"error": f"Nova Lite failed: {str(e)}"}
    
    def _try_sonnet_extraction(self, raw_text: str, document_type: str) -> Dict[str, Any]:
        """Try extraction with Claude 3.5 Sonnet for complex documents."""
        try:
            prompt = f"""You are an expert at extracting structured data from complex {document_type} documents, especially legal invoices with detailed time entries.

Analyze this text and extract comprehensive billing information:

{raw_text}

Extract the following information in JSON format:

1. BASIC INFORMATION:
   - vendor_name: The law firm or company name (look for "LLP", "LLC", firm letterhead)
   - invoice_number: Invoice/matter number
   - total_amount: Final total amount due (extract the number from "Total Amount Due", "Total", etc.)
   - date: Invoice date in YYYY-MM-DD format
   - payment_terms: Payment terms (e.g., "Net 30", "Payable in 90 days")

2. DETAILED LINE ITEMS:
   For legal invoices, extract time entries, rate summaries, and disbursements:
   - Each time entry with date, attorney name, description, hours worked
   - Rate summaries showing attorney name, total hours, hourly rate, total amount
   - Any disbursements or additional costs

3. ATTORNEY INFORMATION:
   - Extract individual attorney details: name, hours worked, hourly rate, total billed

Return ONLY valid JSON with this structure:
{{
  "vendor_name": "Law Firm Name",
  "invoice_number": "12345",
  "total_amount": 27531.83,
  "date": "2023-04-18",
  "payment_terms": "Payable in 90 days",
  "line_items": [
    {{
      "description": "Legal services description",
      "quantity": 2.5,
      "rate": 1000.00,
      "amount": 2500.00,
      "person": "Attorney Name",
      "date": "2023-03-08"
    }}
  ]
}}

Be thorough in extracting time entries and attorney billing details. Return valid JSON only:"""

            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = self.client.invoke_model(
                modelId=self.fallback_model_id,
                body=json.dumps(payload)
            )
            
            result = json.loads(response['body'].read())
            response_text = result['content'][0]['text']
            
            return self._parse_json_response(response_text)
            
        except Exception as e:
            return {"error": f"Claude 3.5 Sonnet failed: {str(e)}"}
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from model response."""
        try:
            # Extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                structured_data = json.loads(json_text)
                
                return structured_data
            else:
                return {"error": "No valid JSON found in response"}
                
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing failed: {str(e)}"}
    
    def _is_extraction_successful(self, result: Dict[str, Any]) -> bool:
        """Check if extraction was successful."""
        if 'error' in result:
            return False
        
        # Check if we have at least basic required fields
        has_vendor = result.get('vendor_name') and result.get('vendor_name') != 'Not found'
        has_total = result.get('total_amount') and isinstance(result.get('total_amount'), (int, float))
        
        # Consider successful if we have either vendor name or total amount
        return has_vendor or has_total
    
    def _fallback_extraction(self, raw_text: str) -> Dict[str, Any]:
        """Simple fallback extraction if Nova Lite fails."""
        import re
        
        extracted = {}
        
        # Simple regex patterns
        amount_match = re.search(r'\$[\d,]+\.?\d*', raw_text)
        if amount_match:
            try:
                amount_str = amount_match.group().replace('$', '').replace(',', '')
                extracted['total_amount'] = float(amount_str)
            except:
                pass
        
        # Look for invoice numbers
        invoice_match = re.search(r'(?:invoice|inv)[\s#:]*(\w+)', raw_text, re.IGNORECASE)
        if invoice_match:
            extracted['invoice_number'] = invoice_match.group(1)
        
        return extracted
    
    def chat_with_streaming(self, prompt: str, context: str = "") -> Dict[str, Any]:
        """
        Generate a conversational response using Claude Haiku.
        """
        try:
            # Create a natural conversation prompt
            full_prompt = f"{context}\n\nUser: {prompt}\n\nAssistant:"
            
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ]
            }
            
            response = self.client.invoke_model(
                modelId=self.chat_model_id,
                body=json.dumps(payload)
            )
            
            result = json.loads(response['body'].read())
            response_text = result['content'][0]['text']
            
            return {
                "success": True,
                "response": response_text.strip()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Claude chat error: {str(e)}"
            }
    
    def validate_extraction(self, extracted_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Use Claude to validate and improve extracted data.
        
        Args:
            extracted_data: Previously extracted structured data
            raw_text: Original raw text for reference
            
        Returns:
            Validation results with corrections
        """
        prompt = f"""
        Please review this extracted data against the original text and provide validation.
        
        Extracted Data:
        {json.dumps(extracted_data, indent=2)}
        
        Original Text:
        {raw_text}
        
        Return a JSON object with:
        - is_valid: boolean indicating if extraction looks correct
        - confidence_score: overall confidence (0-1)
        - corrections: object with any field corrections needed
        - warnings: array of potential issues found
        - suggestions: array of improvement suggestions
        
        Return only valid JSON:
        """
        
        return self._call_claude(prompt)
    
    def _call_claude(self, message: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Internal method to call Claude and return parsed JSON.
        
        Args:
            message: Prompt to send to Claude
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON response
        """
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.1  # Low temperature for consistent formatting
        }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )
            
            response_body = json.loads(response["body"].read())
            claude_response = response_body["content"][0]["text"]
            
            # Try to parse as JSON
            try:
                return json.loads(claude_response)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text with error
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": claude_response
                }
                
        except Exception as e:
            return {
                "error": f"Claude API error: {str(e)}"
            }
    
    def _call_claude_with_tools(self, messages: List[Dict], tools: List[Dict], max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Call Claude with tool calling capabilities.
        
        Args:
            messages: Conversation messages
            tools: Available tools for Claude to use
            max_tokens: Maximum tokens to generate
            
        Returns:
            Claude response with potential tool calls
        """
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
            "tools": tools,
            "temperature": 0.1
        }
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )
            
            response_body = json.loads(response["body"].read())
            return response_body
                
        except Exception as e:
            return {
                "error": f"Claude tool calling error: {str(e)}"
            }