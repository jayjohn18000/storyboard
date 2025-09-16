import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from '../index';

// Get API base URL from environment or use default
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const baseApi = createApi({
  reducerPath: 'baseApi',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      // Get token from state or localStorage
      const state = getState() as RootState;
      const token = state.user.token || localStorage.getItem('legal-sim-token');
      
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      
      headers.set('content-type', 'application/json');
      return headers;
    },
  }),
  tagTypes: ['Case', 'Evidence', 'Storyboard', 'Render', 'User'],
  endpoints: () => ({}),
});
