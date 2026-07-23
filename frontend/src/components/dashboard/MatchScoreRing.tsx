import { useEffect, useRef, useState } from 'react';
import styles from './MatchScoreRing.module.css';

interface MatchScoreRingProps {
  score: number; // 0–100
  size?: number;
}

function getColor(score: number): string {
  if (score >= 90) return 'var(--color-success)';
  if (score >= 70) return 'var(--color-warning)';
  return 'var(--color-danger)';
}

function getLabel(score: number): string {
  if (score >= 90) return 'Excellent';
  if (score >= 70) return 'Good';
  return 'Poor';
}

export function MatchScoreRing({ score, size = 96 }: MatchScoreRingProps) {
  const strokeWidth = 7;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const [animatedScore, setAnimatedScore] = useState(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const duration = 700;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimatedScore(Math.round(eased * score));
      if (t < 1) frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); };
  }, [score]);

  const offset = circumference - (animatedScore / 100) * circumference;
  const color = getColor(score);

  return (
    <div className={styles.wrapper} style={{ width: size, height: size }}>
      <svg width={size} height={size} className={styles.svg}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={strokeWidth}
        />
        {/* Fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 50ms linear' }}
        />
      </svg>
      <div className={styles.center}>
        <span className={styles.score} style={{ color }}>{animatedScore}</span>
        <span className={styles.label}>{getLabel(score)}</span>
      </div>
    </div>
  );
}
