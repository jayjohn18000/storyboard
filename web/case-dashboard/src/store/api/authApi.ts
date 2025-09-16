import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'attorney' | 'viewer';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  expiresAt: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  role?: 'attorney' | 'viewer';
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_BASE_URL}/api/v1/auth`,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('legal-sim-token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['User'],
  endpoints: (builder) => ({
    login: builder.mutation<LoginResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['User'],
      // Mock login for development
      transformResponse: (response, meta, arg) => ({
        user: {
          id: 'user-001',
          email: arg.email,
          name: arg.email.split('@')[0],
          role: 'attorney',
        },
        token: 'mock-jwt-token',
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      }),
    }),
    register: builder.mutation<LoginResponse, RegisterRequest>({
      query: (userData) => ({
        url: '/register',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),
    refreshToken: builder.mutation<{ token: string; expiresAt: string }, void>({
      query: () => ({
        url: '/refresh',
        method: 'POST',
      }),
    }),
    getCurrentUser: builder.query<User, void>({
      query: () => '/me',
      providesTags: ['User'],
      // Mock current user for development
      transformResponse: () => ({
        id: 'user-001',
        email: 'demo@legal-sim.com',
        name: 'Demo User',
        role: 'attorney',
      }),
    }),
    updateProfile: builder.mutation<User, Partial<User>>({
      query: (updates) => ({
        url: '/profile',
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: ['User'],
    }),
    changePassword: builder.mutation<void, { currentPassword: string; newPassword: string }>({
      query: (passwords) => ({
        url: '/change-password',
        method: 'POST',
        body: passwords,
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useRefreshTokenMutation,
  useGetCurrentUserQuery,
  useUpdateProfileMutation,
  useChangePasswordMutation,
} = authApi;
