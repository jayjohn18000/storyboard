import React, { useState, useEffect, useCallback } from 'react';
import {
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  CpuChipIcon,
  ServerIcon,
  FilmIcon
} from '@heroicons/react/24/outline';
import { useGetQueueStatsQuery } from '../../../store/api/rendersApi';

interface RenderJob {
  id: string;
  caseId: string;
  profile: 'neutral' | 'cinematic';
  status: 'queued' | 'rendering' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  startTime: Date;
  estimatedCompletion?: Date;
  framesRendered: number;
  totalFrames: number;
  renderTime: number;
  queuePosition?: number;
  error?: string;
  resultPath?: string;
  checksum?: string;
}

interface RenderProgressMonitorProps {
  renderJobs: RenderJob[];
  onCancelJob: (jobId: string) => void;
  onRetryJob: (jobId: string) => void;
  onDownloadResult: (jobId: string) => void;
  refreshInterval?: number;
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage: number;
  diskUsage: number;
  activeWorkers: number;
  queueLength: number;
}

export const RenderProgressMonitor: React.FC<RenderProgressMonitorProps> = ({
  renderJobs,
  onCancelJob,
  onRetryJob,
  onDownloadResult,
  refreshInterval = 5000
}) => {
  const [selectedJob, setSelectedJob] = useState<RenderJob | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Get queue stats from API
  const { data: queueStats, isLoading: statsLoading } = useGetQueueStatsQuery();
  
  // Calculate system metrics from queue stats and render jobs
  const systemMetrics: SystemMetrics = {
    cpuUsage: 45.2, // Mock - would come from system metrics API
    memoryUsage: 67.8, // Mock - would come from system metrics API
    gpuUsage: 23.1, // Mock - would come from system metrics API
    diskUsage: 34.5, // Mock - would come from system metrics API
    activeWorkers: queueStats?.processing || 0,
    queueLength: queueStats?.queued || 0
  };

  const getStatusColor = (status: RenderJob['status']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'rendering': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'cancelled': return 'text-gray-600 bg-gray-100';
      case 'queued': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: RenderJob['status']) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon className="w-4 h-4" />;
      case 'rendering': return <ArrowPathIcon className="w-4 h-4 animate-spin" />;
      case 'failed': return <ExclamationTriangleIcon className="w-4 h-4" />;
      case 'cancelled': return <PauseIcon className="w-4 h-4" />;
      case 'queued': return <ClockIcon className="w-4 h-4" />;
      default: return <ClockIcon className="w-4 h-4" />;
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getEstimatedTimeRemaining = (job: RenderJob) => {
    if (job.status !== 'rendering' || job.totalFrames === 0) return null;
    
    const framesPerSecond = job.framesRendered / (job.renderTime || 1);
    const remainingFrames = job.totalFrames - job.framesRendered;
    const estimatedSeconds = remainingFrames / framesPerSecond;
    
    return formatDuration(estimatedSeconds);
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <FilmIcon className="w-8 h-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-800">Render Progress Monitor</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsRefreshing(!isRefreshing)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              isRefreshing 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <ArrowPathIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">CPU Usage</p>
              <p className="text-2xl font-bold text-gray-800">{systemMetrics.cpuUsage.toFixed(1)}%</p>
            </div>
            <CpuChipIcon className="w-8 h-8 text-blue-500" />
          </div>
          <div className="mt-2 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${systemMetrics.cpuUsage}%` }}
            />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Memory Usage</p>
              <p className="text-2xl font-bold text-gray-800">{systemMetrics.memoryUsage.toFixed(1)}%</p>
            </div>
            <ServerIcon className="w-8 h-8 text-green-500" />
          </div>
          <div className="mt-2 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${systemMetrics.memoryUsage}%` }}
            />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">GPU Usage</p>
              <p className="text-2xl font-bold text-gray-800">{systemMetrics.gpuUsage.toFixed(1)}%</p>
            </div>
            <CpuChipIcon className="w-8 h-8 text-purple-500" />
          </div>
          <div className="mt-2 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-purple-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${systemMetrics.gpuUsage}%` }}
            />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Workers</p>
              <p className="text-2xl font-bold text-gray-800">{systemMetrics.activeWorkers}</p>
            </div>
            <ServerIcon className="w-8 h-8 text-orange-500" />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Queue: {systemMetrics.queueLength} jobs
          </p>
        </div>
      </div>

      {/* Render Jobs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-800">Render Jobs</h2>
        </div>
        
        <div className="divide-y">
          {renderJobs.map((job) => (
            <div 
              key={job.id} 
              className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                selectedJob?.id === job.id ? 'bg-blue-50' : ''
              }`}
              onClick={() => setSelectedJob(job)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
                    {getStatusIcon(job.status)}
                    <span>{job.status.toUpperCase()}</span>
                  </div>
                  
                  <div>
                    <p className="font-medium text-gray-800">Job {job.id}</p>
                    <p className="text-sm text-gray-600">
                      Case: {job.caseId} • Profile: {job.profile}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  {/* Progress */}
                  {job.status === 'rendering' && (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">
                        {job.framesRendered}/{job.totalFrames} frames
                      </span>
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{job.progress.toFixed(1)}%</span>
                    </div>
                  )}
                  
                  {/* Queue Position */}
                  {job.status === 'queued' && job.queuePosition && (
                    <span className="text-sm text-gray-600">
                      Position: {job.queuePosition}
                    </span>
                  )}
                  
                  {/* Duration */}
                  <span className="text-sm text-gray-600">
                    {formatDuration(job.renderTime)}
                  </span>
                  
                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    {job.status === 'rendering' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onCancelJob(job.id);
                        }}
                        className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
                      >
                        Cancel
                      </button>
                    )}
                    
                    {job.status === 'failed' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRetryJob(job.id);
                        }}
                        className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                      >
                        Retry
                      </button>
                    )}
                    
                    {job.status === 'completed' && job.resultPath && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDownloadResult(job.id);
                        }}
                        className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600"
                      >
                        Download
                      </button>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Error Message */}
              {job.status === 'failed' && job.error && (
                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  Error: {job.error}
                </div>
              )}
              
              {/* Estimated Time */}
              {job.status === 'rendering' && (
                <div className="mt-2 text-sm text-gray-600">
                  Estimated time remaining: {getEstimatedTimeRemaining(job) || 'Calculating...'}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">Job Details</h3>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="Close job details"
              >
                <ExclamationTriangleIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Job ID</label>
                <p className="text-gray-800">{selectedJob.id}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-600">Case ID</label>
                <p className="text-gray-800">{selectedJob.caseId}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-600">Render Profile</label>
                <p className="text-gray-800">{selectedJob.profile}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-600">Status</label>
                <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedJob.status)}`}>
                  {getStatusIcon(selectedJob.status)}
                  <span>{selectedJob.status.toUpperCase()}</span>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-600">Progress</label>
                <p className="text-gray-800">{selectedJob.framesRendered}/{selectedJob.totalFrames} frames ({selectedJob.progress.toFixed(1)}%)</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-600">Render Time</label>
                <p className="text-gray-800">{formatDuration(selectedJob.renderTime)}</p>
              </div>
              
              {selectedJob.checksum && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Checksum</label>
                  <p className="text-gray-800 font-mono text-sm">{selectedJob.checksum}</p>
                </div>
              )}
              
              {selectedJob.error && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Error</label>
                  <p className="text-red-700 bg-red-50 p-2 rounded">{selectedJob.error}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RenderProgressMonitor;
