import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-toastify';
import { FileBarChart, Download, Plus, Eye, X, BarChart3 } from 'lucide-react';
import { getReports, generateReport, generateEnhancedReport, downloadReport, sendReportEmail, deleteReport } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell, LineChart, Line } from 'recharts';

const Reports = () => {
  const [reportType, setReportType] = useState('executive_summary');
  const [selectedReport, setSelectedReport] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showChartModal, setShowChartModal] = useState(false);
  const [selectedCharts, setSelectedCharts] = useState([]);
  const [bossEmail, setBossEmail] = useState('');
  const [bossName, setBossName] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [senderPassword, setSenderPassword] = useState('');
  const [customMessage, setCustomMessage] = useState('');
  const [emailSelectedCharts, setEmailSelectedCharts] = useState([]);

  const queryClient = useQueryClient();
  const { data: reports, isLoading } = useQuery('reports', getReports);

  const generateMutation = useMutation(generateReport, {
    onSuccess: (data) => {
      toast.success('Report generated successfully!');
      // Auto-refresh the reports list
      queryClient.invalidateQueries('reports');
    },
    onError: (error) => {
      toast.error(`Failed to generate report: ${error.response?.data?.error || error.message}`);
    },
  });

  const generateEnhancedMutation = useMutation(generateEnhancedReport, {
    onSuccess: (data) => {
      toast.success('Enhanced report generated successfully!');
      // Auto-refresh the reports list
      queryClient.invalidateQueries('reports');
    },
    onError: (error) => {
      toast.error(`Failed to generate enhanced report: ${error.response?.data?.error || error.message}`);
    },
  });

  const sendEmailMutation = useMutation(sendReportEmail, {
    onSuccess: (data) => {
      toast.success(`Report sent successfully to ${data.sent_to}!`);
      setShowEmailModal(false);
    },
    onError: (error) => {
      toast.error(`Failed to send report: ${error.response?.data?.error || error.message}`);
    },
  });

  const deleteMutation = useMutation(deleteReport, {
    onSuccess: () => {
      toast.success('Report deleted successfully!');
      queryClient.invalidateQueries('reports');
    },
    onError: (error) => {
      toast.error('Error deleting report: ' + (error.response?.data?.error || error.message));
    },
  });

  const handleGenerateReport = () => {
    const parameters = {};

    // Use enhanced reports for new report types
    const enhancedTypes = ['comprehensive_analysis', 'cohort_performance', 'email_effectiveness', 'executive_summary'];
    
    if (enhancedTypes.includes(reportType)) {
      generateEnhancedMutation.mutate({
        report_type: reportType,
        parameters,
      });
    } else {
      generateMutation.mutate({
        report_type: reportType,
        parameters,
      });
    }
  };

  const handleSendEmail = (report) => {
    setSelectedReport(report);
    setShowEmailModal(true);
    // Initialize with all available charts if report has chart data
    if (report.chart_data) {
      setEmailSelectedCharts(Object.keys(report.chart_data));
    } else {
      setEmailSelectedCharts([]);
    }
  };

  const handlePreviewCharts = (report) => {
    setSelectedReport(report);
    setShowChartModal(true);
    // Initialize selected charts with all available charts
    if (report.chart_data) {
      setSelectedCharts(Object.keys(report.chart_data));
    }
  };

  const handleChartToggle = (chartKey) => {
    setSelectedCharts(prev => 
      prev.includes(chartKey) 
        ? prev.filter(key => key !== chartKey)
        : [...prev, chartKey]
    );
  };

  const handleSendEmailSubmit = () => {
    if (!selectedReport || !bossEmail || !bossName || !senderEmail || !senderPassword) {
      toast.error('Please fill in all required fields');
      return;
    }

    sendEmailMutation.mutate({
      report_id: selectedReport.id,
      boss_email: bossEmail,
      boss_name: bossName,
      sender_email: senderEmail,
      sender_password: senderPassword,
      custom_message: customMessage,
      selected_charts: emailSelectedCharts,
    });
  };

  const handleDeleteReport = (reportId) => {
    if (window.confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
      deleteMutation.mutate(reportId);
    }
  };

  const renderChart = (chartKey, chartData) => {
    if (!chartData || !chartData.data) return null;

    // Professional color schemes
    const professionalColors = {
      primary: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
      executive: ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#7209B7', '#F77F00', '#8E44AD'],
      modern: ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22']
    };

    const colors = professionalColors.executive;

    const getChartTitle = (key) => {
      const titles = {
        'participation_overview': 'Participation Overview',
        'cohort_performance': 'Cohort Performance',
        'kpi_dashboard': 'Key Performance Indicators',
        'email_validation': 'Email Validation Status',
        'attendance_status': 'Attendance Status',
        'cohort_distribution': 'Cohort Distribution',
        'software_needs': 'Software Requirements',
        'email_success_rates': 'Email Campaign Success Rates',
        'overall_email_stats': 'Email Delivery Statistics',
        'cohort_sizes': 'Cohort Sizes',
        'attendance_rates': 'Attendance Rates',
        'cohort_types': 'Cohort Types Distribution'
      };
      return titles[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    switch (chartData.type) {
      case 'pie':
        return (
          <div key={chartKey} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-xl font-semibold text-gray-800">{getChartTitle(chartKey)}</h4>
              <div className="text-sm text-gray-500">
                Total: {chartData.data.reduce((sum, item) => sum + item.value, 0)}
              </div>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <RechartsPieChart>
                <Pie
                  data={chartData.data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent, value }) => `${name}: ${value} (${(percent * 100).toFixed(1)}%)`}
                  outerRadius={100}
                  innerRadius={30}
                  fill="#1f77b4"
                  dataKey="value"
                  stroke="#fff"
                  strokeWidth={2}
                >
                  {chartData.data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name) => [value, name]}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{ 
                    backgroundColor: '#f9fafb', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
        );

      case 'bar':
        return (
          <div key={chartKey} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-xl font-semibold text-gray-800">{getChartTitle(chartKey)}</h4>
              <div className="text-sm text-gray-500">
                {chartData.data.length} items
              </div>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart 
                data={chartData.data}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="label" 
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={{ stroke: '#d1d5db' }}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={{ stroke: '#d1d5db' }}
                />
                <Tooltip 
                  formatter={(value, name) => [value, name]}
                  labelStyle={{ color: '#374151', fontWeight: '500' }}
                  contentStyle={{ 
                    backgroundColor: '#f9fafb', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar 
                  dataKey="value" 
                  fill={colors[0]}
                  radius={[4, 4, 0, 0]}
                  stroke="#fff"
                  strokeWidth={1}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'line':
        return (
          <div key={chartKey} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-xl font-semibold text-gray-800">{getChartTitle(chartKey)}</h4>
              <div className="text-sm text-gray-500">
                Trend Analysis
              </div>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart 
                data={chartData.data}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="label" 
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={{ stroke: '#d1d5db' }}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#d1d5db' }}
                  tickLine={{ stroke: '#d1d5db' }}
                />
                <Tooltip 
                  formatter={(value, name) => [value, name]}
                  labelStyle={{ color: '#374151', fontWeight: '500' }}
                  contentStyle={{ 
                    backgroundColor: '#f9fafb', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke={colors[0]} 
                  strokeWidth={3}
                  dot={{ fill: colors[0], strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: colors[0], strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      default:
        return null;
    }
  };

  const handleDownload = (reportId) => {
    downloadReport(reportId)
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${reportId}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      })
      .catch((error) => {
        toast.error(`Failed to download report: ${error.message}`);
      });
  };

  const handleViewDetails = (report) => {
    setSelectedReport(report);
    setShowDetailsModal(true);
  };

  const getStatusBadge = (status) => {
    const baseClasses = 'badge';
    switch (status) {
      case 'completed':
        return `${baseClasses} badge-success`;
      case 'failed':
        return `${baseClasses} badge-error`;
      case 'generating':
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
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="mt-1 text-sm text-gray-500">
          Generate and download various reports for data analysis and system monitoring.
        </p>
      </div>

      {/* Generate New Report */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Generate New Report</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Report Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="input"
            >
              <optgroup label="Enhanced Reports (Recommended)">
                <option value="executive_summary">📊 Executive Summary Report</option>
                <option value="comprehensive_analysis">📈 Comprehensive Analysis Report</option>
                <option value="cohort_performance">👥 Cohort Performance Report</option>
                <option value="email_effectiveness">📧 Email Effectiveness Report</option>
              </optgroup>
              <optgroup label="Standard Reports">
                <option value="data_analysis">Data Analysis Report</option>
                <option value="cohort_analysis">Cohort Analysis Report</option>
                <option value="email_summary">Email Summary Report</option>
                <option value="bpa_processing">BPA Processing Report</option>
                <option value="file_validation">File Validation Report</option>
              </optgroup>
            </select>
          </div>
          <div>
            <label className="label">Report Name</label>
            <input
              type="text"
              value={`${reportType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Report - ${new Date().toLocaleDateString()}`}
              readOnly
              className="input bg-gray-50"
            />
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={handleGenerateReport}
            disabled={generateMutation.isLoading}
            className="btn btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            {generateMutation.isLoading ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Report List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">Generated Reports</h2>
          <span className="text-sm text-gray-500">
            {reports?.length || 0} report{reports?.length !== 1 ? 's' : ''}
          </span>
        </div>

        {reports?.length === 0 ? (
          <div className="text-center py-12">
            <FileBarChart className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No reports</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by generating your first report.</p>
          </div>
        ) : (
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table className="table">
              <thead>
                <tr>
                  <th>Report Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Records</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Array.isArray(reports) && reports.map((report) => (
                  <tr key={report.id}>
                    <td>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{report.name}</p>
                        {report.summary && (
                          <p className="text-xs text-gray-500">{report.summary}</p>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="text-sm text-gray-900">
                        {report.get_report_type_display}
                      </span>
                    </td>
                    <td>
                      <span className={getStatusBadge(report.status)}>
                        {report.status}
                      </span>
                    </td>
                    <td>
                      <span className="text-sm text-gray-900">{report.total_records}</span>
                    </td>
                    <td>
                      <span className="text-sm text-gray-500">
                        {new Date(report.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        {report.status === 'completed' && report.file && (
                          <button
                            onClick={() => handleDownload(report.id)}
                            className="text-primary-600 hover:text-primary-900"
                            title="Download Report"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                        )}
                        {report.status === 'completed' && report.chart_data && Object.keys(report.chart_data).length > 0 && (
                          <button
                            onClick={() => handlePreviewCharts(report)}
                            className="text-blue-600 hover:text-blue-900"
                            title="Preview Charts"
                          >
                            <BarChart3 className="h-4 w-4" />
                          </button>
                        )}
                        {report.status === 'completed' && (
                          <button
                            onClick={() => handleSendEmail(report)}
                            className="text-green-600 hover:text-green-900"
                            title="Send to Boss"
                          >
                            📧
                          </button>
                        )}
                        <button
                          onClick={() => handleViewDetails(report)}
                          className="text-gray-600 hover:text-gray-900"
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteReport(report.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete Report"
                          disabled={deleteMutation.isLoading}
                        >
                          🗑️
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

      {/* Report Types Info */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="text-lg font-medium text-blue-900 mb-4">Report Types</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <h4 className="font-medium mb-2">Data Analysis Report</h4>
            <p>Comprehensive analysis of participant data including email validation, attendance statistics, and data quality metrics.</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">Cohort Analysis Report</h4>
            <p>Detailed breakdown of cohort assignments, participant distribution, and cohort characteristics.</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">Email Summary Report</h4>
            <p>Summary of email campaigns including delivery statistics, success rates, and recipient engagement.</p>
          </div>
          <div>
            <h4 className="font-medium mb-2">BPA Processing Report</h4>
            <p>Business Process Automation results including duplicate resolution and cohort balancing outcomes.</p>
          </div>
        </div>
      </div>

      {/* Report Details Modal */}
      {showDetailsModal && selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                Report Details - {selectedReport.name}
              </h2>
              <button
                onClick={() => setShowDetailsModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Report Information</h3>
                <div className="space-y-2">
                  <p><span className="font-medium">Name:</span> {selectedReport.name}</p>
                  <p><span className="font-medium">Type:</span> {selectedReport.get_report_type_display}</p>
                  <p><span className="font-medium">Status:</span> 
                    <span className={`ml-2 ${getStatusBadge(selectedReport.status)}`}>
                      {selectedReport.status}
                    </span>
                  </p>
                  <p><span className="font-medium">Total Records:</span> {selectedReport.total_records}</p>
                  <p><span className="font-medium">Created:</span> {new Date(selectedReport.created_at).toLocaleString()}</p>
                  {selectedReport.completed_at && (
                    <p><span className="font-medium">Completed:</span> {new Date(selectedReport.completed_at).toLocaleString()}</p>
                  )}
                  {selectedReport.created_by && (
                    <p><span className="font-medium">Created By:</span> {selectedReport.created_by_username || 'Unknown'}</p>
                  )}
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Summary</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  {selectedReport.summary ? (
                    <p className="text-sm text-gray-700">{selectedReport.summary}</p>
                  ) : (
                    <p className="text-sm text-gray-500 italic">No summary available</p>
                  )}
                </div>
                
                {selectedReport.error_message && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-red-700 mb-2">Error Message</h4>
                    <div className="bg-red-50 p-3 rounded-lg">
                      <p className="text-sm text-red-700">{selectedReport.error_message}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {selectedReport.parameters && Object.keys(selectedReport.parameters).length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Parameters</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                    {JSON.stringify(selectedReport.parameters, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {selectedReport.file && selectedReport.status === 'completed' && (
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => handleDownload(selectedReport.id)}
                  className="btn btn-primary"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Report
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Send Email Modal */}
      {showEmailModal && selectedReport && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-2/3 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Send Report to Boss</h3>
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="label">Report</label>
                  <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                    {selectedReport.name} - {selectedReport.get_report_type_display}
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Boss Name *</label>
                    <input
                      type="text"
                      value={bossName}
                      onChange={(e) => setBossName(e.target.value)}
                      className="input"
                      placeholder="Mr. Scott, Andy, etc."
                    />
                  </div>
                  <div>
                    <label className="label">Boss Email Address *</label>
                    <input
                      type="email"
                      value={bossEmail}
                      onChange={(e) => setBossEmail(e.target.value)}
                      className="input"
                      placeholder="boss@company.com"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Your Gmail Address *</label>
                    <input
                      type="email"
                      value={senderEmail}
                      onChange={(e) => setSenderEmail(e.target.value)}
                      className="input"
                      placeholder="your.email@gmail.com"
                    />
                  </div>
                  <div>
                    <label className="label">Gmail App Password *</label>
                    <input
                      type="password"
                      value={senderPassword}
                      onChange={(e) => setSenderPassword(e.target.value)}
                      className="input"
                      placeholder="16-character app password"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="label">Custom Message (Optional)</label>
                  <textarea
                    value={customMessage}
                    onChange={(e) => setCustomMessage(e.target.value)}
                    className="input"
                    rows={3}
                    placeholder="Add a personal message to accompany the report..."
                  />
                </div>
                
                {/* Chart Selection for Email */}
                {selectedReport && selectedReport.chart_data && Object.keys(selectedReport.chart_data).length > 0 && (
                  <div>
                    <label className="label">Include Charts in Email</label>
                    <p className="text-sm text-gray-600 mb-3">
                      Select which charts to include as images in the email:
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {Object.keys(selectedReport.chart_data).map((chartKey) => {
                        const chartData = selectedReport.chart_data[chartKey];
                        const chartTitle = chartKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        return (
                          <label key={chartKey} className="flex items-center space-x-2 p-2 border rounded hover:bg-gray-50 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={emailSelectedCharts.includes(chartKey)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setEmailSelectedCharts(prev => [...prev, chartKey]);
                                } else {
                                  setEmailSelectedCharts(prev => prev.filter(key => key !== chartKey));
                                }
                              }}
                              className="rounded"
                            />
                            <span className="text-sm font-medium">{chartTitle}</span>
                            <span className="text-xs text-gray-500">({chartData.type})</span>
                          </label>
                        );
                      })}
                    </div>
                    {emailSelectedCharts.length === 0 && (
                      <p className="text-sm text-amber-600 mt-2">
                        ⚠️ No charts selected. The email will only include the text report.
                      </p>
                    )}
                  </div>
                )}
                
                <div className="bg-blue-50 p-3 rounded border border-blue-200">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> Use your Gmail address and App Password (not your regular password). 
                    Make sure 2FA is enabled and you've generated an App Password in your Google Account settings.
                  </p>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendEmailSubmit}
                  disabled={sendEmailMutation.isLoading}
                  className="btn btn-primary"
                >
                  {sendEmailMutation.isLoading ? 'Sending...' : 'Send Report'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart Preview Modal */}
      {showChartModal && selectedReport && selectedReport.chart_data && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-4/5 lg:w-3/4 xl:w-2/3 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Chart Preview - {selectedReport.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {selectedReport.summary} • {selectedReport.records_analyzed} records analyzed
                  </p>
                </div>
                <button
                  onClick={() => setShowChartModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              {/* Chart Selection */}
              <div className="mb-6">
                <h4 className="text-md font-medium text-gray-700 mb-3">Select Charts to Display:</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {Object.keys(selectedReport.chart_data).map((chartKey) => (
                    <label key={chartKey} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedCharts.includes(chartKey)}
                        onChange={() => handleChartToggle(chartKey)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700 capitalize">
                        {chartKey.replace('_', ' ')}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Charts Display */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {selectedCharts.map((chartKey) => {
                  const chartData = selectedReport.chart_data[chartKey];
                  return renderChart(chartKey, chartData);
                })}
              </div>
              
              {selectedCharts.length === 0 && (
                <div className="text-center py-8">
                  <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No charts selected</h3>
                  <p className="mt-1 text-sm text-gray-500">Select charts above to preview them.</p>
                </div>
              )}
              
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowChartModal(false)}
                  className="btn btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
