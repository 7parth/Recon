import { useState } from 'react';
import { api } from '../../lib/api';
import { Button } from '../ui/Button';
import { X } from 'lucide-react';
import styles from './StartRunModal.module.css';

interface StartRunModalProps {
  onClose: () => void;
  onRunStarted: (threadId: string) => void;
}

export function StartRunModal({ onClose, onRunStarted }: StartRunModalProps) {
  const [jobUrl, setJobUrl] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a resume file.');
      return;
    }
    if (!jobUrl && !jobDesc) {
      setError('Please provide either a Job URL or a Job Description.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Upload and parse resume
      const parseRes = await api.parseResume(file);
      const resumeText: string = parseRes.resume_text;
      const resumeStorageUrl: string | undefined = parseRes.resume_storage_url;

      if (!resumeText) {
        throw new Error('Failed to get resume text from parser.');
      }

      // 2. Start run
      const runRes: any = await api.startRun({
        job_url: jobUrl || undefined,
        job_description: jobDesc || undefined,
        resume_text: resumeText,
        resume_storage_url: resumeStorageUrl,
      });

      onRunStarted(runRes.thread_id);
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred while starting the run.');
      setLoading(false);
    }
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 className={styles.title}>Run New Pipeline</h2>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={20} strokeWidth={1.5} />
          </button>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.field}>
            <label className={styles.label}>Resume (PDF)</label>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className={styles.fileInput}
              disabled={loading}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Job URL</label>
            <input
              type="url"
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              placeholder="https://boards.greenhouse.io/..."
              className={styles.input}
              disabled={loading}
            />
          </div>

          <div className={styles.divider}>OR</div>

          <div className={styles.field}>
            <label className={styles.label}>Raw Job Description</label>
            <textarea
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              placeholder="Paste raw text if URL is unsupported..."
              className={styles.textarea}
              rows={5}
              disabled={loading}
            />
          </div>

          <div className={styles.footer}>
            <Button variant="secondary" type="button" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? 'Starting...' : 'Start Pipeline'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
