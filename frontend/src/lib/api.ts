/* ── Typed fetch wrappers for FastAPI ── */

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

// ── Runs ──
export const api = {
  startRun: (body: { job_url?: string; job_description?: string; resume_url: string }) =>
    request('/runs/start', { method: 'POST', body: JSON.stringify(body) }),

  getRunStatus: (threadId: string) =>
    request(`/runs/${threadId}/status`),

  getReviewPayload: (threadId: string) =>
    request(`/runs/${threadId}/review`),

  approveRun: (threadId: string, body: { approved: boolean; feedback?: string }) =>
    request(`/runs/${threadId}/approve`, { method: 'POST', body: JSON.stringify(body) }),

  // ── Resume ──
  parseResume: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE}/resume/parse`, { method: 'POST', body: form }).then((r) => r.json());
  },

  // ── Jobs ──
  searchJobs: (query: string) =>
    request(`/jobs/search?q=${encodeURIComponent(query)}`),

  // ── History ──
  getHistory: () => request('/history'),
  getHistoryDetail: (threadId: string) => request(`/history/${threadId}`),
};
