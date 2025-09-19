import React from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ClockIcon,
  DocumentTextIcon,
  LinkIcon,
  UserIcon
} from '@heroicons/react/24/outline';

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
  coverage: {
    evidenceCoverage: number;
    timelineCoverage: number;
    actorCoverage: number;
  };
  metrics: {
    totalBeats: number;
    totalDuration: number;
    evidenceReferences: number;
    actorReferences: number;
  };
}

interface ValidationPanelProps {
  validationResult: ValidationResult | null;
  isLoading: boolean;
  onFixSuggestion?: (suggestion: string) => void;
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({
  validationResult,
  isLoading,
  onFixSuggestion
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          <span className="text-sm text-gray-600">Validating storyboard...</span>
        </div>
      </div>
    );
  }

  if (!validationResult) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="text-center text-gray-500">
          <DocumentTextIcon className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p>No validation results available</p>
        </div>
      </div>
    );
  }

  const getStatusIcon = () => {
    if (validationResult.isValid) {
      return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
    } else if (validationResult.errors.length > 0) {
      return <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />;
    } else {
      return <InformationCircleIcon className="w-6 h-6 text-yellow-500" />;
    }
  };

  const getStatusText = () => {
    if (validationResult.isValid) {
      return 'Valid';
    } else if (validationResult.errors.length > 0) {
      return 'Invalid';
    } else {
      return 'Has Warnings';
    }
  };

  const getStatusColor = () => {
    if (validationResult.isValid) {
      return 'text-green-600 bg-green-100';
    } else if (validationResult.errors.length > 0) {
      return 'text-red-600 bg-red-100';
    } else {
      return 'text-yellow-600 bg-yellow-100';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <h3 className="font-medium text-gray-800">Validation Results</h3>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}>
                {getStatusText()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="p-4 border-b">
        <h4 className="font-medium text-gray-800 mb-3">Storyboard Metrics</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center space-x-2">
            <ClockIcon className="w-4 h-4 text-blue-500" />
            <div>
              <p className="text-sm text-gray-600">Total Duration</p>
              <p className="text-lg font-semibold text-gray-800">
                {Math.floor(validationResult.metrics.totalDuration / 60)}m {validationResult.metrics.totalDuration % 60}s
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <DocumentTextIcon className="w-4 h-4 text-green-500" />
            <div>
              <p className="text-sm text-gray-600">Total Beats</p>
              <p className="text-lg font-semibold text-gray-800">{validationResult.metrics.totalBeats}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <LinkIcon className="w-4 h-4 text-purple-500" />
            <div>
              <p className="text-sm text-gray-600">Evidence References</p>
              <p className="text-lg font-semibold text-gray-800">{validationResult.metrics.evidenceReferences}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <UserIcon className="w-4 h-4 text-orange-500" />
            <div>
              <p className="text-sm text-gray-600">Actor References</p>
              <p className="text-lg font-semibold text-gray-800">{validationResult.metrics.actorReferences}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Coverage */}
      <div className="p-4 border-b">
        <h4 className="font-medium text-gray-800 mb-3">Coverage Analysis</h4>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Evidence Coverage</span>
              <span className="text-gray-800">{validationResult.coverage.evidenceCoverage}%</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${validationResult.coverage.evidenceCoverage}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Timeline Coverage</span>
              <span className="text-gray-800">{validationResult.coverage.timelineCoverage}%</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${validationResult.coverage.timelineCoverage}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Actor Coverage</span>
              <span className="text-gray-800">{validationResult.coverage.actorCoverage}%</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${validationResult.coverage.actorCoverage}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Errors */}
      {validationResult.errors.length > 0 && (
        <div className="p-4 border-b">
          <h4 className="font-medium text-red-800 mb-3 flex items-center">
            <ExclamationTriangleIcon className="w-4 h-4 mr-2" />
            Errors ({validationResult.errors.length})
          </h4>
          <ul className="space-y-2">
            {validationResult.errors.map((error, index) => (
              <li key={index} className="text-sm text-red-700 flex items-start">
                <span className="text-red-500 mr-2">•</span>
                <span>{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {validationResult.warnings.length > 0 && (
        <div className="p-4 border-b">
          <h4 className="font-medium text-yellow-800 mb-3 flex items-center">
            <ExclamationTriangleIcon className="w-4 h-4 mr-2" />
            Warnings ({validationResult.warnings.length})
          </h4>
          <ul className="space-y-2">
            {validationResult.warnings.map((warning, index) => (
              <li key={index} className="text-sm text-yellow-700 flex items-start">
                <span className="text-yellow-500 mr-2">•</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {validationResult.suggestions.length > 0 && (
        <div className="p-4">
          <h4 className="font-medium text-blue-800 mb-3 flex items-center">
            <InformationCircleIcon className="w-4 h-4 mr-2" />
            Suggestions ({validationResult.suggestions.length})
          </h4>
          <ul className="space-y-2">
            {validationResult.suggestions.map((suggestion, index) => (
              <li key={index} className="text-sm text-blue-700 flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span className="flex-1">{suggestion}</span>
                {onFixSuggestion && (
                  <button
                    onClick={() => onFixSuggestion(suggestion)}
                    className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded hover:bg-blue-200"
                  >
                    Fix
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Success Message */}
      {validationResult.isValid && validationResult.errors.length === 0 && validationResult.warnings.length === 0 && (
        <div className="p-4">
          <div className="text-center text-green-600">
            <CheckCircleIcon className="w-8 h-8 mx-auto mb-2" />
            <p className="font-medium">Storyboard is valid!</p>
            <p className="text-sm text-gray-600">No errors or warnings found.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationPanel;
