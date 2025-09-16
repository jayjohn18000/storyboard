import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

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
      const token = localStorage.getItem('legal-sim-token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Storyboard'],
  endpoints: (builder) => ({
    getStoryboards: builder.query<Storyboard[], { caseId?: string }>({
      query: ({ caseId }) => (caseId ? `?caseId=${caseId}` : ''),
      providesTags: ['Storyboard'],
      // Mock data for development
      transformResponse: () => [
        {
          id: 'sb-001',
          caseId: 'case-001',
          title: 'Main Timeline',
          content: `@time[0.0] #actor[John] ~action[enters room] ^evidence[doc-001]
John walks into the courtroom and takes his seat.

@time[5.0] #actor[Judge] ~action[addresses court] ^evidence[audio-001@00:30]
The judge calls the court to order and begins the proceedings.`,
          beats: [
            {
              id: 'beat-001',
              timestamp: 0,
              description: 'John walks into the courtroom and takes his seat',
              actors: ['John'],
              evidenceAnchors: [{ evidenceId: 'doc-001', description: 'Contract document' }],
              confidence: 0.9,
              disputed: false,
              duration: 5,
            },
            {
              id: 'beat-002',
              timestamp: 5,
              description: 'The judge calls the court to order and begins the proceedings',
              actors: ['Judge'],
              evidenceAnchors: [{ evidenceId: 'audio-001', timestamp: 30, description: 'Court recording' }],
              confidence: 0.95,
              disputed: false,
              duration: 10,
            },
          ],
          isValid: true,
          validationErrors: [],
          createdAt: '2024-01-15T00:00:00Z',
          updatedAt: '2024-01-20T00:00:00Z',
          createdBy: 'John Attorney',
        },
      ],
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
