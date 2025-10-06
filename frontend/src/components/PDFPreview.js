import React, { useState } from 'react';
import { X, ZoomIn, ZoomOut, RotateCw, FileText, Image, ChevronLeft, ChevronRight } from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up the worker for PDF.js
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const PDFPreview = ({ invoice, onClose }) => {
  const [scale, setScale] = useState(1.0);
  const [rotation, setRotation] = useState(0);
  const [viewMode, setViewMode] = useState('split'); // 'split', 'text', 'pdf'
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3.0));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(prev + 1, numPages));
  };

  // Create data URL from base64
  const pdfDataUrl = invoice.fileBase64 ? `data:application/pdf;base64,${invoice.fileBase64}` : null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {invoice.document_name || invoice.fileName}
            </h2>
            <p className="text-sm text-gray-500">
              Extracted with {invoice.confidence}% confidence • {invoice.extraction_metadata?.total_pages || numPages || 1} page(s)
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1 mr-4">
              <button
                onClick={() => setViewMode('text')}
                className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'text' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Text Only"
              >
                <FileText className="h-4 w-4 inline mr-1" />
                Text
              </button>
              <button
                onClick={() => setViewMode('split')}
                className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'split' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Split View"
              >
                Split
              </button>
              <button
                onClick={() => setViewMode('pdf')}
                className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  viewMode === 'pdf' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                } ${!invoice.fileBase64 ? 'opacity-50 cursor-not-allowed' : ''}`}
                title={invoice.fileBase64 ? "PDF Preview" : "PDF not available - file data missing"}
                disabled={!invoice.fileBase64}
              >
                <Image className="h-4 w-4 inline mr-1" />
                PDF
              </button>
            </div>
            
            {/* Preview Controls */}
            {viewMode === 'pdf' && (
              <div className="flex items-center space-x-1 mr-4">
                <button
                  onClick={handleZoomOut}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded"
                  title="Zoom Out"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-600 px-2">
                  {Math.round(scale * 100)}%
                </span>
                <button
                  onClick={handleZoomIn}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded"
                  title="Zoom In"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={handleRotate}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded ml-2"
                  title="Rotate"
                >
                  <RotateCw className="h-4 w-4" />
                </button>
              </div>
            )}
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className={`flex h-[calc(90vh-100px)] ${viewMode === 'split' ? 'divide-x divide-gray-200' : ''}`}>
          {/* Raw Text Preview */}
          {(viewMode === 'text' || viewMode === 'split') && (
            <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} overflow-y-auto p-4`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-gray-900">Extracted Text</h3>
                <span className="text-xs text-gray-500">
                  {invoice.rawText ? `${invoice.rawText.split(/\s+/).length} words` : '0 words'}
                </span>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 h-full">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono overflow-y-auto max-h-[calc(90vh-200px)]">
                  {invoice.rawText || 'No raw text available. The document may not have been processed yet.'}
                </pre>
              </div>
            </div>
          )}

          {/* PDF Preview */}
          {viewMode === 'pdf' && pdfDataUrl && (
            <div className="w-full overflow-hidden flex flex-col">
              {/* Page Navigation */}
              {numPages > 1 && (
                <div className="flex items-center justify-center p-2 border-b border-gray-200 bg-gray-50">
                  <button
                    onClick={goToPrevPage}
                    disabled={pageNumber <= 1}
                    className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <span className="text-sm text-gray-700 mx-4">
                    Page {pageNumber} of {numPages}
                  </span>
                  <button
                    onClick={goToNextPage}
                    disabled={pageNumber >= numPages}
                    className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              )}
              
              {/* PDF Viewer */}
              <div className="flex-1 overflow-auto flex items-center justify-center bg-gray-100 p-4">
                <Document
                  file={pdfDataUrl}
                  onLoadSuccess={onDocumentLoadSuccess}
                  loading={
                    <div className="text-center text-gray-500">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                      <p>Loading PDF...</p>
                    </div>
                  }
                  error={
                    <div className="text-center text-red-500">
                      <p className="mb-2">Failed to load PDF</p>
                      <p className="text-sm text-gray-500">Try refreshing or use Text view</p>
                    </div>
                  }
                >
                  <Page
                    pageNumber={pageNumber}
                    scale={scale}
                    rotate={rotation}
                    renderTextLayer={true}
                    renderAnnotationLayer={true}
                    className="shadow-lg"
                  />
                </Document>
              </div>
            </div>
          )}

          {/* PDF Not Available Fallback */}
          {viewMode === 'pdf' && !pdfDataUrl && (
            <div className="w-full flex items-center justify-center p-8">
              <div className="text-center text-gray-500">
                <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">PDF Not Available</h3>
                <p className="text-sm">The original PDF file data is not available for preview.</p>
                <p className="text-sm">You can still view the extracted text and structured data.</p>
                <button
                  onClick={() => setViewMode('text')}
                  className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  View Extracted Text
                </button>
              </div>
            </div>
          )}

          {/* Structured Data Preview */}
          {(viewMode === 'split') && (
            <div className="w-1/2 overflow-y-auto p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Structured Data</h3>
              
              {invoice.data ? (
                <div className="space-y-4">
                  {/* Basic Info */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Invoice Information</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-blue-700">Vendor:</span>
                        <span className="font-medium">{invoice.data.vendor_name || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Invoice #:</span>
                        <span className="font-medium">{invoice.data.invoice_number || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Date:</span>
                        <span className="font-medium">{invoice.data.date || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-700">Total:</span>
                        <span className="font-medium text-green-600">
                          ${invoice.data.total_amount?.toFixed(2) || '0.00'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Line Items */}
                  {invoice.data.line_items && invoice.data.line_items.length > 0 && (
                    <div className="bg-green-50 rounded-lg p-4">
                      <h4 className="font-medium text-green-900 mb-2">Line Items</h4>
                      <div className="space-y-2">
                        {invoice.data.line_items.map((item, index) => (
                          <div key={index} className="text-sm border-b border-green-200 pb-2 last:border-b-0">
                            <div className="font-medium text-green-900">{item.description}</div>
                            <div className="flex justify-between text-green-700 mt-1">
                              <span>Qty: {item.quantity}</span>
                              <span>Unit: ${item.unit_price?.toFixed(2) || '0.00'}</span>
                              <span className="font-medium">Total: ${item.total?.toFixed(2) || '0.00'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Payment Terms */}
                  {invoice.data.payment_terms && (
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <h4 className="font-medium text-yellow-900 mb-2">Payment Terms</h4>
                      <p className="text-sm text-yellow-800">{invoice.data.payment_terms}</p>
                    </div>
                  )}

                  {/* Validation Results */}
                  {invoice.validation && (
                    <div className="bg-purple-50 rounded-lg p-4">
                      <h4 className="font-medium text-purple-900 mb-2">AI Validation</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-purple-700">Valid:</span>
                          <span className={`font-medium ${
                            invoice.validation.is_valid ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {invoice.validation.is_valid ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-purple-700">Confidence:</span>
                          <span className="font-medium">{(invoice.validation.confidence_score * 100).toFixed(1)}%</span>
                        </div>
                        
                        {invoice.validation.suggestions && invoice.validation.suggestions.length > 0 && (
                          <div className="mt-3">
                            <div className="text-purple-700 mb-1">Suggestions:</div>
                            <ul className="list-disc list-inside space-y-1 text-purple-600">
                              {invoice.validation.suggestions.map((suggestion, index) => (
                                <li key={index} className="text-xs">{suggestion}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  No structured data available
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFPreview; 