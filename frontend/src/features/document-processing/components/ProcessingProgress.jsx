import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, AlertCircle, Loader } from 'lucide-react';

const ProcessingProgress = ({ job }) => {
  const [elapsedTime, setElapsedTime] = useState(0);

  // Debug logging
  console.log('ProcessingProgress received job:', job);

  useEffect(() => {
    let interval;
    
    if (job?.status === 'processing') {
      // Use job.started_at if available, otherwise use current time
      const startTime = job.started_at ? new Date(job.started_at) : new Date();
      
      const updateElapsedTime = () => {
        const now = new Date();
        const elapsed = Math.floor((now - startTime) / 1000);
        setElapsedTime(elapsed);
      };
      
      // Update immediately
      updateElapsedTime();
      
      // Then update every second
      interval = setInterval(updateElapsedTime, 1000);
    } else {
      setElapsedTime(0);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [job?.status, job?.started_at]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'processing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'Not started';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end - start) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Processing Status</h3>
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getStatusColor(job.status)}`}>
          {getStatusIcon(job.status)}
          <span className="text-sm font-medium capitalize">
            {job.status === 'processing' ? `Processing (${elapsedTime}s)` : job.status}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      {job.status === 'processing' && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Processing document with {job.chunking_methods?.length || 0} method{(job.chunking_methods?.length || 0) > 1 ? 's' : ''}...</span>
            <span>{Math.min(95, Math.max(10, (elapsedTime * 2) + 10))}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-1000 ease-out relative"
              style={{ 
                width: `${Math.min(95, Math.max(10, (elapsedTime * 2) + 10))}%`
              }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
            </div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Started {elapsedTime}s ago</span>
            <span>Estimated completion: {Math.max(0, 30 - elapsedTime)}s</span>
          </div>
        </div>
      )}

      {/* Job Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Document</label>
          <p className="text-sm text-gray-900">{job.document?.name}</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Duration</label>
          <p className="text-sm text-gray-900">
            {formatDuration(job.started_at, job.completed_at)}
          </p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Started</label>
          <p className="text-sm text-gray-900">
            {job.started_at ? new Date(job.started_at).toLocaleString() : 'Not started'}
          </p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Completed</label>
          <p className="text-sm text-gray-900">
            {job.completed_at ? new Date(job.completed_at).toLocaleString() : 'In progress'}
          </p>
        </div>
      </div>

      {/* Selected Methods */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Chunking Methods</label>
        <div className="flex flex-wrap gap-2">
          {job.chunking_methods?.map((method) => (
            <span
              key={method.id}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              {method.name}
            </span>
          ))}
        </div>
      </div>

      {/* Error Message */}
      {job.status === 'failed' && job.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Processing Failed</h3>
              <p className="text-sm text-red-700 mt-1">{job.error_message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results Summary */}
      {job.status === 'completed' && job.chunking_results && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Processing Completed</h3>
              <p className="text-sm text-green-700 mt-1">
                Successfully processed with {job.chunking_results.length} chunking method{job.chunking_results.length > 1 ? 's' : ''}.
                Total chunks generated: {job.chunking_results.reduce((sum, result) => sum + result.total_chunks, 0)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessingProgress;
