import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/Button';
import type { DiscoverySession, SessionStatus } from '../../lib/types';
import styles from './DiscoverySessionCard.module.css';

interface DiscoverySessionCardProps {
  session: DiscoverySession | null;
}

const STATUS_LABELS: Record<SessionStatus, string> = {
  running: 'RUNNING',
  completed: 'COMPLETED',
  failed: 'FAILED',
  cancelled: 'CANCELLED',
  completed_with_errors: 'COMPLETED W/ ERRORS',
};

export function DiscoverySessionCard({ session }: DiscoverySessionCardProps) {
  const navigate = useNavigate();

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.sectionLabel}>Latest Discovery Session</span>
      </div>

      <div className={styles.body}>
        {session ? (
          <>
            <div className={styles.statusRow}>
              <span
                className={`${styles.statusBadge} ${styles[`status_${session.session_status}`]}`}
              >
                {STATUS_LABELS[session.session_status]}
              </span>
            </div>

            <div className={styles.stats}>
              <div className={styles.stat}>
                <span className={styles.statValue}>{session.jobs_found}</span>
                <span className={styles.statLabel}>Jobs Found</span>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.stat}>
                <span className={styles.statValue}>{session.jobs_pending_review}</span>
                <span className={styles.statLabel}>Pending Review</span>
              </div>
            </div>
          </>
        ) : (
          <div className={styles.emptyState}>
            <span className={styles.emptyText}>No sessions yet</span>
          </div>
        )}

        <Button
          variant="secondary"
          size="md"
          className={styles.startBtn}
          onClick={() => navigate('/discovery')}
        >
          Start Discovery
        </Button>
      </div>
    </div>
  );
}
