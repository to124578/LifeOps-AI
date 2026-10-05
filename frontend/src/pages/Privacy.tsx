import { Trash2 } from "lucide-react";
import { useState } from "react";
import { api, resetSession } from "../api";
import { Card, ErrorBox } from "../components/ui";

export default function Privacy() {
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const wipe = async () => {
    if (!confirm("Delete all analyses from this browser session? This can't be undone.")) return;
    setErr("");
    try {
      const r = await api.deleteSession();
      resetSession();
      setMsg(`Deleted ${r.deleted_analyses} analysis(es).`);
    } catch (e) {
      setErr((e as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <h1 className="text-2xl font-bold">Privacy & limits</h1>
      <Card className="space-y-3 p-5 text-sm text-slate-700">
        <p><strong>What is stored.</strong> The text you submit and the extracted plan are saved in the server database so you can come back to them. Uploaded files themselves are read in memory and not kept.</p>
        <p><strong>Who sees it.</strong> Your text (or the image/PDF for OCR) is sent to the configured AI provider to extract the plan. The API key stays on the server.</p>
        <p><strong>Sessions.</strong> There are no accounts. Your browser gets a random session id, and "Delete" removes everything saved under it.</p>
        <p><strong>Not advice.</strong> This tool organizes information. It is not legal, medical, financial, immigration or government advice. Always check important dates with the original sender.</p>
        <p><strong>Known limits.</strong> OCR can misread text. Relative deadlines ("within 24 hours") are counted from when you analyzed the document unless you set a received time. Calendar events use floating local time.</p>
      </Card>
      {msg && <div className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{msg}</div>}
      {err && <ErrorBox>{err}</ErrorBox>}
      <button onClick={wipe} className="inline-flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-2.5 font-medium text-white hover:bg-rose-700"><Trash2 className="h-4 w-4" />Delete my session data</button>
    </div>
  );
}
