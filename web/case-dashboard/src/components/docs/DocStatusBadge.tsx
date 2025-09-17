import React from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

export type DocStatus = 'UPLOADING' | 'PARSING' | 'EMBEDDING' | 'INDEXED' | 'ERROR';

interface DocStatusBadgeProps {
  status: DocStatus;
  className?: string;
}

export const DocStatusBadge: React.FC<DocStatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusConfig = (status: DocStatus) => {
    switch (status) {
      case 'UPLOADING':
        return {
          icon: ArrowPathIcon,
          text: 'Uploading',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-800',
          iconColor: 'text-blue-600',
          animate: true
        };
      case 'PARSING':
        return {
          icon: ArrowPathIcon,
          text: 'Parsing',
          bgColor: 'bg-yellow-100',
          textColor: 'text-yellow-800',
          iconColor: 'text-yellow-600',
          animate: true
        };
      case 'EMBEDDING':
        return {
          icon: ArrowPathIcon,
          text: 'Embedding',
          bgColor: 'bg-purple-100',
          textColor: 'text-purple-800',
          iconColor: 'text-purple-600',
          animate: true
        };
      case 'INDEXED':
        return {
          icon: CheckCircleIcon,
          text: 'Indexed',
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          iconColor: 'text-green-600',
          animate: false
        };
      case 'ERROR':
        return {
          icon: ExclamationTriangleIcon,
          text: 'Error',
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          iconColor: 'text-red-600',
          animate: false
        };
      default:
        return {
          icon: ClockIcon,
          text: 'Unknown',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          iconColor: 'text-gray-600',
          animate: false
        };
    }
  };

  const config = getStatusConfig(status);
  const IconComponent = config.icon;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} ${className}`}>
      <IconComponent 
        className={`w-3 h-3 mr-1 ${config.iconColor} ${config.animate ? 'animate-spin' : ''}`} 
      />
      {config.text}
    </span>
  );
};

export default DocStatusBadge;
