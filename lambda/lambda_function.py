import json
import os
import boto3
import base64
import tempfile
import hashlib
from datetime import datetime
from typing import Dict, Any
from pypdf import PdfReader

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')

# Environment variables
S3_BUCKET = os.environ['S3_BUCKET_NAME']
NOVA_LITE_MODEL = os.environ['NOVA_LITE_MODEL']
CLAUDE_SONNET_MODEL = os.environ['CLAUDE_SONNET_MODEL']
CLAUDE_HAIKU_MODEL = os.environ['CLAUDE_HAIKU_MODEL']

def lambda_handler(event, context):
    """Main Lambda handler for invoice processing"""
    
    # Handle CORS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': ''
        }
    
    try:
        # Parse request
        path = event.get('path', '').rstrip('/')
        method = event.get('httpMethod', '')
        
        if path == '/process-document' and method == 'POST':
            return process_document(event)
        elif path == '/update-document' and method == 'POST':
            return update_document(event)
        elif path == '/chat' and method == 'POST':
            return handle_chat(event)
        elif path.startswith('/session/') and path.endswith('/delete') and method == 'DELETE':
            return delete_session(event)
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        pass
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def process_document(event):
    """Process uploaded document"""
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
            
        file_data = body.get('file_data')
        file_name = body.get('file_name')
        session_id = body.get('session_id')
        
        # Generate session_id if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        if not all([file_data, file_name]):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing required fields: file_data and file_name'})
            }
        
        # Decode file
        file_content = base64.b64decode(file_data)
        
        # Extract text
        raw_text = extract_text_from_pdf(file_content)
        
        # Extract structured data using AI
        structured_data = extract_structured_data(raw_text)
        
        # Store in S3
        doc_id = store_document(file_content, file_name, session_id, raw_text, structured_data)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'document_id': doc_id,
                'session_id': session_id,
                'structured_data': structured_data,
                'raw_text': raw_text,
                'file_data': file_data
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def update_document(event):
    """Update document structured data"""
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
            
        document_id = body.get('document_id')
        session_id = body.get('session_id')
        structured_data = body.get('structured_data')
        
        if not all([document_id, session_id, structured_data]):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing required fields: document_id, session_id, structured_data'})
            }
        
        # Update metadata in S3
        metadata_key = f"sessions/{session_id}/metadata/{document_id}.json"
        
        try:
            # Get existing metadata
            metadata_response = s3_client.get_object(
                Bucket=S3_BUCKET,
                Key=metadata_key
            )
            metadata = json.loads(metadata_response['Body'].read())
            
            # Update structured data
            metadata['structured_data'] = structured_data
            metadata['updated_at'] = datetime.utcnow().isoformat()
            
            # Save updated metadata
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=metadata_key,
                Body=json.dumps(metadata),
                ContentType='application/json'
            )
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': True,
                    'message': 'Document updated successfully',
                    'document_id': document_id
                })
            }
            
        except s3_client.exceptions.NoSuchKey:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Document not found'})
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def handle_chat(event):
    """Handle chat requests"""
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
            
        message = body.get('message')
        session_id = body.get('session_id')
        
        if not all([message, session_id]):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing message or session_id'})
            }
        
        # Get session documents
        session_docs = get_session_documents(session_id)
        
        if not session_docs:
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'success': True,
                    'response': "No documents found in this session. Please upload some invoices first."
                })
            }
        
        # Create context from all documents
        context = []
        for doc in session_docs:
            context.append({
                'filename': doc['filename'],
                'data': doc['structured_data']
            })
        
        # Generate response using Claude
        response = generate_chat_response(message, context)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'response': response,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def delete_session(event):
    """Delete all session data"""
    try:
        path_params = event.get('pathParameters', {})
        session_id = path_params.get('sessionId')
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing session ID'})
            }
        
        # Delete all objects with session prefix
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=f"sessions/{session_id}/"
        )
        
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            s3_client.delete_objects(
                Bucket=S3_BUCKET,
                Delete={'Objects': objects_to_delete}
            )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'message': 'Session deleted successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }

