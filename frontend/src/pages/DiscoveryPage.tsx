import { useState, useEffect, useRef } from 'react';
import { api, type DiscoveryPreferencesUpdate } from '../lib/api';
import type { DiscoveryPreferences, DiscoverySession, SessionStatus } from '../lib/types';
import styles from './DiscoveryPage.module.css';

/* ── Helpers ── */

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getStatusColor(status: SessionStatus | string): string {
  switch (status) {
    case 'running':               return 'var(--color-accent)';
    case 'completed':             return 'var(--color-success)';
    case 'completed_with_errors': return 'var(--color-warning)';
    case 'failed':                return 'var(--color-danger)';
    case 'cancelled':             return 'var(--color-text-tertiary)';
    default:                      return 'var(--color-text-secondary)';
  }
}

function getStatusLabel(status: SessionStatus | string): string {
  switch (status) {
    case 'running':               return 'RUNNING';
    case 'completed':             return 'COMPLETED';
    case 'completed_with_errors': return 'COMPLETED W/ ERRORS';
    case 'failed':                return 'FAILED';
    case 'cancelled':             return 'CANCELLED';
    default:                      return status.toUpperCase();
  }
}

/* ── Tag input chip component ── */
interface TagInputProps {
  id: string;
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
}

function TagInput({ id, label, tags, onChange, placeholder, maxTags }: TagInputProps) {
  const [input, setInput] = useState('');

  function addTag(raw: string) {
    const value = raw.trim();
    if (!value) return;
    if (tags.includes(value)) { setInput(''); return; }
    if (maxTags && tags.length >= maxTags) return;
    onChange([...tags, value]);
    setInput('');
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(input.replace(/,$/, ''));
    } else if (e.key === 'Backspace' && !input && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    // Auto-add on trailing comma
    if (val.endsWith(',')) {
      addTag(val.slice(0, -1));
    } else {
      setInput(val);
    }
  }

  const atMax = maxTags !== undefined && tags.length >= maxTags;

  return (
    <div className={styles.field}>
      <label className={`${styles.fieldLabel} label`} htmlFor={id}>{label}</label>
      <div className={styles.tagInputWrapper}>
        {tags.map((tag) => (
          <span key={tag} className={styles.chip}>
            {tag}
            <button
              type="button"
              className={styles.chipRemove}
              onClick={() => onChange(tags.filter(t => t !== tag))}
              aria-label={`Remove ${tag}`}
            >
              ×
            </button>
          </span>
        ))}
        {!atMax && (
          <input
            id={id}
            type="text"
            className={styles.tagInput}
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={tags.length === 0 ? placeholder : undefined}
            autoComplete="off"
            spellCheck={false}
          />
        )}
      </div>
      {maxTags && (
        <p className={styles.fieldHint}>{tags.length}/{maxTags} {atMax ? '— limit reached' : ''}</p>
      )}
    </div>
  );
}

/* ── Session detail modal ── */
interface SessionModalProps {
  session: DiscoverySession;
  onClose: () => void;
}

