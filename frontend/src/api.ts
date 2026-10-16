export type Source = "live" | "test";

export interface ServiceInfo {
  interface: string;
  provider: string;
  mode: Source;
}

export interface AppConfig {
  video_id: string;
  video_url: string;
  services: ServiceInfo[];
}

export interface ClipAnalysis {
  text: string;
  model: string;
  prompt_version: string;
  source: Source;
  cached: boolean;
}

export interface Detection {
  label: string;
  confidence: number;
  time_s: number;
  box: [number, number, number, number];
}

export interface ClipDetections {
  detections: Detection[];
  model: string;
  prompt_version: string;
  source: Source;
  cached: boolean;
}

/** Timestamps are seconds from the start of the source video. */
export interface EvidenceCard {
  video_id: string;
  start_s: number;
  end_s: number;
  score: number;
  search_text: string;
  search_source: Source;
  clip_url: string | null;
  clip_source: Source;
  analysis: ClipAnalysis;
  detections: ClipDetections;
}

export interface JobError {
  service: string | null;
  kind: string;
  message: string;
}

export interface Job {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  stage: string;
  request: { video_id: string; question: string; top_k: number };
  created_at: string;
  updated_at: string;
  result: {
    answer: { text: string; model: string; source: Source };
    evidence: EvidenceCard[];
  } | null;
  error: JobError | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  const response = await fetch(path, {
    ...init,
    headers,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (body.detail != null) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {}
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  config: () => request<AppConfig>("/api/config"),
  createJob: (video_id: string, question: string) =>
    request<Job>("/api/jobs", { method: "POST", body: JSON.stringify({ video_id, question }) }),
  job: (id: string) => request<Job>(`/api/jobs/${id}`),
};
