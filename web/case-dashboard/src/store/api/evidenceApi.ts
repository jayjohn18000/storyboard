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
      query: ({ caseId }) => (caseId ? `?case_id_filter=${caseId}` : ''),
      providesTags: ['Evidence'],
      transformResponse: (response: any[]) => {
        return response.map(evidence => ({
          id: evidence.id,
          name: evidence.metadata?.filename || evidence.filename,
          type: evidence.evidence_type || 'document',
          size: evidence.metadata?.size_bytes || evidence.file_size,
          sha256: evidence.metadata?.checksum || evidence.file_hash,
          uploadedAt: evidence.metadata?.uploaded_at || evidence.uploaded_at,
          uploadedBy: evidence.metadata?.uploaded_by || evidence.uploaded_by,
          caseId: evidence.case_id,
          description: evidence.metadata?.description || '',
          chainOfCustody: evidence.chain_of_custody || [],
          status: evidence.status === 'processed' ? 'completed' : 
                  evidence.status === 'failed' ? 'error' : 'processing',
          metadata: evidence.processing_result || {},
        }));
      },
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
