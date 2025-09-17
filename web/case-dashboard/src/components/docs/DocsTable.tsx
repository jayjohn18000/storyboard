import React, { useState } from 'react';
import {
  DocumentTextIcon,
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  TrashIcon,
  CalendarIcon,
  UserIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { Evidence } from '../../store/api/evidenceApi';
import { DocStatusBadge, DocStatus } from './DocStatusBadge';

interface DocsTableProps {
  evidence: Evidence[];
  selectedDocs: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  onRefresh: () => void;
}

export const DocsTable: React.FC<DocsTableProps> = ({
  evidence,
  selectedDocs,
  onSelectionChange,
  onRefresh
}) => {
  const [sortBy, setSortBy] = useState<'name' | 'uploadedAt' | 'size' | 'status'>('uploadedAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(evidence.map(e => e.id));
    } else {
      onSelectionChange([]);
    }
  };

  const handleSelectOne = (id: string, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedDocs, id]);
    } else {
      onSelectionChange(selectedDocs.filter(selectedId => selectedId !== id));
    }
  };

  const handleSort = (column: typeof sortBy) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const sortedEvidence = [...evidence].sort((a, b) => {
    let aValue: any, bValue: any;
    
    switch (sortBy) {
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case 'uploadedAt':
        aValue = new Date(a.uploadedAt).getTime();
        bValue = new Date(b.uploadedAt).getTime();
        break;
      case 'size':
        aValue = a.size;
        bValue = b.size;
        break;
      case 'status':
        aValue = a.status;
        bValue = b.status;
        break;
      default:
        return 0;
    }

    if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/') || type === 'image') return <PhotoIcon className="w-5 h-5 text-blue-500" />;
    if (type.startsWith('video/') || type === 'video') return <VideoCameraIcon className="w-5 h-5 text-purple-500" />;
    if (type.startsWith('audio/') || type === 'audio') return <SpeakerWaveIcon className="w-5 h-5 text-orange-500" />;
    return <DocumentTextIcon className="w-5 h-5 text-gray-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const mapStatusToDocStatus = (status: string): DocStatus => {
    switch (status) {
      case 'processing':
        return 'PARSING';
      case 'completed':
        return 'INDEXED';
      case 'error':
        return 'ERROR';
      default:
        return 'UPLOADING';
    }
  };

  const SortIcon: React.FC<{ column: typeof sortBy }> = ({ column }) => {
    if (sortBy !== column) return null;
    return (
      <span className="ml-1">
        {sortOrder === 'asc' ? '↑' : '↓'}
      </span>
    );
  };

  if (evidence.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
        <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
        <p className="text-gray-500">Upload some documents to get started.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedDocs.length === evidence.length && evidence.length > 0}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      title="Select all documents"
                      aria-label="Select all documents"
                    />
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('name')}
              >
                Name <SortIcon column="name" />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('size')}
              >
                Size <SortIcon column="size" />
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('status')}
              >
                Status <SortIcon column="status" />
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700"
                onClick={() => handleSort('uploadedAt')}
              >
                Uploaded <SortIcon column="uploadedAt" />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedEvidence.map((doc) => (
              <React.Fragment key={doc.id}>
                <tr className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedDocs.includes(doc.id)}
                      onChange={(e) => handleSelectOne(doc.id, e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      title={`Select ${doc.name}`}
                      aria-label={`Select ${doc.name}`}
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getFileIcon(doc.type)}
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">{doc.name}</div>
                        {doc.description && (
                          <div className="text-sm text-gray-500">{doc.description}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900 capitalize">{doc.type}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatFileSize(doc.size)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <DocStatusBadge status={mapStatusToDocStatus(doc.status)} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-900">
                      <CalendarIcon className="w-4 h-4 mr-1 text-gray-400" />
                      {formatDate(doc.uploadedAt)}
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <UserIcon className="w-4 h-4 mr-1 text-gray-400" />
                      {doc.uploadedBy}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setExpandedRow(expandedRow === doc.id ? null : doc.id)}
                        className="text-blue-600 hover:text-blue-900"
                        title="View details"
                      >
                        <EyeIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = `/api/v1/evidence/${doc.id}/download`;
                          link.download = doc.name;
                          link.click();
                        }}
                        className="text-green-600 hover:text-green-900"
                        title="Download"
                      >
                        <DocumentArrowDownIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
                
                {/* Expanded Row */}
                {expandedRow === doc.id && (
                  <tr>
                    <td colSpan={7} className="px-6 py-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">File Information</h4>
                          <dl className="space-y-1">
                            <div className="flex justify-between">
                              <dt className="text-sm text-gray-500">SHA-256:</dt>
                              <dd className="text-sm text-gray-900 font-mono">{doc.sha256}</dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-sm text-gray-500">Case ID:</dt>
                              <dd className="text-sm text-gray-900">{doc.caseId || 'Not assigned'}</dd>
                            </div>
                            {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                              <div>
                                <dt className="text-sm text-gray-500 mb-1">Metadata:</dt>
                                <dd className="text-sm text-gray-900">
                                  <pre className="bg-white p-2 rounded border text-xs overflow-x-auto">
                                    {JSON.stringify(doc.metadata, null, 2)}
                                  </pre>
                                </dd>
                              </div>
                            )}
                          </dl>
                        </div>
                        
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Chain of Custody</h4>
                          {doc.chainOfCustody && doc.chainOfCustody.length > 0 ? (
                            <ul className="space-y-1">
                              {doc.chainOfCustody.map((custodian, index) => (
                                <li key={index} className="text-sm text-gray-900 flex items-center">
                                  <ClockIcon className="w-3 h-3 mr-1 text-gray-400" />
                                  {custodian}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-sm text-gray-500">No chain of custody recorded</p>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
        <div className="flex items-center justify-between">
          <div className="flex-1 flex justify-between sm:hidden">
            <button className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
              Previous
            </button>
            <button className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing <span className="font-medium">1</span> to <span className="font-medium">{evidence.length}</span> of{' '}
                <span className="font-medium">{evidence.length}</span> results
              </p>
            </div>
            <div>
              <button
                onClick={onRefresh}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocsTable;
