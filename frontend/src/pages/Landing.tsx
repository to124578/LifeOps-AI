import { ArrowRight, CalendarCheck, FileSearch, GitBranch, ShieldCheck, Workflow } from "lucide-react";
import { Link } from "react-router-dom";
import PipelineProgress from "../components/PipelineProgress";
import { Card } from "../components/ui";

const features = [
  { icon: <FileSearch className="h-5 w-5" />, t: "Evidence for every claim", d: "Each action, date and risk carries a quote from your document. The Verification Agent checks that quote really exists - fabricated ones get flagged." },
  { icon: <ShieldCheck className="h-5 w-5" />, t: "Deadline Shield", d: "Hard vs suggested dates, days left, and the prerequisites you still need before each deadline. Never invents a date." },
  { icon: <GitBranch className="h-5 w-5" />, t: "Action Graph", d: "See how requirements, dependent tasks and deadlines connect, from input to done." },
  { icon: <CalendarCheck className="h-5 w-5" />, t: "Portable Action Pack", d: "Export .ics calendar events plus a standard JSON / Markdown pack other apps can consume." },
];

export default function Landing() {
  return (
    <div className="space-y-14 py-6">
      <section className="mx-auto max-w-3xl text-center">
        <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700"><Workflow className="h-3.5 w-3.5" />Documents in, to-do list out</p>
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">Turn confusing information into <span className="text-indigo-600">clear action.</span></h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-600">Paste an email, notice, bill or screenshot. LifeOps tells you what you must do, by when, what you need first, and what can go wrong - with evidence for each point.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/analyze" className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white shadow-sm hover:bg-indigo-700">Analyze something <ArrowRight className="h-4 w-4" /></Link>
          <Link to="/analyze?sample=offer" className="rounded-xl border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50">Try the internship-offer demo</Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {features.map((f) => (
          <Card key={f.t} className="p-5">
            <div className="mb-2 flex items-center gap-2 font-semibold text-indigo-700">{f.icon}{f.t}</div>
            <p className="text-sm text-slate-600">{f.d}</p>
          </Card>
        ))}
      </section>

      <section className="grid items-center gap-8 md:grid-cols-2">
        <div>
          <h2 className="text-2xl font-bold">A visible five-stage pipeline</h2>
          <p className="mt-3 text-slate-600">The stages run one after another. You see each stage's real output and timing, and the verification step is plain code, not another model's opinion.</p>
        </div>
        <Card className="p-5"><PipelineProgress stages={[]} /></Card>
      </section>
    </div>
  );
}
