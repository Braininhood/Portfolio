import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-toastify';
import { Upload, FileText, CheckCircle, AlertCircle, X, FileSpreadsheet, ExternalLink } from 'lucide-react';
import { uploadFile, getFiles, deleteFile } from '../services/api';
import MicrosoftFormsImport from '../components/MicrosoftFormsImport';

const FileUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadMethod, setUploadMethod] = useState('excel'); // 'excel' or 'forms'
  const queryClient = useQueryClient();

  const { data: files, isLoading } = useQuery('files', getFiles, {
    initialData: [],
  });

  const uploadMutation = useMutation(uploadFile, {
    onSuccess: () => {
      queryClient.invalidateQueries('files');
      queryClient.invalidateQueries('dashboard-stats');
      toast.success('File uploaded successfully!');
    },
    onError: (error) => {
      toast.error(`Upload failed: ${error.response?.data?.error || error.message}`);
    },
  });

  const deleteMutation = useMutation(deleteFile, {
    onSuccess: () => {
      queryClient.invalidateQueries('files');
      queryClient.invalidateQueries('dashboard-stats');
      toast.success('File deleted successfully!');
    },
    onError: (error) => {
      toast.error(`Delete failed: ${error.response?.data?.error || error.message}`);
    },
  });

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    // Validate file type
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      toast.error('Please upload an Excel file (.xlsx or .xls)');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    setUploading(true);
    uploadMutation.mutate(file, {
      onSettled: () => setUploading(false),
    });
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
  });

  const handleDelete = (fileId) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      deleteMutation.mutate(fileId);
    }
  };

  const handleFormsImport = (importData) => {
    toast.success(`Successfully imported ${importData.participants} participants from Microsoft Forms!`);
    queryClient.invalidateQueries('files');
    queryClient.invalidateQueries('dashboard-stats');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status) => {
    const baseClasses = 'badge';
    switch (status) {
      case 'processed':
        return `${baseClasses} badge-success`;
      case 'error':
        return `${baseClasses} badge-error`;
      case 'processing':
        return `${baseClasses} badge-warning`;
      default:
        return `${baseClasses} badge-info`;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">File Upload</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload Excel files containing participant data for processing and analysis.
        </p>
      </div>

      {/* Upload Method Selection */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Choose Upload Method</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => setUploadMethod('excel')}
            className={`p-4 border-2 rounded-lg text-left transition-colors ${
              uploadMethod === 'excel'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <FileSpreadsheet className="h-8 w-8 text-blue-500 mb-2" />
            <h3 className="font-medium text-gray-900">Upload Excel File</h3>
            <p className="text-sm text-gray-500">Upload .xlsx or .xls files from your computer</p>
          </button>
          
          <button
            onClick={() => setUploadMethod('forms')}
            className={`p-4 border-2 rounded-lg text-left transition-colors ${
              uploadMethod === 'forms'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <ExternalLink className="h-8 w-8 text-green-500 mb-2" />
            <h3 className="font-medium text-gray-900">Import from Microsoft Forms</h3>
            <p className="text-sm text-gray-500">Import data directly from Microsoft Forms</p>
          </button>
        </div>
      </div>

      {/* Upload Area */}
      <div className="card">
        {uploadMethod === 'excel' ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-400 bg-primary-50'
                : 'border-gray-300 hover:border-gray-400'
            } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <input {...getInputProps()} disabled={uploading} />
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <div className="mt-4">
              <p className="text-lg font-medium text-gray-900">
                {isDragActive
                  ? 'Drop the file here...'
                  : uploading
                  ? 'Uploading...'
                  : 'Drag & drop an Excel file here, or click to select'}
              </p>
              <p className="mt-2 text-sm text-gray-500">
                Supports .xlsx and .xls files up to 10MB
              </p>
            </div>
          </div>
        ) : (
          <MicrosoftFormsImport onImport={handleFormsImport} />
        )}
      </div>

      {/* File List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">Uploaded Files</h2>
          <span className="text-sm text-gray-500">
            {Array.isArray(files) ? files.length : 0} file{(Array.isArray(files) ? files.length : 0) !== 1 ? 's' : ''}
          </span>
        </div>

        {!files || files.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">No files uploaded yet</p>
          </div>
        ) : (
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table className="table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Status</th>
                  <th>Participants</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Array.isArray(files) && files.map((file) => (
                  <tr key={file.id}>
                    <td>
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-gray-400 mr-3" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {file.uploaded_by_username || 'Unknown user'}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center">
                        {getStatusIcon(file.status)}
                        <span className={`ml-2 ${getStatusBadge(file.status)}`}>
                          {file.status}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="text-sm text-gray-900">{file.participant_count}</span>
                    </td>
                    <td>
                      <span className="text-sm text-gray-500">
                        {new Date(file.uploaded_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleDelete(file.id)}
                          className="text-red-600 hover:text-red-900"
                          disabled={deleteMutation.isLoading}
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card bg-blue-50 border-blue-200">
          <h3 className="text-lg font-medium text-blue-900 mb-2">Excel File Requirements</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Files must be in Excel format (.xlsx or .xls)</li>
            <li>• Maximum file size: 10MB</li>
            <li>• Required columns: full_name, moodle_email, attending, need_365, etc.</li>
            <li>• Files are automatically processed after upload</li>
            <li>• Processing status will be shown in the file list</li>
          </ul>
        </div>

        <div className="card bg-green-50 border-green-200">
          <h3 className="text-lg font-medium text-green-900 mb-2">Microsoft Forms Import</h3>
          <ul className="text-sm text-green-800 space-y-1">
            <li>• Import data directly from Microsoft Forms</li>
            <li>• No file size limitations</li>
            <li>• Automatic data validation and processing</li>
            <li>• Real-time import status updates</li>
            <li>• Supports all standard form field types</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
