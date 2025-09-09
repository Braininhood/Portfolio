import React, { useState } from 'react';
import { useMutation } from 'react-query';
import { toast } from 'react-toastify';
import { TestTube } from 'lucide-react';
import { testEmailConnection } from '../services/api';

const EmailSystem = () => {
  const [senderEmail, setSenderEmail] = useState('');
  const [senderPassword, setSenderPassword] = useState('');


  const testConnectionMutation = useMutation(testEmailConnection, {
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Email connection test successful!');
      } else {
        toast.error(`Connection test failed: ${data.message}`);
      }
    },
    onError: (error) => {
      toast.error(`Connection test failed: ${error.response?.data?.error || error.message}`);
    },
  });


  const handleTestConnection = () => {
    if (!senderEmail || !senderPassword) {
      toast.error('Please enter email and password');
      return;
    }

    testConnectionMutation.mutate({
      sender_email: senderEmail,
      sender_password: senderPassword,
    });
  };


  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Email Configuration</h1>
        <p className="mt-1 text-sm text-gray-500">
          Configure your Gmail settings for sending emails to cohort participants.
        </p>
      </div>

      {/* Email Configuration */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Gmail Credentials</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Gmail Address</label>
            <input
              type="email"
              value={senderEmail}
              onChange={(e) => setSenderEmail(e.target.value)}
              placeholder="your.email@gmail.com"
              className="input"
            />
          </div>
          <div>
            <label className="label">App Password</label>
            <input
              type="password"
              value={senderPassword}
              onChange={(e) => setSenderPassword(e.target.value)}
              placeholder="Your Gmail app password"
              className="input"
            />
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={handleTestConnection}
            disabled={!senderEmail || !senderPassword || testConnectionMutation.isLoading}
            className="btn btn-secondary"
          >
            <TestTube className="h-4 w-4 mr-2" />
            {testConnectionMutation.isLoading ? 'Testing...' : 'Test Connection'}
          </button>
        </div>
      </div>

      {/* Gmail Setup Guide */}
      <div className="card bg-blue-50 border-blue-200">
        <h2 className="text-lg font-medium text-blue-900 mb-4">Gmail Setup Guide</h2>
        
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-medium text-blue-900 mb-2">Step 1: Enable 2-Factor Authentication</h3>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Go to your <a href="https://myaccount.google.com/security" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Google Account settings</a></li>
              <li>Click on "Security" in the left sidebar</li>
              <li>Under "Signing in to Google", click "2-Step Verification"</li>
              <li>Follow the prompts to set up 2FA if not already enabled</li>
            </ol>
          </div>

          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-medium text-blue-900 mb-2">Step 2: Generate App Password</h3>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>In the same Security section, scroll down to "2-Step Verification"</li>
              <li>At the bottom, click "App passwords"</li>
              <li>Select "Mail" as the app type</li>
              <li>Choose "Other (custom name)" and enter "Data Automation"</li>
              <li>Click "Generate" and copy the 16-character password</li>
            </ol>
          </div>

          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-medium text-blue-900 mb-2">Step 3: Test Your Setup</h3>
            <p className="text-sm text-blue-800 mb-3">
              Use the "Test Connection" button above to verify your Gmail credentials work correctly.
            </p>
            <div className="bg-yellow-50 p-3 rounded border border-yellow-200">
              <p className="text-sm text-yellow-800">
                <strong>Important:</strong> Use your regular Gmail address but the App Password (not your regular password) in the password field.
              </p>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h3 className="font-medium text-blue-900 mb-2">Troubleshooting</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Make sure 2FA is enabled before generating app passwords</li>
              <li>App passwords are 16 characters with no spaces</li>
              <li>If connection fails, try generating a new app password</li>
              <li>Ensure "Less secure app access" is disabled (we use app passwords instead)</li>
            </ul>
          </div>
        </div>
      </div>


    </div>
  );
};

export default EmailSystem;
