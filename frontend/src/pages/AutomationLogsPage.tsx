import { useState, useEffect, useRef, useCallback } from 'react';
import { useDashboardData } from '../hooks/useDashboardData';
import styles from './AutomationLogsPage.module.css';

/* ── Types ── */

interface LogEntry {
  id: string;
  thread_id: string;
  ts: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS' | 'DEBUG';
  message: string;
  context?: string;
}

const DEMO_LOGS: LogEntry[] = [
  { id: 'e1', thread_id: 'demo', ts: '--:--:--.---', level: 'INFO', message: 'No active automation runs yet.', context: 'system' },
  { id: 'e2', thread_id: 'demo', ts: '--:--:--.---', level: 'INFO', message: 'Select a run below and approve it to trigger automation.', context: 'system' },
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

/* ── Run selector ── */
function RunSelector({
  runs,
  selected,
  onSelect,
}: {
  runs: { thread_id: string; status: string; created_at: string }[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  if (runs.length === 0) return null;
  return (
    <div className={styles.runSelector}>
      <label className={`${styles.runLabel} mono`}>Run</label>
      <select
        id="log-run-select"
        className={styles.runSelect}
        value={selected}
        onChange={e => onSelect(e.target.value)}
      >
        {runs.map(r => {
          const date = new Date(r.created_at).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
          });
          return (
            <option key={r.thread_id} value={r.thread_id}>
              {r.thread_id.slice(0, 8)}… · {r.status} · {date}
            </option>
          );
        })}
      </select>
    </div>
  );
}

/* ── Main page ── */
export function AutomationLogsPage() {
  const { history, loading } = useDashboardData();
  const [filter, setFilter] = useState<'ALL' | LogEntry['level']>('ALL');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [liveCount, setLiveCount] = useState(0);   // entries received via SSE (not replay)
  const [selectedThread, setSelectedThread] = useState('');
  const [connected, setConnected] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [visibleCount, setVisibleCount] = useState(0);

  const esRef = useRef<EventSource | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Derive runs list from history (only runs that went through automation) ──
  const allRuns = history.map(r => ({
    thread_id: r.thread_id,
    status: (r as any).status || (r as any).submission_status || 'unknown',
    created_at: r.created_at,
  }));

  // Auto-select first run
  useEffect(() => {
    if (!selectedThread && allRuns.length > 0) {
      setSelectedThread(allRuns[0].thread_id);
    }
  }, [allRuns.length]);

  // ── SSE connection ─────────────────────────────────────────────────────────
  const connectSSE = useCallback((threadId: string) => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }

    setLogs([]);
    setLiveCount(0);
    setConnected(false);

    if (!threadId) return;

    // First fetch buffered snapshot via JSON (fast, no streaming overhead)
    fetch(`/api/v1/runs/${threadId}/logs`)
      .then(r => r.json())
      .then((data: { entries: LogEntry[] }) => {
        if (data.entries?.length > 0) {
          setLogs(data.entries);
          setVisibleCount(data.entries.length);
        }
      })
      .catch(() => {/* ignore if run has no logs yet */});

    // Then open SSE for live updates
    const es = new EventSource(`/api/v1/runs/${threadId}/logs/stream`);
    esRef.current = es;

    es.onopen = () => setConnected(true);

    es.onmessage = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'log') {
          setLogs(prev => [...prev, data as LogEntry]);
          setLiveCount(c => c + 1);
          setVisibleCount(c => c + 1);
        }
      } catch {/* ignore malformed */}
    };

    es.onerror = () => setConnected(false);

    return () => { es.close(); };
  }, []);

  useEffect(() => {
    if (selectedThread) {
      return connectSSE(selectedThread);
    }
  }, [selectedThread, connectSSE]);

  // Cleanup on unmount
  useEffect(() => () => { esRef.current?.close(); }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [visibleCount]);

  // ── Replay animation (only for historical snapshot) ──────────────────────
  function startPlayback() {
    setVisibleCount(0);
    setPlaying(true);
  }

  useEffect(() => {
    if (!playing) return;
    if (visibleCount >= logs.length) { setPlaying(false); return; }
    intervalRef.current = setInterval(() => {
      setVisibleCount(c => {
        if (c >= logs.length) {
          setPlaying(false);
          if (intervalRef.current) clearInterval(intervalRef.current);
          return c;
        }
        return c + 1;
      });
    }, 100);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, logs.length]);

  // ── Filter ────────────────────────────────────────────────────────────────
  const filtered = filter === 'ALL' ? logs : logs.filter(l => l.level === filter);
  const FILTERS: Array<'ALL' | LogEntry['level']> = ['ALL', 'INFO', 'DEBUG', 'WARN', 'ERROR', 'SUCCESS'];

  const displayLogs = (logs.length === 0 && !loading) ? DEMO_LOGS : filtered;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Automation Logs</h1>
        <p className={styles.subtitle}>
          Playwright browser automation trace — every form fill, upload, and click.
        </p>
      </div>

      {/* Run selector */}
      {!loading && (
        <RunSelector runs={allRuns} selected={selectedThread} onSelect={setSelectedThread} />
      )}

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
          {connected && (
            <span className={`${styles.liveIndicator} mono`}>
              <span className={styles.liveDot} />LIVE
            </span>
          )}
          {liveCount > 0 && (
            <span className={`${styles.lineCount} mono`}>+{liveCount} new</span>
          )}
          <span className={`${styles.lineCount} mono`}>{displayLogs.length} lines</span>
          {logs.length > 0 && (
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
          <span className={`${styles.terminalTitle} mono`}>
            recon / automation / {selectedThread ? `${selectedThread.slice(0, 8)}.log` : 'browser.log'}
          </span>
        </div>
        <div className={styles.terminalBody}>
          {displayLogs.map((entry, i) => (
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
