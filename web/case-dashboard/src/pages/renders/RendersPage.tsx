import React, { useState } from 'react';
import { RenderProgressMonitor } from '../../../../shared/components/render/RenderProgressMonitor';

export const RendersPage: React.FC = () => {
  const [renderJobs, setRenderJobs] = useState([
    {
      id: 'render-001',
      caseId: 'case-001',
      profile: 'neutral' as const,
      status: 'rendering' as const,
      progress: 65,
      startTime: new Date('2024-01-20T10:00:00'),
      framesRendered: 130,
      totalFrames: 200,
      renderTime: 1800,
      queuePosition: undefined,
      error: undefined,
      resultPath: undefined,
      checksum: undefined,
    },
    {
      id: 'render-002',
      caseId: 'case-002',
      profile: 'cinematic' as const,
      status: 'completed' as const,
      progress: 100,
      startTime: new Date('2024-01-19T14:30:00'),
      framesRendered: 300,
      totalFrames: 300,
      renderTime: 3600,
      queuePosition: undefined,
      error: undefined,
      resultPath: '/renders/render-002.mp4',
      checksum: 'a1b2c3d4e5f6...',
    },
    {
      id: 'render-003',
      caseId: 'case-003',
      profile: 'neutral' as const,
      status: 'queued' as const,
      progress: 0,
      startTime: new Date('2024-01-20T15:00:00'),
      framesRendered: 0,
      totalFrames: 150,
      renderTime: 0,
      queuePosition: 2,
      error: undefined,
      resultPath: undefined,
      checksum: undefined,
    },
  ]);

  const handleCancelJob = (jobId: string) => {
    setRenderJobs(prev => prev.map(job => 
      job.id === jobId 
        ? { ...job, status: 'cancelled' as const, queuePosition: undefined }
        : job
    ));
  };

  const handleRetryJob = (jobId: string) => {
    setRenderJobs(prev => prev.map(job => 
      job.id === jobId 
        ? { ...job, status: 'queued' as const, progress: 0, error: undefined, queuePosition: 1 }
        : job
    ));
  };

  const handleDownloadResult = (jobId: string) => {
    const job = renderJobs.find(j => j.id === jobId);
    if (job?.resultPath) {
      // In a real app, this would trigger a download
      console.log(`Downloading result for job ${jobId}: ${job.resultPath}`);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Render Progress Monitor</h1>
        <p className="text-gray-600">Monitor and manage video rendering jobs</p>
      </div>
      
      <RenderProgressMonitor
        renderJobs={renderJobs}
        onCancelJob={handleCancelJob}
        onRetryJob={handleRetryJob}
        onDownloadResult={handleDownloadResult}
      />
    </div>
  );
};
