import React, { useState } from 'react';
import { RenderProgressMonitor } from '../../shared/components/render/RenderProgressMonitor';
import { 
  useGetRendersQuery, 
  useCancelRenderMutation, 
  useRetryRenderMutation,
  useDownloadRenderQuery,
  RenderJob 
} from '../../store/api/rendersApi';

export const RendersPage: React.FC = () => {
  const [selectedCaseId, setSelectedCaseId] = useState<string | undefined>();
  
  // Fetch renders data
  const { data: renderJobs = [], isLoading, error } = useGetRendersQuery({ 
    caseId: selectedCaseId 
  });
  
  // Mutations
  const [cancelRender] = useCancelRenderMutation();
  const [retryRender] = useRetryRenderMutation();

  const handleCancelJob = async (jobId: string) => {
    try {
      await cancelRender(jobId).unwrap();
    } catch (error) {
      console.error('Failed to cancel render:', error);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      await retryRender(jobId).unwrap();
    } catch (error) {
      console.error('Failed to retry render:', error);
    }
  };

  const handleDownloadResult = (jobId: string) => {
    // Trigger download query
    const downloadUrl = `/api/v1/renders/${jobId}/download`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `render_${jobId}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Transform render jobs to match the component interface
  const transformedRenderJobs = renderJobs.map(job => ({
    id: job.id,
    caseId: job.case_id,
    profile: job.profile as 'neutral' | 'cinematic',
    status: (job.status === 'processing' ? 'rendering' : 
             job.status === 'queued' ? 'queued' :
             job.status === 'completed' ? 'completed' :
             job.status === 'failed' ? 'failed' :
             job.status === 'cancelled' ? 'cancelled' : 'queued') as 'queued' | 'rendering' | 'completed' | 'failed' | 'cancelled',
    progress: job.progress_percentage,
    startTime: new Date(job.started_at || job.created_at),
    framesRendered: job.frames_rendered,
    totalFrames: job.total_frames,
    renderTime: job.render_time_seconds,
    queuePosition: job.status === 'queued' ? 1 : undefined,
    error: job.error_message || undefined,
    resultPath: job.output_path || undefined,
    checksum: job.checksum || undefined,
  }));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading renders...</div>
      </div>
    );
  }

  if (error) {
    console.error('Renders API Error:', error);
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">
          Error loading renders: {JSON.stringify(error, null, 2)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Render Progress Monitor</h1>
          <p className="text-gray-600">Monitor and manage video rendering jobs</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={selectedCaseId || ''}
            onChange={(e) => setSelectedCaseId(e.target.value || undefined)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filter renders by case"
          >
            <option value="">All Cases</option>
            {/* TODO: Add case options from cases API */}
          </select>
        </div>
      </div>
      
      <RenderProgressMonitor
        renderJobs={transformedRenderJobs}
        onCancelJob={handleCancelJob}
        onRetryJob={handleRetryJob}
        onDownloadResult={handleDownloadResult}
      />
    </div>
  );
};
