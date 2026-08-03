import { useState, useEffect, useCallback } from 'react';
import styles from './IntegrationsPage.module.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ApiKey {
  id: string;
  label: string;
  envVar: string;
  description: string;
  placeholder: string;
  link?: string;
  linkLabel?: string;
}

interface LinkedInAuthStatus {
  authenticated: boolean;
  session_file_exists: boolean;
  session_path: string;
  message: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const API_KEYS: ApiKey[] = [
  {
    id: 'nvidia-api-key',
    label: 'NVIDIA API Key',
    envVar: 'NVIDIA_API_KEY',
    description: 'Required for LLM inference via NVIDIA AI Endpoints (llama-4-scout, etc.)',
    placeholder: 'nvapi-…',
    link: 'https://build.nvidia.com',
    linkLabel: 'build.nvidia.com',
  },
  {
    id: 'supabase-url',
    label: 'Supabase Project URL',
    envVar: 'SUPABASE_URL',
    description: 'Your Supabase project URL for PostgreSQL + Storage.',
    placeholder: 'https://xxxx.supabase.co',
    link: 'https://app.supabase.com',
    linkLabel: 'app.supabase.com',
  },
  {
    id: 'supabase-anon-key',
    label: 'Supabase Anon Key',
    envVar: 'SUPABASE_ANON_KEY',
    description: 'Public anon key — used for client-side Supabase operations.',
    placeholder: 'eyJ…',
  },
  {
    id: 'supabase-service-key',
    label: 'Supabase Service Role Key',
    envVar: 'SUPABASE_SERVICE_ROLE_KEY',
    description: 'Secret service role key — used by the backend for admin operations.',
    placeholder: 'eyJ…',
  },
  {
    id: 'supabase-db-url',
    label: 'Supabase DB URL',
    envVar: 'SUPABASE_DB_URL',
    description: 'Direct PostgreSQL connection string for async SQLAlchemy + AsyncPostgresSaver.',
    placeholder: 'postgresql+asyncpg://postgres:[password]@db.xxxx.supabase.co:5432/postgres',
  },
];

const API_BASE = 'http://localhost:8000/api/v1';

// ── Icons ─────────────────────────────────────────────────────────────────────

function CopyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <rect x="4" y="4" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M2 8V2h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function ExternalIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <path d="M1.5 8.5L8.5 1.5M8.5 1.5H4M8.5 1.5V6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function LinkedInIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
    </svg>
  );
}

function CheckCircleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="6" stroke="var(--color-success)" strokeWidth="1.4"/>
      <path d="M4 7l2.5 2.5L10 5" stroke="var(--color-success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="6" stroke="var(--color-warning)" strokeWidth="1.4"/>
      <path d="M7 4v3M7 9.5v.5" stroke="var(--color-warning)" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

// ── KeyCard component ─────────────────────────────────────────────────────────

function KeyCard({ item }: { item: ApiKey }) {
  const [visible, setVisible] = useState(false);
  const [copied, setCopied] = useState(false);

  function copyEnvVar() {
    navigator.clipboard.writeText(item.envVar);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className={styles.card}>
      <div className={styles.cardTop}>
        <div className={styles.cardMeta}>
          <span className={styles.cardLabel}>{item.label}</span>
          <code className={`${styles.envVar} mono`}>{item.envVar}</code>
        </div>
        <div className={styles.cardActions}>
          {item.link && (
            <a
              href={item.link}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.linkBtn}
              id={`int-link-${item.id}`}
            >
              {item.linkLabel} <ExternalIcon />
            </a>
          )}
          <button
            className={`${styles.copyBtn} ${copied ? styles.copyDone : ''}`}
            onClick={copyEnvVar}
            id={`int-copy-${item.id}`}
            title="Copy env variable name"
          >
            {copied ? 'Copied!' : <><CopyIcon /> Copy var</>}
          </button>
        </div>
      </div>
      <p className={styles.cardDesc}>{item.description}</p>
      <div className={styles.valueRow}>
        <input
          id={item.id}
          className={styles.valueInput}
          type={visible ? 'text' : 'password'}
          placeholder={item.placeholder}
          defaultValue=""
          readOnly
          onClick={() => setVisible(v => !v)}
          style={{ cursor: 'pointer' }}
          title="Values are read from backend .env — click to toggle visibility"
        />
        <span className={styles.backendNote}>Set in backend/.env</span>
      </div>
    </div>
  );
}

// ── LinkedIn Session Card ──────────────────────────────────────────────────────

