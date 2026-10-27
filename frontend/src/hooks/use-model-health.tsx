'use client';

import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useResource } from '@/hooks/use-resource';
import type { Health } from '@/lib/types';

const ModelHealthContext = createContext<ReturnType<typeof useResource<Health>> | null>(null);

export function ModelHealthProvider({ children }: { children: ReactNode }) {
  const health = useResource<Health>('/api/health');
  return <ModelHealthContext.Provider value={health}>{children}</ModelHealthContext.Provider>;
}

export function useModelHealth() {
  const health = useContext(ModelHealthContext);
  if (!health) throw new Error('ModelHealthProvider belum dipasang.');
  return health;
}
