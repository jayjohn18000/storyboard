import React, { useState } from 'react';
import {
  DocumentTextIcon,
  CloudArrowUpIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  DocumentArrowDownIcon,
  TrashIcon,
  EyeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useGetEvidenceQuery, useDeleteEvidenceMutation } from '../../store/api/evidenceApi';
import { DocsUpload } from '../../components/docs/DocsUpload';
import { DocStatusBadge } from '../../components/docs/DocStatusBadge';
import { DocsTable } from '../../components/docs/DocsTable';

export const DocsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [showUpload, setShowUpload] = useState(false);

  const { data: evidenceData, isLoading, error, refetch } = useGetEvidenceQuery({});
  const [deleteEvidence] = useDeleteEvidenceMutation();

  // Filter evidence based on search and filters
  const filteredEvidence = evidenceData?.filter(evidence => {
    const matchesSearch = evidence.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         evidence.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || evidence.status === statusFilter;
    const matchesType = typeFilter === 'all' || evidence.type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  }) || [];

  const handleDeleteSelected = async () => {
    try {
      await Promise.all(selectedDocs.map(id => deleteEvidence(id)));
      setSelectedDocs([]);
      refetch();
    } catch (error) {
      console.error('Failed to delete evidence:', error);
    }
  };

  const handleDownloadSelected = () => {
    selectedDocs.forEach(id => {
      const evidence = evidenceData?.find(e => e.id === id);
      if (evidence) {
        // Create download link
        const link = document.createElement('a');
        link.href = `/api/v1/evidence/${id}/download`;
        link.download = evidence.name;
        link.click();
      }
    });
  };

  const getStats = () => {
    if (!evidenceData) return { total: 0, processing: 0, completed: 0, error: 0 };
    
    return {
      total: evidenceData.length,
      processing: evidenceData.filter(e => e.status === 'processing').length,
      completed: evidenceData.filter(e => e.status === 'completed').length,
      error: evidenceData.filter(e => e.status === 'error').length,
    };
  };

  const stats = getStats();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
        <p className="text-red-600 mb-4">Failed to load documents</p>
        <button 
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">Documents</h1>
            <p className="text-gray-600">Manage and organize your case evidence</p>
          </div>
          
          <div className="flex items-center space-x-3">
            {selectedDocs.length > 0 && (
              <>
                <button
                  onClick={handleDownloadSelected}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center space-x-2"
                >
                  <DocumentArrowDownIcon className="w-4 h-4" />
                  <span>Download ({selectedDocs.length})</span>
                </button>
                <button
                  onClick={handleDeleteSelected}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center space-x-2"
                >
                  <TrashIcon className="w-4 h-4" />
                  <span>Delete ({selectedDocs.length})</span>
                </button>
              </>
            )}
            <button
              onClick={() => setShowUpload(true)}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2"
            >
              <CloudArrowUpIcon className="w-4 h-4" />
              <span>Upload Documents</span>
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
            </div>
            <DocumentTextIcon className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Processing</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.processing}</p>
            </div>
            <ClockIcon className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
            </div>
            <CheckCircleIcon className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Errors</p>
              <p className="text-2xl font-bold text-red-600">{stats.error}</p>
            </div>
            <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <div className="flex gap-4">
            <div className="relative">
              <FunnelIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                title="Filter by status"
                aria-label="Filter by status"
              >
                <option value="all">All Status</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="error">Error</option>
              </select>
            </div>
            
            <div className="relative">
              <FunnelIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                title="Filter by type"
                aria-label="Filter by type"
              >
                <option value="all">All Types</option>
                <option value="document">Documents</option>
                <option value="image">Images</option>
                <option value="video">Videos</option>
                <option value="audio">Audio</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <DocsTable
        evidence={filteredEvidence}
        selectedDocs={selectedDocs}
        onSelectionChange={setSelectedDocs}
        onRefresh={refetch}
      />

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-800">Upload Documents</h2>
              <button
                onClick={() => setShowUpload(false)}
                className="text-gray-400 hover:text-gray-600"
                title="Close upload modal"
                aria-label="Close upload modal"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <DocsUpload
              onUploadComplete={() => {
                setShowUpload(false);
                refetch();
              }}
              onUploadError={(error) => {
                console.error('Upload error:', error);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DocsPage;