function SessionModal({ session, onClose }: SessionModalProps) {
  const backdropRef = useRef<HTMLDivElement>(null);

  function handleBackdropClick(e: React.MouseEvent) {
    if (e.target === backdropRef.current) onClose();
  }

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const statusColor = getStatusColor(session.session_status);

  return (
    <div className={styles.modalBackdrop} ref={backdropRef} onClick={handleBackdropClick}>
      <div className={styles.modal} role="dialog" aria-modal="true" aria-label="Session details">
        <div className={styles.modalHeader}>
          <div>
            <h2 className={styles.modalTitle}>Session Details</h2>
            <p className={`${styles.modalId} mono`}>{session.session_id}</p>
          </div>
          <button className={styles.modalClose} onClick={onClose} aria-label="Close modal">×</button>
        </div>

        <div className={styles.modalBody}>
          <div className={styles.modalRow}>
            <span className={styles.modalRowLabel}>Status</span>
            <span className={styles.badge} style={{ borderColor: statusColor, color: statusColor }}>
              {getStatusLabel(session.session_status)}
            </span>
          </div>
          <div className={styles.modalRow}>
            <span className={styles.modalRowLabel}>Started</span>
            <span className={`${styles.modalRowValue} mono`}>{formatDate(session.started_at)}</span>
          </div>
          {session.completed_at && (
            <div className={styles.modalRow}>
              <span className={styles.modalRowLabel}>Completed</span>
              <span className={`${styles.modalRowValue} mono`}>{formatDate(session.completed_at)}</span>
            </div>
          )}

          <div className={styles.modalDivider} />

          <div className={styles.modalCounters}>
            <div className={styles.counterCard}>
              <span className={styles.counterValue}>{session.jobs_found}</span>
              <span className={styles.counterLabel}>Found</span>
            </div>
            <div className={styles.counterCard}>
              <span className={styles.counterValue}>{session.jobs_processed}</span>
              <span className={styles.counterLabel}>Processed</span>
            </div>
            <div className={styles.counterCard}>
              <span className={styles.counterValue}>{session.jobs_pending_review}</span>
              <span className={styles.counterLabel}>In Review</span>
            </div>
            <div className={styles.counterCard}>
              <span className={styles.counterValue}>{session.jobs_applied}</span>
              <span className={styles.counterLabel}>Applied</span>
            </div>
            <div className={styles.counterCard}>
              <span className={styles.counterValue}>{session.jobs_skipped}</span>
              <span className={styles.counterLabel}>Skipped</span>
            </div>
            <div className={styles.counterCard}>
              <span className={styles.counterValue}>{session.jobs_failed}</span>
              <span className={styles.counterLabel}>Failed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Main page ── */

const PREF_DEFAULTS: DiscoveryPreferences = {
  target_role: '',
  preferred_locations: [],
  excluded_companies: [],
  max_jobs_per_session: 10,
  updated_at: null,
};

export function DiscoveryPage() {
  const [prefs, setPrefs] = useState<DiscoveryPreferences>(PREF_DEFAULTS);
  const [prefsDirty, setPrefsDirty] = useState(false);
  const [prefsSaved, setPrefsSaved] = useState(false);
  const [prefsError, setPrefsError] = useState<string | null>(null);

  const [sessions, setSessions] = useState<DiscoverySession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  const [sessionRunning, setSessionRunning] = useState(false);
  const [conflictBanner, setConflictBanner] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const [selectedSession, setSelectedSession] = useState<DiscoverySession | null>(null);

  /* Load preferences and sessions on mount */
  useEffect(() => {
    api.getDiscoveryPreferences()
      .then(data => setPrefs(data))
      .catch(() => {});

    loadSessions();
  }, []);

  async function loadSessions() {
    setSessionsLoading(true);
    try {
      const data = await api.listDiscoverySessions();
      setSessions(data);
      const running = data.some(s => s.session_status === 'running');
      setSessionRunning(running);
    } catch {
      /* noop */
    } finally {
      setSessionsLoading(false);
    }
  }

  /* Preferences handlers */
  function updatePref<K extends keyof DiscoveryPreferences>(key: K, value: DiscoveryPreferences[K]) {
    setPrefs(p => ({ ...p, [key]: value }));
    setPrefsDirty(true);
    setPrefsSaved(false);
    setPrefsError(null);
  }

  async function handleSavePrefs(e: React.FormEvent) {
    e.preventDefault();
    setPrefsError(null);
    const body: DiscoveryPreferencesUpdate = {
      target_role: prefs.target_role,
      preferred_locations: prefs.preferred_locations,
      excluded_companies: prefs.excluded_companies,
      max_jobs_per_session: prefs.max_jobs_per_session,
    };
    try {
      const updated = await api.updateDiscoveryPreferences(body);
      setPrefs(updated);
      setPrefsDirty(false);
      setPrefsSaved(true);
      setTimeout(() => setPrefsSaved(false), 2500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes('422')) {
        setPrefsError('Validation error: please check your inputs and try again.');
      } else {
        setPrefsError('Failed to save preferences. Please try again.');
      }
    }
  }

  /* Start session */
  async function handleStartSession() {
    setConflictBanner(null);
    setStartError(null);
    try {
      await api.startDiscoverySession();
      setSessionRunning(true);
      await loadSessions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes('409')) {
        setConflictBanner('A discovery session is already running.');
        setSessionRunning(true);
      } else if (msg.includes('422')) {
        setStartError('Validation error: check your discovery preferences before starting.');
      } else {
        setStartError('Failed to start session. Please try again.');
      }
    }
  }

  /* Cancel session */
  async function handleCancelSession(sessionId: string) {
    setCancellingId(sessionId);
    try {
      await api.cancelDiscoverySession(sessionId);
      setConflictBanner(null);
      await loadSessions();
    } catch {
      /* noop */
    } finally {
      setCancellingId(null);
    }
  }

  const runningSession = sessions.find(s => s.session_status === 'running');

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Job Discovery</h1>
          <p className={styles.subtitle}>
            Configure automated job discovery and manage active sessions.
          </p>
        </div>
        <button className={styles.refreshBtn} onClick={loadSessions} type="button">
          ↻ Refresh
        </button>
      </div>

      <div className={styles.layout}>
        {/* ── Preferences form ── */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={`${styles.sectionLabel} label`}>Preferences</span>
          </div>

          {/* 422 validation error banner */}
          {prefsError && (
            <div className={`${styles.banner} ${styles.bannerError}`} role="alert">
              {prefsError}
            </div>
          )}

          <form onSubmit={handleSavePrefs} className={styles.form} id="discovery-prefs-form">
            <div className={styles.field}>
              <label className={`${styles.fieldLabel} label`} htmlFor="discovery-target-role">
                Target Role
              </label>
              <input
                id="discovery-target-role"
                type="text"
                className={styles.input}
                value={prefs.target_role}
                onChange={e => updatePref('target_role', e.target.value)}
                placeholder="e.g. Software Engineer"
                autoComplete="off"
                spellCheck={false}
              />
            </div>

            <TagInput
              id="discovery-locations"
              label="Preferred Locations"
              tags={prefs.preferred_locations}
              onChange={tags => updatePref('preferred_locations', tags)}
              placeholder="e.g. San Francisco — press Enter or comma to add"
              maxTags={5}
            />

            <TagInput
              id="discovery-excluded-companies"
              label="Excluded Companies"
              tags={prefs.excluded_companies}
              onChange={tags => updatePref('excluded_companies', tags)}
              placeholder="e.g. Megacorp — press Enter or comma to add"
            />

            <div className={styles.field}>
              <label className={`${styles.fieldLabel} label`} htmlFor="discovery-max-jobs">
                Max Jobs Per Session
              </label>
              <input
                id="discovery-max-jobs"
                type="number"
                className={`${styles.input} ${styles.inputNarrow}`}
                min={1}
                max={50}
                value={prefs.max_jobs_per_session}
                onChange={e => {
                  const v = Math.max(1, Math.min(50, Number(e.target.value)));
                  updatePref('max_jobs_per_session', v);
                }}
              />
              <p className={styles.fieldHint}>Between 1 and 50</p>
            </div>

            <div className={styles.formFooter}>
              {prefsSaved && (
                <span className={styles.savedBadge} role="status">✓ Saved</span>
              )}
              <button
                id="discovery-save-prefs-btn"
                type="submit"
                className={styles.saveBtn}
                disabled={!prefsDirty}
              >
                Save Preferences
              </button>
            </div>
          </form>
        </div>

        {/* ── Start session ── */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={`${styles.sectionLabel} label`}>Session Control</span>
          </div>

          {/* 409 conflict banner */}
          {conflictBanner && (
            <div className={`${styles.banner} ${styles.bannerWarning}`} role="alert">
              {conflictBanner}
              {runningSession && (
                <>
                  {' — '}
                  <button
                    type="button"
                    className={styles.bannerLink}
                    onClick={() => handleCancelSession(runningSession.session_id)}
                    disabled={cancellingId === runningSession.session_id}
                  >
                    {cancellingId === runningSession.session_id ? 'Cancelling…' : 'Cancel session'}
                  </button>
                </>
              )}
            </div>
          )}

          {/* Start error banner */}
          {startError && (
            <div className={`${styles.banner} ${styles.bannerError}`} role="alert">
              {startError}
            </div>
          )}

          <div className={styles.sessionControlBody}>
            <p className={styles.sessionControlDesc}>
              Starts an automated discovery run based on your preferences. Only one session can run at a time.
            </p>
            <button
              id="discovery-start-btn"
              type="button"
              className={styles.startBtn}
              disabled={sessionRunning}
              onClick={handleStartSession}
            >
              {sessionRunning ? '● Session Running…' : 'Start Discovery Session'}
            </button>
            {sessionRunning && (
              <p className={styles.sessionRunningHint}>
                A session is currently active. Wait for it to finish or cancel it above.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ── Recent sessions table ── */}
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <span className={`${styles.sectionLabel} label`}>Recent Sessions</span>
          {!sessionsLoading && (
            <span className={`${styles.countPill} mono`}>{sessions.length}</span>
          )}
        </div>

        {sessionsLoading && (
          <div className={styles.skeletons}>
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className={styles.skeleton} style={{ animationDelay: `${i * 80}ms` }} />
            ))}
          </div>
        )}

        {!sessionsLoading && sessions.length === 0 && (
          <div className={styles.emptyState}>
            <p className={styles.emptyTitle}>No sessions yet</p>
            <p className={styles.emptySubtitle}>Start a discovery session to see results here.</p>
          </div>
        )}

        {!sessionsLoading && sessions.length > 0 && (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.th}>Started</th>
                  <th className={styles.th}>Status</th>
                  <th className={`${styles.th} ${styles.thRight}`}>Found</th>
                  <th className={`${styles.th} ${styles.thRight}`}>Processed</th>
                  <th className={`${styles.th} ${styles.thRight}`}>In Review</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(session => {
                  const statusColor = getStatusColor(session.session_status);
                  return (
                    <tr
                      key={session.session_id}
                      className={styles.tr}
                      onClick={() => setSelectedSession(session)}
                      tabIndex={0}
                      role="button"
                      aria-label={`View details for session started ${formatDate(session.started_at)}`}
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setSelectedSession(session); }}
                    >
                      <td className={`${styles.td} mono`}>{formatDate(session.started_at)}</td>
                      <td className={styles.td}>
                        <span
                          className={styles.badge}
                          style={{ borderColor: statusColor, color: statusColor }}
                        >
                          {getStatusLabel(session.session_status)}
                        </span>
                      </td>
                      <td className={`${styles.td} ${styles.tdRight} mono`}>{session.jobs_found}</td>
                      <td className={`${styles.td} ${styles.tdRight} mono`}>{session.jobs_processed}</td>
                      <td className={`${styles.td} ${styles.tdRight} mono`}>{session.jobs_pending_review}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Session detail modal ── */}
      {selectedSession && (
        <SessionModal
          session={selectedSession}
          onClose={() => setSelectedSession(null)}
        />
      )}
    </div>
  );
}
