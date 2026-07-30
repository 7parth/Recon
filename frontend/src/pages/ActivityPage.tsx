import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDashboardData } from '../hooks/useDashboardData';
import type { ApplicationRecord } from '../lib/types';
import styles from './ActivityPage.module.css';

/* ── Derive timeline events from application history ── */
interface Event {
  id: string;
  title: string;
  description: string;
  timeAgo: string;
  status: 'done' | 'active' | 'pending';
  iconType: 'run' | 'review' | 'apply' | 'reject';
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

function deriveEvents(records: ApplicationRecord[]): Event[] {
  const events: Event[] = [];
  for (const r of records) {
    // Run started
    events.push({
      id: `${r.thread_id}-start`,
      title: `Run started — ${r.job_title || 'Untitled Role'}`,
      description: `${r.company || 'Unknown company'} · Match score: ${Math.round(r.match_score ?? 0)}%`,
      timeAgo: timeAgo(r.created_at),
      status: 'done',
      iconType: 'run',
    });
    // Review or apply
    if (r.approval_status === 'pending') {
      events.push({
        id: `${r.thread_id}-review`,
        title: `Awaiting review — ${r.job_title || 'Untitled Role'}`,
        description: `Tailored resume and cover letter ready for your approval.`,
        timeAgo: timeAgo(r.created_at),
        status: 'active',
        iconType: 'review',
      });
    } else if (r.approval_status === 'approved' && r.submission_status === 'applied') {
      events.push({
        id: `${r.thread_id}-applied`,
        title: `Application submitted — ${r.job_title || 'Untitled Role'}`,
        description: `${r.company || 'Unknown company'} · Automated submission complete.`,
        timeAgo: r.updated_at ? timeAgo(r.updated_at) : timeAgo(r.created_at),
        status: 'done',
        iconType: 'apply',
      });
    } else if (r.approval_status === 'rejected') {
      events.push({
        id: `${r.thread_id}-reject`,
        title: `Application rejected — ${r.job_title || 'Untitled Role'}`,
        description: `Rejected and archived. Run again with updated materials.`,
        timeAgo: timeAgo(r.created_at),
        status: 'done',
        iconType: 'reject',
      });
    }
  }
  return events;
}

function EventIcon({ type, status }: { type: string; status: string }) {
  if (status === 'active') {
    return (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
        <circle cx="5" cy="5" r="5" />
      </svg>
    );
  }
  if (type === 'apply') {
    return (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <path d="M2 5.5L4 7.5L8 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    );
  }
  if (type === 'reject') {
    return (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <path d="M2.5 2.5L7.5 7.5M7.5 2.5L2.5 7.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
      </svg>
    );
  }
  if (type === 'review') {
    return (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <circle cx="5" cy="5" r="3.5" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M5 3v2l1 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      </svg>
    );
  }
  // 'run' — play icon
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
      <path d="M2 1.5L8.5 5L2 8.5V1.5Z" />
    </svg>
  );
}

export function ActivityPage() {
  const navigate = useNavigate();
  const { history, loading } = useDashboardData();

  const events = useMemo(() => {
    const sorted = [...history].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    return deriveEvents(sorted);
  }, [history]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Activity</h1>
        <p className={styles.subtitle}>
          A chronological log of every pipeline event, review action, and application outcome.
        </p>
      </div>

      {loading && (
        <div className={styles.timeline}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className={styles.skeletonEvent} style={{ animationDelay: `${i * 80}ms` }} />
          ))}
        </div>
      )}

      {!loading && events.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>No activity yet</p>
          <p className={styles.emptySubtitle}>Start your first pipeline run from the Dashboard.</p>
          <button className={styles.ctaBtn} onClick={() => navigate('/')}>
            Go to Dashboard →
          </button>
        </div>
      )}

      {!loading && events.length > 0 && (
        <>
          <div className={styles.countBar}>
            <span className={`${styles.count} mono`}>{events.length}</span>
            <span className={styles.countLabel}>event{events.length !== 1 ? 's' : ''}</span>
          </div>
          <div className={styles.timeline}>
            {events.map((event, i) => {
              const nodeClass = event.status === 'done'
                ? styles.nodeDone
                : event.status === 'active'
                ? styles.nodeActive
                : styles.nodePending;
              return (
                <div key={event.id} className={styles.event}>
                  {i !== events.length - 1 && <div className={styles.connector} />}
                  <div className={`${styles.node} ${nodeClass}`}>
                    <EventIcon type={event.iconType} status={event.status} />
                  </div>
                  <div className={styles.content}>
                    <div className={styles.topRow}>
                      <span className={styles.eventTitle}>{event.title}</span>
                      <span className={`${styles.timeAgo} mono`}>{event.timeAgo}</span>
                    </div>
                    <p className={styles.description}>{event.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
