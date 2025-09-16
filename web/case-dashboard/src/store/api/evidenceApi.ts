import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface Evidence {
  id: string;
  name: string;
  type: string;
  size: number;
  sha256: string;
  uploadedAt: string;
  uploadedBy: string;
  caseId?: string;
  description?: string;
  chainOfCustody: string[];
  status: 'processing' | 'completed' | 'error';
  metadata?: {
    duration?: number;
    pageCount?: number;
    resolution?: string;
    format?: string;
  };
}

export interface UploadEvidenceRequest {
  file: File;
  caseId?: string;
  description?: string;
  chainOfCustody?: string[];
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const evidenceApi = createApi({
  reducerPath: 'evidenceApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_BASE_URL}/api/v1/evidence`,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('legal-sim-token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Evidence'],
  endpoints: (builder) => ({
    getEvidence: builder.query<Evidence[], { caseId?: string }>({
      query: ({ caseId }) => (caseId ? `?caseId=${caseId}` : ''),
      providesTags: ['Evidence'],
      // Mock data for development
      transformResponse: () => [
        {
          id: 'ev-001',
          name: 'Contract_Amendment.pdf',
          type: 'document',
          size: 1024000,
          sha256: 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
          uploadedAt: '2024-01-20T10:30:00Z',
          uploadedBy: 'John Attorney',
          caseId: 'case-001',
          description: 'Contract amendment document',
          chainOfCustody: ['John Attorney', 'Legal Team'],
          status: 'completed',
          metadata: {
            pageCount: 5,
            format: 'PDF',
          },
        },
        {
          id: 'ev-002',
          name: 'Meeting_Recording.mp3',
          type: 'audio',
          size: 5120000,
          sha256: 'b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567',
          uploadedAt: '2024-01-19T14:15:00Z',
          uploadedBy: 'Jane Lawyer',
          caseId: 'case-001',
          description: 'Meeting recording',
          chainOfCustody: ['Jane Lawyer'],
          status: 'completed',
          metadata: {
            duration: 1800,
            format: 'MP3',
          },
        },
      ],
    }),
    getEvidenceById: builder.query<Evidence, string>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'Evidence', id }],
    }),
    uploadEvidence: builder.mutation<Evidence, UploadEvidenceRequest>({
      query: ({ file, caseId, description, chainOfCustody }) => {
        const formData = new FormData();
        formData.append('file', file);
        if (caseId) formData.append('caseId', caseId);
        if (description) formData.append('description', description);
        if (chainOfCustody) formData.append('chainOfCustody', JSON.stringify(chainOfCustody));
        
        return {
          url: '/upload',
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: ['Evidence'],
    }),
    updateEvidence: builder.mutation<Evidence, { id: string; updates: Partial<Evidence> }>({
      query: ({ id, updates }) => ({
        url: `/${id}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Evidence', id }],
    }),
    deleteEvidence: builder.mutation<void, string>({
      query: (id) => ({
        url: `/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Evidence'],
    }),
    verifyChecksum: builder.mutation<{ valid: boolean }, { id: string; checksum: string }>({
      query: ({ id, checksum }) => ({
        url: `/${id}/verify`,
        method: 'POST',
        body: { checksum },
      }),
    }),
  }),
});

export const {
  useGetEvidenceQuery,
  useGetEvidenceByIdQuery,
  useUploadEvidenceMutation,
  useUpdateEvidenceMutation,
  useDeleteEvidenceMutation,
  useVerifyChecksumMutation,
} = evidenceApi;
