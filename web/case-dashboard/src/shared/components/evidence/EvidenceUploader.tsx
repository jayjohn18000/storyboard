import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  CloudArrowUpIcon, 
  DocumentIcon, 
  PhotoIcon, 
  VideoCameraIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface EvidenceFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  sha256?: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
  metadata?: {
    caseId?: string;
    description?: string;
    chainOfCustody?: string[];
  };
}

interface EvidenceUploaderProps {
  caseId?: string;
  onUploadComplete: (files: EvidenceFile[]) => void;
  onUploadError: (error: string) => void;
  maxFileSize?: number;
  acceptedTypes?: string[];
  multiple?: boolean;
}

export const EvidenceUploader: React.FC<EvidenceUploaderProps> = ({
  caseId,
  onUploadComplete,
  onUploadError,
  maxFileSize = 100 * 1024 * 1024, // 100MB
  acceptedTypes = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.mp4', '.mp3', '.wav'],
  multiple = true
}) => {
  const [files, setFiles] = useState<EvidenceFile[]>([]);
  const [isCalculatingHash, setIsCalculatingHash] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const calculateSHA256 = async (file: File): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsCalculatingHash(true);
    
    try {
      const newFiles: EvidenceFile[] = await Promise.all(
        acceptedFiles.map(async (file) => {
          // Validate file size
          if (file.size > maxFileSize) {
            throw new Error(`File ${file.name} exceeds maximum size of ${maxFileSize / (1024 * 1024)}MB`);
          }

          // Calculate SHA-256 hash
          const sha256 = await calculateSHA256(file);
          
          return {
            id: crypto.randomUUID(),
            file,
            name: file.name,
            size: file.size,
            type: file.type,
            sha256,
            status: 'uploading' as const,
            progress: 0,
            metadata: {
              caseId,
              description: '',
              chainOfCustody: []
            }
          };
        })
      );

      setFiles(prev => [...prev, ...newFiles]);
      
      // Upload files
      for (const file of newFiles) {
        await uploadFile(file);
      }
      
      onUploadComplete(newFiles);
    } catch (error) {
      onUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsCalculatingHash(false);
    }
  }, [maxFileSize, caseId, onUploadComplete, onUploadError]);

  const uploadFile = async (file: EvidenceFile) => {
    try {
      // Create FormData for upload
      const formData = new FormData();
      formData.append('file', file.file);
      if (file.metadata?.caseId) formData.append('caseId', file.metadata.caseId);
      if (file.metadata?.description) formData.append('description', file.metadata.description);
      if (file.metadata?.chainOfCustody) formData.append('chainOfCustody', JSON.stringify(file.metadata.chainOfCustody));

      // Upload with progress tracking
      const response = await fetch('/api/v1/evidence/upload', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('legal-sim-token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Update file status
      setFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { ...f, progress: 100, status: 'completed' }
          : f
      ));

      return result;
    } catch (error) {
      setFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { ...f, status: 'error', error: error instanceof Error ? error.message : 'Upload failed' }
          : f
      ));
      throw error;
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => {
      acc[type] = [];
      return acc;
    }, {} as Record<string, string[]>),
    multiple,
    disabled: isCalculatingHash
  });

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const updateMetadata = (fileId: string, metadata: Partial<EvidenceFile['metadata']>) => {
    setFiles(prev => prev.map(f => 
      f.id === fileId 
        ? { ...f, metadata: { ...f.metadata, ...metadata } }
        : f
    ));
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <PhotoIcon className="w-8 h-8 text-blue-500" />;
    if (type.startsWith('video/')) return <VideoCameraIcon className="w-8 h-8 text-purple-500" />;
    if (type.includes('pdf') || type.includes('document')) return <DocumentIcon className="w-8 h-8 text-red-500" />;
    return <DocumentIcon className="w-8 h-8 text-gray-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${isCalculatingHash ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} ref={fileInputRef} />
        <CloudArrowUpIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          {isDragActive ? 'Drop files here' : 'Drag & drop evidence files here'}
        </p>
        <p className="text-sm text-gray-500 mb-4">
          or click to browse files
        </p>
        <p className="text-xs text-gray-400">
          Accepted formats: {acceptedTypes.join(', ')} (Max {maxFileSize / (1024 * 1024)}MB)
        </p>
        {isCalculatingHash && (
          <div className="mt-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-sm text-gray-500 mt-2">Calculating file integrity...</p>
          </div>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Uploaded Files</h3>
          {files.map((file) => (
            <div key={file.id} className="bg-white border rounded-lg p-4 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getFileIcon(file.type)}
                  <div>
                    <p className="font-medium text-gray-800">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(file.size)} • {file.type}
                    </p>
                    {file.sha256 && (
                      <p className="text-xs text-gray-400 font-mono">
                        SHA-256: {file.sha256.substring(0, 16)}...
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {/* Status Icon */}
                  {file.status === 'completed' && (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  )}
                  {file.status === 'error' && (
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                  )}
                  {file.status === 'uploading' && (
                    <div className="w-5 h-5">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    </div>
                  )}
                  
                  {/* Progress Bar */}
                  {file.status === 'uploading' && (
                    <div className="w-24">
                      <div className="bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  {/* Remove Button */}
                  <button
                    onClick={() => removeFile(file.id)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                    title="Remove file"
                    aria-label={`Remove ${file.name}`}
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
              
              {/* Metadata Form */}
              <div className="mt-4 pt-4 border-t">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Description
                    </label>
                    <input
                      type="text"
                      value={file.metadata?.description || ''}
                      onChange={(e) => updateMetadata(file.id, { description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Brief description of evidence"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Chain of Custody
                    </label>
                    <input
                      type="text"
                      value={file.metadata?.chainOfCustody?.join(', ') || ''}
                      onChange={(e) => updateMetadata(file.id, { 
                        chainOfCustody: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Comma-separated list of custodians"
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EvidenceUploader;
