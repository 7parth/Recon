import { useDashboardData } from '../hooks/useDashboardData';
import type { ApplicationRecord } from '../lib/types';
import styles from './ResumesPage.module.css';

function DownloadIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6.5 1v7M3.5 5.5l3 3 3-3M2 10.5h9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function FileIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M9 1H3a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V5L9 1Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
      <path d="M9 1v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
      <path d="M5 8h6M5 10.5h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

function matchTierClass(score: number) {
  if (score >= 90) return styles.tierHigh;
  if (score >= 70) return styles.tierGood;
  return styles.tierLow;
}

function matchTierLabel(score: number) {
  if (score >= 90) return 'HIGH MATCH';
  if (score >= 70) return 'GOOD MATCH';
  return 'LOW MATCH';
}

function ResumeCard({ app }: { app: ApplicationRecord }) {
  const letter = (app.company || '?').charAt(0).toUpperCase();
  const date = new Date(app.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const score = Math.round(app.match_score ?? 0);

  return (
    <div className={styles.card}>
      {/* Card header */}
      <div className={styles.cardHeader}>
        <div className={styles.logo}>{letter}</div>
        <div className={styles.cardInfo}>
          <h3 className={styles.jobTitle}>{app.job_title || 'Untitled Role'}</h3>
          <span className={styles.company}>{app.company || '—'}</span>
        </div>
        <div className={`${styles.tier} ${matchTierClass(score)}`}>
          {matchTierLabel(score)}
        </div>
      </div>

      {/* Score + date */}
      <div className={styles.cardMeta}>
        <span className={`${styles.score} mono`}>
          <span className={styles.scoreValue}>{score}</span>
          <span className={styles.scorePct}>%</span>
        </span>
        <span className={styles.date}>{date}</span>
      </div>

      {/* Document links */}
      <div className={styles.docLinks}>
        {app.resume_url ? (
          <a
            href={app.resume_url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.docBtn}
            id={`resume-original-${app.thread_id}`}
          >
            <DownloadIcon />
            Original Resume
          </a>
        ) : (
          <span className={styles.docBtnDisabled}><FileIcon /> No original</span>
        )}
        {app.tailored_resume_url ? (
          <a
            href={app.tailored_resume_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`${styles.docBtn} ${styles.docBtnAccent}`}
            id={`resume-tailored-${app.thread_id}`}
          >
            <DownloadIcon />
            Tailored Resume
          </a>
        ) : (
          <span className={styles.docBtnDisabled}><FileIcon /> No tailored resume</span>
        )}
      </div>
    </div>
  );
}

export function ResumesPage() {
  const { history, loading } = useDashboardData();

  // Show all apps — even those without a resume URL, so user can see what ran
  const apps = history;

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <h1 className={styles.title}>Resumes</h1>
        </div>
        <div className={styles.skeletons}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className={styles.skeleton} style={{ animationDelay: `${i * 80}ms` }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Resumes</h1>
        <p className={styles.subtitle}>
          Original and tailored resume documents across all application runs.
        </p>
      </div>

      {apps.length === 0 ? (
        <div className={styles.emptyState}>
          <FileIcon />
          <p className={styles.emptyTitle}>No resumes on record</p>
          <p className={styles.emptySubtitle}>Start a run from the Dashboard to upload your first resume.</p>
        </div>
      ) : (
        <>
          <div className={styles.countBar}>
            <span className={`${styles.count} mono`}>{apps.length}</span>
            <span className={styles.countLabel}>application{apps.length !== 1 ? 's' : ''}</span>
          </div>
          <div className={styles.grid}>
            {apps.map(app => (
              <ResumeCard key={app.thread_id} app={app} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
