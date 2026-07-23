import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { RunStatus } from '../lib/types';

export function usePipelineRun(threadId: string | null) {
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!threadId) {
      setRunStatus(null);
      return;
    }

    let intervalId: ReturnType<typeof setInterval>;

    const poll = async () => {
      try {
        const data = await api.getRunStatus(threadId);
        setRunStatus(data);

        // Stop polling if completed, failed, or skipped
        if (['completed', 'failed', 'skipped', 'pending_review'].includes(data.status)) {
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Failed to poll run status:', err);
      }
    };

    setLoading(true);
    poll().finally(() => setLoading(false));

    intervalId = setInterval(poll, 2000);

    return () => clearInterval(intervalId);
  }, [threadId]);

  return { runStatus, loading };
}
