import React from 'react';
import { useQuery } from 'react-query';
import { 
  Upload, 
  FileText, 
  Users, 
  Mail, 
  BarChart3, 
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';
import { api } from '../services/api';

const Dashboard = () => {
  const { data: stats, isLoading } = useQuery('dashboard-stats', api.getDashboardStats, {
    initialData: {
      total_files: 0,
      total_participants: 0,
      total_cohorts: 0,
      emails_sent: 0,
      recent_files: [],
    },
  });

  const quickActions = [
    {
      title: 'Upload Files',
      description: 'Upload Excel files for processing',
      icon: Upload,
      href: '/upload',
      color: 'bg-blue-500',
    },
    {
      title: 'Analyze Data',
      description: 'Run data analysis on uploaded files',
      icon: BarChart3,
      href: '/analysis',
      color: 'bg-green-500',
    },
    {
      title: 'Manage Cohorts',
      description: 'Create and manage participant cohorts',
      icon: Users,
      href: '/cohorts',
      color: 'bg-purple-500',
    },
    {
      title: 'Send Emails',
      description: 'Send emails to cohort participants',
      icon: Mail,
      href: '/email',
      color: 'bg-orange-500',
    },
  ];

  const StatCard = ({ title, value, icon: Icon, color, change }) => (
    <div className="card">
      <div className="flex items-center">
        <div className={`p-3 rounded-md ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '+' : ''}{change}% from last month
            </p>
          )}
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
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome to the Data Automation System. Manage your Excel files, participants, and cohorts.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Files"
          value={stats?.total_files || 0}
          icon={FileText}
          color="bg-blue-500"
          change={12}
        />
        <StatCard
          title="Participants"
          value={stats?.total_participants || 0}
          icon={Users}
          color="bg-green-500"
          change={8}
        />
        <StatCard
          title="Cohorts"
          value={stats?.total_cohorts || 0}
          icon={BarChart3}
          color="bg-purple-500"
          change={-2}
        />
        <StatCard
          title="Emails Sent"
          value={stats?.emails_sent || 0}
          icon={Mail}
          color="bg-orange-500"
          change={15}
        />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <a
                key={action.title}
                href={action.href}
                className="card hover:shadow-lg transition-shadow duration-200 cursor-pointer"
              >
                <div className="flex items-center">
                  <div className={`p-3 rounded-md ${action.color}`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-sm font-medium text-gray-900">{action.title}</h3>
                    <p className="text-sm text-gray-500">{action.description}</p>
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Files</h3>
          <div className="space-y-3">
            {Array.isArray(stats?.recent_files) && stats.recent_files.map((file) => (
              <div key={file.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {file.participant_count} participants • {file.status}
                    </p>
                  </div>
                </div>
                <div className="flex items-center">
                  {file.status === 'processed' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : file.status === 'error' ? (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  ) : (
                    <Clock className="h-5 w-5 text-yellow-500" />
                  )}
                </div>
              </div>
            )) || (
              <p className="text-sm text-gray-500">No recent files</p>
            )}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Status</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <span className="badge badge-success">Online</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Email Service</span>
              <span className="badge badge-success">Online</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">File Processing</span>
              <span className="badge badge-success">Online</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">BPA Engine</span>
              <span className="badge badge-success">Online</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
