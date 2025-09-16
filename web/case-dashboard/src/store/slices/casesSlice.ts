import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Case } from '../api/casesApi';

interface CasesState {
  selectedCaseId: string | null;
  filters: {
    status: string;
    mode: string;
    jurisdiction: string;
  };
  searchTerm: string;
  sortBy: 'createdAt' | 'updatedAt' | 'title';
  sortOrder: 'asc' | 'desc';
}

const initialState: CasesState = {
  selectedCaseId: null,
  filters: {
    status: 'all',
    mode: 'all',
    jurisdiction: 'all',
  },
  searchTerm: '',
  sortBy: 'updatedAt',
  sortOrder: 'desc',
};

const casesSlice = createSlice({
  name: 'cases',
  initialState,
  reducers: {
    setSelectedCase: (state, action: PayloadAction<string | null>) => {
      state.selectedCaseId = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<CasesState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    setSearchTerm: (state, action: PayloadAction<string>) => {
      state.searchTerm = action.payload;
    },
    setSorting: (state, action: PayloadAction<{ sortBy: CasesState['sortBy']; sortOrder: CasesState['sortOrder'] }>) => {
      state.sortBy = action.payload.sortBy;
      state.sortOrder = action.payload.sortOrder;
    },
    clearFilters: (state) => {
      state.filters = {
        status: 'all',
        mode: 'all',
        jurisdiction: 'all',
      };
      state.searchTerm = '';
    },
  },
});

export const {
  setSelectedCase,
  setFilters,
  setSearchTerm,
  setSorting,
  clearFilters,
} = casesSlice.actions;

export default casesSlice.reducer;
