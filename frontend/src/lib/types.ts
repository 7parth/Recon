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

export interface ApplicationRecord {
  thread_id: string;
  job_title: string;
  company: string;
  match_score: number;
  ats_score?: number;
  submission_status: SubmissionStatus;
  approval_status: ApprovalStatus;
  applied_at?: string;
  created_at: string;
  resume_url?: string;
  tailored_resume_url?: string;
  cover_letter_url?: string;
}

export interface ReviewPayload {
  thread_id: string;
  job_title: string;
  company: string;
  location: string;
  match_score: number;
  ats_score: number;
  matched_keywords: string[];
  missing_keywords: string[];
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
