import json
import base64
import boto3
import uuid
import time
from typing import Dict, Any, Optional
import sys
import os

# Add the backend directory to the path so we can import our clients
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from clients.local_text_extractor import LocalTextExtractor
from clients.claude_client import ClaudeClient


class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with local text extraction and Claude AI formatting."""
        self.text_extractor = LocalTextExtractor()
        self.claude = ClaudeClient()
        self.s3_client = boto3.client('s3', region_name='us-west-2')
        
        self.bucket_name = "invoices-bucket-01"
    
    def process_document(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Main Lambda handler for document processing using local text extraction and Claude AI.
        
        Processes documents by:
        1. Extracting text using local Python libraries (PyPDF2)
        2. Formatting extracted text into structured data using Claude AI
        3. Validating the extraction results
        
        Args:
            event: Lambda event containing document data
            context: Lambda context
            
        Returns:
            Processed document data with structured fields or error response
        """
        try:
            # Parse the incoming request
            body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
            
            # Handle different input methods
            if 'file_data' in body:
                # Direct file upload (base64 encoded)
                return self._process_direct_upload(body)
            elif 's3_key' in body:
                # File already in S3
                return self._process_s3_file(body)
            else:
                return {
                    'statusCode': 400,
                    'headers': self._get_cors_headers(),
                    'body': json.dumps({
                        'error': 'Missing file_data or s3_key in request'
                    })
                }
                
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': self._get_cors_headers(),
                'body': json.dumps({
                    'error': f'Processing failed: {str(e)}'
                })
            }
    
    def _process_direct_upload(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Process a document uploaded directly in the request using local text extraction."""
        try:
            # Get file data
            file_data = body['file_data']  # base64 encoded
            file_name = body.get('file_name', f'document_{uuid.uuid4().hex}')
            document_type = body.get('document_type', 'invoice')
            
            # Decode the file
            document_bytes = base64.b64decode(file_data)
            
            # Extract text using Local Text Extractor
            extraction_result = self.text_extractor.extract_text_from_bytes(document_bytes, file_name)
            
            if 'error' in extraction_result:
                return {
                    'statusCode': 422,
                    'headers': self._get_cors_headers(),
                    'body': json.dumps({
                        'error': 'Text extraction failed',
                        'details': extraction_result
                    })
                }
            
            # Format text using Claude
            raw_text = extraction_result['raw_text']
            formatting_result = self.claude.format_extracted_text(raw_text, document_type)
            
            if 'error' in formatting_result:
                return {
                    'statusCode': 422,
                    'headers': self._get_cors_headers(),
                    'body': json.dumps({
                        'error': 'Text formatting failed',
                        'details': formatting_result
                    })
                }
            
            # Validate the extraction
            validation_result = self.claude.validate_extraction(formatting_result, raw_text)
            
            # Prepare final response
            result = {
                'success': True,
                'document_name': file_name,
                'extraction_metadata': extraction_result.get('extraction_metadata', {}),
                'extraction_confidence': extraction_result.get('average_confidence', 0),
                'structured_data': formatting_result,
                'validation': validation_result,
                'raw_text': raw_text,
                'processing_timestamp': time.time()
            }
            
            return {
                'statusCode': 200,
                'headers': self._get_cors_headers(),
                'body': json.dumps(result)
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': self._get_cors_headers(),
                'body': json.dumps({
                    'error': f'Direct upload processing failed: {str(e)}'
                })
            }
    
    def _process_s3_file(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Download and process a document from S3 using local text extraction."""
        try:
            s3_key = body['s3_key']
            bucket_name = body.get('bucket_name', self.bucket_name)
            document_type = body.get('document_type', 'invoice')
            
            # Download file from S3
            try:
                response = self.s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                document_bytes = response['Body'].read()
            except Exception as s3_error:
                return {
                    'statusCode': 422,
                    'headers': self._get_cors_headers(),
                    'body': json.dumps({
                        'error': 'S3 file download failed',
                        'details': str(s3_error)
                    })
                }
            
            # Extract text using Local Text Extractor
            extraction_result = self.text_extractor.extract_text_from_bytes(document_bytes, s3_key)
            
            if 'error' in extraction_result:
                return {
                    'statusCode': 422,
                    'headers': self._get_cors_headers(),
                    'body': json.dumps({
                        'error': 'Text extraction failed',
                        'details': extraction_result
                    })
                }
            
            # Format text using Claude
            raw_text = extraction_result['raw_text']
            formatting_result = self.claude.format_extracted_text(raw_text, document_type)
            
            if 'error' in formatting_result:
                return {
                    'statusCode': 422,
                    'headers': self._get_cors_headers(),
                    'body': json.dumps({
                        'error': 'Text formatting failed',
                        'details': formatting_result,
                        'raw_text': raw_text
                    })
                }
            
            # Validate the extraction
            validation_result = self.claude.validate_extraction(formatting_result, raw_text)
            
            # Prepare final response
            result = {
                'success': True,
                'document_name': s3_key,
                'bucket_name': bucket_name,
                'extraction_metadata': extraction_result.get('extraction_metadata', {}),
                'extraction_confidence': extraction_result.get('average_confidence', 0),
                'structured_data': formatting_result,
                'validation': validation_result,
                'raw_text': raw_text,
                'processing_timestamp': time.time()
            }
            
            return {
                'statusCode': 200,
                'headers': self._get_cors_headers(),
                'body': json.dumps(result)
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': self._get_cors_headers(),
                'body': json.dumps({
                    'error': f'S3 processing failed: {str(e)}'
                })
            }
    
    def _get_cors_headers(self) -> Dict[str, str]:
        """Get CORS headers for the response."""
        return {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }


# Global processor instance (for Lambda container reuse)
processor = DocumentProcessor()

def lambda_handler(event, context):
    """
    Lambda entry point for document processing.
    
    Expected event format:
    {
        "body": {
            "file_data": "base64_encoded_file_content",
            "file_name": "document.pdf",
            "document_type": "invoice"
        }
    }
    
    Or for S3 files:
    {
        "body": {
            "s3_key": "documents/invoice.pdf",
            "bucket_name": "optional-bucket-name",
            "document_type": "invoice"
        }
    }
    """
    return processor.process_document(event, context)