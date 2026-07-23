import { useCountUp } from '../../hooks/useCountUp';
import styles from './StatCard.module.css';

interface StatCardProps {
  label: string;
  value: number;
  subLabel: string;
  icon: React.ReactNode;
  iconColor?: string;
  isPercent?: boolean;
}

export function StatCard({ label, value, subLabel, icon, iconColor, isPercent }: StatCardProps) {
  const animated = useCountUp(value, 900);

  return (
    <div className={styles.card}>
      <div className={styles.top}>
        <span className={styles.label}>{label}</span>
        <span className={styles.icon} style={{ color: iconColor ?? 'var(--color-text-secondary)' }}>
          {icon}
        </span>
      </div>
      <div className={styles.value}>
        {animated}{isPercent ? '' : ''}
      </div>
      <div className={styles.subLabel}>{subLabel}</div>
    </div>
  );
}
