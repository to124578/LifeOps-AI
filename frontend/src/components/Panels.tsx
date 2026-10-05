import { AlertTriangle, CalendarDays, ClipboardCopy, FileJson, FileText, HelpCircle, ListChecks, MessageCircleQuestion, Send, Siren } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { api, download } from "../api";
import type { Analysis, WhatIfResult } from "../types";
import { findQuote } from "../lib";
import { Card, ConfBadge, ErrorBox, EvidenceChip, SectionTitle, Spinner } from "./ui";

const PRESETS: [string, string][] = [
  ["miss", "What happens if I miss this?"],
  ["before", "What do I need before I start?"],
  ["fastest", "What is the fastest path?"],
  ["delegate", "What can I delegate?"],
  ["missing", "What information is missing?"],
];

export function WhatIf({ a }: { a: Analysis }) {
  const [results, setResults] = useState<WhatIfResult[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const ask = async (body: { preset?: string; question?: string }) => {
    setBusy(true); setErr("");
    try { const r = await api.whatIf(a.id, body); setResults((x) => [r, ...x]); if (body.question) setQ(""); } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };
  return (
    <section aria-label="What-if simulator">
      <SectionTitle icon={<MessageCircleQuestion className="h-5 w-5 text-indigo-600" />}>What-if simulator</SectionTitle>
      <Card className="p-4">
        <p className="mb-3 text-xs text-slate-500">Answers come only from your document. If the source doesn't say, you'll be told so instead of getting a guess.</p>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map(([k, label]) => (
            <button key={k} disabled={busy} onClick={() => ask({ preset: k })} className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-50">{label}</button>
          ))}
        </div>
        <div className="mt-3 flex gap-2">
          <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && q.trim() && ask({ question: q })} maxLength={500} placeholder="Or ask your own question…" aria-label="Ask your own what-if question"
            className="min-w-0 flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" />
          <button disabled={busy || !q.trim()} onClick={() => ask({ question: q })} className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
            {busy ? <Spinner className="h-4 w-4" /> : <Send className="h-4 w-4" />}Ask
          </button>
        </div>
        {err && <div className="mt-3"><ErrorBox>{err}</ErrorBox></div>}
        <ul className="mt-4 space-y-3">
          {results.map((r, i) => (
            <li key={i} className="rounded-xl border border-slate-200 p-3">
              <p className="text-sm font-semibold">{r.question}</p>
              <span className={`mt-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${r.status === "answered" ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-amber-50 text-amber-800 ring-amber-200"}`}>
                {r.status === "answered" ? "Grounded in the source" : r.status === "partial" ? "Partly stated in the source" : <><AlertTriangle className="h-3 w-3" />Not stated in the source</>}
              </span>
              <p className="mt-2 whitespace-pre-line text-sm text-slate-700">{r.answer}</p>
              {r.sources.map((s, j) => <p key={j} className="mt-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-xs italic text-slate-600">“{s.quote}” {s.verified ? "✓ verified" : "(partial match)"}</p>)}
              {r.verify_with && <p className="mt-2 text-xs font-medium text-amber-800">Verify with: {r.verify_with}</p>}
            </li>
          ))}
        </ul>
      </Card>
    </section>
  );
}

export function InfoPanels({ a, onEvidence }: { a: Analysis; onEvidence: (q: string) => void }) {
  return (
    <div className="space-y-6">
      <section aria-label="Requirements">
        <SectionTitle icon={<ListChecks className="h-5 w-5 text-slate-600" />}>What you need</SectionTitle>
        <Card className="divide-y divide-slate-100">
          {a.requirements.map((r) => (
            <div key={r.id} className="space-y-1 p-3 text-sm">
              <p className="font-medium">{r.item} {!r.required && <span className="text-xs font-normal text-slate-500">(optional / conditional)</span>}</p>
              <div className="flex flex-wrap gap-1.5"><ConfBadge c={r.confidence} /><EvidenceChip status={r.evidence_status} quote={r.evidence} onOpen={onEvidence} /></div>
            </div>
          ))}
          {a.requirements.length === 0 && <p className="p-4 text-sm text-slate-500">No separate requirements found.</p>}
        </Card>
      </section>
      <section aria-label="Risks">
        <SectionTitle icon={<Siren className="h-5 w-5 text-rose-600" />}>Risks</SectionTitle>
        <Card className="divide-y divide-slate-100">
          {a.risks.map((r) => (
            <div key={r.id} className="space-y-1 p-3 text-sm">
              <p className="font-medium">{r.description}</p>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${r.severity === "high" ? "bg-rose-50 text-rose-700 ring-rose-200" : "bg-amber-50 text-amber-700 ring-amber-200"}`}>{r.severity} severity</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${r.stated_in_source ? "bg-emerald-50 text-emerald-700 ring-emerald-200" : "bg-slate-100 text-slate-600 ring-slate-200"}`}>{r.stated_in_source ? "Stated in source" : "Inference - not in source"}</span>
                {r.stated_in_source && <EvidenceChip status={r.evidence_status} quote={r.evidence} onOpen={onEvidence} />}
              </div>
            </div>
          ))}
          {a.risks.length === 0 && <p className="p-4 text-sm text-slate-500">No risks found in the source.</p>}
        </Card>
      </section>
      <section aria-label="Open questions">
        <SectionTitle icon={<HelpCircle className="h-5 w-5 text-amber-600" />}>Still unclear</SectionTitle>
        <Card className="divide-y divide-slate-100">
          {a.questions.map((q) => (
            <div key={q.id} className="p-3 text-sm"><p className="font-medium">{q.question}</p>{q.reason && <p className="text-xs text-slate-500">{q.reason}</p>}</div>
          ))}
          {a.questions.length === 0 && <p className="p-4 text-sm text-slate-500">Nothing ambiguous was detected.</p>}
        </Card>
      </section>
    </div>
  );
}

