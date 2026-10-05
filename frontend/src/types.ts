export type Conf = "high" | "medium" | "low";
export type EvStatus = "verified" | "partial" | "unsupported" | "none";

export interface Stage { name: string; label: string; status: "running" | "done" | "failed" | "degraded"; ms: number; summary: string }
export interface Action {
  id: string; key: string; title: string; description: string; owner: string | null; priority: "high" | "medium" | "low";
  status: "todo" | "done"; due_at: string | null; confidence: Conf; evidence: string | null; evidence_status: EvStatus;
  effort_minutes: number | null; can_delegate: boolean | null; needs_verification: boolean; order_index: number; in_minimum_path: boolean;
}
export interface Deadline {
  id: string; key: string; label: string; due_at: string | null; date_text: string | null; kind: "hard" | "suggested" | "event" | "unknown";
  confidence: Conf; evidence: string | null; evidence_status: EvStatus; needs_verification: boolean; assumed_anchor: boolean;
  status: "open" | "done"; action_ids: string[];
  prerequisites: { action_id: string; title: string; status: string }[];
  unmet_requirements: { id: string; item: string }[];
  suggested_prerequisites: { deadline_id: string; description: string; reason: string }[];
}
export interface Requirement { id: string; item: string; required: boolean; status: string; confidence: Conf; evidence: string | null; evidence_status: EvStatus; action_ids: string[] }
export interface Risk { id: string; description: string; severity: "high" | "medium" | "low"; stated_in_source: boolean; confidence: Conf; evidence: string | null; evidence_status: EvStatus }
export interface Analysis {
  id: string; title: string; source_type: string; source_name: string; document_type: string; language: string; summary: string;
  status: "processing" | "done" | "failed"; stage: string; error: string | null; created_at: string; overall_confidence: Conf | "";
  verification_notes: string[]; verification_stats: Record<string, number>; intake_notes: string[]; sensitive_domains: string[];
  disclaimer: string | null; provider: string; pipeline: Stage[]; actions: Action[]; deadlines: Deadline[]; requirements: Requirement[];
  dependencies: { id: string; from_action_id: string; to_action_id: string; reason: string }[];
  risks: Risk[]; questions: { id: string; question: string; reason: string }[]; minimum_path: string[]; raw_text: string;
}
export interface Sample { id: string; label: string; blurb: string; text: string }
export interface WhatIfResult { question: string; answer: string; status: "answered" | "unknown" | "partial"; method: string; sources: { quote: string; verified: boolean }[]; verify_with: string | null }
export interface Health { status: string; ai_provider: string; model: string; ai_configured: boolean; demo_mode: boolean }
export interface RecentItem { id: string; title: string; status: string; document_type: string; created_at: string; overall_confidence: string }
