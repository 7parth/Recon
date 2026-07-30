/* ── Shared lib types — mirrors FastAPI Pydantic schemas ── */

export type ApprovalStatus = 'approved' | 'rejected' | 'pending';
export type SubmissionStatus = 'applied' | 'failed' | 'skipped';
export type PipelineStepStatus = 'done' | 'active' | 'pending';

export interface RunStatus {
  thread_id: string;
  status: 'running' | 'pending_review' | 'completed' | 'failed' | 'skipped';
  current_step?: string;
  match_score?: number;
  job_title?: string;
  company?: string;
  location?: string;
  started_at: string;
}

/**
 * ApplicationRecord — matches ApplicationRecordResponse from the backend.
 *
 * The backend's single `status` column is split into two computed fields:
 *   submission_status — "applied" | "skipped" | "failed" | null
 *   approval_status   — "approved" | "rejected" | "pending"
 *
 * Display fields (job_title, company) are denormalised from the graph state
 * and written to the DB after each run completes.
 */
export interface ApplicationRecord {
  id: string;
  thread_id: string;
  status: string;                            // raw DB status

  // Display metadata (populated after pipeline completes)
  job_title?: string;
  company?: string;

  // Computed split status fields
  submission_status?: SubmissionStatus | null;
  approval_status?: ApprovalStatus;

  // Scores & documents
  match_score?: number;
  resume_url?: string;
  resume_storage_url?: string;
  tailored_resume_url?: string;
  cover_letter_url?: string;

  // Review
  rejection_feedback?: string;
  error_message?: string;

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface ReviewPayload {
  thread_id: string;
  job_title?: string;
  company?: string;
  company_name?: string;
  location?: string;
  match_score: number;
  ats_score?: number;
  matched_keywords?: string[];
  missing_keywords?: string[];
  tailored_resume: string;
  cover_letter: string;
}

export interface JobSearchResult {
  title: string;
  company: string;
  location: string;
  url: string;
  snippet: string;
}

export interface StatSummary {
  total_applications: number;
  total_applied: number;
  in_review: number;
  skipped_failed: number;
  avg_match_score: number;
}
