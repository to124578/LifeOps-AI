import type { Analysis, Health, RecentItem, Sample, WhatIfResult } from "./types";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

export function sessionId(): string {
  let id = localStorage.getItem("lifeops_session");
  if (!id) { id = crypto.randomUUID(); localStorage.setItem("lifeops_session", id); }
  return id;
}
export function resetSession() { localStorage.removeItem("lifeops_session"); }

export function localNowISO(): string {
  const d = new Date(), p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:00`;
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  let r: Response;
  try {
    r = await fetch(path, { ...init, headers: { "X-Session-Id": sessionId(), ...(init.headers || {}) } });
  } catch {
    throw new ApiError(0, "network", "Can't reach the server. Check your connection and try again.");
  }
  if (!r.ok) {
    let code = "error", msg = `Request failed (${r.status}).`;
    try { const j = await r.json(); code = j.error || code; msg = j.message || j.detail || msg; } catch { /* non-JSON */ }
    throw new ApiError(r.status, code, msg);
  }
  const ct = r.headers.get("content-type") || "";
  return (ct.includes("json") ? r.json() : r.text()) as Promise<T>;
}

const json = (body: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api = {
  health: () => req<Health>("/api/health"),
  samples: () => req<Sample[]>(`/api/samples?today=${localNowISO().slice(0, 10)}`),
  recent: () => req<RecentItem[]>("/api/analyses"),
  analyzeText: (text: string, received_at?: string) =>
    req<{ id: string }>("/api/analyze/text", json({ text, client_now: localNowISO(), received_at: received_at || null })),
  analyzeFile: (file: File, received_at?: string) => {
    const f = new FormData();
    f.append("file", file); f.append("client_now", localNowISO());
    if (received_at) f.append("received_at", received_at);
    return req<{ id: string }>("/api/analyze", { method: "POST", body: f });
  },
  get: (id: string) => req<Analysis>(`/api/analysis/${id}`),
  completeTask: (id: string, completed: boolean) => req<Analysis>(`/api/tasks/${id}/complete`, json({ completed })),
  completeDeadline: (id: string, completed: boolean) => req<Analysis>(`/api/deadlines/${id}/complete`, json({ completed })),
  whatIf: (id: string, body: { preset?: string; question?: string }) => req<WhatIfResult>(`/api/analysis/${id}/whatif`, json(body)),
  deleteSession: () => req<{ deleted_analyses: number }>(`/api/session/${sessionId()}`, { method: "DELETE" }),
};

/** Download through fetch so the session header + friendly errors work; falls back to the browser's save dialog. */
export async function download(path: string, filename: string) {
  const r = await fetch(path, { headers: { "X-Session-Id": sessionId() } });
  if (!r.ok) {
    let msg = "Download failed.";
    try { msg = (await r.json()).message || msg; } catch { /* ignore */ }
    throw new ApiError(r.status, "download", msg);
  }
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement("a");
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
