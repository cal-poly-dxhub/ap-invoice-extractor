import uuid
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.session_lock = threading.Lock()
        self.cleanup_interval = 300  # 5 minutes
        self.session_timeout = 7200  # 2 hours
        self._start_cleanup_thread()
    
    def create_session(self, invoices: List[Dict[str, Any]]) -> str:
        """Create a new session with invoice data and embeddings."""
        session_id = str(uuid.uuid4())
        
        with self.session_lock:
            # Generate embeddings for invoices
            embeddings, texts = self._generate_embeddings(invoices)
            
            self.sessions[session_id] = {
                "id": session_id,
                "invoices": invoices,
                "embeddings": embeddings,
                "texts": texts,
                "vectorizer": None,  # Will store TF-IDF vectorizer if used
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(seconds=self.session_timeout),
                "last_accessed": datetime.now()
            }
        
        print(f"✅ Created session {session_id} with {len(invoices)} invoices")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data and update last accessed time."""
        with self.session_lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session["last_accessed"] = datetime.now()
                return session
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a specific session."""
        with self.session_lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                print(f"🗑️ Deleted session {session_id}")
                return True
            return False
    
    def _generate_embeddings(self, invoices: List[Dict[str, Any]]):
        """Generate simple TF-IDF embeddings for invoices."""
        texts = []
        
        for invoice in invoices:
            # Create searchable text from invoice data
            text_parts = []
            
            # Get structured data
            if invoice.get('structured_data'):
                data = invoice['structured_data']
                text_parts.append(f"Vendor {data.get('vendor_name', '')}")
                text_parts.append(f"Invoice {data.get('invoice_number', '')}")
                text_parts.append(f"Amount {data.get('total_amount', 0)} dollars")
                text_parts.append(f"Date {data.get('date', '')}")
                text_parts.append(f"Terms {data.get('payment_terms', '')}")
                
                # Add line items
                if data.get('line_items'):
                    for item in data['line_items']:
                        desc = item.get('description', '')
                        if desc:
                            text_parts.append(f"Item {desc}")
            
            # Add raw text if available
            raw_text = invoice.get('raw_text', '')
            if raw_text:
                # Take more text and clean it up
                clean_text = raw_text.replace('\n', ' ').replace('\r', ' ')
                text_parts.append(clean_text[:1000])  # First 1000 chars
            
            # Add document name
            doc_name = invoice.get('document_name', '')
            if doc_name:
                text_parts.append(f"Document {doc_name}")
            
            full_text = " ".join(text_parts).strip()
            if full_text:
                texts.append(full_text)
            else:
                # Fallback text to ensure we have something
                texts.append(f"Document {doc_name or 'Unknown'} invoice data")
        
        # Generate TF-IDF embeddings with more lenient settings
        if len(texts) > 0:
            try:
                vectorizer = TfidfVectorizer(
                    max_features=500, 
                    stop_words='english',
                    min_df=1,  # Include words that appear in at least 1 document
                    max_df=0.9,  # Exclude words that appear in more than 90% of documents
                    lowercase=True,
                    token_pattern=r'\b\w+\b'  # Simple word pattern
                )
                embeddings = vectorizer.fit_transform(texts).toarray()
                return embeddings, texts
            except ValueError as e:
                print(f"⚠️ TF-IDF failed: {e}, using simple text storage")
                # Fallback: just store texts without embeddings
                return np.array([]), texts
        
        return np.array([]), texts
    
    def _start_cleanup_thread(self):
        """Start background thread to cleanup expired sessions."""
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired_sessions()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = datetime.now()
        expired_sessions = []
        
        with self.session_lock:
            for session_id, session in self.sessions.items():
                if current_time > session["expires_at"]:
                    expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_count(self) -> int:
        """Get current number of active sessions."""
        with self.session_lock:
            return len(self.sessions)

# Global session manager instance
session_manager = SessionManager() 