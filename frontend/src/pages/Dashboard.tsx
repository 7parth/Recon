import { useSearchParams, useNavigate } from 'react-router-dom';
import { Briefcase, CheckCircle, Clock, XCircle, TrendingUp } from 'lucide-react';
import { StatCard } from '../components/ui/StatCard';
import { PipelineRun } from '../components/dashboard/PipelineRun';
import { ReviewQueue } from '../components/dashboard/ReviewQueue';
import { ApplicationsTable } from '../components/dashboard/ApplicationsTable';
import { ActivityTimeline } from '../components/dashboard/ActivityTimeline';
import { useDashboardData } from '../hooks/useDashboardData';
import { usePipelineRun } from '../hooks/usePipelineRun';
import styles from './Dashboard.module.css';
import type { PipelineStep } from '../components/dashboard/PipelineStepper';
import type { BadgeVariant } from '../components/ui/Badge';

function getSteps(currentStep?: string, status?: string): PipelineStep[] {
  const stepsList = [
    { key: 'parsed', label: 'Resume Parsed' },
    { key: 'job', label: 'Job Parsed' },
    { key: 'company', label: 'Company Researched' },
    { key: 'match', label: 'Match Scored' },
    { key: 'tailored', label: 'Tailored Resume' },
    { key: 'cover', label: 'Cover Letter' },
    { key: 'review', label: 'Review' },
    { key: 'applied', label: 'Applied' },
    { key: 'tracking', label: 'Tracking' },
  ];

  let currentIndex = -1;
  // If status is pending_review, current step is 'review' and done
  if (status === 'pending_review') {
    currentIndex = stepsList.findIndex(s => s.key === 'review');
  } else if (currentStep) {
    currentIndex = stepsList.findIndex(s => s.key === currentStep);
  }

  // If completed/failed/skipped, everything up to tracking is done
  if (['completed', 'failed', 'skipped'].includes(status || '')) {
    currentIndex = stepsList.length - 1;
  }

  return stepsList.map((s, i) => {
    let state: 'done' | 'active' | 'pending' = 'pending';
    if (i < currentIndex) state = 'done';
    if (i === currentIndex) {
      state = status === 'completed' || status === 'pending_review' ? 'done' : 'active';
    }
    return { ...s, status: state };
  });
}

// Fallback timeline events if backend doesn't provide
const TIMELINE_EVENTS = [
  { id: '1', title: 'System initialized', description: 'Recon is ready for new jobs', timeAgo: 'Now', status: 'done' as const, iconType: 'settings' as const },
];

export function Dashboard() {
  const [searchParams] = useSearchParams();
  const threadId = searchParams.get('run');
  const navigate = useNavigate();

  const { history, stats, loading } = useDashboardData();
  const { runStatus } = usePipelineRun(threadId);

  const STATS_DATA = [
    { label: 'Applications', value: stats.total_applications, sub: 'Total applied', icon: <Briefcase size={20} />, color: 'var(--color-accent)' },
    { label: 'Applied', value: stats.total_applied, sub: 'Success', icon: <CheckCircle size={20} />, color: 'var(--color-success)' },
    { label: 'In Review', value: stats.in_review, sub: 'Pending approval', icon: <Clock size={20} />, color: 'var(--color-warning)' },
    { label: 'Skipped / Failed', value: stats.skipped_failed, sub: 'Rejected/Error', icon: <XCircle size={20} />, color: 'var(--color-danger)' },
    { label: 'Avg. Match Score', value: stats.avg_match_score, sub: 'Overall', icon: <TrendingUp size={20} />, color: 'var(--color-success)' },
  ];

  const pendingApps = history.filter(h => h.approval_status === 'pending');
  const recentApps = history.slice(0, 5).map(app => ({
    id: app.thread_id,
    jobTitle: app.job_title || 'Unknown Job',
    company: app.company || 'Unknown Company',
    matchScore: app.match_score || 0,
    status: app.submission_status === 'skipped' ? 'skipped' : (app.approval_status === 'pending' ? 'in_review' : 'applied'),
    appliedOn: app.applied_at ? new Date(app.applied_at).toLocaleDateString() : 'N/A',
    logoLetter: (app.company || '?').charAt(0).toUpperCase(),
    logoColor: '#333',
  }));

  const queueItems = pendingApps.map(app => ({
    id: app.thread_id,
    jobTitle: app.job_title || 'Unknown Job',
    company: app.company || 'Unknown Company',
    location: 'Remote', // TODO: fetch from backend if available
    matchScore: app.match_score || 0,
    matchTier: ((app.match_score || 0) >= 90 ? 'high_match' : 'good_match') as BadgeVariant,
    timeAgo: app.created_at ? new Date(app.created_at).toLocaleDateString() : 'Unknown',
    logoLetter: (app.company || '?').charAt(0).toUpperCase(),
    logoColor: '#4285F4',
  }));

  const pipelineSteps = getSteps(runStatus?.current_step, runStatus?.status);

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>Dashboard</h1>
        <p className={styles.subtitle}>Welcome back, Rishabh.</p>
      </div>

      <div className={styles.statsRow}>
        {STATS_DATA.map((stat, i) => (
          <StatCard
            key={i}
            label={stat.label}
            value={stat.value}
            subLabel={stat.sub}
            icon={stat.icon}
            iconColor={stat.color}
          />
        ))}
      </div>

      <div className={styles.mainLayout}>
        <div className={styles.leftColumn}>
          {runStatus && (
            <PipelineRun
              jobTitle={runStatus.job_title || 'Unknown Job'}
              company={runStatus.company || 'Unknown Company'}
              location={runStatus.location || 'Remote'}
              runId={runStatus.thread_id}
              startedAgo={new Date(runStatus.started_at).toLocaleTimeString()}
              status={runStatus.status === 'pending_review' ? 'in_review' : runStatus.status as any}
              steps={pipelineSteps}
              matchScore={runStatus.match_score || 0}
              topSkills={['Python', 'React', 'TypeScript']} // Wait for backend to supply these
              whatsNext={
                runStatus.status === 'pending_review'
                  ? 'Please review the tailored resume and cover letter. You can approve, request changes, or provide feedback.'
                  : runStatus.status === 'running' ? 'Pipeline is running. Please wait for completion.' : 'Pipeline finished.'
              }
              onReview={() => navigate(`/review/${runStatus.thread_id}`)}
            />
          )}
          {!runStatus && (
            <div style={{ padding: 'var(--space-6)', background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
              No active pipeline run. Click "RUN NEW PIPELINE" to start.
            </div>
          )}
          <ApplicationsTable applications={recentApps} />
        </div>
        <div className={styles.rightColumn}>
          <ReviewQueue items={queueItems} total={queueItems.length} />
          <ActivityTimeline events={TIMELINE_EVENTS} />
        </div>
      </div>
    </div>
  );
}
