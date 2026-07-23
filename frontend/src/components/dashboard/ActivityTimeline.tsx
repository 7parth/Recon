import { ArrowRight, User, Check, Settings2, Play, Circle } from 'lucide-react';
import styles from './ActivityTimeline.module.css';

export interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  timeAgo: string;
  status: 'done' | 'active' | 'pending';
  iconType: 'user' | 'check' | 'settings' | 'play' | 'circle';
}

interface ActivityTimelineProps {
  events: TimelineEvent[];
  onViewAll?: () => void;
}

function getIcon(type: string, status: string) {
  const size = 12;
  const stroke = 2;
  if (status === 'pending') return <Circle size={10} strokeWidth={stroke} fill="currentColor" />;
  switch (type) {
    case 'user': return <User size={size} strokeWidth={stroke} />;
    case 'check': return <Check size={size} strokeWidth={3} />;
    case 'settings': return <Settings2 size={size} strokeWidth={stroke} />;
    case 'play': return <Play size={size} strokeWidth={stroke} fill="currentColor" />;
    default: return <Circle size={10} strokeWidth={stroke} fill="currentColor" />;
  }
}

export function ActivityTimeline({ events, onViewAll }: ActivityTimelineProps) {
  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.sectionLabel}>Activity Timeline</span>
        <button className={styles.viewAll} onClick={onViewAll}>
          View All <ArrowRight size={12} strokeWidth={2} />
        </button>
      </div>

      <div className={styles.timeline}>
        {events.map((event, i) => (
          <div key={event.id} className={styles.event}>
            {/* Connector line (skip on last item) */}
            {i !== events.length - 1 && <div className={styles.connector} />}
            
            <div className={`${styles.node} ${styles[`node_${event.status}`]}`}>
              {getIcon(event.iconType, event.status)}
            </div>
            
            <div className={styles.content}>
              <div className={styles.topRow}>
                <span className={styles.title}>{event.title}</span>
                <span className={styles.timeAgo}>{event.timeAgo}</span>
              </div>
              <p className={styles.description}>{event.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
