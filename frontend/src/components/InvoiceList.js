import React, { useState } from 'react';
import { 
  Eye, Edit2, Download, ChevronLeft, ChevronRight, 
  CheckCircle, AlertCircle, Search, Filter 
} from 'lucide-react';
import InvoiceEditor from './InvoiceEditor';
import PDFPreview from './PDFPreview';
import ChatInterface from './ChatInterface';
import * as XLSX from 'xlsx';

const InvoiceList = ({ invoices, sessionId = null }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Filter and search invoices
  const filteredInvoices = invoices.filter(invoice => {
    const matchesSearch = invoice.document_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (invoice.data?.vendor_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (invoice.data?.invoice_number || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || invoice.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Pagination
  const totalPages = Math.ceil(filteredInvoices.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentInvoices = filteredInvoices.slice(startIndex, endIndex);

  const formatCurrency = (amount) => {
    if (!amount) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const exportToExcel = () => {
    const glReadyData = invoices
      .filter(inv => inv.status === 'success')
      .map(inv => ({
        'Document': inv.document_name,
        'Vendor': inv.data?.vendor_name || '',
        'Invoice Number': inv.data?.invoice_number || '',
        'Date': inv.data?.date || '',
        'Account': 'Accounts Payable', // GL Account
        'Description': inv.data?.line_items?.[0]?.description || '',
        'Debit': inv.data?.total_amount || 0,
        'Credit': 0,
        'Reference': inv.data?.invoice_number || '',
        'Entity': 'Cal Poly Pomona Foundation' // Default entity
      }));

    const worksheet = XLSX.utils.json_to_sheet(glReadyData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'GL_Import');
    
    // Set column widths
    const colWidths = [
      { wch: 25 }, // Document
      { wch: 30 }, // Vendor
      { wch: 15 }, // Invoice Number
      { wch: 12 }, // Date
      { wch: 20 }, // Account
      { wch: 40 }, // Description
      { wch: 12 }, // Debit
      { wch: 12 }, // Credit
      { wch: 15 }, // Reference
      { wch: 25 }  // Entity
    ];
    worksheet['!cols'] = colWidths;

    XLSX.writeFile(workbook, `GL_Import_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  const exportToCSV = () => {
    const glReadyData = invoices
      .filter(inv => inv.status === 'success')
      .map(inv => ({
        'Document': inv.document_name,
        'Vendor': inv.data?.vendor_name || '',
        'Invoice Number': inv.data?.invoice_number || '',
        'Date': inv.data?.date || '',
        'Account': 'Accounts Payable',
        'Description': inv.data?.line_items?.[0]?.description || '',
        'Debit': inv.data?.total_amount || 0,
        'Credit': 0,
        'Reference': inv.data?.invoice_number || '',
        'Entity': 'Cal Poly Pomona Foundation'
      }));

    const csv = [
      Object.keys(glReadyData[0]).join(','),
      ...glReadyData.map(row => Object.values(row).map(val => `"${val}"`).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `GL_Import_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by filename, vendor, or invoice number..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 
                         focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
          
          <div className="flex gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                       focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Status</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
            </select>
            
            <button
              onClick={exportToExcel}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg 
                       transition-colors duration-200 flex items-center space-x-2"
            >
              <Download className="h-4 w-4" />
              <span>Excel</span>
            </button>
            
            <button
              onClick={exportToCSV}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg 
                       transition-colors duration-200 flex items-center space-x-2"
            >
              <Download className="h-4 w-4" />
              <span>CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Invoice Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {currentInvoices.map((invoice) => (
          <div key={invoice.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  {invoice.status === 'success' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className="text-sm font-medium text-gray-900 truncate">
                    {invoice.document_name}
                  </span>
                </div>
                
                <div className="flex space-x-1">
                  {invoice.status === 'success' && (
                    <>
                      <button
                        onClick={() => setSelectedInvoice(invoice)}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                        title="Preview PDF"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setEditingInvoice(invoice)}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded"
                        title="Edit data"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {invoice.status === 'success' ? (
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">Vendor:</span>
                    <span className="ml-2 font-medium">{invoice.data?.vendor_name || 'Unknown'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Invoice #:</span>
                    <span className="ml-2">{invoice.data?.invoice_number || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Amount:</span>
                    <span className="ml-2 font-medium text-green-600">
                      {formatCurrency(invoice.data?.total_amount)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Date:</span>
                    <span className="ml-2">{invoice.data?.date || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Confidence:</span>
                    <span className="ml-2">{invoice.confidence}%</span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-red-600">
                  Error: {invoice.error}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-white px-4 py-3 border border-gray-200 rounded-lg">
          <div className="text-sm text-gray-700">
            Showing {startIndex + 1} to {Math.min(endIndex, filteredInvoices.length)} of{' '}
            {filteredInvoices.length} results
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            
            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      {selectedInvoice && (
        <PDFPreview
          invoice={selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
        />
      )}

      {editingInvoice && (
        <InvoiceEditor
          invoice={editingInvoice}
          onSave={(updatedData) => {
            // Update the invoice data
            const updatedInvoices = invoices.map(inv => 
              inv.id === editingInvoice.id 
                ? { ...inv, data: updatedData }
                : inv
            );
            setEditingInvoice(null);
          }}
          onClose={() => setEditingInvoice(null)}
        />
      )}

      {/* Chat Interface */}
      <ChatInterface invoices={filteredInvoices} sessionId={sessionId} />
    </div>
  );
};

export default InvoiceList; 