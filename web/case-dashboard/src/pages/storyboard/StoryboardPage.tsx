import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
// import { StoryboardEditor } from '../../shared/components/storyboard/StoryboardEditor';

export const StoryboardPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [content, setContent] = useState(`@time[0.0] #actor[John] ~action[enters room] ^evidence[doc-001]
John walks into the courtroom and takes his seat.

@time[5.0] #actor[Judge] ~action[addresses court] ^evidence[audio-001@00:30]
The judge calls the court to order and begins the proceedings.

@time[10.0] #actor[Lawyer] ~action[presents evidence] ^evidence[doc-002@page:5]
The lawyer presents the key evidence to the jury.`);

  // These will be used when StoryboardEditor is re-enabled
  // const [isValid, setIsValid] = useState(true);
  // const [errors, setErrors] = useState<string[]>([]);
  // const [beats, setBeats] = useState<any[]>([]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Storyboard Editor</h1>
        <p className="text-gray-600">Create and edit timeline beats using StoryDoc syntax</p>
      </div>
      
      <div className="h-[600px]">
        <div className="bg-white p-6 rounded-lg shadow h-full">
          <h2 className="text-xl font-semibold mb-4">Storyboard Editor</h2>
          <p className="text-gray-600 mb-4">Storyboard ID: {id}</p>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full h-96 p-4 border border-gray-300 rounded-md font-mono text-sm"
            placeholder="Enter your storyboard content here..."
          />
          <p className="text-sm text-gray-500 mt-2">
            The StoryboardEditor component will be integrated here once ReactFlow issues are resolved.
          </p>
        </div>
      </div>
    </div>
  );
};
