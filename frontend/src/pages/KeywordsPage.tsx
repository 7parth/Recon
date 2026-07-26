import { useState, useEffect } from 'react';
import styles from './KeywordsPage.module.css';

const STORAGE_KEY = 'recon_keywords';

const DEFAULT_SKILLS = [
  'Python', 'TypeScript', 'React', 'FastAPI', 'PostgreSQL',
  'Docker', 'Kubernetes', 'AWS', 'Machine Learning', 'REST APIs',
];

function TagIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M7.5 1H12.5V6L7 11.5L2.5 7L7.5 1Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
      <circle cx="10" cy="4" r="1" fill="currentColor"/>
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 2L8 8M8 2L2 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function KeywordsPage() {
  const [keywords, setKeywords] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      setKeywords(raw ? JSON.parse(raw) : DEFAULT_SKILLS);
    } catch {
      setKeywords(DEFAULT_SKILLS);
    }
  }, []);

  function addKeyword() {
    const trimmed = input.trim();
    if (!trimmed || keywords.includes(trimmed)) return;
    setKeywords(k => [...k, trimmed]);
    setInput('');
    setSaved(false);
  }

  function removeKeyword(kw: string) {
    setKeywords(k => k.filter(x => x !== kw));
    setSaved(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') { e.preventDefault(); addKeyword(); }
    if (e.key === ',') { e.preventDefault(); addKeyword(); }
  }

  function handleSave() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keywords));
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  function handleReset() {
    setKeywords(DEFAULT_SKILLS);
    setSaved(false);
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Skills &amp; Keywords</h1>
        <p className={styles.subtitle}>
          Your skill set and keywords — used by the ATS audit agent to evaluate resume coverage.
        </p>
      </div>

      {/* Stats strip */}
      <div className={styles.stats}>
        <div className={styles.statItem}>
          <span className={`${styles.statValue} mono`}>{keywords.length}</span>
          <span className={styles.statLabel}>Keywords defined</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>These appear in ATS keyword audits during pipeline runs.</span>
        </div>
      </div>

      {/* Add input */}
      <div className={styles.addSection}>
        <span className="label">Add Keyword</span>
        <div className={styles.addRow}>
          <input
            id="kw-input"
            className={styles.input}
            type="text"
            placeholder="e.g. LangGraph, Supabase, Node.js (Enter or comma to add)"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            autoComplete="off"
            spellCheck={false}
          />
          <button
            id="kw-add-btn"
            className={styles.addBtn}
            onClick={addKeyword}
            disabled={!input.trim()}
          >
            Add
          </button>
        </div>
      </div>

      {/* Keyword cloud */}
      <div className={styles.cloudSection}>
        <span className="label">Your Keywords</span>
        <div className={styles.cloud}>
          {keywords.length === 0 && (
            <p className={styles.emptyCloud}>No keywords added yet.</p>
          )}
          {keywords.map(kw => (
            <div key={kw} className={styles.tag} id={`kw-tag-${kw.replace(/\s/g, '-')}`}>
              <TagIcon />
              <span className={styles.tagText}>{kw}</span>
              <button
                className={styles.removeBtn}
                onClick={() => removeKeyword(kw)}
                aria-label={`Remove ${kw}`}
              >
                <XIcon />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className={styles.actions}>
        <button id="kw-reset-btn" className={styles.resetBtn} onClick={handleReset}>
          Reset to defaults
        </button>
        <div className={styles.saveGroup}>
          {saved && (
            <span className={styles.savedBadge}>
              <CheckIcon /> Saved
            </span>
          )}
          <button id="kw-save-btn" className={styles.saveBtn} onClick={handleSave}>
            Save Keywords
          </button>
        </div>
      </div>

      {/* Info note */}
      <div className={styles.note}>
        <span className="label" style={{ color: 'var(--color-text-tertiary)' }}>
          Stored locally · Not sent to any server
        </span>
      </div>
    </div>
  );
}
