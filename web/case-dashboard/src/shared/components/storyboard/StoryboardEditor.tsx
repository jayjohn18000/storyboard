import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';
import {
  DocumentTextIcon,
  EyeIcon,
  CodeBracketIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  ShareIcon
} from '@heroicons/react/24/outline';
import { StoryboardFlowEditor } from '../../../components/storyboard/StoryboardFlowEditor';
import ValidationPanel from '../../../components/storyboard/ValidationPanel';

interface StoryboardBeat {
  id: string;
  timestamp: number;
  description: string;
  actors: string[];
  evidenceAnchors: EvidenceAnchor[];
  confidence: number;
  disputed: boolean;
  duration: number;
}

interface EvidenceAnchor {
  evidenceId: string;
  timestamp?: number;
  pageNumber?: number;
  description: string;
}

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

interface StoryboardEditorProps {
  initialContent: string;
  evidenceList: Array<{ id: string; name: string; type: string }>;
  onContentChange: (content: string) => void;
  onValidationChange: (isValid: boolean, errors: string[]) => void;
  onBeatsExtracted: (beats: StoryboardBeat[]) => void;
  useFlowEditor?: boolean;
}

const StoryDocSyntaxHighlighter: React.FC<{ content: string }> = ({ content }) => {
  // Simple syntax highlighting for StoryDoc format
  const highlightSyntax = (text: string) => {
    const patterns = [
      { regex: /@time\[([^\]]+)\]/g, className: 'text-blue-600 font-semibold' },
      { regex: /#actor\[([^\]]+)\]/g, className: 'text-green-600 font-semibold' },
      { regex: /~action\[([^\]]+)\]/g, className: 'text-purple-600 font-semibold' },
      { regex: /\^evidence\[([^\]]+)\]/g, className: 'text-red-600 font-semibold' },
      { regex: /\/\*.*?\*\//g, className: 'text-gray-500 italic' },
      { regex: /\/\/.*$/gm, className: 'text-gray-500 italic' }
    ];

    let highlighted = text;
    patterns.forEach(({ regex, className }) => {
      highlighted = highlighted.replace(regex, `<span class="${className}">$&</span>`);
    });

    return highlighted;
  };

  return (
    <div 
      className="prose prose-sm max-w-none p-4 bg-gray-50 rounded border"
      dangerouslySetInnerHTML={{ __html: highlightSyntax(content) }}
    />
  );
};

