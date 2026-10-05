import { AlertTriangle, CheckCircle2, HelpCircle, Quote, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";
import type { Conf, EvStatus } from "../types";
import { confLabel, evLabel } from "../lib";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-slate-200 bg-white shadow-sm ${className}`}>{children}</div>;
}

export function SectionTitle({ icon, children, right }: { icon?: ReactNode; children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between gap-2">
      <h2 className="flex items-center gap-2 text-base font-semibold text-slate-900">{icon}{children}</h2>
      {right}
    </div>
  );
}

const confStyle: Record<Conf, string> = {
  high: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  medium: "bg-amber-50 text-amber-700 ring-amber-200",
  low: "bg-rose-50 text-rose-700 ring-rose-200",
};
export function ConfBadge({ c, label = "Confidence" }: { c: Conf | ""; label?: string }) {
  if (!c) return null;
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${confStyle[c]}`}>{label}: {confLabel[c]}</span>;
}

const evStyle: Record<EvStatus, string> = {
  verified: "bg-emerald-50 text-emerald-700 ring-emerald-200 hover:bg-emerald-100",
  partial: "bg-amber-50 text-amber-700 ring-amber-200 hover:bg-amber-100",
  unsupported: "bg-rose-50 text-rose-700 ring-rose-200 hover:bg-rose-100",
  none: "bg-slate-50 text-slate-500 ring-slate-200",
};
export function EvidenceChip({ status, quote, onOpen }: { status: EvStatus; quote: string | null; onOpen?: (q: string) => void }) {
  const Icon = status === "verified" ? CheckCircle2 : status === "none" ? HelpCircle : AlertTriangle;
  const clickable = !!quote && !!onOpen && status !== "none";
  return (
    <button type="button" disabled={!clickable} onClick={() => quote && onOpen?.(quote)} title={quote || "The model gave no supporting quote"}
      className={`inline-flex max-w-full items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${evStyle[status]} ${clickable ? "cursor-pointer" : "cursor-default"}`}>
      <Icon className="h-3 w-3 shrink-0" /><span className="truncate">{evLabel[status]}</span>
    </button>
  );
}

export function Quoted({ text }: { text: string | null }) {
  if (!text) return null;
  return (
    <p className="mt-2 flex gap-1.5 rounded-lg bg-slate-50 px-2.5 py-1.5 text-xs italic text-slate-600">
      <Quote className="mt-0.5 h-3 w-3 shrink-0 text-slate-400" /><span>{text}</span>
    </p>
  );
}

export function NeedsVerification() {
  return <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800"><ShieldAlert className="h-3 w-3" />Needs verification</span>;
}

export function Spinner({ className = "h-5 w-5" }: { className?: string }) {
  return <span className={`inline-block animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600 ${className}`} />;
}

export function ErrorBox({ children }: { children: ReactNode }) {
  return <div role="alert" className="flex gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><div>{children}</div></div>;
}
