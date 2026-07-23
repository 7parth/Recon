import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import type { ReviewPayload } from '../lib/types';
import { Tabs } from '../components/ui/Tabs';
import { Button } from '../components/ui/Button';
import { MatchScoreRing } from '../components/dashboard/MatchScoreRing';
import styles from './ReviewDetail.module.css';

export function ReviewDetail() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  
  const [payload, setPayload] = useState<ReviewPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [activeTab, setActiveTab] = useState('resume');
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!threadId) return;
    
    api.getReviewPayload(threadId)
      .then(setPayload)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [threadId]);

  const handleApprove = async () => {
    if (!threadId) return;
    setSubmitting(true);
    try {
      await api.approveRun(threadId, { approved: true });
      navigate(`/?run=${threadId}`);
    } catch (err: any) {
      alert(`Failed to approve: ${err.message}`);
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!threadId) return;
    if (!feedback.trim()) {
      alert("Please provide feedback for what needs to be changed.");
      return;
    }
    setSubmitting(true);
    try {
      await api.approveRun(threadId, { approved: false, feedback });
      // Go back to dashboard to watch it re-run
      navigate(`/?run=${threadId}`);
    } catch (err: any) {
      alert(`Failed to request changes: ${err.message}`);
      setSubmitting(false);
    }
  };

  if (loading) return <div className={styles.center}>Loading review payload...</div>;
  if (error) return <div className={styles.center}>Error: {error}</div>;
  if (!payload) return <div className={styles.center}>No payload found.</div>;

  return (
    <div className={styles.page}>
      {/* HEADER */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logo}>{payload.company.charAt(0).toUpperCase()}</div>
          <div className={styles.jobInfo}>
            <h1 className={styles.jobTitle}>{payload.job_title}</h1>
            <p className={styles.companyMeta}>{payload.company} · {payload.location}</p>
          </div>
        </div>
        
        <div className={styles.headerRight}>
          <div className={styles.scoreBlock}>
            <span className={styles.scoreLabel}>Final Match</span>
            <MatchScoreRing score={payload.match_score} size={48} />
          </div>
          <div className={styles.actions}>
            <Button variant="primary" onClick={handleApprove} disabled={submitting}>
              Approve & Submit
            </Button>
          </div>
        </div>
      </header>

      {/* SPLIT PANE */}
      <div className={styles.splitLayout}>
        
        {/* LEFT PANE: Context & ATS Analysis */}
        <div className={styles.leftPane}>
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>ATS Keyword Analysis</h3>
            <p className={styles.subtext}>ATS Score: <strong>{payload.ats_score}%</strong></p>
            
            <div className={styles.keywordLists}>
              <div className={styles.keywordGroup}>
                <span className={styles.groupLabel}>Found in Resume</span>
                <div className={styles.pillContainer}>
                  {payload.matched_keywords.length > 0 
                    ? payload.matched_keywords.map(kw => <span key={kw} className={`${styles.pill} ${styles.pillMatched}`}>{kw}</span>)
                    : <span className={styles.noneText}>None found</span>
                  }
                </div>
              </div>
              
              <div className={styles.keywordGroup}>
                <span className={styles.groupLabel}>Missing (Consider adding)</span>
                <div className={styles.pillContainer}>
                  {payload.missing_keywords.length > 0 
                    ? payload.missing_keywords.map(kw => <span key={kw} className={`${styles.pill} ${styles.pillMissing}`}>{kw}</span>)
                    : <span className={styles.noneText}>None missing!</span>
                  }
                </div>
              </div>
            </div>
          </section>

          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>Request Changes</h3>
            <p className={styles.subtext}>If the generated resume or cover letter needs adjustments, provide feedback here and the agents will re-tailor them.</p>
            <textarea 
              className={styles.feedbackInput} 
              placeholder="e.g. Remove the bullet point about Jenkins, emphasize Docker more."
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              disabled={submitting}
            />
            <Button variant="secondary" onClick={handleReject} disabled={submitting} className={styles.rejectBtn}>
              Re-Tailor Artifacts
            </Button>
          </section>
        </div>

        {/* RIGHT PANE: Generated Artifacts Preview */}
        <div className={styles.rightPane}>
          <Tabs 
            tabs={[
              { id: 'resume', label: 'Tailored Resume' },
              { id: 'cover_letter', label: 'Cover Letter' }
            ]}
            activeId={activeTab}
            onChange={setActiveTab}
          />
          
          <div className={styles.documentPreview}>
            {activeTab === 'resume' ? (
              <pre className={styles.markdown}>{payload.tailored_resume}</pre>
            ) : (
              <pre className={styles.markdown}>{payload.cover_letter}</pre>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
