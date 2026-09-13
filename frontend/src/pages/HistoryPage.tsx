/**
 * HistoryPage — Full application history with state-transition event log.
 *
 * Distinct from ApplicationsPage (which is a data table of runs).
 * This page shows a per-run expandable timeline: every status change,
 * document generation, review decision, and submission outcome.
 *
 * Data source: GET /api/v1/history (list) + GET /api/v1/history/{thread_id} (detail).
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDashboardData } from '../hooks/useDashboardData';
import type { ApplicationRecord } from '../lib/types';
import { api } from '../lib/api';
import styles from './HistoryPage.module.css';

/* ── Helpers ── */

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

/* ── Status badge ── */
const STATUS_MAP: Record<string, { label: string; color: string }> = {
  applied:        { label: 'APPLIED',        color: 'var(--color-success)' },
  skipped:        { label: 'SKIPPED',        color: 'var(--color-warning)' },
  failed:         { label: 'FAILED',         color: 'var(--color-danger)'  },
  pending_review: { label: 'IN REVIEW',      color: 'var(--color-warning)' },
  pending:        { label: 'IN REVIEW',      color: 'var(--color-warning)' },
  running:        { label: 'RUNNING',        color: 'var(--color-accent)'  },
  approved:       { label: 'APPROVED',       color: 'var(--color-success)' },
  rejected:       { label: 'REJECTED',       color: 'var(--color-danger)'  },
};

function StatusBadge({ status }: { status: string }) {
  const m = STATUS_MAP[status] ?? { label: status.toUpperCase(), color: 'var(--color-text-tertiary)' };
  return (
    <span
      className={styles.badge}
      style={{ borderColor: m.color, color: m.color }}
    >
      {m.label}
    </span>
  );
}

/* ── Timeline events derived from a single ApplicationRecord ── */
interface TimelineEvent {
  key: string;
  icon: string;
  label: string;
  detail?: string;
  ts?: string;
  status: 'done' | 'active' | 'skipped';
}

function buildTimeline(r: ApplicationRecord & { rejection_feedback?: string }): TimelineEvent[] {
  const status = r.status || r.submission_status || '';
  const events: TimelineEvent[] = [
    {
      key: 'started',
      icon: '🚀',
      label: 'Pipeline started',
      detail: `Resume parsed · Job analysed · Company researched`,
      ts: r.created_at,
      status: 'done',
    },
    {
      key: 'match',
      icon: '🎯',
      label: 'Matching & ATS audit',
      detail: r.match_score != null ? `Match score: ${Math.round(r.match_score)}%` : 'Match score: —',
      status: r.match_score != null ? 'done' : 'skipped',
    },
    {
      key: 'tailor',
      icon: '✍️',
      label: 'Resume tailored & cover letter drafted',
      detail: r.tailored_resume_url ? 'Documents saved to storage' : 'Documents generated',
      status: status !== 'running' ? 'done' : 'active',
    },
    {
      key: 'review',
      icon: '👁️',
      label: 'Human review',
      detail:
        status === 'approved' || status === 'applied' || status === 'skipped'
          ? 'Approved by reviewer'
          : status === 'rejected'
          ? `Rejected${r.rejection_feedback ? ` — "${r.rejection_feedback}"` : ''}`
          : status === 'pending_review' || status === 'pending'
          ? 'Awaiting reviewer decision'
          : '—',
      status:
        ['approved', 'applied', 'skipped', 'failed'].includes(status)
          ? 'done'
          : status === 'pending_review' || status === 'pending'
          ? 'active'
          : 'skipped',
    },
    {
      key: 'apply',
      icon: '📤',
      label: 'Application submitted',
      detail:
        status === 'applied'
          ? 'Automation completed successfully'
          : status === 'skipped'
          ? 'Platform not supported — skipped'
          : status === 'failed'
          ? 'Submission failed'
          : '—',
      status:
        status === 'applied'
          ? 'done'
          : status === 'skipped' || status === 'failed'
          ? 'skipped'
          : 'skipped',
    },
  ];
  return events;
}

