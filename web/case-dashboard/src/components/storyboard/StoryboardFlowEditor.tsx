/* eslint-disable react/forbid-dom-props */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  NodeTypes,
  EdgeTypes,
  ReactFlowProvider,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
import './StoryboardFlowEditor.css';
import {
  DocumentTextIcon,
  EyeIcon,
  CodeBracketIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  PlusIcon,
  TrashIcon,
  LinkIcon,
  ClockIcon,
  UserIcon,
  DocumentIcon
} from '@heroicons/react/24/outline';

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

interface StoryboardFlowEditorProps {
  initialContent: string;
  evidenceList: Array<{ id: string; name: string; type: string }>;
  onContentChange: (content: string) => void;
  onValidationChange: (isValid: boolean, errors: string[]) => void;
  onBeatsExtracted: (beats: StoryboardBeat[]) => void;
}

// Custom Node Types
const BeatNode: React.FC<{ data: any }> = ({ data }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [description, setDescription] = useState(data.description);

  const handleSave = () => {
    data.onUpdate({ ...data, description });
    setIsEditing(false);
  };

  return (
    <div className="bg-white border-2 border-gray-300 rounded-lg p-4 min-w-[200px] shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <ClockIcon className="w-4 h-4 text-blue-500" />
          <span className="text-sm font-medium text-gray-700">
            {data.timestamp}s
          </span>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-gray-400 hover:text-gray-600"
            title="Edit beat"
          >
            <DocumentTextIcon className="w-3 h-3" />
          </button>
          <button
            onClick={() => data.onDelete(data.id)}
            className="text-gray-400 hover:text-red-600"
            title="Delete beat"
          >
            <TrashIcon className="w-3 h-3" />
          </button>
        </div>
      </div>
      
      {isEditing ? (
        <div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded p-2 mb-2"
            rows={3}
            placeholder="Enter beat description..."
            aria-label="Beat description"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleSave}
              className="px-2 py-1 bg-blue-500 text-white text-xs rounded"
            >
              Save
            </button>
            <button
              onClick={() => {
                setDescription(data.description);
                setIsEditing(false);
              }}
              className="px-2 py-1 bg-gray-500 text-white text-xs rounded"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-800 mb-2">{data.description}</p>
          
          {data.actors && data.actors.length > 0 && (
            <div className="mb-2">
              <div className="flex items-center space-x-1 mb-1">
                <UserIcon className="w-3 h-3 text-green-500" />
                <span className="text-xs text-gray-600">Actors:</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {data.actors.map((actor: string, index: number) => (
                  <span
                    key={index}
                    className="px-1 py-0.5 bg-green-100 text-green-800 text-xs rounded"
                  >
                    {actor}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {data.evidenceAnchors && data.evidenceAnchors.length > 0 && (
            <div>
              <div className="flex items-center space-x-1 mb-1">
                <DocumentIcon className="w-3 h-3 text-red-500" />
                <span className="text-xs text-gray-600">Evidence:</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {data.evidenceAnchors.map((anchor: EvidenceAnchor, index: number) => (
                  <span
                    key={index}
                    className="px-1 py-0.5 bg-red-100 text-red-800 text-xs rounded"
                  >
                    {anchor.evidenceId}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Duration: {data.duration}s
            </span>
            <div className="flex items-center space-x-1">
              <span className="text-xs text-gray-500">
                Confidence: {Math.round(data.confidence * 100)}%
              </span>
              {data.disputed && (
                <ExclamationTriangleIcon className="w-3 h-3 text-yellow-500" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const EvidenceNode: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-3 min-w-[150px] shadow-sm">
      <div className="flex items-center space-x-2 mb-2">
        <DocumentIcon className="w-4 h-4 text-blue-500" />
        <span className="text-sm font-medium text-blue-800">{data.name}</span>
      </div>
      <p className="text-xs text-blue-700">{data.type}</p>
    </div>
  );
};

const nodeTypes: NodeTypes = {
  beat: BeatNode,
  evidence: EvidenceNode,
};

const edgeTypes: EdgeTypes = {};

export const StoryboardFlowEditor: React.FC<StoryboardFlowEditorProps> = ({
  initialContent,
  evidenceList,
  onContentChange,
  onValidationChange,
  onBeatsExtracted
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [viewMode, setViewMode] = useState<'flow' | 'text' | 'split'>('flow');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentBeat, setCurrentBeat] = useState(0);
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null);

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

  // Convert beats to React Flow nodes and edges
  const beatsToFlow = useCallback((beats: StoryboardBeat[]) => {
    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];

    // Create beat nodes
    beats.forEach((beat, index) => {
      flowNodes.push({
        id: beat.id,
        type: 'beat',
        position: { x: index * 250, y: 0 },
        data: {
          ...beat,
          onUpdate: (updatedBeat: StoryboardBeat) => {
            const updatedBeats = beats.map(b => b.id === updatedBeat.id ? updatedBeat : b);
            onBeatsExtracted(updatedBeats);
            updateContentFromBeats(updatedBeats);
          },
          onDelete: (beatId: string) => {
            const updatedBeats = beats.filter(b => b.id !== beatId);
            onBeatsExtracted(updatedBeats);
            updateContentFromBeats(updatedBeats);
          }
        }
      });

      // Create edges between consecutive beats
      if (index > 0) {
        flowEdges.push({
          id: `edge-${beats[index - 1].id}-${beat.id}`,
          source: beats[index - 1].id,
          target: beat.id,
          type: 'smoothstep',
          animated: true
        });
      }
    });

    // Create evidence nodes
    const evidenceIds = new Set<string>();
    beats.forEach(beat => {
      beat.evidenceAnchors.forEach(anchor => {
        evidenceIds.add(anchor.evidenceId);
      });
    });

    evidenceIds.forEach((evidenceId, index) => {
      const evidence = evidenceList.find(e => e.id === evidenceId);
      if (evidence) {
        flowNodes.push({
          id: `evidence-${evidenceId}`,
          type: 'evidence',
          position: { x: Number(index) * 200, y: 200 },
          data: evidence
        });
      }
    });

    // Create edges from beats to evidence
    beats.forEach(beat => {
      beat.evidenceAnchors.forEach(anchor => {
        flowEdges.push({
          id: `evidence-edge-${beat.id}-${anchor.evidenceId}`,
          source: beat.id,
          target: `evidence-${anchor.evidenceId}`,
          type: 'straight',
          // eslint-disable-next-line react/forbid-dom-props
          style: { stroke: '#ef4444', strokeWidth: 2 }
        });
      });
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [evidenceList, onBeatsExtracted]);

  // Update content from beats
  const updateContentFromBeats = useCallback((beats: StoryboardBeat[]) => {
    const content = beats.map(beat => {
      let lines = [`@time[${beat.timestamp}]`];
      
      beat.actors.forEach(actor => {
        lines.push(`#actor[${actor}]`);
      });
      
      if (beat.description) {
        lines.push(`~action[${beat.description}]`);
      }
      
      beat.evidenceAnchors.forEach(anchor => {
        const timestamp = anchor.timestamp ? `@${anchor.timestamp}` : '';
        lines.push(`^evidence[${anchor.evidenceId}${timestamp}]`);
      });
      
      return lines.join('\n');
    }).join('\n\n');
    
    onContentChange(content);
  }, [onContentChange]);

  // Initialize flow from content
  useEffect(() => {
    if (initialContent) {
      const beats = parseStoryDoc(initialContent);
      const { nodes: flowNodes, edges: flowEdges } = beatsToFlow(beats);
      setNodes(flowNodes);
      setEdges(flowEdges);
      onBeatsExtracted(beats);
    }
  }, [initialContent, parseStoryDoc, beatsToFlow, setNodes, setEdges, onBeatsExtracted]);

  // Validate content
  const validateContent = useCallback(async (beats: StoryboardBeat[]) => {
    setIsValidating(true);
    const errors: string[] = [];

    try {
      // Validate beats
      beats.forEach((beat, index) => {
        if (!beat.description || beat.description.trim() === '') {
          errors.push(`Beat ${index + 1}: Missing description`);
        }
        
        if (beat.timestamp < 0) {
          errors.push(`Beat ${index + 1}: Invalid timestamp`);
        }
        
        if (beat.duration <= 0) {
          errors.push(`Beat ${index + 1}: Invalid duration`);
        }
        
        // Check for temporal conflicts
        if (index > 0) {
          const prevBeat = beats[index - 1];
          if (beat.timestamp < prevBeat.timestamp + prevBeat.duration) {
            errors.push(`Beat ${index + 1}: Overlaps with previous beat`);
          }
        }
        
        // Validate evidence references
        beat.evidenceAnchors.forEach(anchor => {
          const evidence = evidenceList.find(e => e.id === anchor.evidenceId);
          if (!evidence) {
            errors.push(`Beat ${index + 1}: Evidence ${anchor.evidenceId} not found`);
          }
        });
      });

      setValidationErrors(errors);
      onValidationChange(errors.length === 0, errors);
    } catch (error) {
      errors.push(`Validation error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setValidationErrors(errors);
      onValidationChange(false, errors);
    } finally {
      setIsValidating(false);
    }
  }, [evidenceList, onValidationChange]);

  // Handle connection creation
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges]
  );

  // Add new beat
  const addBeat = useCallback(() => {
    const newBeat: StoryboardBeat = {
      id: crypto.randomUUID(),
      timestamp: nodes.length * 5,
      description: 'New beat',
      actors: [],
      evidenceAnchors: [],
      confidence: 0.8,
      disputed: false,
      duration: 3
    };

    const beats = parseStoryDoc(initialContent);
    beats.push(newBeat);
    const { nodes: flowNodes, edges: flowEdges } = beatsToFlow(beats);
    setNodes(flowNodes);
    setEdges(flowEdges);
    onBeatsExtracted(beats);
    updateContentFromBeats(beats);
  }, [nodes.length, initialContent, parseStoryDoc, beatsToFlow, setNodes, setEdges, onBeatsExtracted, updateContentFromBeats]);

  // Playback simulation
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && nodes.length > 0) {
      interval = setInterval(() => {
        setCurrentBeat(prev => {
          const nextBeat = prev + 1;
          if (nextBeat >= nodes.length) {
            setIsPlaying(false);
            return 0;
          }
          return nextBeat;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, nodes.length]);

  // Validate when beats change
  useEffect(() => {
    const beats = parseStoryDoc(initialContent);
    validateContent(beats);
  }, [initialContent, parseStoryDoc, validateContent]);

  return (
    <div className="w-full h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <DocumentTextIcon className="w-5 h-5 text-gray-600" />
            <span className="font-medium text-gray-800">Storyboard Flow Editor</span>
          </div>
          
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setViewMode('flow')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'flow' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              Flow
            </button>
            <button
              onClick={() => setViewMode('text')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'text' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              Text
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
            onClick={addBeat}
            className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 flex items-center space-x-1"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Add Beat</span>
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
        {/* Flow Editor */}
        {(viewMode === 'flow' || viewMode === 'split') && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col`}>
            <ReactFlowProvider>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                onInit={(instance) => {
                  reactFlowInstance.current = instance;
                }}
                fitView
              >
                <Controls />
                <Background />
                <MiniMap />
              </ReactFlow>
            </ReactFlowProvider>
          </div>
        )}

        {/* Text Editor */}
        {(viewMode === 'text' || viewMode === 'split') && (
          <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} flex flex-col border-l`}>
            <div className="p-4 bg-gray-50 border-b">
              <h4 className="font-medium text-gray-800">StoryDoc Text</h4>
            </div>
            <div className="flex-1 overflow-auto">
              <pre className="p-4 text-sm font-mono bg-gray-50 whitespace-pre-wrap">
                {initialContent}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Playback Indicator */}
      {isPlaying && nodes.length > 0 && (
        <div className="p-4 bg-purple-50 border-t">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-purple-800">
              Playing Beat {currentBeat + 1} of {nodes.length}
            </span>
            <div className="flex-1 bg-purple-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-300 progress-bar"
                style={{ '--progress-width': `${((currentBeat + 1) / nodes.length) * 100}%` } as React.CSSProperties}
              />
            </div>
            <span className="text-sm text-purple-600">
              {nodes[currentBeat]?.data?.timestamp?.toFixed(1)}s
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryboardFlowEditor;
