import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { getAuthToken } from '../../utils/auth';

export interface Case {
  id: string;
  title: string;
  mode: 'sandbox' | 'demonstrative';
  jurisdiction: string;
  status: 'draft' | 'active' | 'archived' | 'closed';
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  evidenceCount: number;
  storyboardCount: number;
  renderCount: number;
  validationStatus: 'valid' | 'invalid' | 'pending';
  coveragePercentage: number;
}

export interface CreateCaseRequest {
  title: string;
  mode: 'sandbox' | 'demonstrative';
  jurisdiction: string;
  description?: string;
}

export interface UpdateCaseRequest {
  id: string;
  title?: string;
  mode?: 'sandbox' | 'demonstrative';
  jurisdiction?: string;
  status?: 'draft' | 'active' | 'archived' | 'closed';
  description?: string;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const casesApi = createApi({
  reducerPath: 'casesApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_BASE_URL}/api/v1/cases`,
    prepareHeaders: (headers) => {
      const token = getAuthToken();
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Case'],
  endpoints: (builder) => ({
    getCases: builder.query<Case[], void>({
      query: () => '',
      providesTags: ['Case'],
      transformResponse: (response: any[]) => {
        // Transform backend response to frontend format
        return response.map(caseData => ({
          id: caseData.id,
          title: caseData.metadata?.title || caseData.title,
          mode: caseData.metadata?.case_type === 'DEMONSTRATIVE' ? 'demonstrative' : 'sandbox',
          jurisdiction: caseData.metadata?.jurisdiction || 'Unknown',
          status: caseData.status?.toLowerCase() || 'draft',
          createdAt: caseData.created_at,
          updatedAt: caseData.updated_at,
          createdBy: caseData.metadata?.created_by || caseData.created_by || 'Unknown',
          evidenceCount: caseData.evidence_ids?.length || 0,
          storyboardCount: caseData.storyboard_ids?.length || 0,
          renderCount: caseData.render_ids?.length || 0,
          validationStatus: 'pending' as const,
          coveragePercentage: 0,
        }));
      },
    }),
    getCase: builder.query<Case, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Case', id }],
      transformResponse: (response: any) => ({
        id: response.id,
        title: response.metadata?.title || response.title,
        mode: response.metadata?.case_type === 'DEMONSTRATIVE' ? 'demonstrative' : 'sandbox',
        jurisdiction: response.metadata?.jurisdiction || 'Unknown',
        status: response.status?.toLowerCase() || 'draft',
        createdAt: response.created_at,
        updatedAt: response.updated_at,
        createdBy: response.metadata?.created_by || response.created_by || 'Unknown',
        evidenceCount: response.evidence_ids?.length || 0,
        storyboardCount: response.storyboard_ids?.length || 0,
        renderCount: response.render_ids?.length || 0,
        validationStatus: 'pending' as const,
        coveragePercentage: 0,
      }),
    }),
    createCase: builder.mutation<Case, CreateCaseRequest>({
      query: (newCase) => ({
        url: '',
        method: 'POST',
        body: newCase,
      }),
      invalidatesTags: ['Case'],
    }),
    updateCase: builder.mutation<Case, UpdateCaseRequest>({
      query: ({ id, ...updates }) => ({
        url: `/${id}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Case', id }],
    }),
    deleteCase: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Case'],
    }),
  }),
});

export const {
  useGetCasesQuery,
  useGetCaseQuery,
  useCreateCaseMutation,
  useUpdateCaseMutation,
  useDeleteCaseMutation,
} = casesApi;
