import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-toastify';
import { Users, Mail, FileText, Eye, Send, X } from 'lucide-react';
import { getCohorts, createCohorts, getFiles, getCohortParticipants, getEmailTemplates, sendEmails, generateEmailTemplates, getEmailConfig } from '../services/api';

const CohortManagement = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [selectedCohort, setSelectedCohort] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailTemplate, setEmailTemplate] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [selectedRecipients, setSelectedRecipients] = useState([]);
  const [senderEmail, setSenderEmail] = useState('');
  const [senderPassword, setSenderPassword] = useState('');
  const [delayBetweenEmails, setDelayBetweenEmails] = useState(1);
  const [newlyCreatedCohorts, setNewlyCreatedCohorts] = useState([]);
  const [showNewCohortsOnly, setShowNewCohortsOnly] = useState(false);
  const [emailResults, setEmailResults] = useState(null);
  const queryClient = useQueryClient();

  const { data: cohorts, isLoading: cohortsLoading } = useQuery('cohorts', getCohorts, {
    initialData: [],
  });
  const { data: files, isLoading: filesLoading } = useQuery('files', getFiles, {
    initialData: [],
  });
  const { data: emailTemplates, isLoading: templatesLoading, error: templatesError } = useQuery('emailTemplates', getEmailTemplates, {
    initialData: [],
    select: (data) => {
      // Handle different API response formats
      if (Array.isArray(data)) {
        return data;
      }
      if (data && data.results && Array.isArray(data.results)) {
        return data.results;
      }
      return [];
    },
  });
  const { data: cohortParticipants, isLoading: participantsLoading } = useQuery(
    ['cohortParticipants', selectedCohort?.id],
    () => getCohortParticipants(selectedCohort.id),
    {
      enabled: !!selectedCohort,
      initialData: [],
    }
  );
  
  const { data: emailConfig } = useQuery('emailConfig', getEmailConfig, {
    enabled: showEmailModal,
    initialData: null,
  });

  const createCohortsMutation = useMutation(createCohorts, {
    onSuccess: (data) => {
      queryClient.invalidateQueries('cohorts');
      queryClient.invalidateQueries('dashboard-stats');
      setNewlyCreatedCohorts(data.cohort_details || []);
      setShowNewCohortsOnly(true);
      toast.success(`Created ${data.cohorts_created} cohorts successfully!`);
      setSelectedFiles([]);
    },
    onError: (error) => {
      toast.error(`Failed to create cohorts: ${error.response?.data?.error || error.message}`);
    },
  });

  const sendEmailsMutation = useMutation(sendEmails, {
    onSuccess: (data) => {
      setEmailResults(data);
      toast.success(`Emails sent successfully! Sent: ${data.sent_count}, Failed: ${data.failed_count}, Skipped Invalid: ${data.skipped_invalid || 0}`);
    },
    onError: (error) => {
      toast.error(`Failed to send emails: ${error.response?.data?.error || error.message}`);
    },
  });

  const generateTemplatesMutation = useMutation(generateEmailTemplates, {
    onSuccess: (data) => {
      queryClient.invalidateQueries('emailTemplates');
      toast.success(`Generated ${data.templates_created} email templates successfully!`);
    },
    onError: (error) => {
      toast.error(`Failed to generate templates: ${error.response?.data?.error || error.message}`);
    },
  });

  const handleFileToggle = (fileId) => {
    setSelectedFiles(prev => 
      prev.includes(fileId) 
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  };

  const handleCreateCohorts = () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select at least one file to create cohorts from');
      return;
    }
    createCohortsMutation.mutate(selectedFiles);
  };

  const handleViewDetails = (cohort) => {
    setSelectedCohort(cohort);
    setShowDetailsModal(true);
  };

  const handleSendEmails = (cohort) => {
    setSelectedCohort(cohort);
    setShowEmailModal(true);
    setEmailResults(null);
    // Pre-select all participants with valid emails
    if (cohortParticipants) {
      setSelectedRecipients(cohortParticipants.filter(p => p.email_valid).map(p => p.id));
    }
    // Ensure templates are loaded
    queryClient.invalidateQueries('emailTemplates');
    // Auto-fill sender email if available
    if (emailConfig?.sender_email) {
      setSenderEmail(emailConfig.sender_email);
    }
  };

  const handleRecipientToggle = (participantId) => {
    setSelectedRecipients(prev => 
      prev.includes(participantId)
        ? prev.filter(id => id !== participantId)
        : [...prev, participantId]
    );
  };

  const handleTemplateSelect = (template) => {
    setEmailSubject(template.subject);
    setEmailTemplate(template.body);
  };

  const handleSendEmailsSubmit = () => {
    if (!emailSubject || !emailTemplate || selectedRecipients.length === 0) {
      toast.error('Please fill in all required fields and select recipients');
      return;
    }
    if (!senderEmail || !senderPassword) {
      toast.error('Please provide sender email and password');
      return;
    }

    // For now, we'll use the first email template ID
    // In a real implementation, you'd create a new template or use an existing one
    const templateId = emailTemplates?.[0]?.id || 1;
    
    sendEmailsMutation.mutate({
      template_id: templateId,
      cohort_id: selectedCohort.id,
      sender_email: senderEmail,
      sender_password: senderPassword,
      custom_subject: emailSubject,
      custom_body: emailTemplate,
      recipient_ids: selectedRecipients,
      delay_between_emails: delayBetweenEmails
    });
  };

  const CohortCard = ({ cohort }) => (
    <div className="card hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Users className="h-8 w-8 text-primary-600 mr-3" />
          <div>
            <h3 className="text-lg font-medium text-gray-900">{cohort.name}</h3>
            <p className="text-sm text-gray-500">{cohort.get_cohort_type_display}</p>
          </div>
        </div>
        <span className="badge badge-info">{cohort.participant_count} participants</span>
      </div>
      
      <p className="text-sm text-gray-600 mb-4">{cohort.description}</p>
      
      <div className="flex space-x-2">
        <button 
          onClick={() => handleViewDetails(cohort)}
          className="btn btn-secondary text-sm"
        >
          <Eye className="h-4 w-4 mr-1" />
          View Details
        </button>
        <button 
          onClick={() => handleSendEmails(cohort)}
          className="btn btn-primary text-sm"
        >
          <Mail className="h-4 w-4 mr-1" />
          Send Emails
        </button>
      </div>
    </div>
  );

  if (cohortsLoading || filesLoading) {
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
        <h1 className="text-2xl font-bold text-gray-900">Cohort Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Create and manage participant cohorts based on their characteristics and needs.
        </p>
      </div>

      {/* Create Cohorts Section */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Create New Cohorts</h2>
        <p className="text-sm text-gray-600 mb-4">
          Select processed files to automatically create cohorts based on participant data.
        </p>
        
        <div className="space-y-3 mb-4">
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
            </label>
          ))}
        </div>

        {files?.filter(file => file.status === 'processed').length === 0 && (
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">No processed files available for cohort creation</p>
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            onClick={() => generateTemplatesMutation.mutate([])}
            disabled={generateTemplatesMutation.isLoading}
            className="btn btn-secondary"
          >
            <Mail className="h-4 w-4 mr-2" />
            {generateTemplatesMutation.isLoading ? 'Generating...' : 'Generate Email Templates'}
          </button>
          <button
            onClick={handleCreateCohorts}
            disabled={selectedFiles.length === 0 || createCohortsMutation.isLoading}
            className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createCohortsMutation.isLoading ? 'Creating Cohorts...' : 'Create Cohorts'}
          </button>
        </div>
      </div>

      {/* Cohorts Display */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">
            {showNewCohortsOnly ? 'Newly Created Cohorts' : 'All Cohorts'}
          </h2>
          <div className="flex items-center space-x-4">
            {newlyCreatedCohorts.length > 0 && (
              <button
                onClick={() => setShowNewCohortsOnly(!showNewCohortsOnly)}
                className={`btn btn-sm ${showNewCohortsOnly ? 'btn-primary' : 'btn-secondary'}`}
              >
                {showNewCohortsOnly ? 'Show All Cohorts' : 'Show New Cohorts Only'}
              </button>
            )}
            <span className="text-sm text-gray-500">
              {(showNewCohortsOnly ? newlyCreatedCohorts : cohorts)?.length || 0} cohort{(showNewCohortsOnly ? newlyCreatedCohorts : cohorts)?.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {(showNewCohortsOnly ? newlyCreatedCohorts : cohorts)?.length === 0 ? (
          <div className="text-center py-12">
            <Users className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {showNewCohortsOnly ? 'No new cohorts created' : 'No cohorts'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {showNewCohortsOnly ? 'Create cohorts to see them here.' : 'Get started by creating cohorts from your data files.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {Array.isArray(showNewCohortsOnly ? newlyCreatedCohorts : cohorts) && (showNewCohortsOnly ? newlyCreatedCohorts : cohorts).map((cohort) => (
              <CohortCard key={cohort.id} cohort={cohort} />
            ))}
          </div>
        )}
      </div>

      {/* Cohort Types Info */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="text-lg font-medium text-blue-900 mb-4">Cohort Types</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <h4 className="font-medium mb-2">Main Cohorts</h4>
            <ul className="space-y-1">
              <li>• Primary Cohort - Attending original dates</li>
              <li>• Alternative Cohort - Need different dates</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Technical Cohorts</h4>
            <ul className="space-y-1">
              <li>• Need Software Setup - Require MS Office 365</li>
              <li>• Software Ready - Already have software</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Support Cohorts</h4>
            <ul className="space-y-1">
              <li>• High Support - Refugees/disabled participants</li>
              <li>• Standard Support - Regular participants</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Communication Cohorts</h4>
            <ul className="space-y-1">
              <li>• Moodle Ready - Valid email addresses</li>
              <li>• Email Correction Needed - Invalid emails</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Cohort Details Modal */}
      {showDetailsModal && selectedCohort && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                {selectedCohort.name} - Details
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
                <h3 className="text-lg font-medium text-gray-900 mb-3">Cohort Information</h3>
                <div className="space-y-2">
                  <p><span className="font-medium">Type:</span> {selectedCohort.get_cohort_type_display}</p>
                  <p><span className="font-medium">Description:</span> {selectedCohort.description}</p>
                  <p><span className="font-medium">Participants:</span> {selectedCohort.participant_count}</p>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Participants</h3>
                {participantsLoading ? (
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                ) : (
                  <div className="max-h-64 overflow-y-auto">
                    {cohortParticipants?.map((participant) => (
                      <div key={participant.id} className="flex items-center justify-between py-2 border-b">
                        <div>
                          <p className="font-medium">{participant.full_name}</p>
                          <p className="text-sm text-gray-500">{participant.email}</p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`badge ${participant.email_valid ? 'badge-success' : 'badge-error'}`}>
                            {participant.email_valid ? 'Valid' : 'Invalid'}
                          </span>
                          {participant.attending && (
                            <span className="badge badge-info">
                              {participant.attending}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Email Sending Modal */}
      {showEmailModal && selectedCohort && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            {templatesLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                <span className="ml-3 text-gray-600">Loading email templates...</span>
              </div>
            ) : Array.isArray(emailTemplates) ? (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold text-gray-900">
                    Send Emails to {selectedCohort.name}
                  </h2>
                  <button
                    onClick={() => setShowEmailModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-6 w-6" />
                  </button>
                </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Email Template Editor */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Email Template</h3>
                
                {/* Template Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Template
                  </label>
                  {templatesError ? (
                    <div className="text-red-600 text-sm mb-2">
                      Error loading templates: {templatesError.message}
                    </div>
                  ) : null}
                  <select
                    onChange={(e) => {
                      const template = emailTemplates?.find(t => t.id === parseInt(e.target.value));
                      if (template) handleTemplateSelect(template);
                    }}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    disabled={templatesLoading}
                  >
                    <option value="">
                      {templatesLoading ? 'Loading templates...' : 'Choose a template...'}
                    </option>
                    {Array.isArray(emailTemplates) && emailTemplates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Subject */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject
                  </label>
                  <input
                    type="text"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="Email subject..."
                  />
                </div>

                {/* Email Body */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Body
                  </label>
                  <textarea
                    value={emailTemplate}
                    onChange={(e) => setEmailTemplate(e.target.value)}
                    rows={12}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="Email body... Use {name}, {email}, {software_status} for placeholders"
                  />
                </div>

                {/* Sender Credentials */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sender Email
                    </label>
                    <input
                      type="email"
                      value={senderEmail}
                      onChange={(e) => setSenderEmail(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="your-email@gmail.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      App Password
                    </label>
                    <input
                      type="password"
                      value={senderPassword}
                      onChange={(e) => setSenderPassword(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="Gmail app password"
                    />
                  </div>
                </div>

                {/* Timing Controls */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Delay Between Emails (seconds)
                  </label>
                  <select
                    value={delayBetweenEmails}
                    onChange={(e) => setDelayBetweenEmails(parseInt(e.target.value))}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value={0}>No delay (fastest)</option>
                    <option value={1}>1 second (recommended)</option>
                    <option value={2}>2 seconds</option>
                    <option value={5}>5 seconds (safer)</option>
                    <option value={10}>10 seconds (very safe)</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Higher delays reduce spam risk but take longer to send
                  </p>
                </div>
              </div>

              {/* Recipients Selection */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">
                  Select Recipients ({selectedRecipients.length} selected)
                </h3>
                
                <div className="mb-4">
                  <button
                    onClick={() => {
                      const validParticipants = cohortParticipants?.filter(p => p.email_valid).map(p => p.id) || [];
                      setSelectedRecipients(validParticipants);
                    }}
                    className="btn btn-secondary text-sm mr-2"
                  >
                    Select All Valid
                  </button>
                  <button
                    onClick={() => setSelectedRecipients([])}
                    className="btn btn-secondary text-sm"
                  >
                    Clear All
                  </button>
                </div>

                <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md">
                  {cohortParticipants?.map((participant) => (
                    <label key={participant.id} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedRecipients.includes(participant.id)}
                        onChange={() => handleRecipientToggle(participant.id)}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <div className="ml-3 flex-1">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{participant.full_name}</p>
                            <p className="text-xs text-gray-500">{participant.email}</p>
                          </div>
                          <span className={`badge ${participant.email_valid ? 'badge-success' : 'badge-error'}`}>
                            {participant.email_valid ? 'Valid' : 'Invalid'}
                          </span>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
              <button
                onClick={() => setShowEmailModal(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSendEmailsSubmit}
                disabled={sendEmailsMutation.isLoading || selectedRecipients.length === 0}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sendEmailsMutation.isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Send Emails ({selectedRecipients.length})
                  </>
                )}
              </button>
            </div>

            {/* Email Results */}
            {emailResults && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-lg font-medium text-gray-900 mb-3">Email Sending Results</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{emailResults.sent_count}</div>
                    <div className="text-sm text-gray-600">Sent Successfully</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{emailResults.failed_count}</div>
                    <div className="text-sm text-gray-600">Failed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">{emailResults.skipped_invalid || 0}</div>
                    <div className="text-sm text-gray-600">Skipped (Invalid)</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{emailResults.total_attempted}</div>
                    <div className="text-sm text-gray-600">Total Attempted</div>
                  </div>
                </div>
                
                {emailResults.invalid_emails && emailResults.invalid_emails.length > 0 && (
                  <div className="mt-4">
                    <h5 className="font-medium text-gray-900 mb-2">Invalid Emails Skipped:</h5>
                    <div className="max-h-32 overflow-y-auto">
                      {emailResults.invalid_emails.map((invalid, index) => (
                        <div key={index} className="text-sm text-gray-600 py-1">
                          {invalid.name} ({invalid.email}) - {invalid.reason}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="mt-4 flex justify-between">
                  <button
                    onClick={() => {
                      setShowEmailModal(false);
                      setEmailResults(null);
                      setEmailTemplate('');
                      setEmailSubject('');
                      setSelectedRecipients([]);
                    }}
                    className="btn btn-secondary"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      // TODO: Implement download report functionality
                      toast.info('Download report feature coming soon!');
                    }}
                    className="btn btn-primary"
                  >
                    Download Full Report
                  </button>
                </div>
              </div>
            )}
              </>
            ) : (
              <div className="text-center py-12">
                <div className="text-red-600 mb-4">Error loading email templates</div>
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="btn btn-secondary"
                >
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CohortManagement;
