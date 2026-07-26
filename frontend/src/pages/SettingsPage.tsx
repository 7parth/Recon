import { useState, useEffect } from 'react';
import styles from './SettingsPage.module.css';

const STORAGE_KEY = 'recon_settings';

interface AppSettings {
  match_threshold: number;
  nvidia_model: string;
  embedding_model: string;
  auto_apply: boolean;
  enable_notifications: boolean;
}

const DEFAULTS: AppSettings = {
  match_threshold: 70,
  nvidia_model: 'meta/llama-4-scout-17b-16e-instruct',
  embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
  auto_apply: false,
  enable_notifications: true,
};

const NVIDIA_MODELS = [
  'meta/llama-4-scout-17b-16e-instruct',
  'meta/llama-3.1-70b-instruct',
  'meta/llama-3.1-8b-instruct',
  'nvidia/llama-3.1-nemotron-70b-instruct',
  'mistralai/mixtral-8x7b-instruct-v0.1',
];

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function SectionHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className={styles.sectionHeader}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      {description && <p className={styles.sectionDesc}>{description}</p>}
    </div>
  );
}

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULTS);
  const [saved, setSaved] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setSettings({ ...DEFAULTS, ...JSON.parse(raw) });
    } catch {}
  }, []);

  function update<K extends keyof AppSettings>(key: K, value: AppSettings[K]) {
    setSettings(s => ({ ...s, [key]: value }));
    setDirty(true);
    setSaved(false);
  }

  function handleSave() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    setSaved(true);
    setDirty(false);
    setTimeout(() => setSaved(false), 2500);
  }

  function handleReset() {
    setSettings(DEFAULTS);
    setDirty(true);
    setSaved(false);
  }

  const scoreColor = settings.match_threshold >= 80
    ? 'var(--color-success)'
    : settings.match_threshold >= 60
    ? 'var(--color-warning)'
    : 'var(--color-danger)';

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Preferences</h1>
        <p className={styles.subtitle}>
          Configure pipeline behavior, thresholds, and model choices.
        </p>
      </div>

      <div className={styles.sections}>
        {/* ── Pipeline ── */}
        <div className={styles.section}>
          <SectionHeader title="Pipeline" description="Controls how runs are scored and gated." />

          <div className={styles.fieldRow}>
            <div className={styles.fieldInfo}>
              <label className={`${styles.fieldLabel} label`} htmlFor="setting-threshold">
                Match Score Threshold
              </label>
              <p className={styles.fieldDesc}>
                Applications with a score below this threshold are auto-skipped.
              </p>
            </div>
            <div className={styles.sliderGroup}>
              <span className={`${styles.sliderVal} mono`} style={{ color: scoreColor }}>
                {settings.match_threshold}%
              </span>
              <input
                id="setting-threshold"
                type="range"
                min={40}
                max={95}
                step={5}
                value={settings.match_threshold}
                onChange={e => update('match_threshold', Number(e.target.value))}
                className={styles.slider}
              />
              <div className={styles.sliderLabels}>
                <span>40%</span>
                <span>95%</span>
              </div>
            </div>
          </div>

          <div className={styles.fieldRow}>
            <div className={styles.fieldInfo}>
              <label className={`${styles.fieldLabel} label`} htmlFor="setting-auto-apply">
                Auto-Apply After Approval
              </label>
              <p className={styles.fieldDesc}>
                When enabled, the apply agent runs immediately after you approve a review.
              </p>
            </div>
            <button
              id="setting-auto-apply"
              role="switch"
              aria-checked={settings.auto_apply}
              className={`${styles.toggle} ${settings.auto_apply ? styles.toggleOn : ''}`}
              onClick={() => update('auto_apply', !settings.auto_apply)}
            >
              <span className={styles.toggleKnob} />
            </button>
          </div>
        </div>

        {/* ── Models ── */}
        <div className={styles.section}>
          <SectionHeader title="Models" description="LLM and embedding model selection for the agent graph." />

          <div className={styles.fieldRow}>
            <div className={styles.fieldInfo}>
              <label className={`${styles.fieldLabel} label`} htmlFor="setting-nvidia-model">
                NVIDIA LLM Model
              </label>
              <p className={styles.fieldDesc}>
                Used for extraction (temp 0.2) and creative generation (temp 0.7).
              </p>
            </div>
            <select
              id="setting-nvidia-model"
              className={styles.select}
              value={settings.nvidia_model}
              onChange={e => update('nvidia_model', e.target.value)}
            >
              {NVIDIA_MODELS.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div className={styles.fieldRow}>
            <div className={styles.fieldInfo}>
              <label className={`${styles.fieldLabel} label`} htmlFor="setting-emb-model">
                Embedding Model
              </label>
              <p className={styles.fieldDesc}>
                Sentence-transformers model for pre-filter similarity scoring.
              </p>
            </div>
            <input
              id="setting-emb-model"
              className={styles.input}
              type="text"
              value={settings.embedding_model}
              onChange={e => update('embedding_model', e.target.value)}
              spellCheck={false}
              autoComplete="off"
            />
          </div>
        </div>

        {/* ── Notifications ── */}
        <div className={styles.section}>
          <SectionHeader title="Notifications" description="In-app notification preferences." />

          <div className={styles.fieldRow}>
            <div className={styles.fieldInfo}>
              <label className={`${styles.fieldLabel} label`} htmlFor="setting-notifications">
                Review Queue Alerts
              </label>
              <p className={styles.fieldDesc}>
                Show badge count in sidebar when applications are pending review.
              </p>
            </div>
            <button
              id="setting-notifications"
              role="switch"
              aria-checked={settings.enable_notifications}
              className={`${styles.toggle} ${settings.enable_notifications ? styles.toggleOn : ''}`}
              onClick={() => update('enable_notifications', !settings.enable_notifications)}
            >
              <span className={styles.toggleKnob} />
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <button id="settings-reset-btn" className={styles.resetBtn} onClick={handleReset}>
          Reset to defaults
        </button>
        <div className={styles.saveGroup}>
          {saved && (
            <span className={styles.savedBadge}>
              <CheckIcon /> Saved
            </span>
          )}
          <button
            id="settings-save-btn"
            className={styles.saveBtn}
            onClick={handleSave}
            disabled={!dirty}
          >
            Save Preferences
          </button>
        </div>
      </div>

      <p className={styles.storageNote}>
        Settings stored locally in browser — not synced to backend.
      </p>
    </div>
  );
}
