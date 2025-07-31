#!/usr/bin/env python3
"""
Local API server for testing the React frontend with the Lambda function.
Run this to test your frontend without deploying to AWS.
"""

import os
import sys
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from lambda_functions.document_processor import lambda_handler
from clients.session_manager import session_manager
from clients.chat_handler import ChatHandler

app = FastAPI(title="Invoice Processor API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DocumentRequest(BaseModel):
    file_data: str
    file_name: str
    document_type: str = "invoice"

class S3DocumentRequest(BaseModel):
    s3_key: str
    bucket_name: Optional[str] = None
    document_type: str = "invoice"

class CreateSessionRequest(BaseModel):
    invoices: List[dict]

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.get("/")
async def root():
    return {"message": "Invoice Processor API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "invoice-processor"}

@app.post("/process-document")
async def process_document(request: DocumentRequest):
    """Process a document using the Lambda function."""
    try:
        print(f"🔍 Processing document: {request.file_name}")
        
        # Create Lambda event format
        event = {
            "body": json.dumps({
                "file_data": request.file_data,
                "file_name": request.file_name,
                "document_type": request.document_type
            })
        }
        
        print("📝 Calling lambda_handler...")
        # Call the Lambda handler
        result = lambda_handler(event, None)
        print(f"✅ Lambda result status: {result.get('statusCode', 'unknown')}")
        
        # Parse the Lambda response
        if result["statusCode"] == 200:
            response_body = json.loads(result["body"])
            print("🎉 Processing successful")
            return response_body
        else:
            error_body = json.loads(result["body"])
            error_msg = error_body.get("error", "Processing failed")
            print(f"❌ Processing failed: {error_msg}")
            raise HTTPException(
                status_code=result["statusCode"],
                detail=error_msg
            )
            
    except Exception as e:
        print(f"💥 Exception in API: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-s3-document")
async def process_s3_document(request: S3DocumentRequest):
    """Process a document from S3 using the Lambda function."""
    try:
        # Create Lambda event format
        event = {
            "body": json.dumps({
                "s3_key": request.s3_key,
                "bucket_name": request.bucket_name,
                "document_type": request.document_type
            })
        }
        
        # Call the Lambda handler
        result = lambda_handler(event, None)
        
        # Parse the Lambda response
        if result["statusCode"] == 200:
            response_body = json.loads(result["body"])
            return response_body
        else:
            error_body = json.loads(result["body"])
            raise HTTPException(
                status_code=result["statusCode"],
                detail=error_body.get("error", "Processing failed")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-session")
async def create_session(request: CreateSessionRequest):
    """Create a new chat session with invoice data."""
    try:
        print(f"🎯 Creating session with {len(request.invoices)} invoices")
        
        # Create session with embeddings
        session_id = session_manager.create_session(request.invoices)
        
        return {
            "success": True,
            "session_id": session_id,
            "invoice_count": len(request.invoices),
            "message": "Session created successfully"
        }
        
    except Exception as e:
        print(f"💥 Session creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_invoices(request: ChatRequest):
    """Chat about invoices in a specific session."""
    try:
        print(f"💬 Chat request for session {request.session_id}: {request.message}")
        
        # Get session data
        session_data = session_manager.get_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Initialize chat handler
        chat_handler = ChatHandler()
        
        # Process the chat message
        result = chat_handler.handle_chat(request.message, session_data)
        
        if result.get("success"):
            print(f"✅ Chat response generated")
            return {
                "success": True,
                "response": result["response"],
                "session_id": request.session_id
            }
        else:
            print(f"❌ Chat error: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error"))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get status of a specific session."""
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "invoice_count": len(session_data.get("invoices", [])),
        "created_at": session_data.get("created_at").isoformat(),
        "expires_at": session_data.get("expires_at").isoformat(),
        "active": True
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session."""
    success = session_manager.delete_session(session_id)
    
    if success:
        return {"success": True, "message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions/stats")
async def get_session_stats():
    """Get current session statistics."""
    return {
        "active_sessions": session_manager.get_session_count(),
        "max_concurrent_users": 20
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Invoice Processor API Server")
    print("📱 Frontend URL: http://localhost:3000")
    print("🔗 API URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True
    ) 