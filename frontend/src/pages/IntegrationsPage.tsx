import { useState } from 'react';
import styles from './IntegrationsPage.module.css';

interface ApiKey {
  id: string;
  label: string;
  envVar: string;
  description: string;
  placeholder: string;
  link?: string;
  linkLabel?: string;
}

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

function KeyCard({ item }: { item: ApiKey }) {
  const [visible, setVisible] = useState(false);
  const [copied, setCopied] = useState(false);
  const val = `\${${item.envVar}}`;

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

export function IntegrationsPage() {
  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Integrations</h1>
        <p className={styles.subtitle}>
          API keys and service connections used by the Recon backend. All keys are stored server-side in <code className="mono">/backend/.env</code>.
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

      {/* Key cards */}
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
SUPABASE_DB_URL=postgresql+asyncpg://postgres:[pw]@db.xxxx.supabase.co:5432/postgres`}
        </pre>
      </div>
    </div>
  );
}
