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
        self.embedding_model = "amazon.titan-embed-text-v2:0"
        
        # File-based document store (replace with actual OpenSearch when available)
        self.storage_dir = "/tmp/opensearch_storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        self.documents_file = os.path.join(self.storage_dir, "documents.pkl")
        self.embeddings_file = os.path.join(self.storage_dir, "embeddings.pkl")
        
        print(f"🔧 OpenSearchClient initialized - ID: {id(self)}")
        print(f"📁 Storage directory: {self.storage_dir}")
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings using Amazon Titan."""
        try:
            body = json.dumps({
                "inputText": text
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.embedding_model,
                body=body
            )
            
            result = json.loads(response['body'].read())
            return result['embedding']
            
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []
    
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
            
            # Step 2: Generate embeddings for text
            print(f"Generating embeddings for {filename}...")
            embeddings = self.generate_embeddings(raw_text)
            
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
                'embeddings': embeddings,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata
            }
            
            # Step 4: Store in document store (replace with OpenSearch)
            documents = self._load_documents()
            embeddings_dict = self._load_embeddings()
            
            documents[doc_id] = document
            embeddings_dict[doc_id] = embeddings
            
            self._save_documents(documents)
            self._save_embeddings(embeddings_dict)
            
            print(f"✅ Document stored: {filename} (ID: {doc_id})")

            return {
                'success': True,
                'document_id': doc_id,
                's3_location': s3_key,
                'embedding_dimensions': len(embeddings),
                'ready_for_search': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to store document: {str(e)}"
            }
    
    def semantic_search(self, query: str, session_id: str, limit: int = 5) -> Dict[str, Any]:
        """Perform semantic search using cosine similarity."""
        documents = self._load_documents()
        embeddings_dict = self._load_embeddings()
        
        print(f"📊 Search - Total documents: {len(documents)}")
        print(f"📊 All document sessions: {[doc['session_id'] for doc in documents.values()]}")
        print(f"📊 Looking for session: {session_id}")

        try:
            # Generate query embeddings
            query_embeddings = self.generate_embeddings(query)
            if not query_embeddings:
                return {'success': False, 'error': 'Failed to generate query embeddings'}
            
            # Filter documents by session
            session_docs = {doc_id: doc for doc_id, doc in documents.items() 
                           if doc['session_id'] == session_id}
            
            if not session_docs:
                return {
                    'success': True,
                    'results': [],
                    'message': 'No documents found in this session'
                }
            
            # Calculate similarities
            similarities = []
            for doc_id, doc in session_docs.items():
                doc_embeddings = embeddings_dict.get(doc_id, [])
                
                if doc_embeddings:
                    similarity = self._cosine_similarity(query_embeddings, doc_embeddings)
                    similarities.append((similarity, doc_id, doc))
            
            # Sort by similarity and return top results (lower threshold for testing)
            similarities.sort(reverse=True, key=lambda x: x[0])
            
            results = []
            for similarity, doc_id, doc in similarities[:limit]:
                # Lower threshold for testing - include any similarity > 0
                if similarity > 0:
                    results.append({
                        'document_id': doc_id,
                        'filename': doc['filename'],
                        'similarity_score': similarity,
                        'content_snippet': doc['raw_text'][:300] + "..." if len(doc['raw_text']) > 300 else doc['raw_text'],
                        'structured_data': doc['structured_data'],
                        's3_location': doc['s3_location']
                    })
            
            return {
                'success': True,
                'results': results,
                'query': query,
                'session_id': session_id,
                'total_found': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Search failed: {str(e)}"
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
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import math
            
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            
            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception:
            return 0
    
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
    
    def _load_embeddings(self) -> Dict:
        """Load embeddings from file."""
        try:
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading embeddings: {e}")
        return {}
    
    def _save_embeddings(self, embeddings: Dict):
        """Save embeddings to file."""
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(embeddings, f)
        except Exception as e:
            print(f"Error saving embeddings: {e}")


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