import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Plus, Upload, X, FileText } from 'lucide-react';

const FileUpload = ({ onFilesAdded, files, onRemoveFile }) => {
  const onDrop = useCallback((acceptedFiles) => {
    onFilesAdded(acceptedFiles);
  }, [onFilesAdded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'text/markdown': ['.md']
    },
    multiple: true
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragActive 
            ? 'border-primary-400 bg-primary-50' 
            : 'border-gray-300 hover:border-gray-400 bg-white'
          }
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className={`
              p-4 rounded-full transition-colors duration-200
              ${isDragActive ? 'bg-primary-100' : 'bg-gray-100'}
            `}>
              {isDragActive ? (
                <Upload className="h-8 w-8 text-primary-600" />
              ) : (
                <Plus className="h-8 w-8 text-gray-600" />
              )}
            </div>
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop files here' : 'Upload invoice files'}
            </p>
            <p className="text-gray-500 mt-1">
              Drag and drop files here, or click to browse
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Supports PDF, TXT, JSON, CSV, MD files
            </p>
          </div>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Selected Files ({files.length})
            </h3>
          </div>
          
          <div className="divide-y divide-gray-200">
            {files.map((file) => (
              <div key={file.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <FileText className="h-8 w-8 text-gray-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => onRemoveFile(file.id)}
                  className="flex-shrink-0 p-1 rounded-full text-gray-400 hover:text-red-500 
                           hover:bg-red-50 transition-colors duration-200"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload; 