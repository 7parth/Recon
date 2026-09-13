/* ── Shared lib types — mirrors FastAPI Pydantic schemas ── */

export type ApprovalStatus = 'approved' | 'rejected' | 'pending';
export type SubmissionStatus = 'applied' | 'failed' | 'skipped';
export type PipelineStepStatus = 'done' | 'active' | 'pending';

/**
 * RunStatus — mirrors backend RunStatus schema.
 * status "awaiting_review" is the API-level name for DB "pending_review".
 */
export interface RunStatus {
  thread_id: string;
  status: 'running' | 'awaiting_review' | 'completed' | 'failed' | 'skipped';
  submission_status?: SubmissionStatus | null;
  error?: string | null;
  completed_at?: string | null;
  // Display fields populated from DB once the pipeline runs
  job_title?: string | null;
  company?: string | null;
  match_score?: number | null;
  started_at?: string | null;    // ISO timestamp (created_at of the run record)
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
  job_title?: string | null;
  company?: string | null;

  // Computed split status fields
  submission_status?: SubmissionStatus | null;
  approval_status?: ApprovalStatus;

  // Scores & documents
  match_score?: number | null;
  resume_url?: string | null;
  resume_storage_url?: string | null;
  tailored_resume_url?: string | null;
  cover_letter_url?: string | null;

  // Review
  rejection_feedback?: string | null;
  error_message?: string | null;

  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * ReviewPayload — mirrors backend ReviewPayload schema.
 * All fields marked optional were absent in earlier API versions;
 * treat undefined as "not yet available" rather than an error.
 */
export interface ReviewPayload {
  thread_id: string;
  // Job / company identity
  company_name?: string | null;
  job_title?: string | null;
  job_url: string;
  // Scores
  match_score: number;
  ats_score?: number | null;           // 0–100 %, rounded
  ats_keyword_coverage?: number | null; // raw 0.0–1.0
  // ATS keyword breakdown
  matched_keywords?: string[];
  missing_keywords?: string[];
  ats_recommendations?: string | null;
  // Match summary
  match_summary?: {
    overall_score: number;
    strengths: string[];
    weaknesses: string[];
    gap_areas: string[];
  };
  // Artifacts
  tailored_resume: string;
  cover_letter: string;
}

export interface JobSearchResult {
  title: string;
  url: string;
  snippet: string;
  company?: string | null;
  location?: string | null;
}

export interface StatSummary {
  total_applications: number;
  total_applied: number;
  in_review: number;
  skipped_failed: number;
  avg_match_score: number;
}
