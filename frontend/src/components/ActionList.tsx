import { CalendarPlus, CheckCircle2, Circle, Clock, Flag, Link2, Lightbulb, ShieldCheck, UserRound } from "lucide-react";
import { useState } from "react";
import { api, download } from "../api";
import type { Action, Analysis, Deadline } from "../types";
import { KIND_LABEL, daysLeft, fmtDue } from "../lib";
import { Card, ConfBadge, EvidenceChip, NeedsVerification, Quoted, SectionTitle } from "./ui";

const prio: Record<string, string> = { high: "bg-rose-50 text-rose-700 ring-rose-200", medium: "bg-amber-50 text-amber-700 ring-amber-200", low: "bg-slate-50 text-slate-600 ring-slate-200" };
const tone: Record<string, string> = { red: "bg-rose-600 text-white", amber: "bg-amber-500 text-white", green: "bg-emerald-600 text-white", slate: "bg-slate-200 text-slate-700" };

interface Props { a: Analysis; onChange: (a: Analysis) => void; onEvidence: (q: string) => void; onError: (m: string) => void }

export function ActionList({ a, onChange, onEvidence, onError }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const done = a.actions.filter((x) => x.status === "done").length;
  const toggle = async (t: Action) => {
    setBusy(t.id);
    try { onChange(await api.completeTask(t.id, t.status !== "done")); } catch (e) { onError((e as Error).message); } finally { setBusy(null); }
  };
  const depsOf = (id: string) => a.dependencies.filter((d) => d.to_action_id === id).map((d) => a.actions.find((x) => x.id === d.from_action_id)?.title).filter(Boolean);
  return (
    <section aria-label="Action checklist">
      <SectionTitle icon={<CheckCircle2 className="h-5 w-5 text-indigo-600" />} right={<span className="text-sm text-slate-500">{done}/{a.actions.length} done</span>}>Action checklist</SectionTitle>
      <div className="mb-3 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${a.actions.length ? (done / a.actions.length) * 100 : 0}%` }} /></div>
      <ul className="space-y-3">
        {a.actions.map((t, i) => {
          const dl = daysLeft(t.due_at);
          const needs = depsOf(t.id);
          return (
            <li key={t.id}>
              <Card className={`p-4 transition ${t.status === "done" ? "bg-slate-50 opacity-70" : ""}`}>
                <div className="flex items-start gap-3">
                  <button onClick={() => toggle(t)} disabled={busy === t.id} aria-label={t.status === "done" ? "Mark as not done" : "Mark as done"} className="mt-0.5 shrink-0 text-slate-400 hover:text-emerald-600">
                    {t.status === "done" ? <CheckCircle2 className="h-6 w-6 text-emerald-600" /> : <Circle className="h-6 w-6" />}
                  </button>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                      <span className="text-xs font-semibold text-slate-400">#{i + 1}</span>
                      <h3 className={`font-semibold ${t.status === "done" ? "line-through" : ""}`}>{t.title}</h3>
                      {t.in_minimum_path && <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-200">Minimum path</span>}
                    </div>
                    {t.description && <p className="mt-1 text-sm text-slate-600">{t.description}</p>}
                    <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
                      <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-medium ring-1 ring-inset ${prio[t.priority]}`}><Flag className="h-3 w-3" />{t.priority} priority</span>
                      {t.owner && <span className="inline-flex items-center gap-1 rounded-full bg-slate-50 px-2 py-0.5 text-slate-600 ring-1 ring-inset ring-slate-200"><UserRound className="h-3 w-3" />{t.owner}</span>}
                      {t.effort_minutes && <span className="inline-flex items-center gap-1 rounded-full bg-slate-50 px-2 py-0.5 text-slate-600 ring-1 ring-inset ring-slate-200"><Clock className="h-3 w-3" />~{t.effort_minutes} min (est.)</span>}
                      {t.due_at && <span className={`rounded-full px-2 py-0.5 font-medium ${tone[dl.tone]}`}>{fmtDue(t.due_at)} · {dl.text}</span>}
                      <ConfBadge c={t.confidence} />
                      <EvidenceChip status={t.evidence_status} quote={t.evidence} onOpen={onEvidence} />
                      {t.needs_verification && <NeedsVerification />}
                    </div>
                    {needs.length > 0 && <p className="mt-2 flex items-start gap-1.5 text-xs text-slate-500"><Link2 className="mt-0.5 h-3 w-3 shrink-0" />Do first: {needs.join(" · ")}</p>}
                    <Quoted text={t.evidence} />
                  </div>
                </div>
              </Card>
            </li>
          );
        })}
      </ul>
      {a.actions.length === 0 && <Card className="p-6 text-center text-sm text-slate-500">No actions were found in this document. If you expected some, try pasting the full text.</Card>}
    </section>
  );
}

export function DeadlineShield({ a, onChange, onEvidence, onError }: Props) {
  const toggle = async (d: Deadline) => {
    try { onChange(await api.completeDeadline(d.id, d.status !== "done")); } catch (e) { onError((e as Error).message); }
  };
  const cal = async (d: Deadline) => {
    try { await download(`/api/analysis/${a.id}/calendar.ics?deadline_id=${d.id}`, "lifeops-deadline.ics"); } catch (e) { onError((e as Error).message); }
  };
  return (
    <section aria-label="Deadline Shield">
      <SectionTitle icon={<ShieldCheck className="h-5 w-5 text-amber-600" />}>Deadline Shield</SectionTitle>
      {a.deadlines.length === 0 && <Card className="p-5 text-sm text-slate-500">No deadlines were found. Nothing is invented - if you expected one, check the original document.</Card>}
      <ul className="space-y-3">
        {a.deadlines.map((d) => {
          const dl = daysLeft(d.due_at);
          const open = d.prerequisites.filter((p) => p.status !== "done");
          const risky = d.status !== "done" && (open.length > 0 || d.unmet_requirements.length > 0);
          return (
            <li key={d.id}>
              <Card className={`overflow-hidden ${d.status === "done" ? "opacity-70" : ""}`}>
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 bg-amber-50/60 px-4 py-3">
                  <div className="min-w-0">
                    <p className="text-xs font-medium uppercase tracking-wide text-amber-700">{KIND_LABEL[d.kind]}</p>
                    <h3 className={`font-semibold ${d.status === "done" ? "line-through" : ""}`}>{d.label}</h3>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{d.due_at ? fmtDue(d.due_at) : "No exact date"}</p>
                    <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${d.status === "done" ? "bg-emerald-600 text-white" : tone[dl.tone]}`}>{d.status === "done" ? "Done" : dl.text}</span>
                  </div>
                </div>
                <div className="space-y-2 px-4 py-3 text-sm">
                  {d.date_text && <p className="text-slate-600">Source wording: <em>“{d.date_text}”</em></p>}
                  {d.assumed_anchor && <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">This is a relative deadline. It is counted from when you analyzed the document. If the message arrived earlier, the real deadline is earlier - check the original.</p>}
                  {risky && (
                    <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-800">
                      <p className="font-semibold">Before this deadline you still need:</p>
                      <ul className="mt-1 list-inside list-disc">
                        {open.map((p) => <li key={p.action_id}>{p.title}</li>)}
                        {d.unmet_requirements.map((r) => <li key={r.id}>Have ready: {r.item}</li>)}
                      </ul>
                    </div>
                  )}
                  {d.suggested_prerequisites.map((s, i) => (
                    <p key={i} className="flex gap-1.5 rounded-lg bg-indigo-50 px-3 py-2 text-xs text-indigo-900"><Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0" /><span><strong>Suggestion (AI, not from the source):</strong> {s.description} <span className="text-indigo-700">{s.reason}</span></span></p>
                  ))}
                  <div className="flex flex-wrap items-center gap-1.5">
                    <ConfBadge c={d.confidence} />
                    <EvidenceChip status={d.evidence_status} quote={d.evidence} onOpen={onEvidence} />
                    {d.needs_verification && <NeedsVerification />}
                  </div>
                  <Quoted text={d.evidence} />
                  <div className="flex flex-wrap gap-2 pt-1">
                    <button onClick={() => toggle(d)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium hover:bg-slate-50">{d.status === "done" ? "Reopen" : "Mark completed"}</button>
                    <button onClick={() => cal(d)} disabled={!d.due_at} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"><CalendarPlus className="h-3.5 w-3.5" />Add to calendar (.ics)</button>
                  </div>
                </div>
              </Card>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
