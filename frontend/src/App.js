import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import InvoiceProcessor from './components/InvoiceProcessor';
import InvoiceList from './components/InvoiceList';
import { documentAPI } from './services/api';
import './index.css';

function App() {
  const [files, setFiles] = useState([]);
  const [processedInvoices, setProcessedInvoices] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentView, setCurrentView] = useState('upload'); // 'upload' | 'results'
  const [chatSessionId, setChatSessionId] = useState(null);

  const addFiles = (newFiles) => {
    const fileObjects = newFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file: file,
      name: file.name,
      size: file.size,
      status: 'pending'
    }));
    setFiles(prev => [...prev, ...fileObjects]);
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const processFiles = async () => {
    if (files.length === 0) return;
    
    setIsProcessing(true);
    setCurrentView('results');
    
    // The InvoiceProcessor component will handle the actual processing
    // and call setProcessedInvoices when complete
  };

  const resetApp = () => {
    setFiles([]);
    setProcessedInvoices([]);
    setCurrentView('upload');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold text-gray-900">
            Invoice Processor
          </h1>
          <p className="mt-2 text-gray-600">
            Upload and process invoices with AI-powered data extraction
          </p>
        </header>

        {currentView === 'upload' ? (
          <div className="space-y-6">
            <FileUpload 
              onFilesAdded={addFiles}
              files={files}
              onRemoveFile={removeFile}
            />
            
            {files.length > 0 && (
              <div className="flex justify-center">
                <button
                  onClick={processFiles}
                  disabled={isProcessing}
                  className="px-8 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 
                           text-white font-medium rounded-lg transition-colors duration-200 
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                >
                  {isProcessing ? 'Processing...' : 'Extract Invoice Data'}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-xl font-medium text-gray-900">
                Processed Invoices ({processedInvoices.length})
              </h2>
              <button
                onClick={resetApp}
                className="px-4 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 
                         hover:border-gray-400 rounded-lg transition-colors duration-200"
              >
                Upload New Files
              </button>
            </div>
            
            <InvoiceProcessor 
              files={files}
              isProcessing={isProcessing}
              onProcessed={setProcessedInvoices}
              onProcessingComplete={() => setIsProcessing(false)}
              onSessionCreated={setChatSessionId}
            />
            
            <InvoiceList 
              invoices={processedInvoices}
              sessionId={chatSessionId}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App; 