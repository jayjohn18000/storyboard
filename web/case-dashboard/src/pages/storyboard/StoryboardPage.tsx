import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { StoryboardEditor } from '../../../../shared/components/storyboard/StoryboardEditor';

export const StoryboardPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [content, setContent] = useState(`@time[0.0] #actor[John] ~action[enters room] ^evidence[doc-001]
John walks into the courtroom and takes his seat.

@time[5.0] #actor[Judge] ~action[addresses court] ^evidence[audio-001@00:30]
The judge calls the court to order and begins the proceedings.

@time[10.0] #actor[Lawyer] ~action[presents evidence] ^evidence[doc-002@page:5]
The lawyer presents the key evidence to the jury.`);

  const [isValid, setIsValid] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);
  const [beats, setBeats] = useState<any[]>([]);

  // Mock evidence list
  const evidenceList = [
    { id: 'doc-001', name: 'Contract_Amendment.pdf', type: 'document' },
    { id: 'audio-001', name: 'Meeting_Recording.mp3', type: 'audio' },
    { id: 'doc-002', name: 'Evidence_Photo_001.jpg', type: 'photo' },
  ];

  const handleContentChange = (newContent: string) => {
    setContent(newContent);
  };

  const handleValidationChange = (valid: boolean, validationErrors: string[]) => {
    setIsValid(valid);
    setErrors(validationErrors);
  };

  const handleBeatsExtracted = (extractedBeats: any[]) => {
    setBeats(extractedBeats);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Storyboard Editor</h1>
        <p className="text-gray-600">Create and edit timeline beats using StoryDoc syntax</p>
      </div>
      
      <div className="h-[600px]">
        <StoryboardEditor
          initialContent={content}
          evidenceList={evidenceList}
          onContentChange={handleContentChange}
          onValidationChange={handleValidationChange}
          onBeatsExtracted={handleBeatsExtracted}
        />
      </div>
    </div>
  );
};
