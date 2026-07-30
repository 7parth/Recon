import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from '../lib/api';
import type { ApplicationRecord, StatSummary } from '../lib/types';

/* ── Shared state shape ── */
interface DashboardDataContextValue {
  history: ApplicationRecord[];
  stats: StatSummary;
  loading: boolean;
  refetch: () => void;
}

const DEFAULT_STATS: StatSummary = {
  total_applications: 0,
  total_applied: 0,
  in_review: 0,
  skipped_failed: 0,
  avg_match_score: 0,
};

/* ── Context ── */
export const DashboardDataContext = createContext<DashboardDataContextValue>({
  history: [],
  stats: DEFAULT_STATS,
  loading: true,
  refetch: () => {},
});

/* ── Provider — mount once at the AppShell level ── */
export function useDashboardDataProvider(): DashboardDataContextValue {
  const [history, setHistory] = useState<ApplicationRecord[]>([]);
  const [stats, setStats] = useState<StatSummary>(DEFAULT_STATS);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const data: any = await api.getHistory();
      const records: ApplicationRecord[] = Array.isArray(data) ? data : data.items || [];

      setHistory(records);

      if (data.stats) {
        setStats(data.stats);
      } else {
        // Fallback: compute stats client-side from the records
        // Use submission_status (computed by backend) or fall back to raw status
        const applied = records.filter(r => r.submission_status === 'applied' || r.status === 'applied').length;
        const skipped = records.filter(r =>
          ['skipped', 'failed'].includes(r.submission_status ?? '') ||
          ['skipped', 'failed'].includes(r.status)
        ).length;
        const review = records.filter(r => r.approval_status === 'pending' || r.status === 'pending_review').length;
        const avg =
          records.length > 0
            ? Math.round(records.reduce((acc, r) => acc + (r.match_score || 0), 0) / records.length)
            : 0;

        setStats({
          total_applications: records.length,
          total_applied: applied,
          in_review: review,
          skipped_failed: skipped,
          avg_match_score: avg,
        });
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { history, stats, loading, refetch: fetchData };
}

/**
 * useDashboardData — consumer hook.
 * Must be used inside <DashboardDataProvider> (wraps AppShell).
 * All callers share a single fetch — no duplicate /history requests.
 */
export function useDashboardData(): DashboardDataContextValue {
  return useContext(DashboardDataContext);
}
