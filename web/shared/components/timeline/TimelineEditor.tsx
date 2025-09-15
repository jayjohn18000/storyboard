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
  ReactFlowInstance
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  PlayIcon,
  PauseIcon,
  PlusIcon,
  TrashIcon,
  AdjustmentsHorizontalIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface TimelineBeat {
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

interface TimelineEditorProps {
  beats: TimelineBeat[];
  evidenceList: Array<{ id: string; name: string; type: string }>;
  onBeatsChange: (beats: TimelineBeat[]) => void;
  onValidationChange: (isValid: boolean, errors: string[]) => void;
}

const BeatNode: React.FC<{ data: TimelineBeat & { evidenceList: any[] } }> = ({ data }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [localData, setLocalData] = useState(data);

  const handleSave = () => {
    setIsEditing(false);
    // Update parent component
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-green-100 border-green-500';
    if (confidence >= 0.7) return 'bg-yellow-100 border-yellow-500';
    return 'bg-red-100 border-red-500';
  };

  return (
    <div className={`
      bg-white border-2 rounded-lg p-4 shadow-lg min-w-64 max-w-80
      ${getConfidenceColor(localData.confidence)}
      ${localData.disputed ? 'ring-2 ring-red-500' : ''}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-600">
            {localData.timestamp.toFixed(1)}s
          </span>
          {localData.disputed && (
            <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
          )}
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-gray-400 hover:text-gray-600"
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Description */}
      {isEditing ? (
        <textarea
          value={localData.description}
          onChange={(e) => setLocalData({ ...localData, description: e.target.value })}
          className="w-full p-2 border border-gray-300 rounded text-sm resize-none"
          rows={2}
        />
      ) : (
        <p className="text-sm text-gray-800 mb-2">{localData.description}</p>
      )}

      {/* Actors */}
      <div className="mb-2">
        <label className="text-xs font-medium text-gray-600">Actors:</label>
        {isEditing ? (
          <input
            type="text"
            value={localData.actors.join(', ')}
            onChange={(e) => setLocalData({ 
              ...localData, 
              actors: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
            })}
            className="w-full p-1 border border-gray-300 rounded text-xs"
            placeholder="Actor1, Actor2"
          />
        ) : (
          <p className="text-xs text-gray-600">
            {localData.actors.length > 0 ? localData.actors.join(', ') : 'No actors'}
          </p>
        )}
      </div>

      {/* Evidence Anchors */}
      <div className="mb-2">
        <label className="text-xs font-medium text-gray-600">Evidence:</label>
        <div className="space-y-1">
          {localData.evidenceAnchors.map((anchor, index) => (
            <div key={index} className="flex items-center space-x-1">
              <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">
                {anchor.evidenceId}
              </span>
              {anchor.timestamp && (
                <span className="text-xs text-gray-500">
                  @{anchor.timestamp}s
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Confidence Slider */}
      <div className="mb-2">
        <label className="text-xs font-medium text-gray-600">
          Confidence: {Math.round(localData.confidence * 100)}%
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={localData.confidence}
          onChange={(e) => setLocalData({ 
            ...localData, 
            confidence: parseFloat(e.target.value) 
          })}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Dispute Flag */}
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          checked={localData.disputed}
          onChange={(e) => setLocalData({ ...localData, disputed: e.target.checked })}
          className="rounded"
        />
        <label className="text-xs text-gray-600">Disputed</label>
      </div>

      {/* Save Button */}
      {isEditing && (
        <button
          onClick={handleSave}
          className="mt-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
        >
          Save
        </button>
      )}
    </div>
  );
};

const nodeTypes: NodeTypes = {
  beatNode: BeatNode,
};

export const TimelineEditor: React.FC<TimelineEditorProps> = ({
  beats,
  evidenceList,
  onBeatsChange,
  onValidationChange
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null);

  // Convert beats to nodes
  useEffect(() => {
    const newNodes: Node[] = beats.map((beat, index) => ({
      id: beat.id,
      type: 'beatNode',
      position: { x: index * 300, y: 0 },
      data: { ...beat, evidenceList },
    }));

    const newEdges: Edge[] = beats
      .slice(0, -1)
      .map((beat, index) => ({
        id: `edge-${beat.id}-${beats[index + 1].id}`,
        source: beat.id,
        target: beats[index + 1].id,
        type: 'smoothstep',
        animated: true,
      }));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [beats, evidenceList]);

  // Validate timeline
  useEffect(() => {
    const errors: string[] = [];
    
    // Check for temporal consistency
    for (let i = 1; i < beats.length; i++) {
      if (beats[i].timestamp < beats[i - 1].timestamp + beats[i - 1].duration) {
        errors.push(`Beat ${i + 1} overlaps with previous beat`);
      }
    }
    
    // Check for evidence anchors
    beats.forEach((beat, index) => {
      beat.evidenceAnchors.forEach(anchor => {
        const evidence = evidenceList.find(e => e.id === anchor.evidenceId);
        if (!evidence) {
          errors.push(`Beat ${index + 1}: Evidence ${anchor.evidenceId} not found`);
        }
      });
    });
    
    // Check for disputed beats without evidence
    beats.forEach((beat, index) => {
      if (beat.disputed && beat.evidenceAnchors.length === 0) {
        errors.push(`Beat ${index + 1}: Disputed beat has no evidence anchors`);
      }
    });
    
    setValidationErrors(errors);
    onValidationChange(errors.length === 0, errors);
  }, [beats, evidenceList, onValidationChange]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const addBeat = () => {
    const newBeat: TimelineBeat = {
      id: crypto.randomUUID(),
      timestamp: beats.length > 0 ? beats[beats.length - 1].timestamp + 5 : 0,
      description: 'New beat',
      actors: [],
      evidenceAnchors: [],
      confidence: 0.8,
      disputed: false,
      duration: 3
    };
    
    onBeatsChange([...beats, newBeat]);
  };

  const removeBeat = (beatId: string) => {
    onBeatsChange(beats.filter(beat => beat.id !== beatId));
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
  };

  const addEvidenceAnchor = (beatId: string, evidenceId: string) => {
    const beat = beats.find(b => b.id === beatId);
    if (beat) {
      const newAnchor: EvidenceAnchor = {
        evidenceId,
        description: `Reference to ${evidenceId}`,
        timestamp: beat.timestamp
      };
      
      const updatedBeat = {
        ...beat,
        evidenceAnchors: [...beat.evidenceAnchors, newAnchor]
      };
      
      onBeatsChange(beats.map(b => b.id === beatId ? updatedBeat : b));
    }
  };

  return (
    <div className="w-full h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
        <div className="flex items-center space-x-4">
          <button
            onClick={togglePlayback}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            {isPlaying ? (
              <PauseIcon className="w-4 h-4" />
            ) : (
              <PlayIcon className="w-4 h-4" />
            )}
            <span>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>
          
          <button
            onClick={addBeat}
            className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Add Beat</span>
          </button>
        </div>
        
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">
            Time: {currentTime.toFixed(1)}s
          </span>
          
          {validationErrors.length === 0 ? (
            <div className="flex items-center space-x-1 text-green-600">
              <CheckCircleIcon className="w-4 h-4" />
              <span className="text-sm">Valid</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1 text-red-600">
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span className="text-sm">{validationErrors.length} errors</span>
            </div>
          )}
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

      {/* Timeline Flow */}
      <div className="h-96">
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </ReactFlowProvider>
      </div>

      {/* Evidence Picker */}
      <div className="p-4 bg-gray-50 border-t">
        <h4 className="font-medium text-gray-800 mb-2">Available Evidence:</h4>
        <div className="flex flex-wrap gap-2">
          {evidenceList.map(evidence => (
            <button
              key={evidence.id}
              onClick={() => {
                // Add to selected beat or create new anchor
                const selectedNode = nodes.find(n => n.selected);
                if (selectedNode) {
                  addEvidenceAnchor(selectedNode.id, evidence.id);
                }
              }}
              className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded hover:bg-blue-200"
            >
              {evidence.name} ({evidence.type})
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TimelineEditor;
