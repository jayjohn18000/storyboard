import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { getAuthToken } from '../../utils/auth';

export interface StoryboardBeat {
  id: string;
  timestamp: number;
  description: string;
  actors: string[];
  evidenceAnchors: EvidenceAnchor[];
  confidence: number;
  disputed: boolean;
  duration: number;
}

export interface EvidenceAnchor {
  evidenceId: string;
  timestamp?: number;
  pageNumber?: number;
  description: string;
}

export interface Storyboard {
  id: string;
  caseId: string;
  title: string;
  content: string;
  beats: StoryboardBeat[];
  isValid: boolean;
  validationErrors: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface CreateStoryboardRequest {
  caseId: string;
  title: string;
  content?: string;
}

export interface UpdateStoryboardRequest {
  id: string;
  title?: string;
  content?: string;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const storyboardsApi = createApi({
  reducerPath: 'storyboardsApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_BASE_URL}/api/v1/storyboards`,
    prepareHeaders: (headers) => {
      const token = getAuthToken();
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Storyboard'],
  endpoints: (builder) => ({
    getStoryboards: builder.query<Storyboard[], { caseId?: string }>({
      query: ({ caseId }) => (caseId ? `?case_id_filter=${caseId}` : ''),
      providesTags: ['Storyboard'],
      transformResponse: (response: any[]) => {
        return response.map(storyboard => ({
          id: storyboard.id,
          caseId: storyboard.case_id,
          title: storyboard.title,
          content: storyboard.content || '',
          beats: [], // Will be parsed from content
          isValid: storyboard.validation_result?.is_valid || false,
          validationErrors: storyboard.validation_result?.errors || [],
          createdAt: storyboard.created_at,
          updatedAt: storyboard.updated_at,
          createdBy: storyboard.created_by || 'Unknown',
        }));
      },
    }),
    getStoryboard: builder.query<Storyboard, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Storyboard', id }],
    }),
    createStoryboard: builder.mutation<Storyboard, CreateStoryboardRequest>({
      query: (newStoryboard) => ({
        url: '',
        method: 'POST',
        body: newStoryboard,
      }),
      invalidatesTags: ['Storyboard'],
    }),
    updateStoryboard: builder.mutation<Storyboard, UpdateStoryboardRequest>({
      query: ({ id, ...updates }) => ({
        url: `/${id}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Storyboard', id }],
    }),
    deleteStoryboard: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Storyboard'],
    }),
    validateStoryboard: builder.mutation<{ isValid: boolean; errors: string[] }, { id: string; content: string }>({
      query: ({ id, content }) => ({
        url: `/${id}/validate`,
        method: 'POST',
        body: { content },
      }),
    }),
    parseStoryboard: builder.mutation<{ beats: StoryboardBeat[] }, { content: string }>({
      query: ({ content }) => ({
        url: '/parse',
        method: 'POST',
        body: { content },
      }),
    }),
  }),
});

export const {
  useGetStoryboardsQuery,
  useGetStoryboardQuery,
  useCreateStoryboardMutation,
  useUpdateStoryboardMutation,
  useDeleteStoryboardMutation,
  useValidateStoryboardMutation,
  useParseStoryboardMutation,
} = storyboardsApi;
