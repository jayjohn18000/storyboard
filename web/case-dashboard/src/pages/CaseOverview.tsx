import React, { useState, useEffect } from 'react';
import {
  DocumentTextIcon,
  PhotoIcon,
  VideoCameraIcon,
  SpeakerWaveIcon,
  PlayIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  UserGroupIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface Case {
  id: string;
  title: string;
  mode: 'sandbox' | 'demonstrative';
  jurisdiction: string;
  status: 'draft' | 'in_review' | 'approved' | 'locked';
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  evidenceCount: number;
  storyboardCount: number;
  renderCount: number;
  validationStatus: 'valid' | 'invalid' | 'pending';
  coveragePercentage: number;
}

interface EvidenceSummary {
  total: number;
  byType: {
    documents: number;
    photos: number;
    videos: number;
    audio: number;
  };
  recent: Array<{
    id: string;
    name: string;
    type: string;
    uploadedAt: Date;
    thumbnail?: string;
  }>;
}

interface TimelinePreview {
  totalDuration: number;
  beatCount: number;
  evidenceAnchors: number;
  disputedBeats: number;
  confidenceScore: number;
}

interface ValidationStatus {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  coveragePercentage: number;
  lastValidated: Date;
}

export const CaseOverview: React.FC = () => {
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [evidenceSummary, setEvidenceSummary] = useState<EvidenceSummary | null>(null);
  const [timelinePreview, setTimelinePreview] = useState<TimelinePreview | null>(null);
  const [validationStatus, setValidationStatus] = useState<ValidationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    const loadCaseData = async () => {
      setIsLoading(true);
      
      // Mock data
      setTimeout(() => {
        setCaseData({
          id: 'case-001',
          title: 'Smith vs. Johnson Contract Dispute',
          mode: 'demonstrative',
          jurisdiction: 'US-Federal',
          status: 'in_review',
          createdAt: new Date('2024-01-15'),
          updatedAt: new Date('2024-01-20'),
          createdBy: 'John Attorney',
          evidenceCount: 25,
          storyboardCount: 3,
          renderCount: 1,
          validationStatus: 'valid',
          coveragePercentage: 95
        });

        setEvidenceSummary({
          total: 25,
          byType: {
            documents: 12,
            photos: 8,
            videos: 3,
            audio: 2
          },
          recent: [
            {
              id: 'ev-001',
              name: 'Contract_Amendment.pdf',
              type: 'document',
              uploadedAt: new Date('2024-01-20T10:30:00'),
              thumbnail: '/thumbnails/doc-thumb.png'
            },
            {
              id: 'ev-002',
              name: 'Meeting_Recording.mp3',
              type: 'audio',
              uploadedAt: new Date('2024-01-19T14:15:00')
            },
            {
              id: 'ev-003',
              name: 'Evidence_Photo_001.jpg',
              type: 'photo',
              uploadedAt: new Date('2024-01-19T09:45:00'),
              thumbnail: '/thumbnails/photo-thumb.jpg'
            }
          ]
        });

        setTimelinePreview({
          totalDuration: 180, // 3 minutes
          beatCount: 15,
          evidenceAnchors: 12,
          disputedBeats: 2,
          confidenceScore: 0.87
        });

        setValidationStatus({
          isValid: true,
          errors: [],
          warnings: ['Beat 7 has low confidence score'],
          coveragePercentage: 95,
          lastValidated: new Date('2024-01-20T15:30:00')
        });

        setIsLoading(false);
      }, 1000);
    };

    loadCaseData();
  }, []);

  const getStatusColor = (status: Case['status']) => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-100';
      case 'in_review': return 'text-blue-600 bg-blue-100';
      case 'draft': return 'text-yellow-600 bg-yellow-100';
      case 'locked': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getModeColor = (mode: Case['mode']) => {
    return mode === 'demonstrative' 
      ? 'text-purple-600 bg-purple-100' 
      : 'text-orange-600 bg-orange-100';
  };

  const getEvidenceIcon = (type: string) => {
    switch (type) {
      case 'document': return <DocumentTextIcon className="w-5 h-5 text-blue-500" />;
      case 'photo': return <PhotoIcon className="w-5 h-5 text-green-500" />;
      case 'video': return <VideoCameraIcon className="w-5 h-5 text-purple-500" />;
      case 'audio': return <SpeakerWaveIcon className="w-5 h-5 text-orange-500" />;
      default: return <DocumentTextIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Case not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">{caseData.title}</h1>
            <div className="flex items-center space-x-4">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(caseData.status)}`}>
                {caseData.status.replace('_', ' ').toUpperCase()}
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getModeColor(caseData.mode)}`}>
                {caseData.mode.toUpperCase()}
              </span>
              <span className="text-sm text-gray-600">
                Jurisdiction: {caseData.jurisdiction}
              </span>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center space-x-2">
              <PlayIcon className="w-4 h-4" />
              <span>Preview Render</span>
            </button>
            <button className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600">
              Export Case
            </button>
          </div>
        </div>
        
        <div className="mt-4 text-sm text-gray-600">
          Created by {caseData.createdBy} on {caseData.createdAt.toLocaleDateString()}
          • Last updated {caseData.updatedAt.toLocaleDateString()}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Evidence Items</p>
              <p className="text-2xl font-bold text-gray-800">{caseData.evidenceCount}</p>
            </div>
            <DocumentTextIcon className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Storyboards</p>
              <p className="text-2xl font-bold text-gray-800">{caseData.storyboardCount}</p>
            </div>
            <ChartBarIcon className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Renders</p>
              <p className="text-2xl font-bold text-gray-800">{caseData.renderCount}</p>
            </div>
            <VideoCameraIcon className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Coverage</p>
              <p className="text-2xl font-bold text-gray-800">{caseData.coveragePercentage}%</p>
            </div>
            <CheckCircleIcon className="w-8 h-8 text-green-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Evidence Summary */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">Evidence Summary</h2>
          </div>
          <div className="p-6">
            {evidenceSummary && (
              <>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="text-center">
                    <DocumentTextIcon className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-gray-800">{evidenceSummary.byType.documents}</p>
                    <p className="text-sm text-gray-600">Documents</p>
                  </div>
                  <div className="text-center">
                    <PhotoIcon className="w-8 h-8 text-green-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-gray-800">{evidenceSummary.byType.photos}</p>
                    <p className="text-sm text-gray-600">Photos</p>
                  </div>
                  <div className="text-center">
                    <VideoCameraIcon className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-gray-800">{evidenceSummary.byType.videos}</p>
                    <p className="text-sm text-gray-600">Videos</p>
                  </div>
                  <div className="text-center">
                    <SpeakerWaveIcon className="w-8 h-8 text-orange-500 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-gray-800">{evidenceSummary.byType.audio}</p>
                    <p className="text-sm text-gray-600">Audio</p>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Recent Uploads</h3>
                  <div className="space-y-2">
                    {evidenceSummary.recent.map((item) => (
                      <div key={item.id} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded">
                        {getEvidenceIcon(item.type)}
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-800">{item.name}</p>
                          <p className="text-xs text-gray-500">
                            {item.type} • {item.uploadedAt.toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Timeline Preview */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">Timeline Preview</h2>
          </div>
          <div className="p-6">
            {timelinePreview && (
              <>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Total Duration</span>
                    <span className="font-medium">{Math.floor(timelinePreview.totalDuration / 60)}m {timelinePreview.totalDuration % 60}s</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Beats</span>
                    <span className="font-medium">{timelinePreview.beatCount}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Evidence Anchors</span>
                    <span className="font-medium">{timelinePreview.evidenceAnchors}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Disputed Beats</span>
                    <span className="font-medium text-red-600">{timelinePreview.disputedBeats}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Confidence Score</span>
                    <span className="font-medium">{Math.round(timelinePreview.confidenceScore * 100)}%</span>
                  </div>
                </div>

                <div className="mt-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-800">Confidence Distribution</span>
                  </div>
                  <div className="bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${timelinePreview.confidenceScore * 100}%` }}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Validation Status */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">Validation Status</h2>
          </div>
          <div className="p-6">
            {validationStatus && (
              <>
                <div className="flex items-center space-x-3 mb-4">
                  {validationStatus.isValid ? (
                    <CheckCircleIcon className="w-6 h-6 text-green-500" />
                  ) : (
                    <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />
                  )}
                  <span className={`font-medium ${
                    validationStatus.isValid ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {validationStatus.isValid ? 'Valid' : 'Invalid'}
                  </span>
                </div>

                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-gray-600">Coverage</span>
                    <div className="mt-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${validationStatus.coveragePercentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">{validationStatus.coveragePercentage}%</span>
                  </div>

                  {validationStatus.warnings.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-yellow-600">Warnings</span>
                      <ul className="text-sm text-yellow-700 mt-1">
                        {validationStatus.warnings.map((warning, index) => (
                          <li key={index}>• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {validationStatus.errors.length > 0 && (
                    <div>
                      <span className="text-sm font-medium text-red-600">Errors</span>
                      <ul className="text-sm text-red-700 mt-1">
                        {validationStatus.errors.map((error, index) => (
                          <li key={index}>• {error}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="text-xs text-gray-500">
                    Last validated: {validationStatus.lastValidated.toLocaleString()}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">Quick Actions</h2>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              <button className="w-full text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">
                <div className="flex items-center space-x-3">
                  <DocumentTextIcon className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-800">Manage Evidence</p>
                    <p className="text-sm text-gray-600">Upload and organize evidence files</p>
                  </div>
                </div>
              </button>

              <button className="w-full text-left p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
                <div className="flex items-center space-x-3">
                  <ChartBarIcon className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="font-medium text-gray-800">Edit Storyboard</p>
                    <p className="text-sm text-gray-600">Create and edit timeline beats</p>
                  </div>
                </div>
              </button>

              <button className="w-full text-left p-3 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors">
                <div className="flex items-center space-x-3">
                  <VideoCameraIcon className="w-5 h-5 text-purple-500" />
                  <div>
                    <p className="font-medium text-gray-800">Start Render</p>
                    <p className="text-sm text-gray-600">Generate video visualization</p>
                  </div>
                </div>
              </button>

              <button className="w-full text-left p-3 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors">
                <div className="flex items-center space-x-3">
                  <UserGroupIcon className="w-5 h-5 text-orange-500" />
                  <div>
                    <p className="font-medium text-gray-800">Collaborate</p>
                    <p className="text-sm text-gray-600">Share with team members</p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CaseOverview;
