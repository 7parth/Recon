import styles from './Badge.module.css';

export type BadgeVariant =
  | 'applied'
  | 'skipped'
  | 'in_review'
  | 'high_match'
  | 'good_match'
  | 'failed';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

const LABEL_MAP: Record<BadgeVariant, string> = {
  applied: 'APPLIED',
  skipped: 'SKIPPED',
  in_review: 'IN REVIEW',
  high_match: 'HIGH MATCH',
  good_match: 'GOOD MATCH',
  failed: 'FAILED',
};

export function Badge({ variant, children }: BadgeProps) {
  return (
    <span className={`${styles.badge} ${styles[variant]}`}>
      {children ?? LABEL_MAP[variant]}
    </span>
  );
}

/** Convenience: derive badge variant from submission_status string */
export function statusToBadge(status: string): BadgeVariant {
  switch (status) {
    case 'applied': return 'applied';
    case 'skipped': return 'skipped';
    case 'failed': return 'failed';
    default: return 'in_review';
  }
}