def extract_text_from_pdf(file_content):
    """Extract text from PDF using pypdf"""
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as pdf_file:
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_structured_data(raw_text):
    """Extract structured data using Nova Lite with Claude fallback"""
    try:
        # Try Nova Lite first
        result = call_nova_lite(raw_text)
        if result and 'vendor_name' in result:
            return result
        
        # Fallback to Claude Sonnet
        result = call_claude_sonnet(raw_text)
        if result and 'vendor_name' in result:
            return result
        
        # Manual fallback
        return {'vendor_name': 'Unknown', 'total_amount': 0}
        
    except Exception as e:
        return {'error': str(e)}

def call_nova_lite(raw_text):
    """Call Nova Lite for extraction"""
    try:
        prompt = f"""Extract invoice data from this text and return ONLY valid JSON:

{raw_text}

Return this exact structure:
{{
  "vendor_name": "company name",
  "invoice_number": "number",
  "total_amount": 123.45,
  "date": "YYYY-MM-DD",
  "payment_terms": "terms",
  "line_items": [
    {{
      "description": "item description",
      "quantity": 1,
      "rate": 100.00,
      "amount": 100.00
    }}
  ]
}}"""

        response = bedrock_client.invoke_model(
            modelId=NOVA_LITE_MODEL,
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"maxTokens": 1000, "temperature": 0.1}
            })
        )
        
        result = json.loads(response['body'].read())
        response_text = result['output']['message']['content'][0]['text']
        
        # Parse JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response_text[json_start:json_end])
        
        return None
        
    except Exception:
        return None

def call_claude_sonnet(raw_text):
    """Call Claude Sonnet for extraction"""
    try:
        prompt = f"""Extract structured data from this invoice text:

{raw_text}

Return valid JSON with vendor_name, invoice_number, total_amount, date, payment_terms, and line_items."""

        response = bedrock_client.invoke_model(
            modelId=CLAUDE_SONNET_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        response_text = result['content'][0]['text']
        
        # Parse JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response_text[json_start:json_end])
        
        return None
        
    except Exception:
        return None

def generate_chat_response(message, context):
    """Generate chat response using Claude Haiku"""
    try:
        prompt = f"""You are analyzing invoice data. Answer the user's question based on this data:

{json.dumps(context, indent=2)}

User question: {message}

Provide a clear, conversational answer."""

        response = bedrock_client.invoke_model(
            modelId=CLAUDE_HAIKU_MODEL,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "temperature": 0.7,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
        
    except Exception as e:
        return f"Sorry, I couldn't process your question: {str(e)}"

def store_document(file_content, filename, session_id, raw_text, structured_data):
    """Store document and metadata in S3"""
    try:
        doc_id = hashlib.md5(f"{session_id}_{filename}".encode()).hexdigest()
        
        # Store PDF
        pdf_key = f"sessions/{session_id}/documents/{filename}"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=pdf_key,
            Body=file_content,
            ContentType='application/pdf'
        )
        
        # Store metadata
        metadata = {
            'id': doc_id,
            'session_id': session_id,
            'filename': filename,
            's3_location': pdf_key,
            'raw_text': raw_text,
            'structured_data': structured_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        metadata_key = f"sessions/{session_id}/metadata/{doc_id}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=metadata_key,
            Body=json.dumps(metadata),
            ContentType='application/json'
        )
        
        return doc_id
        
    except Exception as e:
        raise Exception(f"Failed to store document: {str(e)}")

def get_session_documents(session_id):
    """Get all documents for a session"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=f"sessions/{session_id}/metadata/"
        )
        
        documents = []
        if 'Contents' in response:
            for obj in response['Contents']:
                metadata_response = s3_client.get_object(
                    Bucket=S3_BUCKET,
                    Key=obj['Key']
                )
                metadata = json.loads(metadata_response['Body'].read())
                documents.append(metadata)
        
        return documents
        
    except Exception:
        return []

def get_cors_headers():
    """Return standard CORS headers"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,DELETE',
        'Content-Type': 'application/json'
    }