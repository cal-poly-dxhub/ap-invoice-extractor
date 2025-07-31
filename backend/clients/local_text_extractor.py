import os
import time
from typing import Dict, Any, List, Union
from pathlib import Path
import PyPDF2
import io

class LocalTextExtractor:
    def __init__(self):
        """Initialize local text extractor for multiple file types."""
        self.supported_extensions = {'.pdf', '.txt', '.py', '.json', '.md', '.csv'}
    
    def extract_text_from_bytes(self, document_bytes: bytes, document_name: str = "document") -> Dict[str, Any]:
        """
        Extract text from document bytes using local Python libraries.
        
        Args:
            document_bytes: Document content as bytes
            document_name: Name of the document for reference
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Get file extension
            file_ext = Path(document_name).suffix.lower()
            
            if file_ext not in self.supported_extensions:
                return {
                    "error": f"Unsupported file type: {file_ext}. Supported: {', '.join(self.supported_extensions)}",
                    "document_name": document_name
                }
            
            # Extract text based on file type
            if file_ext == '.pdf':
                return self._extract_from_pdf_bytes(document_bytes, document_name)
            elif file_ext in {'.txt', '.py', '.json', '.md', '.csv'}:
                return self._extract_from_text_bytes(document_bytes, document_name)
            else:
                return {
                    "error": f"Handler not implemented for {file_ext}",
                    "document_name": document_name
                }
                
        except Exception as e:
            return {
                "error": f"Local text extraction failed: {str(e)}",
                "document_name": document_name
            }
    
    def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a file path.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "error": f"File not found: {file_path}",
                    "document_name": os.path.basename(file_path)
                }
            
            with open(file_path, 'rb') as file:
                document_bytes = file.read()
            
            return self.extract_text_from_bytes(document_bytes, os.path.basename(file_path))
            
        except Exception as e:
            return {
                "error": f"File reading failed: {str(e)}",
                "document_name": os.path.basename(file_path)
            }
    
    def extract_text_from_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Extract text from multiple files (bulk processing).
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of extraction results
        """
        results = []
        for file_path in file_paths:
            result = self.extract_text_from_file(file_path)
            results.append(result)
        return results
    
    def _extract_from_pdf_bytes(self, pdf_bytes: bytes, document_name: str) -> Dict[str, Any]:
        """Extract text from PDF bytes using PyPDF2."""
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            text_content = []
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(page_text)
                except Exception as e:
                    # Skip problematic pages but continue
                    text_content.append(f"[Error extracting page {page_num + 1}: {str(e)}]")
            
            raw_text = "\n".join(text_content)
            
            # Create lines by splitting on newlines
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            
            # Estimate word count
            words = raw_text.split()
            
            return {
                "success": True,
                "document_name": document_name,
                "raw_text": raw_text,
                "lines": [{"text": line, "confidence": 100.0} for line in lines],  # Local extraction = 100% confidence
                "words": [{"text": word, "confidence": 100.0} for word in words[:100]],  # Limit words for memory
                "total_lines": len(lines),
                "total_words": len(words),
                "total_pages": total_pages,
                "average_confidence": 100.0,  # Local extraction
                "extraction_metadata": {
                    "extractor": "PyPDF2",
                    "timestamp": time.time(),
                    "file_size_bytes": len(pdf_bytes)
                }
            }
            
        except Exception as e:
            return {
                "error": f"PDF extraction failed: {str(e)}",
                "document_name": document_name
            }
    
    def _extract_from_text_bytes(self, text_bytes: bytes, document_name: str) -> Dict[str, Any]:
        """Extract text from text-based files."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            raw_text = None
            
            for encoding in encodings:
                try:
                    raw_text = text_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if raw_text is None:
                return {
                    "error": "Could not decode text file with supported encodings",
                    "document_name": document_name
                }
            
            # Create lines
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            
            # Estimate word count
            words = raw_text.split()
            
            return {
                "success": True,
                "document_name": document_name,
                "raw_text": raw_text,
                "lines": [{"text": line, "confidence": 100.0} for line in lines],
                "words": [{"text": word, "confidence": 100.0} for word in words[:100]],
                "total_lines": len(lines),
                "total_words": len(words),
                "average_confidence": 100.0,
                "extraction_metadata": {
                    "extractor": "direct_text",
                    "timestamp": time.time(),
                    "file_size_bytes": len(text_bytes),
                    "encoding": "utf-8"
                }
            }
            
        except Exception as e:
            return {
                "error": f"Text extraction failed: {str(e)}",
                "document_name": document_name
            }
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.supported_extensions)
    
    def scan_directory_for_documents(self, directory_path: str) -> List[str]:
        """
        Scan a directory for supported document files.
        
        Args:
            directory_path: Path to directory to scan
            
        Returns:
            List of file paths with supported extensions
        """
        supported_files = []
        directory = Path(directory_path)
        
        if not directory.exists():
            return supported_files
        
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                supported_files.append(str(file_path))
        
        return sorted(supported_files) 