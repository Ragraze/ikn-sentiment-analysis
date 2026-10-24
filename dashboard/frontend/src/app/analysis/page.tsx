'use client';

import { ModelStatus } from '@/components/model-status';
import { PredictionForm } from '@/features/prediction-form';
import { useModelHealth } from '@/hooks/use-model-health';

export default function AnalysisPage() {
  const health = useModelHealth();
  return (
    <>
      <PredictionForm health={health.data} refreshHealth={health.reload} />
      <div className="analysis-status"><ModelStatus showAction={false} /></div>
    </>
  );
}
