import { ArrowRight } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { BadgeVariant } from '../ui/Badge';
import { Button } from '../ui/Button';
import styles from './ReviewQueue.module.css';

export interface ReviewQueueItem {
  id: string;
  jobTitle: string;
  company: string;
  location: string;
  matchScore: number;
  matchTier: BadgeVariant;
  timeAgo: string;
  logoLetter: string;
  logoColor: string;
}

interface ReviewQueueProps {
  items: ReviewQueueItem[];
  total: number;
  onViewAll?: () => void;
  onReviewAll?: () => void;
}

export function ReviewQueue({ items, total, onViewAll, onReviewAll }: ReviewQueueProps) {
  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.sectionLabel}>Review Queue</span>
        <button className={styles.viewAll} onClick={onViewAll}>
          View All ({total}) <ArrowRight size={12} strokeWidth={2} />
        </button>
      </div>

      <div className={styles.list}>
        {items.map((item) => (
          <div key={item.id} className={styles.item}>
            <div className={styles.logo} style={{ background: item.logoColor }}>
              {item.logoLetter}
            </div>
            <div className={styles.info}>
              <span className={styles.jobTitle}>{item.jobTitle}</span>
              <span className={styles.meta}>
                {item.company} · {item.location}
              </span>
            </div>
            <div className={styles.right}>
              <span className={styles.score}>{item.matchScore}%</span>
              <span className={styles.timeAgo}>{item.timeAgo}</span>
              <Badge variant={item.matchTier}>
                {item.matchTier === 'high_match' ? 'HIGH MATCH' : 'GOOD MATCH'}
              </Badge>
            </div>
          </div>
        ))}
      </div>

      <Button variant="secondary" size="md" className={styles.reviewAllBtn} onClick={onReviewAll}>
        Review All
      </Button>
    </div>
  );
}
