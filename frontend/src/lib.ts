import type { Conf, EvStatus } from "./types";

export function parseDue(s: string | null): Date | null {
  if (!s) return null;
  const d = new Date(s.length === 10 ? s + "T23:59:00" : s);
  return isNaN(d.getTime()) ? null : d;
}
export function fmtDue(s: string | null): string {
  const d = parseDue(s);
  if (!d || !s) return "No exact date";
  const date = d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
  return s.length > 10 ? `${date}, ${d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}` : date;
}
export function daysLeft(s: string | null): { text: string; tone: "red" | "amber" | "green" | "slate" } {
  const d = parseDue(s);
  if (!d) return { text: "Needs verification", tone: "slate" };
  const hrs = (d.getTime() - Date.now()) / 36e5;
  if (hrs < 0) return { text: `Overdue by ${Math.max(1, Math.round(-hrs / 24)) } day(s)`, tone: "red" };
  if (hrs < 48) return { text: `${Math.max(1, Math.round(hrs))} hours left`, tone: "red" };
  const days = Math.ceil(hrs / 24);
  return { text: `${days} days left`, tone: days <= 7 ? "amber" : "green" };
}
export const confLabel: Record<Conf, string> = { high: "High", medium: "Medium", low: "Low" };
export const evLabel: Record<EvStatus, string> = { verified: "Quote verified", partial: "Partly matches source", unsupported: "Quote NOT found in source", none: "No source quote" };
export const KIND_LABEL: Record<string, string> = { hard: "Hard deadline", suggested: "Suggested date", event: "Event date", unknown: "Unclear" };
export function sentenceCase(s: string) { return s ? s[0].toUpperCase() + s.slice(1) : s; }

/** Find a quote in the raw text ignoring case/whitespace differences; returns [start, end] or null. */
export function findQuote(raw: string, quote: string): [number, number] | null {
  if (!quote) return null;
  const i = raw.toLowerCase().indexOf(quote.toLowerCase());
  if (i >= 0) return [i, i + quote.length];
  const esc = quote.trim().split(/\s+/).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("\\s+");
  const m = new RegExp(esc, "i").exec(raw);
  return m ? [m.index, m.index + m[0].length] : null;
}
