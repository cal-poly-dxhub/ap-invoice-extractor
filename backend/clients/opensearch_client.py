import boto3
import json
import time
import os
import pickle
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

class OpenSearchClient:
    def __init__(self, region_name: str = "us-west-2"):
        """Initialize OpenSearch client for direct document storage."""
            
        session = boto3.Session()
        self.bedrock_runtime = session.client("bedrock-runtime", region_name=region_name)
        self.s3_client = session.client("s3", region_name=region_name)
        
        # Configuration
        self.s3_bucket = "csu-summer-camp-invoice-extraction-2025-2"
        self.s3_prefix = "invoices/"

        
        # File-based document store (replace with actual OpenSearch when available)
        self.storage_dir = "/tmp/opensearch_storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        self.documents_file = os.path.join(self.storage_dir, "documents.pkl")

        
        print(f"🔧 OpenSearchClient initialized - ID: {id(self)}")
        print(f"📁 Storage directory: {self.storage_dir}")
    

    
    def upload_and_store_document(self, file_content: bytes, filename: str, session_id: str, 
                                 raw_text: str, structured_data: dict) -> Dict[str, Any]:
        """Upload to S3 and store document with embeddings."""
        try:
            # Step 1: Upload to S3 with session prefix
            session_filename = f"{session_id}_{filename}"
            s3_key = f"{self.s3_prefix}{session_filename}"
            
            metadata = {
                'session_id': session_id,
                'original_filename': filename,
                'upload_timestamp': datetime.utcnow().isoformat()
            }
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=file_content,
                Metadata=metadata,
                ContentType='application/pdf'
            )
            
            # Step 2: Skip embeddings generation
            
            # Step 3: Create document record
            doc_id = hashlib.md5(f"{session_id}_{filename}".encode()).hexdigest()
            
            document = {
                'id': doc_id,
                'session_id': session_id,
                'filename': filename,
                'original_filename': filename,
                's3_location': s3_key,
                'raw_text': raw_text,
                'structured_data': structured_data,

                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata
            }
            
            # Step 4: Store in document store
            documents = self._load_documents()
            documents[doc_id] = document
            self._save_documents(documents)
            
            print(f"✅ Document stored: {filename} (ID: {doc_id})")

            return {
                'success': True,
                'document_id': doc_id,
                's3_location': s3_key,

                'ready_for_search': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to store document: {str(e)}"
            }
    

    
    def get_session_documents(self, session_id: str) -> List[Dict]:
        """Get all documents for a session."""
        documents = self._load_documents()
        session_docs = [doc for doc in documents.values() 
                       if doc['session_id'] == session_id]
        return session_docs
    
    def aggregate_data(self, session_id: str, field: str, operation: str = 'sum') -> Dict[str, Any]:
        """Aggregate data across session documents."""
        try:
            session_docs = self.get_session_documents(session_id)
            
            if not session_docs:
                return {'success': False, 'error': 'No documents in session'}
            
            # Extract values for aggregation
            values = []
            for doc in session_docs:
                structured_data = doc.get('structured_data', {})
                
                if field == 'total_amount':
                    amount = structured_data.get('total_amount', 0)
                    if isinstance(amount, (int, float)):
                        values.append(amount)
                elif field == 'vendor_name':
                    vendor = structured_data.get('vendor_name', 'Unknown')
                    values.append(vendor)
            
            # Perform aggregation
            if operation == 'sum' and field == 'total_amount':
                result = sum(values)
            elif operation == 'avg' and field == 'total_amount':
                result = sum(values) / len(values) if values else 0
            elif operation == 'count':
                result = len(values)
            elif field == 'vendor_name':
                # Group by vendor
                vendor_counts = {}
                for vendor in values:
                    vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
                result = vendor_counts
            else:
                result = values
            
            return {
                'success': True,
                'field': field,
                'operation': operation,
                'result': result,
                'document_count': len(session_docs)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Aggregation failed: {str(e)}"
            }
    

    
    def _load_documents(self) -> Dict:
        """Load documents from file."""
        try:
            if os.path.exists(self.documents_file):
                with open(self.documents_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading documents: {e}")
        return {}
    
    def _save_documents(self, documents: Dict):
        """Save documents to file."""
        try:
            with open(self.documents_file, 'wb') as f:
                pickle.dump(documents, f)
        except Exception as e:
            print(f"Error saving documents: {e}")
    



# Global instance to ensure singleton across imports
_global_client = None

def get_opensearch_client():
    global _global_client
    if _global_client is None:
        print("🆕 Creating NEW global OpenSearch client")
        _global_client = OpenSearchClient()
    else:
        print("♻️ Reusing existing global OpenSearch client")
    return _global_client