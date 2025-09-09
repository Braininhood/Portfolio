import React, { useState } from 'react';
import { ExternalLink, Download, AlertCircle, CheckCircle } from 'lucide-react';
import { importFromForms } from '../services/api';

const MicrosoftFormsImport = ({ onImport }) => {
  const [formsUrl, setFormsUrl] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationStatus, setValidationStatus] = useState(null);
  const [error, setError] = useState('');

  const validateFormsUrl = (url) => {
    // Microsoft Forms URL pattern
    const formsPattern = /^https:\/\/forms\.office\.com\/[a-zA-Z0-9\-_\/]+$/;
    return formsPattern.test(url);
  };

  const handleUrlChange = (e) => {
    const url = e.target.value;
    setFormsUrl(url);
    setError('');
    
    if (url && !validateFormsUrl(url)) {
      setValidationStatus('invalid');
      setError('Please enter a valid Microsoft Forms URL');
    } else if (url && validateFormsUrl(url)) {
      setValidationStatus('valid');
    } else {
      setValidationStatus(null);
    }
  };

  const handleImport = async () => {
    if (!formsUrl || !validateFormsUrl(formsUrl)) {
      setError('Please enter a valid Microsoft Forms URL');
      return;
    }

    setIsValidating(true);
    setError('');

    try {
      const result = await importFromForms(formsUrl);
      
      onImport({
        source: 'microsoft_forms',
        url: formsUrl,
        participants: result.participant_count,
        status: 'imported',
        file_id: result.file_id
      });
      
      setFormsUrl('');
      setValidationStatus(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to import from Microsoft Forms. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const getStatusIcon = () => {
    if (validationStatus === 'valid') {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    } else if (validationStatus === 'invalid') {
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
    return null;
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Import from Microsoft Forms</h3>
        <p className="text-sm text-gray-600 mb-4">
          Import participant data directly from Microsoft Forms by providing the form's response URL.
        </p>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Microsoft Forms Response URL
          </label>
          <div className="relative">
            <input
              type="url"
              value={formsUrl}
              onChange={handleUrlChange}
              placeholder="https://forms.office.com/..."
              className="input pr-10"
            />
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              {getStatusIcon()}
            </div>
          </div>
          {error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={handleImport}
            disabled={!formsUrl || validationStatus !== 'valid' || isValidating}
            className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4 mr-2" />
            {isValidating ? 'Importing...' : 'Import from Forms'}
          </button>
          
          <a
            href="https://forms.office.com"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Open Microsoft Forms
          </a>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">How to get the Forms URL:</h4>
        <ol className="text-sm text-blue-800 space-y-1">
          <li>1. Open your Microsoft Forms</li>
          <li>2. Click on "Responses" tab</li>
          <li>3. Click "Open in Excel" or "Export to Excel"</li>
          <li>4. Copy the URL from the browser address bar</li>
          <li>5. Paste it in the field above</li>
        </ol>
      </div>
    </div>
  );
};

export default MicrosoftFormsImport;
