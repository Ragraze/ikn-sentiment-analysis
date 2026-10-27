'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { errorMessage } from '@/lib/format';

export function useResource<T>(url: string) {
  const [state, setState] = useState<{ url: string; data: T | null; loading: boolean; error: string }>({
    url,
    data: null,
    loading: true,
    error: '',
  });
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision(value => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setState({ url, data: null, loading: true, error: '' });
    api<T>(url, { signal: controller.signal })
      .then(data => {
        if (!controller.signal.aborted) setState({ url, data, loading: false, error: '' });
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          setState({ url, data: null, loading: false, error: errorMessage(error) });
        }
      });
    return () => controller.abort();
  }, [url, revision]);

  return {
    data: state.url === url ? state.data : null,
    loading: state.url !== url || state.loading,
    error: state.url === url ? state.error : '',
    reload,
  };
}
