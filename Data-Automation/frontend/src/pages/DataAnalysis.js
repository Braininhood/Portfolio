import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { toast } from 'react-toastify';
import { BarChart3, FileText, Users, CheckCircle, AlertCircle } from 'lucide-react';
import { getFiles, analyzeData } from '../services/api';

const DataAnalysis = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);

  const { data: files, isLoading } = useQuery('files', getFiles);

  const analysisMutation = useMutation(analyzeData, {
    onSuccess: (data) => {
      toast.success('Analysis completed successfully!');
      setAnalysisResults(data);
    },
    onError: (error) => {
      toast.error(`Analysis failed: ${error.response?.data?.error || error.message}`);
    },
  });

  const [analysisResults, setAnalysisResults] = useState(null);

  const handleFileToggle = (fileId) => {
    setSelectedFiles(prev => 
      prev.includes(fileId) 
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  };

  const handleAnalyze = () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select at least one file to analyze');
      return;
    }
    analysisMutation.mutate(selectedFiles);
  };

  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className="card">
      <div className="flex items-center">
        <div className={`p-3 rounded-md ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
      </div>
    </div>
  );

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
        <h1 className="text-2xl font-bold text-gray-900">Data Analysis</h1>
        <p className="mt-1 text-sm text-gray-500">
          Analyze participant data from uploaded Excel files to generate insights and statistics.
        </p>
      </div>

      {/* File Selection */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Select Files to Analyze</h2>
        <div className="space-y-3">
          {Array.isArray(files) && files.filter(file => file.status === 'processed').map((file) => (
            <label key={file.id} className="flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedFiles.includes(file.id)}
                onChange={() => handleFileToggle(file.id)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <div className="ml-3 flex-1">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {file.participant_count} participants • {file.status}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex items-center">
                {file.status === 'processed' ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
              </div>
            </label>
          ))}
        </div>
        
        {files?.filter(file => file.status === 'processed').length === 0 && (
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">No processed files available for analysis</p>
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleAnalyze}
            disabled={selectedFiles.length === 0 || analysisMutation.isLoading}
            className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {analysisMutation.isLoading ? 'Analyzing...' : 'Analyze Selected Files'}
          </button>
        </div>
      </div>

      {/* Analysis Results */}
      {analysisResults && (
        <div className="space-y-6">
          <h2 className="text-lg font-medium text-gray-900">Analysis Results</h2>
          
          {/* Summary Stats */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Participants"
              value={analysisResults.total_participants}
              icon={Users}
              color="bg-blue-500"
            />
            <StatCard
              title="Valid Emails"
              value={analysisResults.valid_emails}
              icon={CheckCircle}
              color="bg-green-500"
              subtitle={`${analysisResults.total_participants > 0 ? ((analysisResults.valid_emails / analysisResults.total_participants) * 100).toFixed(1) : 0}%`}
            />
            <StatCard
              title="Attending"
              value={analysisResults.attending_yes}
              icon={BarChart3}
              color="bg-purple-500"
              subtitle={`${analysisResults.total_participants > 0 ? ((analysisResults.attending_yes / analysisResults.total_participants) * 100).toFixed(1) : 0}%`}
            />
            <StatCard
              title="Need Software"
              value={analysisResults.need_365_yes}
              icon={FileText}
              color="bg-orange-500"
              subtitle={`${analysisResults.total_participants > 0 ? ((analysisResults.need_365_yes / analysisResults.total_participants) * 100).toFixed(1) : 0}%`}
            />
          </div>

          {/* Detailed Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Email Analysis</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Valid emails</span>
                  <span className="text-sm font-medium text-green-600">
                    {analysisResults.valid_emails} ({analysisResults.total_participants > 0 ? ((analysisResults.valid_emails / analysisResults.total_participants) * 100).toFixed(1) : 0}%)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Invalid emails</span>
                  <span className="text-sm font-medium text-red-600">
                    {analysisResults.invalid_emails} ({analysisResults.total_participants > 0 ? ((analysisResults.invalid_emails / analysisResults.total_participants) * 100).toFixed(1) : 0}%)
                  </span>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Attendance Analysis</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Attending</span>
                  <span className="text-sm font-medium text-green-600">
                    {analysisResults.attending_yes} ({analysisResults.total_participants > 0 ? ((analysisResults.attending_yes / analysisResults.total_participants) * 100).toFixed(1) : 0}%)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Not attending</span>
                  <span className="text-sm font-medium text-gray-600">
                    {analysisResults.attending_no} ({analysisResults.total_participants > 0 ? ((analysisResults.attending_no / analysisResults.total_participants) * 100).toFixed(1) : 0}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Email Issues */}
          {analysisResults.email_issues && analysisResults.email_issues.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Email Issues</h3>
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Issue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.isArray(analysisResults.email_issues) && analysisResults.email_issues.slice(0, 10).map((issue, index) => (
                      <tr key={index}>
                        <td>{issue.full_name}</td>
                        <td>{issue.email}</td>
                        <td>
                          <span className="badge badge-error">Invalid format</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {analysisResults.email_issues.length > 10 && (
                  <p className="text-sm text-gray-500 mt-2">
                    Showing first 10 of {analysisResults.email_issues.length} issues
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DataAnalysis;
