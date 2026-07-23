import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { ApplicationRecord, StatSummary, ReviewPayload } from '../lib/types';

export function useDashboardData() {
  const [history, setHistory] = useState<ApplicationRecord[]>([]);
  const [stats, setStats] = useState<StatSummary>({
    total_applications: 0,
    total_applied: 0,
    in_review: 0,
    skipped_failed: 0,
    avg_match_score: 0,
  });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      // In a real app, the backend should expose a /stats endpoint.
      // For now, we fetch history and compute stats on the client if needed,
      // or assume the backend returned it via a paginated response wrapper.
      // Let's fetch history first.
      const data: any = await api.getHistory();
      // Assume the backend returns { items: ApplicationRecord[], stats: StatSummary }
      // If it just returns an array, we'll map it and compute basic stats.
      const records: ApplicationRecord[] = Array.isArray(data) ? data : data.items || [];
      
      setHistory(records);

      if (data.stats) {
        setStats(data.stats);
      } else {
        // Fallback computation
        const applied = records.filter(r => r.submission_status === 'applied').length;
        const skipped = records.filter(r => r.submission_status === 'skipped' || r.submission_status === 'failed').length;
        const review = records.filter(r => r.approval_status === 'pending').length;
        const avg = records.length > 0 
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
  };

  useEffect(() => {
    fetchData();
  }, []);

  return { history, stats, loading, refetch: fetchData };
}
