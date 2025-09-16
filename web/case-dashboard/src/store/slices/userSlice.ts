import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User } from '../api/authApi';

interface UserState {
  currentUser: User | null;
  token: string | null;
  isAuthenticated: boolean;
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    fontSize: 'small' | 'medium' | 'large';
    density: 'compact' | 'comfortable' | 'spacious';
    autoSave: boolean;
    notifications: {
      renderCompletion: boolean;
      evidenceProcessing: boolean;
      validationErrors: boolean;
      emailNotifications: boolean;
    };
  };
  lastActivity: string | null;
}

const initialState: UserState = {
  currentUser: null,
  token: null,
  isAuthenticated: false,
  preferences: {
    theme: 'light',
    fontSize: 'medium',
    density: 'comfortable',
    autoSave: true,
    notifications: {
      renderCompletion: true,
      evidenceProcessing: true,
      validationErrors: true,
      emailNotifications: true,
    },
  },
  lastActivity: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.currentUser = action.payload;
      state.isAuthenticated = true;
    },
    setToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload;
    },
    setAuthenticated: (state, action: PayloadAction<boolean>) => {
      state.isAuthenticated = action.payload;
      if (!action.payload) {
        state.currentUser = null;
        state.token = null;
      }
    },
    updatePreferences: (state, action: PayloadAction<Partial<UserState['preferences']>>) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },
    updateNotificationPreferences: (state, action: PayloadAction<Partial<UserState['preferences']['notifications']>>) => {
      state.preferences.notifications = { ...state.preferences.notifications, ...action.payload };
    },
    setLastActivity: (state, action: PayloadAction<string>) => {
      state.lastActivity = action.payload;
    },
    logout: (state) => {
      state.currentUser = null;
      state.token = null;
      state.isAuthenticated = false;
      state.lastActivity = null;
    },
  },
});

export const {
  setUser,
  setToken,
  setAuthenticated,
  updatePreferences,
  updateNotificationPreferences,
  setLastActivity,
  logout,
} = userSlice.actions;

export default userSlice.reducer;
