import { useState, useRef } from 'react';
import { api } from '../lib/api';
import type { JobSearchResult } from '../lib/types';
import styles from './JobSearchPage.module.css';

function ExternalLinkIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 10L10 2M10 2H5M10 2V7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M9.5 9.5L12.5 12.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

interface JobSearchResponse {
  query: string;
  results: JobSearchResult[];
}

export function JobSearchPage() {
  const [role, setRole] = useState('');
  const [location, setLocation] = useState('');
  const [results, setResults] = useState<JobSearchResult[] | null>(null);
  const [queryLabel, setQueryLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const roleRef = useRef<HTMLInputElement>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const trimmedRole = role.trim();
    if (!trimmedRole) {
      roleRef.current?.focus();
      return;
    }
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await api.searchJobs({ role: trimmedRole, location: location.trim() || undefined }) as JobSearchResponse;
      setResults(data.results ?? []);
      setQueryLabel(data.query ?? trimmedRole);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <h1 className={styles.title}>Job Search</h1>
        <p className={styles.subtitle}>
          Search live job listings via DuckDuckGo. Paste a result URL directly into a new run.
        </p>
      </div>

      {/* ── Search Form ── */}
      <form className={styles.form} onSubmit={handleSearch} id="job-search-form">
        <div className={styles.inputGroup}>
          <label className={`${styles.inputLabel} label`} htmlFor="js-role">Role</label>
          <input
            id="js-role"
            ref={roleRef}
            className={styles.input}
            type="text"
            placeholder="e.g. Senior Software Engineer"
            value={role}
            onChange={e => setRole(e.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <div className={styles.inputGroup}>
          <label className={`${styles.inputLabel} label`} htmlFor="js-location">Location</label>
          <input
            id="js-location"
            className={styles.input}
            type="text"
            placeholder="e.g. Remote, San Francisco"
            value={location}
            onChange={e => setLocation(e.target.value)}
            autoComplete="off"
          />
        </div>
        <button
          id="js-search-btn"
          type="submit"
          className={styles.searchBtn}
          disabled={loading}
        >
          <SearchIcon />
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {/* ── Results Area ── */}
      <div className={styles.resultsArea}>
        {/* Loading skeletons */}
        {loading && (
          <div className={styles.skeletons}>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className={styles.skeleton} style={{ animationDelay: `${i * 60}ms` }} />
            ))}
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className={styles.errorState}>
            <span className={styles.errorDot} />
            <span>{error}</span>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && results !== null && results.length === 0 && (
          <div className={styles.emptyState}>
            <p className={styles.emptyTitle}>No results found</p>
            <p className={styles.emptySubtitle}>Try a different role or broaden the location.</p>
          </div>
        )}

        {/* Results */}
        {!loading && !error && results && results.length > 0 && (
          <>
            <div className={styles.resultsHeader}>
              <span className={`${styles.resultsCount} mono`}>{results.length} results</span>
              <span className={styles.queryLabel}>"{queryLabel}"</span>
            </div>
            <div className={styles.resultsList}>
              {results.map((r, i) => {
                let domain = '';
                try { domain = new URL(r.url).hostname.replace('www.', ''); } catch {}
                return (
                  <div key={i} className={styles.resultCard}>
                    <div className={styles.cardMeta}>
                      <span className={`${styles.domain} mono`}>{domain}</span>
                      <span className={styles.resultIndex} aria-hidden>{String(i + 1).padStart(2, '0')}</span>
                    </div>
                    <h3 className={styles.resultTitle}>{r.title}</h3>
                    {r.snippet && <p className={styles.resultSnippet}>{r.snippet}</p>}
                    <div className={styles.cardActions}>
                      <a
                        href={r.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.openLink}
                        id={`js-result-open-${i}`}
                      >
                        Open listing <ExternalLinkIcon />
                      </a>
                      <button
                        className={styles.copyBtn}
                        id={`js-result-copy-${i}`}
                        onClick={() => navigator.clipboard.writeText(r.url)}
                        title="Copy URL"
                      >
                        Copy URL
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* Initial state */}
        {!loading && !error && results === null && (
          <div className={styles.initialState}>
            <div className={styles.initialIcon}>
              <SearchIcon />
            </div>
            <p>Enter a role and hit Search to find live job listings.</p>
          </div>
        )}
      </div>
    </div>
  );
}
