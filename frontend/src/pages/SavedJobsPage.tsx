import { useState } from 'react';
import styles from './SavedJobsPage.module.css';

const STORAGE_KEY = 'recon_saved_jobs';

export interface SavedJob {
  id: string;
  title: string;
  company: string;
  url: string;
  location: string;
  savedAt: string;
  notes: string;
}

function ExternalIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
      <path d="M1.5 9.5L9.5 1.5M9.5 1.5H5M9.5 1.5V6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
      <path d="M2 3.5h9M5 3.5V2h3v1.5M4 3.5l.5 6.5h4L9 3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function BookmarkIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
      <path d="M8 4h16v24l-8-5-8 5V4Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
    </svg>
  );
}

function useSavedJobs() {
  const [jobs, setJobs] = useState<SavedJob[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch { return []; }
  });

  function remove(id: string) {
    const next = jobs.filter(j => j.id !== id);
    setJobs(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }

  return { jobs, remove };
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

const COLORS = ['#E8471A', '#22C55E', '#F59E0B', '#6366F1', '#EC4899', '#14B8A6'];

function JobCard({ job, onRemove }: { job: SavedJob; onRemove: () => void }) {
  const letter = (job.company || job.title || '?').charAt(0).toUpperCase();
  const color = COLORS[letter.charCodeAt(0) % COLORS.length];
  let domain = '';
  try { domain = new URL(job.url).hostname.replace('www.', ''); } catch {}

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.logo} style={{ background: color }}>{letter}</div>
        <div className={styles.info}>
          <h3 className={styles.jobTitle}>{job.title}</h3>
          <span className={styles.company}>{job.company}</span>
          {job.location && <span className={styles.location}>{job.location}</span>}
        </div>
        <div className={styles.metaRight}>
          <span className={`${styles.savedAt} mono`}>{timeAgo(job.savedAt)}</span>
        </div>
      </div>

      {domain && (
        <div className={`${styles.domain} mono`}>{domain}</div>
      )}

      {job.notes && (
        <p className={styles.notes}>{job.notes}</p>
      )}

      <div className={styles.cardFooter}>
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.openBtn}
          id={`saved-open-${job.id}`}
        >
          Open listing <ExternalIcon />
        </a>
        <button
          className={styles.runBtn}
          id={`saved-run-${job.id}`}
          onClick={() => navigator.clipboard.writeText(job.url)}
          title="Copy URL to start a pipeline run"
        >
          Copy URL for Run
        </button>
        <button
          className={styles.removeBtn}
          id={`saved-remove-${job.id}`}
          onClick={onRemove}
          aria-label="Remove saved job"
        >
          <TrashIcon />
        </button>
      </div>
    </div>
  );
}

export function SavedJobsPage() {
  const { jobs, remove } = useSavedJobs();

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Saved Jobs</h1>
        <p className={styles.subtitle}>
          Bookmarked job listings. Copy a URL to start a new pipeline run.
        </p>
      </div>

      {jobs.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}><BookmarkIcon /></div>
          <p className={styles.emptyTitle}>No saved jobs yet</p>
          <p className={styles.emptySubtitle}>
            Use the Job Search page to discover listings, then bookmark them here.
          </p>
          <a href="/jobs/search" className={styles.searchLink}>
            Search Jobs →
          </a>
        </div>
      ) : (
        <>
          <div className={styles.countBar}>
            <span className={`${styles.count} mono`}>{jobs.length}</span>
            <span className={styles.countLabel}>saved listing{jobs.length !== 1 ? 's' : ''}</span>
          </div>
          <div className={styles.grid}>
            {jobs.map(j => (
              <JobCard key={j.id} job={j} onRemove={() => remove(j.id)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
