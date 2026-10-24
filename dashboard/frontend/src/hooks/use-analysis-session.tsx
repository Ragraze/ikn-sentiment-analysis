'use client';

import { createContext, useContext, useReducer } from 'react';
import type { Dispatch, ReactNode } from 'react';
import { analysisSessionReducer, initialAnalysisSession } from '@/lib/analysis-session';
import type { AnalysisSession } from '@/lib/analysis-session';

type Action = Parameters<typeof analysisSessionReducer>[1];
const AnalysisSessionContext = createContext<{ session: AnalysisSession; dispatch: Dispatch<Action> } | null>(null);

export function AnalysisSessionProvider({ children }: { children: ReactNode }) {
  const [session, dispatch] = useReducer(analysisSessionReducer, initialAnalysisSession);
  return <AnalysisSessionContext.Provider value={{ session, dispatch }}>{children}</AnalysisSessionContext.Provider>;
}

export function useAnalysisSession() {
  const session = useContext(AnalysisSessionContext);
  if (!session) throw new Error('AnalysisSessionProvider belum dipasang.');
  return session;
}
