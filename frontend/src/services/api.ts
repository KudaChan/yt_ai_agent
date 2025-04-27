const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface SummaryRequest {
  video_url: string;
  language: string;
}

export interface SummaryResponse {
  job_id: string;
  status: string;
}

export interface SummaryResult {
  title: string;
  summary: string;
  key_points: string[];
  thumbnail_url?: string;
}

export async function submitSummaryRequest(request: SummaryRequest): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/summarize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to submit summary request');
  }

  return response.json();
}

export async function getSummaryStatus(jobId: string): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/status/${jobId}`);

  if (!response.ok) {
    throw new Error('Failed to get summary status');
  }

  return response.json();
}

export async function getSummaryResult(jobId: string): Promise<SummaryResult> {
  const response = await fetch(`${API_BASE_URL}/results/${jobId}`);

  if (!response.ok) {
    throw new Error('Failed to get summary results');
  }

  return response.json();
}
