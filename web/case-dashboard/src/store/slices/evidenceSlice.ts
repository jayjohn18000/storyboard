import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Evidence } from '../api/evidenceApi';

interface EvidenceState {
  selectedEvidenceIds: string[];
  filters: {
    type: string;
    status: string;
    caseId: string;
  };
  searchTerm: string;
  sortBy: 'uploadedAt' | 'name' | 'size';
  sortOrder: 'asc' | 'desc';
  uploadProgress: Record<string, number>;
}

const initialState: EvidenceState = {
  selectedEvidenceIds: [],
  filters: {
    type: 'all',
    status: 'all',
    caseId: 'all',
  },
  searchTerm: '',
  sortBy: 'uploadedAt',
  sortOrder: 'desc',
  uploadProgress: {},
};

const evidenceSlice = createSlice({
  name: 'evidence',
  initialState,
  reducers: {
    setSelectedEvidence: (state, action: PayloadAction<string[]>) => {
      state.selectedEvidenceIds = action.payload;
    },
    toggleEvidenceSelection: (state, action: PayloadAction<string>) => {
      const id = action.payload;
      const index = state.selectedEvidenceIds.indexOf(id);
      if (index === -1) {
        state.selectedEvidenceIds.push(id);
      } else {
        state.selectedEvidenceIds.splice(index, 1);
      }
    },
    clearEvidenceSelection: (state) => {
      state.selectedEvidenceIds = [];
    },
    setFilters: (state, action: PayloadAction<Partial<EvidenceState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    setSearchTerm: (state, action: PayloadAction<string>) => {
      state.searchTerm = action.payload;
    },
    setSorting: (state, action: PayloadAction<{ sortBy: EvidenceState['sortBy']; sortOrder: EvidenceState['sortOrder'] }>) => {
      state.sortBy = action.payload.sortBy;
      state.sortOrder = action.payload.sortOrder;
    },
    setUploadProgress: (state, action: PayloadAction<{ fileId: string; progress: number }>) => {
      state.uploadProgress[action.payload.fileId] = action.payload.progress;
    },
    clearUploadProgress: (state, action: PayloadAction<string>) => {
      delete state.uploadProgress[action.payload];
    },
    clearFilters: (state) => {
      state.filters = {
        type: 'all',
        status: 'all',
        caseId: 'all',
      };
      state.searchTerm = '';
    },
  },
});

export const {
  setSelectedEvidence,
  toggleEvidenceSelection,
  clearEvidenceSelection,
  setFilters,
  setSearchTerm,
  setSorting,
  setUploadProgress,
  clearUploadProgress,
  clearFilters,
} = evidenceSlice.actions;

export default evidenceSlice.reducer;
