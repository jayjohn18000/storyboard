import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  DocumentTextIcon,
  CalendarIcon,
  UserIcon,
  ChartBarIcon,
  FilmIcon,
} from '@heroicons/react/24/outline';
import { useGetCasesQuery, Case } from '../../store/api/casesApi';

export const CasesPage: React.FC = () => {
  const { data: cases = [], isLoading, error } = useGetCasesQuery();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const getStatusColor = (status: Case['status']) => {
    switch (status) {
      case 'approved': return 'text-success-600 bg-success-100';
      case 'in_review': return 'text-primary-600 bg-primary-100';
      case 'draft': return 'text-warning-600 bg-warning-100';
      case 'locked': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getModeColor = (mode: Case['mode']) => {
    return mode === 'demonstrative' 
      ? 'text-purple-600 bg-purple-100' 
      : 'text-orange-600 bg-orange-100';
  };

  const filteredCases = cases.filter(caseItem => {
    const matchesSearch = caseItem.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         caseItem.jurisdiction.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || caseItem.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-danger-500 text-lg font-medium mb-2">Error loading cases</div>
          <div className="text-gray-600">Please try refreshing the page</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cases</h1>
          <p className="text-gray-600">Manage your legal simulation cases</p>
        </div>
        <button className="btn-primary flex items-center space-x-2">
          <PlusIcon className="w-4 h-4" />
          <span>New Case</span>
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search cases..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <FunnelIcon className="w-4 h-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
              aria-label="Filter by status"
              title="Filter by status"
            >
              <option value="all">All Status</option>
              <option value="draft">Draft</option>
              <option value="in_review">In Review</option>
              <option value="approved">Approved</option>
              <option value="locked">Locked</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cases Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCases.map((caseItem) => (
          <Link
            key={caseItem.id}
            to={`/cases/${caseItem.id}`}
            className="card p-6 hover:shadow-medium transition-shadow"
          >
            <div className="space-y-4">
              {/* Header */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {caseItem.title}
                </h3>
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(caseItem.status)}`}>
                    {caseItem.status.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getModeColor(caseItem.mode)}`}>
                    {caseItem.mode.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{caseItem.jurisdiction}</p>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="flex items-center justify-center mb-1">
                    <DocumentTextIcon className="w-4 h-4 text-blue-500" />
                  </div>
                  <p className="text-lg font-semibold text-gray-900">{caseItem.evidenceCount}</p>
                  <p className="text-xs text-gray-500">Evidence</p>
                </div>
                <div>
                  <div className="flex items-center justify-center mb-1">
                    <ChartBarIcon className="w-4 h-4 text-green-500" />
                  </div>
                  <p className="text-lg font-semibold text-gray-900">{caseItem.storyboardCount}</p>
                  <p className="text-xs text-gray-500">Storyboards</p>
                </div>
                <div>
                  <div className="flex items-center justify-center mb-1">
                    <FilmIcon className="w-4 h-4 text-purple-500" />
                  </div>
                  <p className="text-lg font-semibold text-gray-900">{caseItem.renderCount}</p>
                  <p className="text-xs text-gray-500">Renders</p>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t">
                <div className="flex items-center space-x-1">
                  <UserIcon className="w-4 h-4" />
                  <span>{caseItem.createdBy}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <CalendarIcon className="w-4 h-4" />
                  <span>{new Date(caseItem.updatedAt).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {filteredCases.length === 0 && (
        <div className="text-center py-12">
          <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No cases found</h3>
          <p className="text-gray-600">Try adjusting your search or create a new case.</p>
        </div>
      )}
    </div>
  );
};
