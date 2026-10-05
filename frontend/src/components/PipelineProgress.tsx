import { CheckCircle2, Circle, Loader2, TriangleAlert, XCircle } from "lucide-react";
import type { Stage } from "../types";

const ORDER = [
  ["intake", "Intake Agent", "Reads the source, detects language and type"],
  ["understanding", "Understanding Agent", "Extracts actions, dates, requirements, risks with quotes"],
  ["planning", "Planning Agent", "Orders tasks, finds dependencies, minimum path"],
  ["verification", "Verification Agent", "Checks every quote against the source text"],
  ["action", "Action Agent", "Builds checklist, calendar events, Action Pack"],
];

export default function PipelineProgress({ stages, compact = false }: { stages: Stage[]; compact?: boolean }) {
  const byName = Object.fromEntries(stages.map((s) => [s.name, s]));
  return (
    <ol className={compact ? "flex flex-wrap gap-2" : "space-y-3"}>
      {ORDER.map(([name, label, hint], i) => {
        const s = byName[name];
        const status: string = s?.status ?? "pending";
        const Icon = status === "done" ? CheckCircle2 : status === "running" ? Loader2 : status === "failed" ? XCircle : status === "degraded" ? TriangleAlert : Circle;
        const color = status === "done" ? "text-emerald-600" : status === "running" ? "text-indigo-600" : status === "failed" ? "text-rose-600" : status === "degraded" ? "text-amber-600" : "text-slate-300";
        if (compact)
          return (
            <li key={name} className="inline-flex items-center gap-1.5 rounded-full bg-white px-2.5 py-1 text-xs ring-1 ring-slate-200" title={s?.summary || hint}>
              <Icon className={`h-3.5 w-3.5 ${color}`} />{label.replace(" Agent", "")}{s?.ms ? <span className="text-slate-400">{(s.ms / 1000).toFixed(1)}s</span> : null}
            </li>
          );
        return (
          <li key={name} className="flex items-start gap-3">
            <div className={`mt-0.5 rounded-full ${status === "running" ? "running-ring" : ""}`}><Icon className={`h-6 w-6 ${color} ${status === "running" ? "animate-spin" : ""}`} /></div>
            <div className="min-w-0">
              <p className={`text-sm font-semibold ${status === "pending" ? "text-slate-400" : "text-slate-900"}`}>
                {i + 1}. {label}{s?.ms ? <span className="ml-2 text-xs font-normal text-slate-400">{(s.ms / 1000).toFixed(1)}s</span> : null}
              </p>
              <p className="text-xs text-slate-500">{s?.summary || hint}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
