import React, { useState } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';

const InvoiceEditor = ({ invoice, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    vendor_name: invoice.data?.vendor_name || '',
    invoice_number: invoice.data?.invoice_number || '',
    date: invoice.data?.date || '',
    total_amount: invoice.data?.total_amount || '',
    currency: invoice.data?.currency || 'USD',
    payment_terms: invoice.data?.payment_terms || '',
    tax_amount: invoice.data?.tax_amount || '',
    line_items: invoice.data?.line_items || []
  });

  const updateField = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const updateLineItem = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const addLineItem = () => {
    setFormData(prev => ({
      ...prev,
      line_items: [
        ...prev.line_items,
        {
          description: '',
          quantity: 1,
          unit_price: 0,
          total: 0
        }
      ]
    }));
  };

  const removeLineItem = (index) => {
    setFormData(prev => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index)
    }));
  };

  const calculateLineTotal = (quantity, unitPrice) => {
    return (parseFloat(quantity) || 0) * (parseFloat(unitPrice) || 0);
  };

  const handleSave = () => {
    // Calculate total from line items if they exist
    const calculatedTotal = formData.line_items.reduce((sum, item) => {
      return sum + (parseFloat(item.total) || 0);
    }, 0);

    const updatedData = {
      ...formData,
      total_amount: calculatedTotal > 0 ? calculatedTotal : parseFloat(formData.total_amount) || 0
    };

    onSave(updatedData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Edit Invoice: {invoice.fileName}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Vendor Name
                </label>
                <input
                  type="text"
                  value={formData.vendor_name}
                  onChange={(e) => updateField('vendor_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                           focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Invoice Number
                </label>
                <input
                  type="text"
                  value={formData.invoice_number}
                  onChange={(e) => updateField('invoice_number', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                           focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => updateField('date', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                           focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.total_amount}
                  onChange={(e) => updateField('total_amount', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                           focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* Additional Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">Additional Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Currency
                </label>
                <select
                  value={formData.currency}
                  onChange={(e) => updateField('currency', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                           focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="CAD">CAD</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tax Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.tax_amount}
                  onChange={(e) => updateField('tax_amount', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                           focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Terms
                </label>
                <input
                  type="text"
                  value={formData.payment_terms}
                  onChange={(e) => updateField('payment_terms', e.target.value)}
                  placeholder="e.g., Net 30"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 
                           focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Line Items */}
          <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Line Items</h3>
              <button
                onClick={addLineItem}
                className="px-3 py-1 bg-primary-600 hover:bg-primary-700 text-white rounded-lg 
                         text-sm flex items-center space-x-1"
              >
                <Plus className="h-4 w-4" />
                <span>Add Item</span>
              </button>
            </div>

            <div className="space-y-3">
              {formData.line_items.map((item, index) => (
                <div key={index} className="flex gap-3 items-end">
                  <div className="flex-1">
                    <label className="block text-xs text-gray-500 mb-1">Description</label>
                    <input
                      type="text"
                      value={item.description || ''}
                      onChange={(e) => updateLineItem(index, 'description', e.target.value)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 
                               focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div className="w-20">
                    <label className="block text-xs text-gray-500 mb-1">Qty</label>
                    <input
                      type="number"
                      value={item.quantity || ''}
                      onChange={(e) => {
                        updateLineItem(index, 'quantity', e.target.value);
                        const total = calculateLineTotal(e.target.value, item.unit_price);
                        updateLineItem(index, 'total', total);
                      }}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 
                               focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div className="w-24">
                    <label className="block text-xs text-gray-500 mb-1">Unit Price</label>
                    <input
                      type="number"
                      step="0.01"
                      value={item.unit_price || ''}
                      onChange={(e) => {
                        updateLineItem(index, 'unit_price', e.target.value);
                        const total = calculateLineTotal(item.quantity, e.target.value);
                        updateLineItem(index, 'total', total);
                      }}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 
                               focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div className="w-24">
                    <label className="block text-xs text-gray-500 mb-1">Total</label>
                    <input
                      type="number"
                      step="0.01"
                      value={item.total || ''}
                      onChange={(e) => updateLineItem(index, 'total', e.target.value)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 
                               focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <button
                    onClick={() => removeLineItem(index)}
                    className="p-1 text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300 
                     hover:border-gray-400 rounded-lg transition-colors duration-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg 
                     transition-colors duration-200 flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>Save Changes</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default InvoiceEditor; 