function LinkedInCard() {
  const [status, setStatus] = useState<LinkedInAuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [initiating, setInitiating] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/linkedin/auth/status`);
      if (res.ok) {
        const data: LinkedInAuthStatus = await res.json();
        setStatus(data);
      } else {
        setStatus(null);
      }
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  // Poll every 5 s while initiating (waiting for user to complete login)
  useEffect(() => {
    if (!initiating) return;
    const interval = setInterval(async () => {
      await checkStatus();
      setStatus(prev => {
        if (prev?.authenticated) {
          setInitiating(false);
          setToast('LinkedIn connected successfully!');
        }
        return prev;
      });
    }, 5000);
    return () => clearInterval(interval);
  }, [initiating, checkStatus]);

  async function handleConnect() {
    setInitiating(true);
    try {
      const res = await fetch(`${API_BASE}/linkedin/auth/init`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setToast(data.message || 'Browser opening on server…');
      } else {
        setToast('Failed to start login — check server logs.');
        setInitiating(false);
      }
    } catch {
      setToast('Could not reach backend.');
      setInitiating(false);
    }
    setTimeout(() => setToast(null), 7000);
  }

  async function handleRefresh() {
    setLoading(true);
    await checkStatus();
  }

  const isAuth = status?.authenticated;

  return (
    <div className={`${styles.card} ${styles.linkedinCard}`}>
      {/* Header row */}
      <div className={styles.cardTop}>
        <div className={styles.cardMeta}>
          <div className={styles.linkedinTitle}>
            <span className={styles.linkedinIcon} style={{ color: '#0A66C2' }}>
              <LinkedInIcon />
            </span>
            <span className={styles.cardLabel}>LinkedIn Easy Apply</span>
          </div>
          <span className={styles.cardDesc} style={{ marginBottom: 0 }}>
            Stored Playwright session for automated LinkedIn Easy Apply submissions.
          </span>
        </div>
        <div className={styles.cardActions}>
          <button
            className={styles.copyBtn}
            onClick={handleRefresh}
            disabled={loading}
            id="int-linkedin-refresh"
            title="Re-check session status"
          >
            {loading ? '…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Status row */}
      <div className={styles.linkedinStatus}>
        {loading ? (
          <span className={styles.linkedinStatusText} style={{ color: 'var(--color-text-tertiary)' }}>
            Checking session…
          </span>
        ) : isAuth ? (
          <span className={styles.linkedinStatusText} style={{ color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircleIcon /> Authenticated
          </span>
        ) : (
          <span className={styles.linkedinStatusText} style={{ color: 'var(--color-warning)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <WarningIcon /> {status?.session_file_exists ? 'Session expired' : 'Not connected'}
          </span>
        )}
        {status?.message && !loading && (
          <span className={styles.linkedinMsg}>{status.message}</span>
        )}
      </div>

      {/* CTA buttons */}
      <div className={styles.linkedinActions}>
        {!isAuth && (
          <button
            className={`${styles.connectBtn} ${initiating ? styles.connectBtnBusy : ''}`}
            onClick={handleConnect}
            disabled={initiating || loading}
            id="int-linkedin-connect"
          >
            {initiating ? (
              <>
                <span className={styles.pulse} /> Waiting for login…
              </>
            ) : status?.session_file_exists ? (
              'Re-authenticate'
            ) : (
              'Connect LinkedIn'
            )}
          </button>
        )}
        {isAuth && (
          <button
            className={styles.connectBtn}
            onClick={handleConnect}
            disabled={initiating || loading}
            id="int-linkedin-reauth"
            style={{ background: 'transparent', borderColor: 'var(--color-border)', color: 'var(--color-text-secondary)' }}
          >
            Re-authenticate
          </button>
        )}
        <span className={styles.backendNote} style={{ marginLeft: 'auto' }}>
          Or: <code className="mono" style={{ fontSize: 'var(--text-xs)' }}>python -m app.automation.linkedin_login</code>
        </span>
      </div>

      {/* Toast */}
      {toast && (
        <div className={styles.linkedinToast}>{toast}</div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export function IntegrationsPage() {
  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Integrations</h1>
        <p className={styles.subtitle}>
          API keys and service connections used by the Recon backend. All keys are stored server-side in <code className="mono">backend/.env</code>.
        </p>
      </div>

      {/* Info banner */}
      <div className={styles.banner}>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ flexShrink: 0 }}>
          <circle cx="7" cy="7" r="6" stroke="var(--color-warning)" strokeWidth="1.4"/>
          <path d="M7 4v3M7 9.5v.5" stroke="var(--color-warning)" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <span>
          Keys are never exposed to the browser. Copy the variable name and set it in <code className="mono">backend/.env</code> on your server.
        </span>
      </div>

      {/* LinkedIn Session Card (special) */}
      <div className={styles.cards}>
        <LinkedInCard />
      </div>

      {/* API Key cards */}
      <div className={styles.cards}>
        {API_KEYS.map(k => <KeyCard key={k.id} item={k} />)}
      </div>

      {/* .env.example reference */}
      <div className={styles.envBlock}>
        <div className={styles.envHeader}>
          <span className="label">.env.example reference</span>
        </div>
        <pre className={`${styles.envCode} mono`}>
{`NVIDIA_API_KEY=nvapi-…
NVIDIA_MODEL=meta/llama-4-scout-17b-16e-instruct

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ…
SUPABASE_SERVICE_ROLE_KEY=eyJ…
SUPABASE_DB_URL=postgresql+asyncpg://postgres:[pw]@db.xxxx.supabase.co:5432/postgres

# LinkedIn Easy Apply (generated by running: python -m app.automation.linkedin_login)
LINKEDIN_SESSION_PATH=.linkedin_session.json`}
        </pre>
      </div>
    </div>
  );
}
