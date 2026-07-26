import { useState, useEffect, useRef } from 'react';
import styles from './AutomationLogsPage.module.css';

/* ── Simulated log stream derived from application history ── */

interface LogEntry {
  id: string;
  ts: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS' | 'DEBUG';
  message: string;
  context?: string;
}

const DEMO_LOGS: LogEntry[] = [
  { id: '1',  ts: '12:04:01.332', level: 'INFO',    message: 'BrowserSession.start() — launching Playwright Chromium', context: 'greenhouse.py' },
  { id: '2',  ts: '12:04:01.891', level: 'INFO',    message: 'Navigating to job application URL', context: 'greenhouse.py' },
  { id: '3',  ts: '12:04:02.441', level: 'INFO',    message: 'Detected platform: Greenhouse', context: '_detect_platform' },
  { id: '4',  ts: '12:04:02.892', level: 'DEBUG',   message: 'safe_fill(#first_name) → "Parth"', context: 'browser.py' },
  { id: '5',  ts: '12:04:03.011', level: 'DEBUG',   message: 'safe_fill(#last_name) → "Shah"', context: 'browser.py' },
  { id: '6',  ts: '12:04:03.198', level: 'DEBUG',   message: 'safe_fill(#email) → "parth@example.com"', context: 'browser.py' },
  { id: '7',  ts: '12:04:03.401', level: 'DEBUG',   message: 'safe_fill(#phone) → "+1 (555) 000-0000"', context: 'browser.py' },
  { id: '8',  ts: '12:04:04.012', level: 'INFO',    message: 'upload_file(resume_input, tailored_resume.pdf)', context: 'browser.py' },
  { id: '9',  ts: '12:04:05.223', level: 'INFO',    message: 'Waiting for upload confirmation…', context: 'greenhouse.py' },
  { id: '10', ts: '12:04:06.001', level: 'SUCCESS', message: 'Resume uploaded successfully', context: 'greenhouse.py' },
  { id: '11', ts: '12:04:06.334', level: 'DEBUG',   message: 'safe_fill(#linkedin_url) → "https://linkedin.com/in/parth"', context: 'browser.py' },
  { id: '12', ts: '12:04:07.120', level: 'INFO',    message: 'safe_click(#submit_application)', context: 'browser.py' },
  { id: '13', ts: '12:04:08.441', level: 'SUCCESS', message: 'Application submitted — Greenhouse confirmation detected', context: 'greenhouse.py' },
  { id: '14', ts: '12:04:08.443', level: 'INFO',    message: 'BrowserSession.close()', context: 'browser.py' },
  { id: '15', ts: '12:04:08.450', level: 'INFO',    message: 'submission_status → "applied"', context: 'apply_agent.py' },
];

const EMPTY_LOGS: LogEntry[] = [
  { id: 'e1', ts: '--:--:--.---', level: 'INFO', message: 'No automation runs recorded yet.', context: 'system' },
  { id: 'e2', ts: '--:--:--.---', level: 'INFO', message: 'Logs appear here after a pipeline run reaches the Apply Agent.', context: 'system' },
];

const LEVEL_COLORS: Record<LogEntry['level'], string> = {
  INFO:    'var(--color-text-secondary)',
  DEBUG:   'var(--color-text-tertiary)',
  WARN:    'var(--color-warning)',
  ERROR:   'var(--color-danger)',
  SUCCESS: 'var(--color-success)',
};

function LogRow({ entry, visible }: { entry: LogEntry; visible: boolean }) {
  return (
    <div className={`${styles.logRow} ${visible ? styles.logRowVisible : ''}`}>
      <span className={`${styles.ts} mono`}>{entry.ts}</span>
      <span
        className={`${styles.level} mono`}
        style={{ color: LEVEL_COLORS[entry.level] }}
      >
        {entry.level.padEnd(7)}
      </span>
      {entry.context && (
        <span className={`${styles.ctx} mono`}>[{entry.context}]</span>
      )}
      <span className={styles.msg}>{entry.message}</span>
    </div>
  );
}

export function AutomationLogsPage() {
  const [filter, setFilter] = useState<'ALL' | LogEntry['level']>('ALL');
  const [visibleCount, setVisibleCount] = useState(0);
  const [playing, setPlaying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasRuns = true; // flip to false to show empty state

  const logs = hasRuns ? DEMO_LOGS : EMPTY_LOGS;
  const filtered = filter === 'ALL' ? logs : logs.filter(l => l.level === filter);

  function startPlayback() {
    setVisibleCount(0);
    setPlaying(true);
  }

  useEffect(() => {
    if (!playing) return;
    if (visibleCount >= logs.length) {
      setPlaying(false);
      return;
    }
    intervalRef.current = setInterval(() => {
      setVisibleCount(c => {
        if (c >= logs.length) {
          setPlaying(false);
          if (intervalRef.current) clearInterval(intervalRef.current);
          return c;
        }
        return c + 1;
      });
    }, 120);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, logs.length]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [visibleCount]);

  const FILTERS: Array<'ALL' | LogEntry['level']> = ['ALL', 'INFO', 'DEBUG', 'WARN', 'ERROR', 'SUCCESS'];

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Automation Logs</h1>
        <p className={styles.subtitle}>
          Playwright browser automation trace — every form fill, upload, and click.
        </p>
      </div>

      {/* Toolbar */}
      <div className={styles.toolbar}>
        <div className={styles.filters}>
          {FILTERS.map(f => (
            <button
              key={f}
              id={`log-filter-${f}`}
              className={`${styles.filterBtn} ${filter === f ? styles.filterActive : ''}`}
              onClick={() => setFilter(f)}
              style={f !== 'ALL' ? { color: filter === f ? LEVEL_COLORS[f as LogEntry['level']] : undefined } : undefined}
            >
              {f}
            </button>
          ))}
        </div>
        <div className={styles.toolbarRight}>
          <span className={`${styles.lineCount} mono`}>{filtered.length} lines</span>
          {hasRuns && (
            <button
              id="log-replay-btn"
              className={styles.replayBtn}
              onClick={startPlayback}
              disabled={playing}
            >
              {playing ? 'Replaying…' : '▶  Replay'}
            </button>
          )}
        </div>
      </div>

      {/* Log terminal */}
      <div className={styles.terminal}>
        <div className={styles.terminalHeader}>
          <div className={styles.terminalDots}>
            <span className={styles.dot} style={{ background: '#FF5F56' }} />
            <span className={styles.dot} style={{ background: '#FFBD2E' }} />
            <span className={styles.dot} style={{ background: '#27C93F' }} />
          </div>
          <span className={`${styles.terminalTitle} mono`}>recon / automation / browser.log</span>
        </div>
        <div className={styles.terminalBody}>
          {filtered.map((entry, i) => (
            <LogRow
              key={entry.id}
              entry={entry}
              visible={!playing || i < visibleCount}
            />
          ))}
          {playing && (
            <div className={`${styles.cursor} mono`}>█</div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
