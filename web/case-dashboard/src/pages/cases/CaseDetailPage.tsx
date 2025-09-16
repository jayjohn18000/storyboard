import React from 'react';
import { useParams } from 'react-router-dom';
import { CaseOverview } from '../../pages/CaseOverview';

export const CaseDetailPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();

  return (
    <div>
      <CaseOverview />
    </div>
  );
};
