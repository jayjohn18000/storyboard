import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { RenderJob } from '../api/rendersApi';

interface RendersState {
  selectedRenderId: string | null;
  filters: {
    status: string;
    profile: string;
    caseId: string;
  };
  sortBy: 'startTime' | 'progress' | 'renderTime';
  sortOrder: 'asc' | 'desc';
  autoRefresh: boolean;
  refreshInterval: number;
  systemMetrics: {
    cpuUsage: number;
    memoryUsage: number;
    gpuUsage: number;
    diskUsage: number;
    activeWorkers: number;
    queueLength: number;
  };
}

const initialState: RendersState = {
  selectedRenderId: null,
  filters: {
    status: 'all',
    profile: 'all',
    caseId: 'all',
  },
  sortBy: 'startTime',
  sortOrder: 'desc',
  autoRefresh: true,
  refreshInterval: 5000,
  systemMetrics: {
    cpuUsage: 0,
    memoryUsage: 0,
    gpuUsage: 0,
    diskUsage: 0,
    activeWorkers: 0,
    queueLength: 0,
  },
};

const rendersSlice = createSlice({
  name: 'renders',
  initialState,
  reducers: {
    setSelectedRender: (state, action: PayloadAction<string | null>) => {
      state.selectedRenderId = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<RendersState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    setSorting: (state, action: PayloadAction<{ sortBy: RendersState['sortBy']; sortOrder: RendersState['sortOrder'] }>) => {
      state.sortBy = action.payload.sortBy;
      state.sortOrder = action.payload.sortOrder;
    },
    setAutoRefresh: (state, action: PayloadAction<boolean>) => {
      state.autoRefresh = action.payload;
    },
    setRefreshInterval: (state, action: PayloadAction<number>) => {
      state.refreshInterval = action.payload;
    },
    setSystemMetrics: (state, action: PayloadAction<RendersState['systemMetrics']>) => {
      state.systemMetrics = action.payload;
    },
    clearFilters: (state) => {
      state.filters = {
        status: 'all',
        profile: 'all',
        caseId: 'all',
      };
    },
  },
});

export const {
  setSelectedRender,
  setFilters,
  setSorting,
  setAutoRefresh,
  setRefreshInterval,
  setSystemMetrics,
  clearFilters,
} = rendersSlice.actions;

export default rendersSlice.reducer;
