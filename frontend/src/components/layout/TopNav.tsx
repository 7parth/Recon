import { useState } from 'react';
import { Bell, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StartRunModal } from '../dashboard/StartRunModal';
import styles from './TopNav.module.css';

export function TopNav() {
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  const handleRunStarted = (threadId: string) => {
    navigate(`/?run=${threadId}`);
  };

  return (
    <>
      <header className={styles.nav}>
        <div className={styles.brand}>
          <span className={styles.wordmark}>RECON</span>
          <span className={styles.subtitle}>AI JOB APPLICATION AGENT</span>
        </div>

        <div className={styles.actions}>
          <button className={styles.bellBtn} aria-label="Notifications">
            <Bell size={18} strokeWidth={1.5} />
            <span className={styles.bellDot} />
          </button>

          <button className={styles.pipelineBtn} onClick={() => setShowModal(true)}>
            <Play size={12} strokeWidth={2} />
            RUN NEW PIPELINE
          </button>

          <button className={styles.loginBtn}>LOG IN</button>
        </div>
      </header>

      {showModal && (
        <StartRunModal
          onClose={() => setShowModal(false)}
          onRunStarted={handleRunStarted}
        />
      )}
    </>
  );
}
