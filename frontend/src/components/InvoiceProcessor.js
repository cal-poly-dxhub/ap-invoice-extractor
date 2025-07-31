import React, { useState, useEffect, useCallback } from 'react';
import { documentAPI, chatAPI } from '../services/api';

const InvoiceProcessor = ({ files, isProcessing, onProcessed, onProcessingComplete, onSessionCreated }) => {
  const [processingStatus, setProcessingStatus] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const processInvoices = useCallback(async () => {
    if (!files || files.length === 0) return;

    console.log('🚀 Starting to process invoices...');
    setProcessingStatus(files.map(f => ({ id: f.id, status: 'pending', error: null })));
    
    const processedResults = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setCurrentIndex(i);
      
      try {
        console.log(`📄 Processing file ${i + 1}/${files.length}: ${file.name}`);
        
        // Update status to processing
        setProcessingStatus(prev => 
          prev.map(s => s.id === file.id ? { ...s, status: 'processing' } : s)
        );

        // Convert file to base64
        const fileContent = await fileToBase64(file.file);
        
        const requestData = {
          file_data: fileContent,
          file_name: file.name,
          document_type: 'invoice'
        };

        // Process the document
        const result = await documentAPI.processDocument(requestData);
        
        if (result.success) {
          console.log(`✅ Successfully processed: ${file.name}`);
          console.log('Result structure:', result);
          
          // Map the structured_data to data for UI compatibility
          const resultWithStatus = {
            ...result,
            status: 'success',
            data: result.structured_data || {},  // Map structured_data to data
            confidence: Math.round((result.extraction_confidence || 0) * 100),  // Convert to percentage
            id: file.id,
            document_name: result.document_name || file.name,
            rawText: result.raw_text || '',  // Add raw text for preview
            validation: result.validation || null,  // Add validation data
            extraction_metadata: result.extraction_metadata || {},  // Add metadata for page count
            fileData: fileContent,  // Store original file data for PDF preview
            fileType: file.file.type  // Store file type
          };
          processedResults.push(resultWithStatus);
          
          // Update status to completed
          setProcessingStatus(prev => 
            prev.map(s => s.id === file.id ? { ...s, status: 'completed' } : s)
          );
        } else {
          throw new Error(result.error || 'Processing failed');
        }
        
      } catch (error) {
        console.error(`❌ Error processing ${file.name}:`, error);
        console.error('Error details:', {
          message: error.message,
          stack: error.stack,
          response: error.response
        });
        
        // Get a meaningful error message
        let errorMessage = 'Processing failed';
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        } else if (error.response?.data?.error) {
          errorMessage = error.response.data.error;
        }
        
        // Update status to error
        setProcessingStatus(prev => 
          prev.map(s => s.id === file.id ? { ...s, status: 'error', error: errorMessage } : s)
        );
      }
    }

    // Update processed invoices
    onProcessed(processedResults);
    
    // Create chat session if we have any successful results
    if (processedResults.length > 0) {
      try {
        console.log('🎯 Creating chat session with processed invoices...');
        const sessionResponse = await chatAPI.createSession(processedResults);
        
        if (sessionResponse.success) {
          console.log(`✅ Chat session created: ${sessionResponse.session_id}`);
          onSessionCreated && onSessionCreated(sessionResponse.session_id);
        }
      } catch (error) {
        console.error('❌ Error creating chat session:', error);
      }
    }
    
    // Mark processing as complete
    onProcessingComplete();
    console.log('🏁 Processing complete!');
    
  }, [files, onProcessed, onProcessingComplete, onSessionCreated]);

  // Start processing when files change and we're in processing mode
  useEffect(() => {
    if (isProcessing && files.length > 0) {
      processInvoices();
    }
  }, [isProcessing, files, processInvoices]);

  // Helper function to convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data:mime/type;base64, prefix
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  if (!isProcessing) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center mb-4">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600 mr-3"></div>
        <h3 className="text-lg font-medium text-gray-900">
          Processing Invoices ({currentIndex + 1} of {files.length})
        </h3>
      </div>
      
      <div className="space-y-3">
        {files.map((file, index) => {
          const status = processingStatus.find(s => s.id === file.id);
          
          return (
            <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center">
                <div className="flex-shrink-0 mr-3">
                  {status?.status === 'pending' && (
                    <div className="w-4 h-4 bg-gray-300 rounded-full"></div>
                  )}
                  {status?.status === 'processing' && (
                    <div className="w-4 h-4 bg-primary-500 rounded-full animate-pulse"></div>
                  )}
                  {status?.status === 'completed' && (
                    <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                      <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                  {status?.status === 'error' && (
                    <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                      <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
                
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  {status?.error && (
                    <p className="text-xs text-red-600">{status.error}</p>
                  )}
                </div>
              </div>
              
              <div className="text-xs text-gray-500 capitalize">
                {status?.status || 'pending'}
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="mt-4 text-sm text-gray-600">
        Processing documents and preparing chat session...
      </div>
    </div>
  );
};

export default InvoiceProcessor; 