import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface Case {
  id: string;
  title: string;
  mode: 'sandbox' | 'demonstrative';
  jurisdiction: string;
  status: 'draft' | 'in_review' | 'approved' | 'locked';
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
  status?: 'draft' | 'in_review' | 'approved' | 'locked';
  description?: string;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const casesApi = createApi({
  reducerPath: 'casesApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_BASE_URL}/api/v1/cases`,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('legal-sim-token');
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
      // Mock data for development
      transformResponse: () => [
        {
          id: 'case-001',
          title: 'Smith vs. Johnson Contract Dispute',
          mode: 'demonstrative',
          jurisdiction: 'US-Federal',
          status: 'in_review',
          createdAt: '2024-01-15T00:00:00Z',
          updatedAt: '2024-01-20T00:00:00Z',
          createdBy: 'John Attorney',
          evidenceCount: 25,
          storyboardCount: 3,
          renderCount: 1,
          validationStatus: 'valid',
          coveragePercentage: 95,
        },
        {
          id: 'case-002',
          title: 'Property Boundary Dispute',
          mode: 'sandbox',
          jurisdiction: 'US-State-CA',
          status: 'draft',
          createdAt: '2024-01-18T00:00:00Z',
          updatedAt: '2024-01-19T00:00:00Z',
          createdBy: 'Jane Lawyer',
          evidenceCount: 12,
          storyboardCount: 1,
          renderCount: 0,
          validationStatus: 'pending',
          coveragePercentage: 60,
        },
      ],
    }),
    getCase: builder.query<Case, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Case', id }],
      // Mock data for development
      transformResponse: (response, meta, arg) => ({
        id: arg,
        title: 'Smith vs. Johnson Contract Dispute',
        mode: 'demonstrative',
        jurisdiction: 'US-Federal',
        status: 'in_review',
        createdAt: '2024-01-15T00:00:00Z',
        updatedAt: '2024-01-20T00:00:00Z',
        createdBy: 'John Attorney',
        evidenceCount: 25,
        storyboardCount: 3,
        renderCount: 1,
        validationStatus: 'valid',
        coveragePercentage: 95,
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
