import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { casesApi } from './api/casesApi';
import { evidenceApi } from './api/evidenceApi';
import { storyboardsApi } from './api/storyboardsApi';
import { rendersApi } from './api/rendersApi';
import { authApi } from './api/authApi';
import casesSlice from './slices/casesSlice';
import evidenceSlice from './slices/evidenceSlice';
import storyboardsSlice from './slices/storyboardsSlice';
import rendersSlice from './slices/rendersSlice';
import userSlice from './slices/userSlice';

export const store = configureStore({
  reducer: {
    // API slices
    [casesApi.reducerPath]: casesApi.reducer,
    [evidenceApi.reducerPath]: evidenceApi.reducer,
    [storyboardsApi.reducerPath]: storyboardsApi.reducer,
    [rendersApi.reducerPath]: rendersApi.reducer,
    [authApi.reducerPath]: authApi.reducer,
    
    // Regular slices
    cases: casesSlice,
    evidence: evidenceSlice,
    storyboards: storyboardsSlice,
    renders: rendersSlice,
    user: userSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          // Ignore RTK Query actions
          'casesApi/executeQuery/pending',
          'casesApi/executeQuery/fulfilled',
          'casesApi/executeQuery/rejected',
          'evidenceApi/executeQuery/pending',
          'evidenceApi/executeQuery/fulfilled',
          'evidenceApi/executeQuery/rejected',
          'storyboardsApi/executeQuery/pending',
          'storyboardsApi/executeQuery/fulfilled',
          'storyboardsApi/executeQuery/rejected',
          'rendersApi/executeQuery/pending',
          'rendersApi/executeQuery/fulfilled',
          'rendersApi/executeQuery/rejected',
          'authApi/executeQuery/pending',
          'authApi/executeQuery/fulfilled',
          'authApi/executeQuery/rejected',
        ],
      },
    })
    .concat(casesApi.middleware)
    .concat(evidenceApi.middleware)
    .concat(storyboardsApi.middleware)
    .concat(rendersApi.middleware)
    .concat(authApi.middleware),
});

// Setup RTK Query listeners
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
