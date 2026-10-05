import { AlertTriangle, ChevronDown, Info } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import ActionGraph from "../components/ActionGraph";
import { ActionList, DeadlineShield } from "../components/ActionList";
import { ExportPanel, InfoPanels, SourcePanel, WhatIf } from "../components/Panels";
import PipelineProgress from "../components/PipelineProgress";
import { Card, ConfBadge, ErrorBox } from "../components/ui";
import { daysLeft, fmtDue } from "../lib";
import type { Analysis } from "../types";

type Tab = "plan" | "graph" | "source" | "export";
const TABS: [Tab, string][] = [["plan", "Action plan"], ["graph", "Action graph"], ["source", "Source & evidence"], ["export", "Export"]];

export default function Results() {
  const { id = "" } = useParams();
  const [a, setA] = useState<Analysis | null>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<Tab>("plan");
  const [quote, setQuote] = useState<string | null>(null);
  const [notesOpen, setNotesOpen] = useState(false);

  useEffect(() => {
    let stop = false;
    const tick = async () => {
      try {
        const r = await api.get(id);
        if (stop) return;
        setA(r);
        if (r.status === "processing") setTimeout(tick, 700);
      } catch (e) {
        if (!stop) setErr((e as Error).message);
      }
    };
    tick();
    return () => { stop = true; };
  }, [id]);

  const openEvidence = useCallback((q: string) => { setQuote(q); setTab("source"); }, []);

  if (err) return <div className="mx-auto max-w-xl space-y-3 py-10"><ErrorBox>{err}</ErrorBox><Link to="/analyze" className="text-indigo-600 underline">Back to Analyze</Link></div>;
  if (!a) return <p className="py-20 text-center text-slate-500">Loading...</p>;

  if (a.status === "processing")
    return (
      <div className="mx-auto max-w-xl py-10">
        <h1 className="mb-1 text-xl font-bold">Building your action plan...</h1>
        <p className="mb-5 text-sm text-slate-500">This usually takes 10-30 seconds.</p>
        <Card className="p-5"><PipelineProgress stages={a.pipeline} /></Card>
      </div>
    );

  if (a.status === "failed")
    return (
      <div className="mx-auto max-w-xl space-y-4 py-10">
        <ErrorBox>{a.error || "The analysis failed."}</ErrorBox>
        <Card className="p-5"><PipelineProgress stages={a.pipeline} /></Card>
        <Link to="/analyze" className="inline-block rounded-xl bg-indigo-600 px-5 py-2.5 font-medium text-white">Try again</Link>
      </div>
    );

  const next = a.deadlines.filter((d) => d.status !== "done" && d.due_at).sort((x, y) => (x.due_at! < y.due_at! ? -1 : 1))[0];
  const nl = next ? daysLeft(next.due_at) : null;
  const common = { a, onChange: setA, onEvidence: openEvidence, onError: setErr };

  return (
    <div className="space-y-5">
      <Card className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">{a.document_type || "Document"} · {a.source_name}</p>
            <h1 className="text-2xl font-bold">{a.title}</h1>
            <p className="mt-2 max-w-3xl text-slate-600">{a.summary}</p>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <ConfBadge c={a.overall_confidence} label="Overall confidence" />
            <span className="text-xs text-slate-400">{a.provider}</span>
          </div>
        </div>
        <div className="mt-4"><PipelineProgress stages={a.pipeline} compact /></div>
      </Card>

      {next && nl && (
        <div className={`flex flex-wrap items-center justify-between gap-2 rounded-2xl px-5 py-3 text-white ${nl.tone === "red" ? "bg-rose-600" : nl.tone === "amber" ? "bg-amber-500" : "bg-emerald-600"}`}>
          <p className="font-semibold">Next deadline: {next.label}</p>
          <p className="text-sm">{fmtDue(next.due_at)} · {nl.text}</p>
        </div>
      )}

      {a.disclaimer && <div className="flex gap-2 rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 text-xs text-slate-600"><Info className="mt-0.5 h-4 w-4 shrink-0" />{a.disclaimer}</div>}
      {a.intake_notes.map((n) => <div key={n} className="flex gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800"><AlertTriangle className="h-4 w-4 shrink-0" />{n}</div>)}

      {a.verification_notes.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50">
          <button onClick={() => setNotesOpen(!notesOpen)} className="flex w-full items-center justify-between px-4 py-2.5 text-sm font-medium text-amber-900">
            <span>{a.verification_notes.length} verification note(s)</span><ChevronDown className={`h-4 w-4 transition ${notesOpen ? "rotate-180" : ""}`} />
          </button>
          {notesOpen && <ul className="list-inside list-disc space-y-1 px-4 pb-3 text-sm text-amber-900">{a.verification_notes.map((n) => <li key={n}>{n}</li>)}</ul>}
        </div>
      )}

      <div role="tablist" className="flex gap-1 overflow-x-auto rounded-xl bg-slate-200/60 p-1 text-sm font-medium">
        {TABS.map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={`whitespace-nowrap rounded-lg px-4 py-2 ${tab === k ? "bg-white shadow-sm" : "text-slate-600"}`}>{label}</button>
        ))}
      </div>

      {tab === "plan" && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <DeadlineShield {...common} />
            <ActionList {...common} />
            <WhatIf a={a} />
          </div>
          <InfoPanels a={a} onEvidence={openEvidence} />
        </div>
      )}
      {tab === "graph" && <ActionGraph a={a} onChange={setA} />}
      {tab === "source" && <SourcePanel a={a} quote={quote} />}
      {tab === "export" && <ExportPanel a={a} />}
    </div>
  );
}
