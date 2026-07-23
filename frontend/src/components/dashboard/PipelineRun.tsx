import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { MatchScoreRing } from './MatchScoreRing';
import { PipelineStepper } from './PipelineStepper';
import type { PipelineStep } from './PipelineStepper';
import { SkillTag } from '../ui/SkillTag';
import styles from './PipelineRun.module.css';

interface PipelineRunProps {
  jobTitle: string;
  company: string;
  location: string;
  runId: string;
  startedAgo: string;
  status: 'in_review' | 'running' | 'completed' | 'failed';
  steps: PipelineStep[];
  matchScore: number;
  topSkills: string[];
  whatsNext: string;
  onReview?: () => void;
}

// Placeholder logo for companies
function CompanyLogo({ name }: { name: string }) {
  const initials = name.charAt(0).toUpperCase();
  const colors = ['#4285F4', '#EA4335', '#34A853', '#FF6D00', '#9C27B0', '#00BCD4'];
  const color = colors[name.charCodeAt(0) % colors.length];
  return (
    <div className={styles.logo} style={{ background: color }}>
      {initials}
    </div>
  );
}

export function PipelineRun({
  jobTitle,
  company,
  location,
  runId,
  startedAgo,
  status,
  steps,
  matchScore,
  topSkills,
  whatsNext,
  onReview,
}: PipelineRunProps) {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.sectionLabel}>Current Pipeline Run</span>
      </div>

      <div className={styles.jobRow}>
        <CompanyLogo name={company} />
        <div className={styles.jobInfo}>
          <span className={styles.jobTitle}>{jobTitle}</span>
          <span className={styles.jobMeta}>
            {company} · {location}
          </span>
          <span className={styles.runId}>
            Run ID: {runId} · Started {startedAgo}
          </span>
        </div>
        <Badge variant={status === 'in_review' ? 'in_review' : status === 'running' ? 'in_review' : 'applied'}>
          {status === 'in_review' ? '⏱ IN REVIEW' : status.toUpperCase()}
        </Badge>
      </div>

      <div className={styles.stepperRow}>
        <PipelineStepper steps={steps} />
      </div>

      <div className={styles.bottomRow}>
        <div className={styles.scoreSection}>
          <span className={styles.smallLabel}>Match Score</span>
          <MatchScoreRing score={matchScore} size={88} />
        </div>

        <div className={styles.skillsSection}>
          <span className={styles.smallLabel}>Top Matched Skills</span>
          <SkillTag skills={topSkills} maxVisible={6} />
        </div>

        <div className={styles.nextSection}>
          <span className={styles.smallLabel}>What&apos;s Next?</span>
          <p className={styles.nextText}>{whatsNext}</p>
          <Button variant="primary" size="sm" onClick={onReview}>
            Review Now
          </Button>
        </div>
      </div>
    </div>
  );
}
