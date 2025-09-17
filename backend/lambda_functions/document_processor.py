import json
import base64
import tempfile
import os
import uuid
from typing import Dict, Any

# Import clients
from backend.clients.local_text_extractor import LocalTextExtractor
from backend.clients.claude_client import ClaudeClient
from backend.clients.opensearch_client import get_opensearch_client

# Initialize clients
text_extractor = LocalTextExtractor()
claude_client = ClaudeClient()
opensearch_client = get_opensearch_client()

def lambda_handler(event, context):
    """
    AWS Lambda handler for document processing with direct OpenSearch storage.
    """
    try:
        # Parse the event
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        file_data = body.get('file_data')
        file_name = body.get('file_name', 'unknown.pdf')
        document_type = body.get('document_type', 'invoice')
        session_id = body.get('session_id')
        
        if not file_data:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'No file data provided'
                })
            }
        
        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'No session ID provided'
                })
            }
        
        print(f"Processing document: {file_name} for session: {session_id}")
        
        # Decode the base64 file data
        try:
            file_content = base64.b64decode(file_data)
        except Exception as e:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Invalid base64 data: {str(e)}'
                })
            }
        
        # Step 1: Extract text first
        print("Extracting text...")
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Extract text
            extraction_result = text_extractor.extract_text_from_file(temp_file_path)
            
            if not extraction_result.get('success'):
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'success': False,
                        'error': f"Text extraction failed: {extraction_result.get('error', 'Unknown error')}"
                    })
                }
            
            print(f"Text extracted: {extraction_result.get('total_words', 0)} words")
            
            # Step 2: Format with Claude
            print("Formatting with Claude...")
            raw_text = extraction_result.get('raw_text', '')
            structured_result = claude_client.format_extracted_text(raw_text, document_type)
            
            if 'error' in structured_result:
                print(f"Claude formatting failed: {structured_result['error']}")
                # Continue without structured data
                structured_data = {}
            else:
                structured_data = structured_result
            
            print("Claude formatting completed")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        # Step 3: Upload to S3 and store in OpenSearch with embeddings
        print("Storing in OpenSearch with embeddings...")
        storage_result = opensearch_client.upload_and_store_document(
            file_content=file_content,
            filename=file_name,
            session_id=session_id,
            raw_text=raw_text,
            structured_data=structured_data
        )
        
        if not storage_result['success']:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': f"Storage failed: {storage_result['error']}"
                })
            }
        
        print(f"✅ Document stored with embeddings: {storage_result['document_id']}")
        
        # Prepare response
        response_data = {
            'success': True,
            'document_name': file_name,
            'session_id': session_id,
            'structured_data': structured_data,
            'raw_text': raw_text,

            'extraction_metadata': extraction_result.get('extraction_metadata', {}),
            's3_location': storage_result['s3_location'],
            'document_id': storage_result['document_id'],
            'embedding_dimensions': storage_result['embedding_dimensions'],
            'search_ready': True,
            'processing_time': 'immediate',
            'file_data': file_data  # Add original base64 file data for PDF preview
        }
        
        print(f"Processing completed successfully. Document ready for search.")
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data, default=str)
        }
        
    except Exception as e:
        print(f"Processing error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Document processing failed: {str(e)}'
            })
        }