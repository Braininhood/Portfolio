import React from 'react';
import { useQuery } from 'react-query';
import { AlertCircle } from 'lucide-react';
import { runBPADemo } from '../services/api';

const BPADemo = () => {
  const { data: demoResults, isLoading, error } = useQuery('bpa-demo', runBPADemo);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500" />
          <p className="mt-2 text-sm text-red-600">Failed to load BPA demo</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">BPA Logic Demonstration</h1>
        <p className="mt-1 text-sm text-gray-500">
          See how Business Process Automation handles duplicate registrations and cohort balancing.
        </p>
      </div>

      {/* Business Rule */}
      <div className="card bg-blue-50 border-blue-200">
        <h2 className="text-lg font-medium text-blue-900 mb-2">Business Rule</h2>
        <p className="text-blue-800">
          If a student registers for two cohorts of the same course, they will be added ONLY to whichever cohort currently has the least students enrolled.
        </p>
      </div>

      {/* Demo Results */}
      {demoResults && (
        <div className="space-y-6">
          {/* Original Data */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Original Cohorts</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-700 mb-2">Cohort 1</h3>
                <div className="flex flex-wrap gap-2">
                  {Array.isArray(demoResults.original_cohort1) && demoResults.original_cohort1.map((student, index) => (
                    <span key={index} className="badge badge-info">{student}</span>
                  ))}
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Size: {demoResults.original_cohort1?.length} students
                </p>
              </div>
              <div>
                <h3 className="font-medium text-gray-700 mb-2">Cohort 2</h3>
                <div className="flex flex-wrap gap-2">
                  {Array.isArray(demoResults.original_cohort2) && demoResults.original_cohort2.map((student, index) => (
                    <span key={index} className="badge badge-info">{student}</span>
                  ))}
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Size: {demoResults.original_cohort2?.length} students
                </p>
              </div>
            </div>
          </div>

          {/* Processed Data */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">After BPA Processing</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-700 mb-2">Processed Cohort 1</h3>
                <div className="flex flex-wrap gap-2">
                  {Array.isArray(demoResults.processed_cohort1) && demoResults.processed_cohort1.map((student, index) => (
                    <span key={index} className="badge badge-success">{student}</span>
                  ))}
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Size: {demoResults.processed_cohort1?.length} students
                </p>
              </div>
              <div>
                <h3 className="font-medium text-gray-700 mb-2">Processed Cohort 2</h3>
                <div className="flex flex-wrap gap-2">
                  {Array.isArray(demoResults.processed_cohort2) && demoResults.processed_cohort2.map((student, index) => (
                    <span key={index} className="badge badge-success">{student}</span>
                  ))}
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Size: {demoResults.processed_cohort2?.length} students
                </p>
              </div>
            </div>
          </div>

          {/* Processing Summary */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Processing Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {demoResults.duplicates_found}
                </div>
                <div className="text-sm text-gray-500">Duplicates Found</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {demoResults.duplicates_resolved}
                </div>
                <div className="text-sm text-gray-500">Duplicates Resolved</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {Math.abs((demoResults.processed_cohort1?.length || 0) - (demoResults.processed_cohort2?.length || 0))}
                </div>
                <div className="text-sm text-gray-500">Size Difference</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {demoResults.balancing_achieved ? 'Yes' : 'No'}
                </div>
                <div className="text-sm text-gray-500">Balancing Achieved</div>
              </div>
            </div>
          </div>

          {/* Duplicate Analysis */}
          <div className="card">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Duplicate Analysis</h2>
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-700 mb-2">Duplicates Identified</h3>
                <p className="text-sm text-gray-600">
                  Students who were registered in both cohorts: {demoResults.duplicates_found}
                </p>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="font-medium text-green-700 mb-2">Resolution Applied</h3>
                <p className="text-sm text-green-600">
                  All duplicates were reassigned to the smaller cohort to achieve better balance.
                </p>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-700 mb-2">Final Balance</h3>
                <p className="text-sm text-blue-600">
                  Cohort 1: {demoResults.processed_cohort1?.length} students | 
                  Cohort 2: {demoResults.processed_cohort2?.length} students | 
                  Difference: {Math.abs((demoResults.processed_cohort1?.length || 0) - (demoResults.processed_cohort2?.length || 0))}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* BPA Benefits */}
      <div className="card bg-green-50 border-green-200">
        <h2 className="text-lg font-medium text-green-900 mb-4">BPA Benefits</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-green-800">
          <div>
            <h3 className="font-medium mb-2">Automated Decision Making</h3>
            <ul className="space-y-1">
              <li>• Eliminates manual duplicate resolution</li>
              <li>• Applies consistent business rules</li>
              <li>• Reduces human error</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium mb-2">Cohort Optimization</h3>
            <ul className="space-y-1">
              <li>• Balances cohort sizes automatically</li>
              <li>• Ensures fair distribution</li>
              <li>• Maintains audit trail</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BPADemo;
