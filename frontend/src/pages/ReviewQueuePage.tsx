import { useNavigate } from 'react-router-dom';
import { useDashboardData } from '../hooks/useDashboardData';
import { Badge, type BadgeVariant } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import styles from './ReviewQueuePage.module.css';

export function ReviewQueuePage() {
  const { history, loading } = useDashboardData();
  const navigate = useNavigate();

  const pendingApps = history.filter(h => h.approval_status === 'pending');

  if (loading) {
    return <div className={styles.page}>Loading review queue...</div>;
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Review Queue</h1>
        <p className={styles.subtitle}>Applications requiring human approval before submission.</p>
      </div>

      {pendingApps.length === 0 ? (
        <div className={styles.empty}>
          <p>No applications are currently waiting for review.</p>
        </div>
      ) : (
        <div className={styles.list}>
          {pendingApps.map(app => {
            const logoLetter = (app.company || '?').charAt(0).toUpperCase();
            const matchTier: BadgeVariant = (app.match_score || 0) >= 90 ? 'high_match' : 'good_match';

            return (
              <div key={app.thread_id} className={styles.card} onClick={() => navigate(`/review/${app.thread_id}`)}>
                <div className={styles.cardLeft}>
                  <div className={styles.logo}>{logoLetter}</div>
                  <div className={styles.info}>
                    <h3 className={styles.jobTitle}>{app.job_title}</h3>
                    <p className={styles.company}>{app.company}</p>
                  </div>
                </div>
                
                <div className={styles.cardRight}>
                  <div className={styles.scoreBlock}>
                    <span className={styles.scoreLabel}>Match Score</span>
                    <span className={styles.score}>{app.match_score || 0}%</span>
                  </div>
                  <div className={styles.badgeBlock}>
                    <Badge variant={matchTier}>
                      {matchTier === 'high_match' ? 'HIGH MATCH' : 'GOOD MATCH'}
                    </Badge>
                    <span className={styles.date}>{new Date(app.created_at).toLocaleDateString()}</span>
                  </div>
                  <Button variant="primary" size="sm" onClick={(e) => { e.stopPropagation(); navigate(`/review/${app.thread_id}`); }}>
                    Review Now
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
