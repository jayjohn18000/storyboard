import React from 'react';
import { EvidenceUploader } from '../../../shared/components/evidence/EvidenceUploader';

export const EvidencePage: React.FC = () => {
  const handleUploadComplete = (files: any[]) => {
    console.log('Upload completed:', files);
  };

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Evidence Management</h1>
        <p className="text-gray-600">Upload and manage evidence files for your cases</p>
      </div>
      
      <EvidenceUploader
        onUploadComplete={handleUploadComplete}
        onUploadError={handleUploadError}
      />
    </div>
  );
};
