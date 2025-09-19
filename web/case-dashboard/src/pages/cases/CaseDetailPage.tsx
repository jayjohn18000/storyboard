import React from 'react';
import { useParams } from 'react-router-dom';
import { CaseOverview } from '../../pages/CaseOverview';

export const CaseDetailPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();

  if (!caseId) {
    return <div>Case ID not found</div>;
  }

  return (
    <div>
      <CaseOverview caseId={caseId} />
    </div>
  );
};
