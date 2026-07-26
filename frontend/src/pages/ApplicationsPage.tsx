import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDashboardData } from '../hooks/useDashboardData';
import type { ApplicationRecord } from '../lib/types';
import styles from './ApplicationsPage.module.css';

/* ── Icons ── */
function ExternalLinkIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 10L10 2M10 2H5M10 2V7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

/* ── Badge ── */
function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string }> = {
    applied:  { label: 'APPLIED',     color: 'var(--color-success)' },
    skipped:  { label: 'SKIPPED',     color: 'var(--color-danger)'  },
    failed:   { label: 'FAILED',      color: 'var(--color-danger)'  },
    pending:  { label: 'IN REVIEW',   color: 'var(--color-warning)' },
    approved: { label: 'APPROVED',    color: 'var(--color-success)' },
    rejected: { label: 'REJECTED',    color: 'var(--color-danger)'  },
  };
  const m = map[status] ?? { label: status.toUpperCase(), color: 'var(--color-neutral)' };
  return (
    <span
      style={{
        border: `1px solid ${m.color}`,
        color: m.color,
        fontFamily: 'var(--font-mono)',
        fontSize: 'var(--text-xs)',
        padding: '3px 8px',
        borderRadius: 'var(--radius-sm)',
        letterSpacing: '0.06em',
        whiteSpace: 'nowrap',
      }}
    >
      {m.label}
    </span>
  );
}

/* ── Score pill ── */
function ScorePill({ score }: { score: number }) {
  const color = score >= 90 ? 'var(--color-success)' : score >= 70 ? 'var(--color-warning)' : 'var(--color-danger)';
  return (
    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-base)', color }}>
      {score}%
    </span>
  );
}

/* ── Logo avatar ── */
const COLORS = ['#E8471A', '#22C55E', '#F59E0B', '#6366F1', '#EC4899', '#14B8A6'];
function LogoAvatar({ company }: { company: string }) {
  const letter = (company || '?').charAt(0).toUpperCase();
  const color = COLORS[letter.charCodeAt(0) % COLORS.length];
  return (
    <div style={{
      width: 30, height: 30, borderRadius: 'var(--radius-sm)',
      background: color, display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '11px', fontWeight: 700, color: '#fff', flexShrink: 0,
    }}>
      {letter}
    </div>
  );
}

type SortKey = 'created_at' | 'match_score' | 'company';
type SortDir = 'asc' | 'desc';
type FilterStatus = 'all' | 'applied' | 'skipped' | 'failed' | 'pending';

export function ApplicationsPage() {
  const navigate = useNavigate();
  const { history, loading } = useDashboardData();
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [sortKey, setSortKey] = useState<SortKey>('created_at');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const filtered = useMemo(() => {
    let data = [...history];
    if (search) {
      const q = search.toLowerCase();
      data = data.filter(r =>
        (r.job_title || '').toLowerCase().includes(q) ||
        (r.company || '').toLowerCase().includes(q)
      );
    }
    if (filterStatus !== 'all') {
      data = data.filter(r => r.submission_status === filterStatus || r.approval_status === filterStatus);
    }
    data.sort((a, b) => {
      let va: number | string, vb: number | string;
      if (sortKey === 'match_score') { va = a.match_score ?? 0; vb = b.match_score ?? 0; }
      else if (sortKey === 'company') { va = a.company || ''; vb = b.company || ''; }
      else { va = a.created_at || ''; vb = b.created_at || ''; }
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return data;
  }, [history, search, filterStatus, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  const SortArrow = ({ k }: { k: SortKey }) =>
    sortKey === k ? <span style={{ marginLeft: 4, opacity: 0.6 }}>{sortDir === 'asc' ? '↑' : '↓'}</span> : null;

  const STATUS_FILTERS: FilterStatus[] = ['all', 'applied', 'pending', 'skipped', 'failed'];

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>All Applications</h1>
        <p className={styles.subtitle}>
          Complete history of every pipeline run, with document links and status.
        </p>
      </div>

      {/* Toolbar */}
      <div className={styles.toolbar}>
        <input
          id="apps-search"
          className={styles.searchInput}
          type="text"
          placeholder="Search role or company…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        <div className={styles.filters}>
          {STATUS_FILTERS.map(f => (
            <button
              key={f}
              id={`apps-filter-${f}`}
              className={`${styles.filterBtn} ${filterStatus === f ? styles.filterActive : ''}`}
              onClick={() => setFilterStatus(f)}
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
          <span className={styles.countLabel}>record{filtered.length !== 1 ? 's' : ''}</span>
        </div>
      )}

      {/* Table */}
      <div className={styles.tableWrap}>
        <div className={styles.table}>
          {/* Head */}
          <div className={`${styles.row} ${styles.head}`}>
            <div className={styles.colPosition}>POSITION</div>
            <div className={styles.colScore}>
              <button className={styles.sortBtn} onClick={() => toggleSort('match_score')}>
                MATCH<SortArrow k="match_score" />
              </button>
            </div>
            <div className={styles.colStatus}>STATUS</div>
            <div className={styles.colDate}>
              <button className={styles.sortBtn} onClick={() => toggleSort('created_at')}>
                CREATED<SortArrow k="created_at" />
              </button>
            </div>
            <div className={styles.colDocs}>DOCS</div>
            <div className={styles.colAction} />
          </div>

          {/* Loading skeletons */}
          {loading && Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className={`${styles.row} ${styles.skeleton}`} style={{ animationDelay: `${i * 60}ms` }} />
          ))}

          {/* Empty state */}
          {!loading && filtered.length === 0 && (
            <div className={styles.emptyState}>
              <p className={styles.emptyTitle}>No applications found</p>
              <p className={styles.emptySubtitle}>Start a run from the Dashboard or broaden your search.</p>
            </div>
          )}

          {/* Rows */}
          {!loading && filtered.map((app: ApplicationRecord) => {
            const date = new Date(app.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
            return (
              <div key={app.thread_id} className={styles.row}>
                <div className={styles.colPosition}>
                  <LogoAvatar company={app.company} />
                  <div className={styles.positionInfo}>
                    <span className={styles.jobTitle}>{app.job_title || 'Untitled Role'}</span>
                    <span className={styles.company}>{app.company || '—'}</span>
                  </div>
                </div>
                <div className={styles.colScore}>
                  <ScorePill score={Math.round(app.match_score ?? 0)} />
                </div>
                <div className={styles.colStatus}>
                  <StatusBadge status={app.approval_status === 'pending' ? 'pending' : app.submission_status} />
                </div>
                <div className={`${styles.colDate} mono`} style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>
                  {date}
                </div>
                <div className={styles.colDocs}>
                  {app.tailored_resume_url && (
                    <a href={app.tailored_resume_url} target="_blank" rel="noopener noreferrer"
                      className={styles.docLink} id={`apps-resume-${app.thread_id}`}>
                      Resume <ExternalLinkIcon />
                    </a>
                  )}
                  {app.cover_letter_url && (
                    <a href={app.cover_letter_url} target="_blank" rel="noopener noreferrer"
                      className={styles.docLink} id={`apps-cover-${app.thread_id}`}>
                      Cover <ExternalLinkIcon />
                    </a>
                  )}
                </div>
                <div className={styles.colAction}>
                  {app.approval_status === 'pending' && (
                    <button
                      id={`apps-review-${app.thread_id}`}
                      className={styles.reviewBtn}
                      onClick={() => navigate(`/review/${app.thread_id}`)}
                    >
                      Review →
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
