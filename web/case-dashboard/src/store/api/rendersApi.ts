import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { getAuthToken } from '../../utils/auth';

export interface RenderJob {
  id: string;
  timeline_id: string;
  storyboard_id: string;
  case_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  priority: number;
  created_by: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  width: number;
  height: number;
  fps: number;
  quality: 'draft' | 'standard' | 'high' | 'ultra';
  profile: 'neutral' | 'cinematic';
  deterministic: boolean;
  seed?: number;
  output_format: string;
  output_path: string;
  file_size_bytes: number;
  duration_seconds: number;
  render_time_seconds: number;
  frames_rendered: number;
  total_frames: number;
  progress_percentage: number;
  error_message: string;
  retry_count: number;
  max_retries: number;
  checksum: string;
  golden_frame_checksums: string[];
}

export interface CreateRenderRequest {
  timeline_id: string;
  storyboard_id: string;
  case_id: string;
  width?: number;
  height?: number;
  fps?: number;
  quality?: 'draft' | 'standard' | 'high' | 'ultra';
  profile?: 'neutral' | 'cinematic';
  deterministic?: boolean;
  seed?: number;
  output_format?: string;
  priority?: number;
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
      const token = getAuthToken();
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Render'],
  endpoints: (builder) => ({
    getRenders: builder.query<RenderJob[], { caseId?: string; skip?: number; limit?: number; statusFilter?: string }>({
      query: ({ caseId, skip = 0, limit = 100, statusFilter }) => {
        const params = new URLSearchParams();
        if (caseId) params.append('case_id_filter', caseId);
        if (skip) params.append('skip', skip.toString());
        if (limit) params.append('limit', limit.toString());
        if (statusFilter) params.append('status_filter', statusFilter);
        return `?${params.toString()}`;
      },
      providesTags: ['Render'],
      transformResponse: (response: any[]) => {
        return response.map(render => ({
          id: render.id,
          timeline_id: render.timeline_id,
          storyboard_id: render.storyboard_id,
          case_id: render.case_id,
          status: render.status?.toLowerCase() || 'queued',
          priority: render.priority || 0,
          created_by: render.created_by,
          created_at: render.created_at,
          started_at: render.started_at,
          completed_at: render.completed_at,
          width: render.width || 1920,
          height: render.height || 1080,
          fps: render.fps || 30,
          quality: render.quality?.toLowerCase() || 'standard',
          profile: render.profile || 'neutral',
          deterministic: render.deterministic || true,
          seed: render.seed,
          output_format: render.output_format || 'mp4',
          output_path: render.output_path || '',
          file_size_bytes: render.file_size_bytes || 0,
          duration_seconds: render.duration_seconds || 0,
          render_time_seconds: render.render_time_seconds || 0,
          frames_rendered: render.frames_rendered || 0,
          total_frames: render.total_frames || 0,
          progress_percentage: render.progress_percentage || 0,
          error_message: render.error_message || '',
          retry_count: render.retry_count || 0,
          max_retries: render.max_retries || 3,
          checksum: render.checksum || '',
          golden_frame_checksums: render.golden_frame_checksums || [],
        }));
      },
    }),
    getRender: builder.query<RenderJob, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Render', id }],
    }),
    getCaseRenders: builder.query<RenderJob[], string>({
      query: (caseId) => `/cases/${caseId}/renders`,
      providesTags: (result, error, caseId) => [{ type: 'Render', id: `case-${caseId}` }],
    }),
    createRender: builder.mutation<RenderJob, CreateRenderRequest>({
      query: (newRender) => ({
        url: '',
        method: 'POST',
        body: newRender,
      }),
      invalidatesTags: ['Render'],
    }),
    updateRender: builder.mutation<RenderJob, { id: string; priority?: number }>({
      query: ({ id, priority }) => ({
        url: `/${id}`,
        method: 'PUT',
        body: { priority },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Render', id }],
    }),
    cancelRender: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}`,
        method: 'DELETE',
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
    downloadRender: builder.query<Blob, string>({
      query: (id) => ({
        url: `/${id}/download`,
        method: 'GET',
        responseHandler: (response) => response.blob(),
      }),
    }),
    getRenderStatus: builder.query<{
      status: string;
      progress_percentage: number;
      frames_rendered: number;
      total_frames: number;
      error_message: string;
      render_time_seconds: number;
    }, string>({
      query: (id) => `/${id}/status`,
      providesTags: (result, error, id) => [{ type: 'Render', id }],
    }),
    getQueueStats: builder.query<{
      total_jobs: number;
      queued: number;
      processing: number;
      completed: number;
      failed: number;
      cancelled: number;
    }, void>({
      query: () => '/queue/stats',
      providesTags: ['Render'],
    }),
  }),
});

export const {
  useGetRendersQuery,
  useGetRenderQuery,
  useGetCaseRendersQuery,
  useCreateRenderMutation,
  useUpdateRenderMutation,
  useCancelRenderMutation,
  useRetryRenderMutation,
  useDownloadRenderQuery,
  useGetRenderStatusQuery,
  useGetQueueStatsQuery,
} = rendersApi;
