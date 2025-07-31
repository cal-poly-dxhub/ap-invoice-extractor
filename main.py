#!/usr/bin/env python3
"""
Simple test script for text extraction and formatting functionality.
Tests the LocalTextExtractor and ClaudeClient using documents from test-data folder.
Supports multiple file types and bulk processing.
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path so we can import the clients
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from clients.local_text_extractor import LocalTextExtractor
from clients.claude_client import ClaudeClient

def test_single_document(file_path: str, text_extractor: LocalTextExtractor, claude_client: ClaudeClient):
    """Test extraction and formatting for a single document."""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Get file info
        file_size = os.path.getsize(file_path)
        file_ext = Path(file_path).suffix.lower()
        print(f"📄 Loading {file_ext.upper()} file...")
        print(f"   File size: {file_size:,} bytes")
        
        # Step 2: Extract text using Local Text Extractor
        print("🔍 Extracting text with local extractor...")
        extraction_result = text_extractor.extract_text_from_file(file_path)
        
        if 'error' in extraction_result:
            print(f"   ❌ Extraction Error: {extraction_result['error']}")
            return False
        
        print(f"   ✅ Text extracted successfully!")
        print(f"   📊 Confidence: {extraction_result.get('average_confidence', 0)}%")
        print(f"   📝 Lines: {extraction_result.get('total_lines', 0)}")
        print(f"   🔤 Words: {extraction_result.get('total_words', 0)}")
        
        # Show extractor info
        extractor_type = extraction_result.get('extraction_metadata', {}).get('extractor', 'unknown')
        print(f"   🔧 Extractor: {extractor_type}")
        
        # Show first few lines of raw text
        raw_text = extraction_result.get('raw_text', '')
        print(f"   📋 First 200 chars: {raw_text[:200]}...")
        
        # Step 3: Format text using Claude (only if it looks like an invoice/document)
        if file_ext in {'.pdf', '.txt'} and len(raw_text.strip()) > 50:
            print("🤖 Formatting with Claude...")
            formatting_result = claude_client.format_extracted_text(raw_text, "invoice")
            
            if 'error' in formatting_result:
                print(f"   ❌ Claude Error: {formatting_result['error']}")
                print(f"   📄 Raw text length: {len(raw_text)} chars")
                return False
            
            print(f"   ✅ Text formatted successfully!")
            
            # Display structured data
            print("📋 Structured Data:")
            print(json.dumps(formatting_result, indent=2, default=str))
            
            # Step 4: Validate extraction
            print("✅ Validating extraction...")
            validation_result = claude_client.validate_extraction(formatting_result, raw_text)
            
            if 'error' not in validation_result:
                print("📊 Validation Results:")
                print(json.dumps(validation_result, indent=2, default=str))
            else:
                print(f"   ⚠️  Validation error: {validation_result['error']}")
        else:
            print("⏭️  Skipping Claude formatting (not an invoice-type document)")
        
        return True
        
    except Exception as e:
        print(f"   💥 Unexpected error: {str(e)}")
        return False

def test_bulk_processing(text_extractor: LocalTextExtractor, claude_client: ClaudeClient, file_paths: list):
    """Test bulk processing functionality."""
    print(f"\n{'='*60}")
    print(f"🚀 BULK PROCESSING TEST")
    print(f"{'='*60}")
    
    print(f"📦 Processing {len(file_paths)} files in bulk...")
    results = text_extractor.extract_text_from_multiple_files(file_paths)
    
    successful_extractions = 0
    for i, result in enumerate(results):
        file_name = os.path.basename(file_paths[i])
        if 'error' not in result:
            successful_extractions += 1
            print(f"   ✅ {file_name}: {result.get('total_words', 0)} words")
        else:
            print(f"   ❌ {file_name}: {result['error']}")
    
    print(f"📊 Bulk extraction: {successful_extractions}/{len(file_paths)} successful")
    return successful_extractions

def main():
    """Main test function."""
    print("🚀 Starting Document Processing Test")
    print("=" * 60)
    
    # Initialize clients
    try:
        print("🔧 Initializing clients...")
        text_extractor = LocalTextExtractor()
        claude_client = ClaudeClient()
        print("   ✅ Clients initialized successfully!")
        
        # Show supported file types
        supported_exts = text_extractor.get_supported_extensions()
        print(f"   📄 Supported file types: {', '.join(supported_exts)}")
        
    except Exception as e:
        print(f"   ❌ Client initialization failed: {str(e)}")
        print("   💡 For Claude client, make sure you have AWS credentials configured!")
        return
    
    # Find test documents
    test_data_dir = Path("test-data")
    if not test_data_dir.exists():
        print(f"❌ Test data directory not found: {test_data_dir}")
        return
    
    # Use the extractor's scanning functionality
    document_files = text_extractor.scan_directory_for_documents(str(test_data_dir))
    
    if not document_files:
        print(f"❌ No supported documents found in {test_data_dir}")
        print(f"   Looking for: {', '.join(text_extractor.get_supported_extensions())}")
        return
    
    print(f"📁 Found {len(document_files)} supported documents:")
    for doc_file in document_files:
        file_size = os.path.getsize(doc_file)
        print(f"   • {os.path.basename(doc_file)} ({file_size:,} bytes)")
    
    # Test each document individually
    print(f"\n{'='*60}")
    print(f"🔍 INDIVIDUAL DOCUMENT TESTS")
    print(f"{'='*60}")
    
    successful_tests = 0
    for file_path in document_files:
        success = test_single_document(file_path, text_extractor, claude_client)
        if success:
            successful_tests += 1
    
    # Test bulk processing
    if len(document_files) > 1:
        bulk_successful = test_bulk_processing(text_extractor, claude_client, document_files)
    else:
        bulk_successful = 0
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🏁 Test Summary")
    print(f"{'='*60}")
    print(f"Total Documents: {len(document_files)}")
    print(f"Individual Tests - Successful: {successful_tests}")
    print(f"Individual Tests - Failed: {len(document_files) - successful_tests}")
    if len(document_files) > 1:
        print(f"Bulk Processing - Successful: {bulk_successful}/{len(document_files)}")
    
    if successful_tests == len(document_files):
        print("🎉 All individual tests passed!")
    else:
        print("⚠️  Some tests failed. Check file formats and AWS credentials for Claude.")

if __name__ == "__main__":
    main() 