/* ── Expandable run row ── */
function RunRow({ record }: { record: ApplicationRecord & { rejection_feedback?: string | null } }) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<any>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const status = record.status || record.submission_status || 'unknown';
  const timeline = buildTimeline({ ...record, ...(detail || {}) });

  async function loadDetail() {
    if (detail || loadingDetail) return;
    setLoadingDetail(true);
    try {
      const d = await api.getHistoryDetail(record.thread_id);
      setDetail(d);
    } catch { /* noop */ } finally {
      setLoadingDetail(false);
    }
  }

  function toggle() {
    if (!open) loadDetail();
    setOpen(o => !o);
  }

  return (
    <div className={`${styles.runCard} ${open ? styles.runCardOpen : ''}`}>
      {/* Summary row */}
      <button className={styles.runHeader} onClick={toggle} aria-expanded={open}>
        <div className={styles.runLeft}>
          <span className={`${styles.expandIcon} ${open ? styles.expandIconOpen : ''}`}>›</span>
          <div className={styles.runMeta}>
            <span className={`${styles.threadId} mono`}>{record.thread_id.slice(0, 12)}…</span>
            <span className={styles.timeAgo}>{timeAgo(record.created_at)}</span>
          </div>
        </div>
        <div className={styles.runRight}>
          {record.match_score != null && (
            <span className={`${styles.score} mono`}>{Math.round(record.match_score)}%</span>
          )}
          <StatusBadge status={status} />
          {(status === 'pending_review' || status === 'pending') && (
            <button
              className={styles.reviewBtn}
              onClick={e => { e.stopPropagation(); navigate(`/review/${record.thread_id}`); }}
            >
              Review →
            </button>
          )}
        </div>
      </button>

      {/* Expandable detail */}
      {open && (
        <div className={styles.runDetail}>
          {loadingDetail && (
            <p className={styles.loading}>Loading…</p>
          )}

          {/* Timeline */}
          <div className={styles.timeline}>
            {timeline.map((evt, i) => (
              <div key={evt.key} className={`${styles.timelineItem} ${styles[`status_${evt.status}`]}`}>
                <div className={styles.timelineLeft}>
                  <div className={styles.timelineIcon}>{evt.icon}</div>
                  {i < timeline.length - 1 && <div className={styles.timelineLine} />}
                </div>
                <div className={styles.timelineBody}>
                  <div className={styles.timelineLabel}>{evt.label}</div>
                  {evt.detail && <div className={styles.timelineDetail}>{evt.detail}</div>}
                  {evt.ts && (
                    <div className={`${styles.timelineTs} mono`}>{formatDate(evt.ts)}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Document links */}
          {(record.tailored_resume_url || record.cover_letter_url || record.resume_url) && (
            <div className={styles.docLinks}>
              <span className={styles.docLinksLabel}>Documents</span>
              {record.resume_url && (
                <a href={record.resume_url} target="_blank" rel="noopener noreferrer" className={styles.docLink}>
                  Original Resume ↗
                </a>
              )}
              {record.tailored_resume_url && (
                <a href={record.tailored_resume_url} target="_blank" rel="noopener noreferrer" className={styles.docLink}>
                  Tailored Resume ↗
                </a>
              )}
              {record.cover_letter_url && (
                <a href={record.cover_letter_url} target="_blank" rel="noopener noreferrer" className={styles.docLink}>
                  Cover Letter ↗
                </a>
              )}
            </div>
          )}

          {/* Automation logs link */}
          <div className={styles.detailFooter}>
            <button
              className={styles.logsLink}
              onClick={() => navigate('/automation/logs')}
            >
              View Automation Logs ›
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Filter bar ── */
type StatusFilter = 'all' | 'applied' | 'pending' | 'failed' | 'skipped';

/* ── Page ── */
export function HistoryPage() {
  const { history, loading, refetch } = useDashboardData();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');

  const STATUS_FILTERS: StatusFilter[] = ['all', 'applied', 'pending', 'failed', 'skipped'];

  const filtered = history.filter(r => {
    const status = r.status || r.submission_status || '';
    const matchesStatus =
      statusFilter === 'all' ||
      status === statusFilter ||
      (statusFilter === 'pending' && (status === 'pending_review' || status === 'pending'));
    const q = search.toLowerCase();
    const matchesSearch = !q || r.thread_id.toLowerCase().includes(q);
    return matchesStatus && matchesSearch;
  });

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>History</h1>
          <p className={styles.subtitle}>
            Full state-transition log for every pipeline run.
          </p>
        </div>
        <button className={styles.refreshBtn} onClick={refetch}>↻ Refresh</button>
      </div>

      {/* Toolbar */}
      <div className={styles.toolbar}>
        <input
          id="history-search"
          className={styles.searchInput}
          type="text"
          placeholder="Search by thread ID…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          autoComplete="off"
        />
        <div className={styles.filters}>
          {STATUS_FILTERS.map(f => (
            <button
              key={f}
              id={`history-filter-${f}`}
              className={`${styles.filterBtn} ${statusFilter === f ? styles.filterActive : ''}`}
              onClick={() => setStatusFilter(f)}
            >
              {f === 'all' ? 'ALL' : f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Count */}
      {!loading && (
        <div className={styles.countBar}>
          <span className={`${styles.count} mono`}>{filtered.length}</span>
          <span className={styles.countLabel}>run{filtered.length !== 1 ? 's' : ''}</span>
        </div>
      )}

      {/* List */}
      {loading && (
        <div className={styles.skeletons}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className={styles.skeleton} style={{ animationDelay: `${i * 80}ms` }} />
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>No runs found</p>
          <p className={styles.emptySubtitle}>Start a pipeline run from the Dashboard.</p>
        </div>
      )}

      {!loading && (
        <div className={styles.runList}>
          {filtered.map(r => (
            <RunRow key={r.thread_id} record={r} />
          ))}
        </div>
      )}
    </div>
  );
}
