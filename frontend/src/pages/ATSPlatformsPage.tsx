import styles from './ATSPlatformsPage.module.css';

interface Platform {
  id: string;
  name: string;
  status: 'implemented' | 'stub' | 'planned';
  description: string;
  fields: string[];
  color: string;
}

const PLATFORMS: Platform[] = [
  {
    id: 'greenhouse',
    name: 'Greenhouse',
    status: 'implemented',
    description: 'Full Playwright automation — form fill, resume upload, submit. Handles standard application flow.',
    fields: ['first_name', 'last_name', 'email', 'phone', 'linkedin_url', 'resume (PDF)'],
    color: '#22C55E',
  },
  {
    id: 'lever',
    name: 'Lever',
    status: 'implemented',
    description: 'Full Playwright automation — Lever-hosted forms with dynamic field detection.',
    fields: ['first_name', 'last_name', 'email', 'phone', 'resume (PDF)'],
    color: '#22C55E',
  },
  {
    id: 'workday',
    name: 'Workday',
    status: 'implemented',
    description: 'Full Playwright automation — data-automation-id selectors, multi-step wizard navigation, resume upload with fallback selectors, confirmation detection.',
    fields: ['first_name', 'last_name', 'email', 'phone', 'linkedin_url', 'resume (file)', 'cover_letter'],
    color: '#22C55E',
  },
  {
    id: 'ashby',
    name: 'Ashby',
    status: 'implemented',
    description: 'Full Playwright automation — Apply button click, standard HTML5 form fill, resume upload, cover letter with label-proximity fallback, confirmation detection.',
    fields: ['first_name', 'last_name', 'email', 'phone', 'linkedin_url', 'resume (file)', 'cover_letter'],
    color: '#22C55E',
  },
  {
    id: 'smartrecruiters',
    name: 'SmartRecruiters',
    status: 'implemented',
    description: 'Full Playwright automation — Apply Now click, personal info form fill, file upload with styled-button fallback, cover letter, submit + URL/element confirmation.',
    fields: ['first_name', 'last_name', 'email', 'phone', 'linkedin_url', 'resume (file)', 'cover_letter'],
    color: '#22C55E',
  },
  {
    id: 'linkedin-easy',
    name: 'LinkedIn Easy Apply',
    status: 'implemented',
    description: 'Full Playwright automation — stored-session authentication (one-time manual login), Easy Apply modal navigation, phone fill, resume upload, cover letter, multi-step handling, "Application submitted" confirmation detection.',
    fields: ['phone', 'resume (PDF upload)', 'cover_letter (textarea)', 'multi-step modal navigation'],
    color: '#0A66C2',
  },
  {
    id: 'indeed',
    name: 'Indeed Apply',
    status: 'planned',
    description: 'Indeed\'s apply flow is highly variable. Assessment + parsing roadmap TBD.',
    fields: ['Requires: Indeed account, variable form handling'],
    color: '#6B7280',
  },

];

const STATUS_META = {
  implemented: { label: 'IMPLEMENTED', color: 'var(--color-success)' },
  stub:        { label: 'STUB (IN PROGRESS)', color: 'var(--color-warning)' },
  planned:     { label: 'PLANNED', color: 'var(--color-neutral)' },
};

function CheckIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
      <path d="M1.5 5.5L4.5 8.5L9.5 2.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function ClockIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
      <circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" strokeWidth="1.3"/>
      <path d="M5.5 3v2.5l1.5 1.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  );
}
function CircleIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
      <circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" strokeWidth="1.3"/>
    </svg>
  );
}

function StatusIcon({ status }: { status: Platform['status'] }) {
  if (status === 'implemented') return <CheckIcon />;
  if (status === 'stub') return <ClockIcon />;
  return <CircleIcon />;
}

function PlatformCard({ p }: { p: Platform }) {
  const meta = STATUS_META[p.status];
  return (
    <div className={styles.card} id={`ats-${p.id}`}>
      <div className={styles.cardHeader}>
        <div className={styles.platformLogo} style={{ background: p.color }}>
          {p.name.charAt(0)}
        </div>
        <div className={styles.platformInfo}>
          <h3 className={styles.platformName}>{p.name}</h3>
          <span
            className={`${styles.statusBadge} mono`}
            style={{ borderColor: meta.color, color: meta.color }}
          >
            <StatusIcon status={p.status} />
            {meta.label}
          </span>
        </div>
      </div>
      <p className={styles.desc}>{p.description}</p>
      <div className={styles.fields}>
        <span className="label" style={{ color: 'var(--color-text-tertiary)', marginBottom: '6px', display: 'block' }}>
          Fields
        </span>
        <div className={styles.fieldTags}>
          {p.fields.map(f => (
            <span key={f} className={`${styles.fieldTag} mono`}>{f}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ATSPlatformsPage() {
  const counts = {
    implemented: PLATFORMS.filter(p => p.status === 'implemented').length,
    stub: PLATFORMS.filter(p => p.status === 'stub').length,
    planned: PLATFORMS.filter(p => p.status === 'planned').length,
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>ATS Platforms</h1>
        <p className={styles.subtitle}>
          Playwright automation coverage across Applicant Tracking Systems.
        </p>
      </div>

      {/* Summary strip */}
      <div className={styles.summary}>
        {[
          { label: 'Implemented', count: counts.implemented, color: 'var(--color-success)' },
          { label: 'In Progress', count: counts.stub, color: 'var(--color-warning)' },
          { label: 'Planned',     count: counts.planned, color: 'var(--color-neutral)' },
        ].map(s => (
          <div key={s.label} className={styles.summaryItem}>
            <span className={`${styles.summaryCount} mono`} style={{ color: s.color }}>{s.count}</span>
            <span className={styles.summaryLabel}>{s.label}</span>
          </div>
        ))}
      </div>

      {/* Platform cards */}
      <div className={styles.grid}>
        {PLATFORMS.map(p => <PlatformCard key={p.id} p={p} />)}
      </div>

      <div className={styles.footer}>
        <span className="label" style={{ color: 'var(--color-text-tertiary)' }}>
          Automation layer: <code className="mono" style={{ fontSize: 'var(--text-xs)' }}>backend/app/automation/</code>
          · Playwright headless Chromium
        </span>
      </div>
    </div>
  );
}