export const StoryboardEditor: React.FC<StoryboardEditorProps> = ({
  initialContent,
  evidenceList,
  onContentChange,
  onValidationChange,
  onBeatsExtracted,
  useFlowEditor = false
}) => {
  const [content, setContent] = useState(initialContent);
  const [viewMode, setViewMode] = useState<'edit' | 'preview' | 'split'>('split');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [beats, setBeats] = useState<StoryboardBeat[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentBeat, setCurrentBeat] = useState(0);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [showValidationPanel, setShowValidationPanel] = useState(false);
  const editorRef = useRef<any>(null);

  // Parse StoryDoc content into beats
  const parseStoryDoc = useCallback((text: string): StoryboardBeat[] => {
    const lines = text.split('\n');
    const parsedBeats: StoryboardBeat[] = [];
    let currentBeat: Partial<StoryboardBeat> = {};
    let beatIndex = 0;

    for (const line of lines) {
      const trimmedLine = line.trim();
      
      if (trimmedLine.startsWith('@time[')) {
        // Save previous beat if exists
        if (currentBeat.description) {
          parsedBeats.push({
            id: crypto.randomUUID(),
            timestamp: currentBeat.timestamp || beatIndex * 5,
            description: currentBeat.description || '',
            actors: currentBeat.actors || [],
            evidenceAnchors: currentBeat.evidenceAnchors || [],
            confidence: currentBeat.confidence || 0.8,
            disputed: currentBeat.disputed || false,
            duration: currentBeat.duration || 3
          });
          beatIndex++;
        }
        
        // Start new beat
        const timeMatch = trimmedLine.match(/@time\[([^\]]+)\]/);
        currentBeat = {
          timestamp: timeMatch ? parseFloat(timeMatch[1]) : beatIndex * 5,
          actors: [],
          evidenceAnchors: [],
          confidence: 0.8,
          disputed: false,
          duration: 3
        };
      } else if (trimmedLine.startsWith('#actor[')) {
        const actorMatch = trimmedLine.match(/#actor\[([^\]]+)\]/);
        if (actorMatch && currentBeat.actors) {
          currentBeat.actors.push(actorMatch[1]);
        }
      } else if (trimmedLine.startsWith('~action[')) {
        const actionMatch = trimmedLine.match(/~action\[([^\]]+)\]/);
        if (actionMatch) {
          currentBeat.description = actionMatch[1];
        }
      } else if (trimmedLine.startsWith('^evidence[')) {
        const evidenceMatch = trimmedLine.match(/\^evidence\[([^\]]+)\]/);
        if (evidenceMatch && currentBeat.evidenceAnchors) {
          const evidenceRef = evidenceMatch[1];
          const [evidenceId, timestamp] = evidenceRef.split('@');
          
          currentBeat.evidenceAnchors.push({
            evidenceId,
            timestamp: timestamp ? parseFloat(timestamp) : undefined,
            description: `Reference to ${evidenceId}`
          });
        }
      } else if (trimmedLine && !trimmedLine.startsWith('//') && !trimmedLine.startsWith('/*')) {
        // Regular description line
        if (currentBeat.description) {
          currentBeat.description += ' ' + trimmedLine;
        } else {
          currentBeat.description = trimmedLine;
        }
      }
    }

    // Add final beat
    if (currentBeat.description) {
      parsedBeats.push({
        id: crypto.randomUUID(),
        timestamp: currentBeat.timestamp || beatIndex * 5,
        description: currentBeat.description || '',
        actors: currentBeat.actors || [],
        evidenceAnchors: currentBeat.evidenceAnchors || [],
        confidence: currentBeat.confidence || 0.8,
        disputed: currentBeat.disputed || false,
        duration: currentBeat.duration || 3
      });
    }

    return parsedBeats;
  }, []);

  // Enhanced validation with detailed results
  const validateContent = useCallback(async (text: string) => {
    setIsValidating(true);
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    try {
      // Parse content
      const parsedBeats = parseStoryDoc(text);

      // Validate syntax
      const lines = text.split('\n');
      lines.forEach((line, index) => {
        const trimmedLine = line.trim();
        
        // Check for malformed syntax
        if (trimmedLine.includes('@time[') && !trimmedLine.match(/@time\[([^\]]+)\]/)) {
          errors.push(`Line ${index + 1}: Malformed @time syntax`);
        }
        if (trimmedLine.includes('#actor[') && !trimmedLine.match(/#actor\[([^\]]+)\]/)) {
          errors.push(`Line ${index + 1}: Malformed #actor syntax`);
        }
        if (trimmedLine.includes('~action[') && !trimmedLine.match(/~action\[([^\]]+)\]/)) {
          errors.push(`Line ${index + 1}: Malformed ~action syntax`);
        }
        if (trimmedLine.includes('^evidence[') && !trimmedLine.match(/\^evidence\[([^\]]+)\]/)) {
          errors.push(`Line ${index + 1}: Malformed ^evidence syntax`);
        }
      });

      // Validate evidence references
      parsedBeats.forEach((beat, beatIndex) => {
        beat.evidenceAnchors.forEach(anchor => {
          const evidence = evidenceList.find(e => e.id === anchor.evidenceId);
          if (!evidence) {
            errors.push(`Beat ${beatIndex + 1}: Evidence ${anchor.evidenceId} not found`);
          }
        });
      });

      // Validate temporal consistency
      for (let i = 1; i < parsedBeats.length; i++) {
        if (parsedBeats[i].timestamp < parsedBeats[i - 1].timestamp + parsedBeats[i - 1].duration) {
          errors.push(`Beat ${i + 1}: Overlaps with previous beat`);
        }
      }

      // Calculate metrics
      const totalDuration = parsedBeats.reduce((sum, beat) => sum + beat.duration, 0);
      const evidenceReferences = parsedBeats.reduce((sum, beat) => sum + beat.evidenceAnchors.length, 0);
      const actorReferences = parsedBeats.reduce((sum, beat) => sum + beat.actors.length, 0);

      // Calculate coverage
      const evidenceCoverage = evidenceList.length > 0 ? 
        Math.round((evidenceReferences / evidenceList.length) * 100) : 0;
      const timelineCoverage = parsedBeats.length > 0 ? 
        Math.round((parsedBeats.filter(b => b.duration > 0).length / parsedBeats.length) * 100) : 0;
      const actorCoverage = parsedBeats.length > 0 ? 
        Math.round((parsedBeats.filter(b => b.actors.length > 0).length / parsedBeats.length) * 100) : 0;

      // Generate suggestions
      if (evidenceCoverage < 50) {
        suggestions.push('Consider adding more evidence references to improve coverage');
      }
      if (timelineCoverage < 80) {
        suggestions.push('Some beats have zero duration - consider adding duration values');
      }
      if (actorCoverage < 60) {
        suggestions.push('Consider adding more actor references to improve narrative clarity');
      }
      if (parsedBeats.length < 3) {
        suggestions.push('Consider adding more beats to create a more complete storyboard');
      }

      // Generate warnings
      if (parsedBeats.some(beat => beat.confidence < 0.7)) {
        warnings.push('Some beats have low confidence scores');
      }
      if (parsedBeats.some(beat => beat.disputed)) {
        warnings.push('Some beats are marked as disputed');
      }

      const result: ValidationResult = {
        isValid: errors.length === 0,
        errors,
        warnings,
        suggestions,
        coverage: {
          evidenceCoverage,
          timelineCoverage,
          actorCoverage
        },
        metrics: {
          totalBeats: parsedBeats.length,
          totalDuration,
          evidenceReferences,
          actorReferences
        }
      };

      setValidationResult(result);
      setBeats(parsedBeats);
      onBeatsExtracted(parsedBeats);
    } catch (error) {
      errors.push(`Parse error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    setValidationErrors(errors);
    onValidationChange(errors.length === 0, errors);
    setIsValidating(false);
  }, [parseStoryDoc, evidenceList, onValidationChange, onBeatsExtracted]);

  // Handle content changes
  const handleContentChange = useCallback((value: string | undefined) => {
    const newContent = value || '';
    setContent(newContent);
    onContentChange(newContent);
    
    // Debounced validation
    const timeoutId = setTimeout(() => {
      validateContent(newContent);
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [onContentChange, validateContent]);

  // Auto-link evidence references
  const insertEvidenceReference = (evidenceId: string) => {
    if (editorRef.current) {
      const selection = editorRef.current.getSelection();
      const evidenceRef = `^evidence[${evidenceId}]`;
      editorRef.current.executeEdits('insert-evidence', [{
        range: selection,
        text: evidenceRef,
        forceMoveMarkers: true
      }]);
    }
  };

  // Insert template
  const insertTemplate = () => {
    const template = `@time[0.0] #actor[John] ~action[enters room] ^evidence[doc-001]
John walks into the courtroom and takes his seat.

@time[5.0] #actor[Judge] ~action[addresses court] ^evidence[audio-001@00:30]
The judge calls the court to order and begins the proceedings.

@time[10.0] #actor[Lawyer] ~action[presents evidence] ^evidence[doc-002@page:5]
The lawyer presents the key evidence to the jury.`;

    if (editorRef.current) {
      editorRef.current.setValue(template);
    }
  };

  // Playback simulation
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && beats.length > 0) {
      interval = setInterval(() => {
        setCurrentBeat(prev => {
          const nextBeat = prev + 1;
          if (nextBeat >= beats.length) {
            setIsPlaying(false);
            return 0;
          }
          return nextBeat;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, beats.length]);

  // If useFlowEditor is true, render the Flow Editor
  if (useFlowEditor) {
    return (
      <StoryboardFlowEditor
        initialContent={content}
        evidenceList={evidenceList}
        onContentChange={onContentChange}
        onValidationChange={onValidationChange}
        onBeatsExtracted={onBeatsExtracted}
      />
    );
  }

  return (
    <div className="w-full h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <DocumentTextIcon className="w-5 h-5 text-gray-600" />
            <span className="font-medium text-gray-800">Storyboard Editor</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setViewMode('edit')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'edit' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              <CodeBracketIcon className="w-4 h-4 inline mr-1" />
              Edit
            </button>
            <button
              onClick={() => setViewMode('preview')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'preview' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              <EyeIcon className="w-4 h-4 inline mr-1" />
              Preview
            </button>
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'split' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              Split
            </button>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={insertTemplate}
            className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600"
          >
            Insert Template
          </button>
          
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center space-x-1 px-3 py-1 bg-purple-500 text-white text-sm rounded hover:bg-purple-600"
          >
            {isPlaying ? (
              <PauseIcon className="w-4 h-4" />
            ) : (
              <PlayIcon className="w-4 h-4" />
            )}
            <span>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>
          
          {isValidating && (
            <div className="flex items-center space-x-1">
              <ArrowPathIcon className="w-4 h-4 animate-spin text-blue-500" />
              <span className="text-sm text-gray-600">Validating...</span>
            </div>
          )}
          
          {validationErrors.length === 0 && !isValidating ? (
            <div className="flex items-center space-x-1 text-green-600">
              <CheckCircleIcon className="w-4 h-4" />
              <span className="text-sm">Valid</span>
            </div>
          ) : validationErrors.length > 0 ? (
            <div className="flex items-center space-x-1 text-red-600">
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span className="text-sm">{validationErrors.length} errors</span>
            </div>
          ) : null}
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="p-4 bg-red-50 border-b">
          <h4 className="font-medium text-red-800 mb-2">Validation Errors:</h4>
          <ul className="text-sm text-red-700 space-y-1">
            {validationErrors.map((error, index) => (
              <li key={index}>• {error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Editor Content */}
      <div className="flex-1 flex">
        {/* Editor */}
        {(viewMode === 'edit' || viewMode === 'split') && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col`}>
            <div className="flex-1">
              <Editor
                height="100%"
                defaultLanguage="plaintext"
                value={content}
                onChange={handleContentChange}
                onMount={(editor) => {
                  editorRef.current = editor;
                }}
                options={{
                  minimap: { enabled: false },
                  wordWrap: 'on',
                  lineNumbers: 'on',
                  folding: true,
                  scrollBeyondLastLine: false,
                  automaticLayout: true
                }}
              />
            </div>
          </div>
        )}

        {/* Preview */}
        {(viewMode === 'preview' || viewMode === 'split') && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col border-l`}>
            <div className="p-4 bg-gray-50 border-b">
              <h4 className="font-medium text-gray-800">Preview</h4>
            </div>
            <div className="flex-1 overflow-auto">
              <StoryDocSyntaxHighlighter content={content} />
            </div>
          </div>
        )}
      </div>

      {/* Evidence Picker */}
      <div className="p-4 bg-gray-50 border-t">
        <h4 className="font-medium text-gray-800 mb-2">Insert Evidence Reference:</h4>
        <div className="flex flex-wrap gap-2">
          {evidenceList.map(evidence => (
            <button
              key={evidence.id}
              onClick={() => insertEvidenceReference(evidence.id)}
              className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded hover:bg-blue-200"
            >
              {evidence.name} ({evidence.type})
            </button>
          ))}
        </div>
      </div>

      {/* Playback Indicator */}
      {isPlaying && beats.length > 0 && (
        <div className="p-4 bg-purple-50 border-t">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-purple-800">
              Playing Beat {currentBeat + 1} of {beats.length}
            </span>
            <div className="flex-1 bg-purple-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                // eslint-disable-next-line react/forbid-dom-props
                style={{ width: `${((currentBeat + 1) / beats.length) * 100}%` }}
              />
            </div>
            <span className="text-sm text-purple-600">
              {beats[currentBeat]?.timestamp.toFixed(1)}s
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryboardEditor;
