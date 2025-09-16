import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface RenderJob {
  id: string;
  caseId: string;
  storyboardId?: string;
  profile: 'neutral' | 'cinematic';
  status: 'queued' | 'rendering' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  startTime: string;
  estimatedCompletion?: string;
  framesRendered: number;
  totalFrames: number;
  renderTime: number;
  queuePosition?: number;
  error?: string;
  resultPath?: string;
  checksum?: string;
  seed?: number;
}

export interface CreateRenderRequest {
  caseId: string;
  storyboardId?: string;
  profile: 'neutral' | 'cinematic';
  seed?: number;
}

export interface RenderConfig {
  resolution: '720p' | '1080p' | '4k';
  frameRate: 24 | 30 | 60;
  quality: 'draft' | 'standard' | 'high';
  effects: boolean;
  audio: boolean;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const rendersApi = createApi({
  reducerPath: 'rendersApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_BASE_URL}/api/v1/renders`,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('legal-sim-token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Render'],
  endpoints: (builder) => ({
    getRenders: builder.query<RenderJob[], { caseId?: string }>({
      query: ({ caseId }) => (caseId ? `?caseId=${caseId}` : ''),
      providesTags: ['Render'],
      // Mock data for development
      transformResponse: () => [
        {
          id: 'render-001',
          caseId: 'case-001',
          storyboardId: 'sb-001',
          profile: 'neutral',
          status: 'rendering',
          progress: 65,
          startTime: '2024-01-20T10:00:00Z',
          framesRendered: 130,
          totalFrames: 200,
          renderTime: 1800,
          seed: 42,
        },
        {
          id: 'render-002',
          caseId: 'case-002',
          storyboardId: 'sb-002',
          profile: 'cinematic',
          status: 'completed',
          progress: 100,
          startTime: '2024-01-19T14:30:00Z',
          estimatedCompletion: '2024-01-19T15:30:00Z',
          framesRendered: 300,
          totalFrames: 300,
          renderTime: 3600,
          resultPath: '/renders/render-002.mp4',
          checksum: 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
          seed: 123,
        },
      ],
    }),
    getRender: builder.query<RenderJob, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Render', id }],
    }),
    createRender: builder.mutation<RenderJob, CreateRenderRequest>({
      query: (newRender) => ({
        url: '',
        method: 'POST',
        body: newRender,
      }),
      invalidatesTags: ['Render'],
    }),
    cancelRender: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [{ type: 'Render', id }],
    }),
    retryRender: builder.mutation<RenderJob, string>({
      query: (id) => ({
        url: `/${id}/retry`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, id) => [{ type: 'Render', id }],
    }),
    downloadRender: builder.mutation<{ downloadUrl: string }, string>({
      query: (id) => ({
        url: `/${id}/download`,
        method: 'GET',
      }),
    }),
    getRenderProgress: builder.query<RenderJob, string>({
      query: (id) => `/${id}/progress`,
      providesTags: (result, error, id) => [{ type: 'Render', id }],
      // Polling for real-time updates
      pollingInterval: 5000,
    }),
    getSystemMetrics: builder.query<{
      cpuUsage: number;
      memoryUsage: number;
      gpuUsage: number;
      diskUsage: number;
      activeWorkers: number;
      queueLength: number;
    }, void>({
      query: () => '/system/metrics',
      // Mock system metrics
      transformResponse: () => ({
        cpuUsage: 45.2,
        memoryUsage: 67.8,
        gpuUsage: 23.1,
        diskUsage: 34.5,
        activeWorkers: 3,
        queueLength: 2,
      }),
    }),
  }),
});

export const {
  useGetRendersQuery,
  useGetRenderQuery,
  useCreateRenderMutation,
  useCancelRenderMutation,
  useRetryRenderMutation,
  useDownloadRenderMutation,
  useGetRenderProgressQuery,
  useGetSystemMetricsQuery,
} = rendersApi;