export function SourcePanel({ a, quote }: { a: Analysis; quote: string | null }) {
  const ref = useRef<HTMLElement>(null);
  const range = useMemo(() => (quote ? findQuote(a.raw_text, quote) : null), [a.raw_text, quote]);
  useEffect(() => { ref.current?.scrollIntoView({ block: "center", behavior: "smooth" }); }, [range]);
  return (
    <Card className="p-4">
      <p className="mb-2 text-sm text-slate-600">The original text the plan was built from. {quote ? (range ? "The selected evidence is highlighted." : "That quote could not be located in the source - treat it as unverified.") : "Click any evidence chip in the plan to jump to its quote."}</p>
      <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-4 font-sans text-sm leading-relaxed text-slate-800">
        {range ? (<>{a.raw_text.slice(0, range[0])}<mark ref={ref as never} className="ev">{a.raw_text.slice(range[0], range[1])}</mark>{a.raw_text.slice(range[1])}</>) : a.raw_text}
      </pre>
    </Card>
  );
}

export function ExportPanel({ a }: { a: Analysis }) {
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState(false);
  const withDate = a.deadlines.filter((d) => d.due_at).length;
  const go = async (path: string, name: string) => { setErr(""); try { await download(path, name); } catch (e) { setErr((e as Error).message); } };
  const copyMd = async () => {
    try { const t = await (await fetch(`/api/analysis/${a.id}/export/markdown`)).text(); await navigator.clipboard.writeText(t); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { setErr("Could not copy to the clipboard."); }
  };
  const items: [string, string, React.ReactNode, string, string][] = [
    ["Calendar events (.ics)", `${withDate} deadline(s) with exact dates, with 1-day and 1-hour reminders. Opens in Google/Apple/Outlook calendar.`, <CalendarDays className="h-5 w-5" />, `/api/analysis/${a.id}/calendar.ics`, "lifeops-deadlines.ics"],
    ["Action Pack (JSON)", "Portable, schema-versioned (lifeops.actionpack/1.0) so another app can consume the plan.", <FileJson className="h-5 w-5" />, `/api/analysis/${a.id}/export/json`, "lifeops-action-pack.json"],
    ["Action Pack (Markdown)", "Human-readable checklist with evidence quotes. Paste into Notion, email or print.", <FileText className="h-5 w-5" />, `/api/analysis/${a.id}/export/markdown`, "lifeops-action-pack.md"],
  ];
  return (
    <div className="space-y-4">
      {err && <ErrorBox>{err}</ErrorBox>}
      <div className="grid gap-4 md:grid-cols-3">
        {items.map(([t, d, icon, path, name]) => (
          <Card key={t} className="flex flex-col p-4">
            <div className="mb-2 flex items-center gap-2 font-semibold text-indigo-700">{icon}{t}</div>
            <p className="flex-1 text-sm text-slate-600">{d}</p>
            <button onClick={() => go(path, name)} disabled={t.startsWith("Calendar") && withDate === 0} className="mt-4 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40">Download</button>
          </Card>
        ))}
      </div>
      <button onClick={copyMd} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50"><ClipboardCopy className="h-4 w-4" />{copied ? "Copied!" : "Copy Markdown to clipboard"}</button>
      <p className="text-xs text-slate-500">Deadlines without an exact date are not exported to the calendar - they're marked “Needs verification” instead of guessed. Calendar times are floating local time.</p>
    </div>
  );
}
