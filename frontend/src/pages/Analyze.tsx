import { FileUp, Loader2, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useHealth } from "../App";
import { api } from "../api";
import { Card, ErrorBox } from "../components/ui";
import type { RecentItem, Sample } from "../types";

const OK_EXT = [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".md"];
const MAX_MB = 8;

export default function Analyze() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const health = useHealth();
  const [tab, setTab] = useState<"paste" | "upload">("paste");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [receivedAt, setReceivedAt] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [samples, setSamples] = useState<Sample[]>([]);
  const [recent, setRecent] = useState<RecentItem[]>([]);
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.samples().then(setSamples).catch(() => {});
    api.recent().then(setRecent).catch(() => {});
  }, []);

  const start = async (fn: () => Promise<{ id: string }>) => {
    setBusy(true);
    setErr("");
    try {
      const { id } = await fn();
      nav(`/analysis/${id}`);
    } catch (e) {
      setErr((e as Error).message);
      setBusy(false);
    }
  };

  const useSample = (s: Sample) => start(() => api.analyzeText(s.text));

  useEffect(() => {
    const want = params.get("sample");
    if (want && samples.length) {
      const s = samples.find((x) => x.id === want);
      if (s) useSample(s);
    }
  }, [samples]); // eslint-disable-line

  const pick = (f: File | undefined) => {
    if (!f) return;
    const ext = "." + (f.name.split(".").pop() || "").toLowerCase();
    if (!OK_EXT.includes(ext)) return setErr("That file type isn't supported. Use PDF, PNG/JPG/WEBP or .txt.");
    if (f.size > MAX_MB * 1024 * 1024) return setErr(`That file is over ${MAX_MB} MB.`);
    setErr("");
    setFile(f);
  };

  const submit = () => {
    if (tab === "paste") {
      if (!text.trim()) return setErr("Paste some text first.");
      return start(() => api.analyzeText(text, receivedAt || undefined));
    }
    if (!file) return setErr("Choose a file first.");
    return start(() => api.analyzeFile(file, receivedAt || undefined));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Analyze something</h1>
        <p className="text-slate-600">Paste a message or upload a document, notice, bill or screenshot.</p>
      </div>

      {health && !health.ai_configured && (
        <ErrorBox>The AI key isn't set on the server. Add <code>GEMINI_API_KEY</code> to <code>backend/.env</code> and restart.</ErrorBox>
      )}
      {health?.demo_mode && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">Demo mode: only the three sample documents work. Set a real API key to analyze your own.</div>
      )}

      <Card className="p-4">
        <div className="mb-3 flex gap-1 rounded-xl bg-slate-100 p-1 text-sm font-medium">
          {(["paste", "upload"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`flex-1 rounded-lg px-3 py-1.5 ${tab === t ? "bg-white shadow-sm" : "text-slate-500"}`}>
              {t === "paste" ? "Paste text" : "Upload file"}
            </button>
          ))}
        </div>

        {tab === "paste" ? (
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={12} placeholder="Paste an email, notice, bill or message here..." aria-label="Text to analyze"
            className="w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" />
        ) : (
          <div
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
            onClick={() => input.current?.click()}
            className={`flex h-56 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed text-center ${drag ? "border-indigo-500 bg-indigo-50" : "border-slate-300 bg-slate-50"}`}>
            <FileUp className="mb-2 h-8 w-8 text-slate-400" />
            {file ? <p className="font-medium">{file.name}</p> : <p className="font-medium">Drop a file here or click to browse</p>}
            <p className="mt-1 text-xs text-slate-500">PDF, PNG, JPG, WEBP or .txt, up to {MAX_MB} MB</p>
            <input ref={input} type="file" hidden accept={OK_EXT.join(",")} onChange={(e) => pick(e.target.files?.[0])} />
          </div>
        )}

        <details className="mt-3 text-sm">
          <summary className="cursor-pointer text-slate-500">Advanced: when did you receive this?</summary>
          <p className="mt-2 text-xs text-slate-500">Only matters for deadlines like "within 24 hours". If empty, the clock starts now.</p>
          <input type="datetime-local" value={receivedAt} onChange={(e) => setReceivedAt(e.target.value)} className="mt-1 rounded-lg border border-slate-200 px-2 py-1" />
        </details>

        {err && <div className="mt-3"><ErrorBox>{err}</ErrorBox></div>}

        <button onClick={submit} disabled={busy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-60">
          {busy ? <><Loader2 className="h-4 w-4 animate-spin" />Starting...</> : <><Sparkles className="h-4 w-4" />Build my action plan</>}
        </button>
      </Card>

      <div>
        <p className="mb-2 text-sm font-semibold text-slate-700">Or try a sample</p>
        <div className="grid gap-3 sm:grid-cols-3">
          {samples.map((s) => (
            <button key={s.id} disabled={busy} onClick={() => useSample(s)} className="rounded-xl border border-slate-200 bg-white p-3 text-left hover:border-indigo-300 hover:shadow-sm disabled:opacity-50">
              <p className="font-medium">{s.label}</p>
              <p className="text-xs text-slate-500">{s.blurb}</p>
            </button>
          ))}
        </div>
      </div>

      {recent.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-semibold text-slate-700">Recent analyses</p>
          <Card className="divide-y divide-slate-100">
            {recent.map((r) => (
              <Link key={r.id} to={`/analysis/${r.id}`} className="flex items-center justify-between px-4 py-3 text-sm hover:bg-slate-50">
                <span className="font-medium">{r.title}</span>
                <span className="text-xs text-slate-400">{new Date(r.created_at).toLocaleString()}</span>
              </Link>
            ))}
          </Card>
        </div>
      )}
    </div>
  );
}
