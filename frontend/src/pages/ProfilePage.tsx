import { useState, useEffect } from 'react';
import styles from './ProfilePage.module.css';

const STORAGE_KEY = 'recon_profile';

interface ProfileData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  linkedin_url: string;
  portfolio_url: string;
}

const EMPTY: ProfileData = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  linkedin_url: '',
  portfolio_url: '',
};

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2.5 7L5.5 10L11.5 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function UserCircleIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="23" stroke="currentColor" strokeWidth="1.5"/>
      <circle cx="24" cy="19" r="7" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M8 40c0-8.837 7.163-16 16-16s16 7.163 16 16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

interface FieldProps {
  id: string;
  label: string;
  type?: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
}

function Field({ id, label, type = 'text', placeholder, value, onChange }: FieldProps) {
  return (
    <div className={styles.field}>
      <label className={`${styles.fieldLabel} label`} htmlFor={id}>{label}</label>
      <input
        id={id}
        className={styles.input}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        autoComplete="off"
        spellCheck={false}
      />
    </div>
  );
}

export function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData>(EMPTY);
  const [saved, setSaved] = useState(false);
  const [dirty, setDirty] = useState(false);

  // Load from API / localStorage on mount
  useEffect(() => {
    let localData = EMPTY;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) localData = { ...EMPTY, ...JSON.parse(raw) };
      setProfile(localData);
    } catch {}

    fetch('/api/v1/user/profile')
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data) {
          const merged = { ...EMPTY, ...data };
          setProfile(merged);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
        }
      })
      .catch(() => {});
  }, []);

  function update(key: keyof ProfileData) {
    return (value: string) => {
      setProfile(p => ({ ...p, [key]: value }));
      setDirty(true);
      setSaved(false);
    };
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    
    try {
      await fetch('/api/v1/user/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });
    } catch {}

    setSaved(true);
    setDirty(false);
    setTimeout(() => setSaved(false), 2500);
  }

  const displayName = [profile.first_name, profile.last_name].filter(Boolean).join(' ') || 'Your Name';
  const initials = [profile.first_name[0], profile.last_name[0]].filter(Boolean).join('').toUpperCase() || '?';

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>Profile</h1>
        <p className={styles.subtitle}>
          Your candidate identity — used to pre-fill forms during automated applications.
        </p>
      </div>

      <div className={styles.layout}>
        {/* Avatar / preview panel */}
        <div className={styles.avatarPanel}>
          <div className={styles.avatarCircle}>
            {initials !== '?' ? (
              <span className={styles.avatarInitials}>{initials}</span>
            ) : (
              <span className={styles.avatarIcon}><UserCircleIcon /></span>
            )}
          </div>
          <p className={styles.displayName}>{displayName}</p>
          {profile.email && <p className={styles.displayEmail}>{profile.email}</p>}
          {profile.linkedin_url && (
            <a
              href={profile.linkedin_url.startsWith('http') ? profile.linkedin_url : `https://${profile.linkedin_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.displayLink}
              id="profile-linkedin-preview"
            >
              LinkedIn ↗
            </a>
          )}
          {profile.portfolio_url && (
            <a
              href={profile.portfolio_url.startsWith('http') ? profile.portfolio_url : `https://${profile.portfolio_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.displayLink}
              id="profile-portfolio-preview"
            >
              Portfolio ↗
            </a>
          )}
          <div className={`${styles.storageNote} label`}>Stored locally in browser</div>
        </div>

        {/* Form */}
        <form className={styles.form} onSubmit={handleSave} id="profile-form">
          <div className={styles.section}>
            <span className={`${styles.sectionLabel} label`}>Identity</span>
            <div className={styles.row}>
              <Field id="profile-first-name" label="First Name" placeholder="Parth" value={profile.first_name} onChange={update('first_name')} />
              <Field id="profile-last-name" label="Last Name" placeholder="Shah" value={profile.last_name} onChange={update('last_name')} />
            </div>
            <Field id="profile-email" label="Email" type="email" placeholder="parth@example.com" value={profile.email} onChange={update('email')} />
            <Field id="profile-phone" label="Phone" type="tel" placeholder="+1 (555) 000-0000" value={profile.phone} onChange={update('phone')} />
          </div>

          <div className={styles.section}>
            <span className={`${styles.sectionLabel} label`}>Links</span>
            <Field
              id="profile-linkedin"
              label="LinkedIn URL"
              placeholder="https://linkedin.com/in/username"
              value={profile.linkedin_url}
              onChange={update('linkedin_url')}
            />
            <Field
              id="profile-portfolio"
              label="GitHub / Portfolio URL"
              placeholder="https://github.com/username"
              value={profile.portfolio_url}
              onChange={update('portfolio_url')}
            />
          </div>

          <div className={styles.formFooter}>
            {saved && (
              <span className={styles.savedBadge}>
                <CheckIcon /> Saved
              </span>
            )}
            <button
              id="profile-save-btn"
              type="submit"
              className={styles.saveBtn}
              disabled={!dirty}
            >
              Save Profile
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
