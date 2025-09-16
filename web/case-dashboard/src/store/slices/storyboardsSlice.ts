import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Storyboard, StoryboardBeat } from '../api/storyboardsApi';

interface StoryboardsState {
  selectedStoryboardId: string | null;
  currentContent: string;
  validationErrors: string[];
  isValid: boolean;
  beats: StoryboardBeat[];
  viewMode: 'edit' | 'preview' | 'split';
  isPlaying: boolean;
  currentBeat: number;
  autoSave: boolean;
  lastSaved: string | null;
}

const initialState: StoryboardsState = {
  selectedStoryboardId: null,
  currentContent: '',
  validationErrors: [],
  isValid: true,
  beats: [],
  viewMode: 'split',
  isPlaying: false,
  currentBeat: 0,
  autoSave: true,
  lastSaved: null,
};

const storyboardsSlice = createSlice({
  name: 'storyboards',
  initialState,
  reducers: {
    setSelectedStoryboard: (state, action: PayloadAction<string | null>) => {
      state.selectedStoryboardId = action.payload;
    },
    setCurrentContent: (state, action: PayloadAction<string>) => {
      state.currentContent = action.payload;
    },
    setValidationErrors: (state, action: PayloadAction<string[]>) => {
      state.validationErrors = action.payload;
      state.isValid = action.payload.length === 0;
    },
    setBeats: (state, action: PayloadAction<StoryboardBeat[]>) => {
      state.beats = action.payload;
    },
    setViewMode: (state, action: PayloadAction<StoryboardsState['viewMode']>) => {
      state.viewMode = action.payload;
    },
    setIsPlaying: (state, action: PayloadAction<boolean>) => {
      state.isPlaying = action.payload;
    },
    setCurrentBeat: (state, action: PayloadAction<number>) => {
      state.currentBeat = action.payload;
    },
    nextBeat: (state) => {
      if (state.currentBeat < state.beats.length - 1) {
        state.currentBeat += 1;
      }
    },
    previousBeat: (state) => {
      if (state.currentBeat > 0) {
        state.currentBeat -= 1;
      }
    },
    setAutoSave: (state, action: PayloadAction<boolean>) => {
      state.autoSave = action.payload;
    },
    setLastSaved: (state, action: PayloadAction<string>) => {
      state.lastSaved = action.payload;
    },
    resetStoryboard: (state) => {
      state.currentContent = '';
      state.validationErrors = [];
      state.isValid = true;
      state.beats = [];
      state.isPlaying = false;
      state.currentBeat = 0;
      state.lastSaved = null;
    },
  },
});

export const {
  setSelectedStoryboard,
  setCurrentContent,
  setValidationErrors,
  setBeats,
  setViewMode,
  setIsPlaying,
  setCurrentBeat,
  nextBeat,
  previousBeat,
  setAutoSave,
  setLastSaved,
  resetStoryboard,
} = storyboardsSlice.actions;

export default storyboardsSlice.reducer;
