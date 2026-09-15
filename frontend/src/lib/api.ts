import type {
  RunStatus,
  ApplicationRecord,
  ReviewPayload,
  JobSearchResult,
  DiscoveryPreferences,
  DiscoverySession,
} from './types';

export interface DiscoveryPreferencesUpdate {
  target_role?: string;
  preferred_locations?: string[];
  excluded_companies?: string[];
  max_jobs_per_session?: number;
}

const BASE = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json() as Promise<T>;
}

// ── Runs ──────────────────────────────────────────────────────────────────────
export const api = {
  startRun: (body: {
    job_url?: string;
    job_description?: string;
    resume_text: string;
    resume_storage_url?: string;
  }) =>
    request<{ thread_id: string; status: string; message: string }>(
      '/runs/start',
      { method: 'POST', body: JSON.stringify(body) }
    ),

  getRunStatus: (threadId: string) =>
    request<RunStatus>(`/runs/${threadId}/status`),

  getReviewPayload: (threadId: string) =>
    request<ReviewPayload>(`/runs/${threadId}/review`),

  approveRun: (threadId: string, body: { approved: boolean; feedback?: string }) =>
    request<RunStatus>(`/runs/${threadId}/approve`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // ── Resume ──────────────────────────────────────────────────────────────────
  parseResume: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE}/resume/parse`, { method: 'POST', body: form }).then(
      (r) => r.json() as Promise<{ resume_text: string; resume_storage_url?: string; char_count: number }>
    );
  },

  // ── Jobs ────────────────────────────────────────────────────────────────────
  searchJobs: (params: { role: string; location?: string; max_results?: number }) => {
    const q = new URLSearchParams({ role: params.role });
    if (params.location) q.set('location', params.location);
    if (params.max_results) q.set('max_results', String(params.max_results));
    return request<{ query: string; results: JobSearchResult[] }>(`/jobs/search?${q.toString()}`);
  },

  // ── History ─────────────────────────────────────────────────────────────────
  getHistory: () =>
    request<{ items: ApplicationRecord[]; limit: number; offset: number }>('/history'),

  getHistoryDetail: (threadId: string) =>
    request<ApplicationRecord>(`/history/${threadId}`),

  // ── User profile ─────────────────────────────────────────────────────────────
  getUserProfile: () =>
    request<{
      first_name: string;
      last_name: string;
      email: string;
      phone: string;
      linkedin_url: string;
      portfolio_url: string;
    }>('/user/profile'),

  updateUserProfile: (body: Partial<{
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    linkedin_url: string;
    portfolio_url: string;
  }>) =>
    request<{
      first_name: string;
      last_name: string;
      email: string;
      phone: string;
      linkedin_url: string;
      portfolio_url: string;
    }>('/user/profile', { method: 'PUT', body: JSON.stringify(body) }),

  // ── User settings ─────────────────────────────────────────────────────────────
  getUserSettings: () =>
    request<{
      match_threshold: number;
      nvidia_model: string;
      embedding_model: string;
      auto_apply: boolean;
      enable_notifications: boolean;
    }>('/user/settings'),

  updateUserSettings: (body: Partial<{
    match_threshold: number;
    nvidia_model: string;
    embedding_model: string;
    auto_apply: boolean;
    enable_notifications: boolean;
  }>) =>
    request<{
      match_threshold: number;
      nvidia_model: string;
      embedding_model: string;
      auto_apply: boolean;
      enable_notifications: boolean;
    }>('/user/settings', { method: 'PUT', body: JSON.stringify(body) }),

  // ── Automation logs (snapshot) ────────────────────────────────────────────────
  // For live streaming use EventSource directly: /api/v1/runs/{id}/logs/stream
  getLogs: (threadId: string) =>
    request<{
      entries: {
        id: string;
        thread_id: string;
        ts: string;
        level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS' | 'DEBUG';
        message: string;
        context?: string;
      }[];
    }>(`/runs/${threadId}/logs`),

  // ── Discovery ─────────────────────────────────────────────────────────────────
  getDiscoveryPreferences: () =>
    request<DiscoveryPreferences>('/discovery/preferences'),

  updateDiscoveryPreferences: (body: DiscoveryPreferencesUpdate) =>
    request<DiscoveryPreferences>('/discovery/preferences', {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  startDiscoverySession: () =>
    request<{ session_id: string; session_status: string; message: string }>(
      '/discovery/sessions',
      { method: 'POST' }
    ),

  listDiscoverySessions: () =>
    request<DiscoverySession[]>('/discovery/sessions'),

  getDiscoverySession: (sessionId: string) =>
    request<DiscoverySession>(`/discovery/sessions/${sessionId}`),

  cancelDiscoverySession: (sessionId: string) =>
    request<{ session_id: string; session_status: string }>(
      `/discovery/sessions/${sessionId}/cancel`,
      { method: 'POST' }
    ),

  // ── LinkedIn auth ─────────────────────────────────────────────────────────────
  getLinkedInStatus: () =>
    request<{ authenticated: boolean; session_file_exists: boolean }>('/linkedin/auth/status'),

  initLinkedInAuth: () =>
    request<{ message: string }>('/linkedin/auth/init', { method: 'POST' }),
};
