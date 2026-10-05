import { useMemo, useState } from "react";
import { api } from "../api";
import type { Analysis } from "../types";
import { daysLeft } from "../lib";
import { Card } from "./ui";

const W = 210, H = 60, GX = 80, GY = 16, PAD = 20;

type NodeKind = "source" | "req" | "action" | "deadline" | "done";
interface N { id: string; kind: NodeKind; label: string; sub?: string; col: number; x: number; y: number; status?: string; warn?: boolean; tone?: string }
interface E { from: string; to: string; dashed?: boolean }

function build(a: Analysis) {
  const level: Record<string, number> = {};
  const preds: Record<string, string[]> = {};
  a.dependencies.forEach((d) => (preds[d.to_action_id] ||= []).push(d.from_action_id));
  const lv = (id: string, seen = new Set<string>()): number => {
    if (id in level) return level[id];
    if (seen.has(id)) return 0;
    seen.add(id);
    return (level[id] = (preds[id] || []).length ? 1 + Math.max(...preds[id].map((p) => lv(p, seen))) : 0);
  };
  a.actions.forEach((x) => lv(x.id));
  const maxLv = Math.max(0, ...a.actions.map((x) => level[x.id] ?? 0));
  const hasReq = a.requirements.length > 0, hasDl = a.deadlines.length > 0;
  const reqCol = 1, actStart = hasReq ? 2 : 1;
  const dlCol = actStart + maxLv + 1, doneCol = hasDl ? dlCol + 1 : dlCol;
  const cols: N[][] = Array.from({ length: doneCol + 1 }, () => []);
  const nodes: N[] = [];
  const add = (n: Omit<N, "x" | "y">) => { const full = { ...n, x: 0, y: 0 }; nodes.push(full); cols[n.col].push(full); };

  add({ id: "src", kind: "source", label: a.title, sub: "Input", col: 0 });
  a.requirements.forEach((r) => add({ id: "r" + r.id, kind: "req", label: r.item, sub: r.required ? "Requirement" : "Optional", col: reqCol, warn: r.evidence_status === "unsupported" }));
  a.actions.forEach((x) => add({ id: x.id, kind: "action", label: x.title, sub: x.status === "done" ? "Done" : `Action · ${x.priority}`, col: actStart + (level[x.id] ?? 0), status: x.status, warn: x.needs_verification }));
  a.deadlines.forEach((d) => add({ id: "d" + d.id, kind: "deadline", label: d.label, sub: d.status === "done" ? "Done" : daysLeft(d.due_at).text, col: dlCol, status: d.status, warn: d.needs_verification, tone: daysLeft(d.due_at).tone }));
  add({ id: "done", kind: "done", label: "Done", sub: "All obligations met", col: doneCol });

  const edges: E[] = [];
  const hasIn = new Set<string>();
  a.requirements.forEach((r) => {
    edges.push({ from: "src", to: "r" + r.id });
    r.action_ids.forEach((id) => { edges.push({ from: "r" + r.id, to: id }); hasIn.add(id); });
  });
  a.dependencies.forEach((d) => { edges.push({ from: d.from_action_id, to: d.to_action_id }); hasIn.add(d.to_action_id); });
  a.actions.forEach((x) => { if (!hasIn.has(x.id)) edges.push({ from: "src", to: x.id, dashed: true }); });
  const linked = new Set<string>(), hasOut = new Set(a.dependencies.map((d) => d.from_action_id));
  a.deadlines.forEach((d) => {
    d.action_ids.forEach((id) => { edges.push({ from: id, to: "d" + d.id }); linked.add(id); });
    edges.push({ from: "d" + d.id, to: "done" });
  });
  a.actions.forEach((x) => { if (!hasOut.has(x.id) && !linked.has(x.id)) edges.push({ from: x.id, to: "done" }); });

  const tallest = Math.max(...cols.map((c) => c.length));
  const totalH = tallest * (H + GY) - GY;
  cols.forEach((c, ci) => {
    const colH = c.length * (H + GY) - GY;
    c.forEach((n, i) => { n.x = PAD + ci * (W + GX); n.y = PAD + (totalH - colH) / 2 + i * (H + GY); });
  });
  const HEAD: Record<NodeKind, string> = { source: "Input", req: "Requirements", action: "Actions", deadline: "Deadlines", done: "Done" };
  const heads = cols.map((c) => (c[0] ? HEAD[c[0].kind] : "Actions"));
  return { heads, nodes, edges, width: PAD * 2 + cols.length * W + (cols.length - 1) * GX, height: PAD * 2 + totalH, cols: cols.length };
}

const fill: Record<NodeKind, string> = { source: "#eef2ff", req: "#f8fafc", action: "#ffffff", deadline: "#fffbeb", done: "#ecfdf5" };
const stroke: Record<NodeKind, string> = { source: "#6366f1", req: "#94a3b8", action: "#6366f1", deadline: "#f59e0b", done: "#10b981" };

export default function ActionGraph({ a, onChange }: { a: Analysis; onChange: (a: Analysis) => void }) {
  const g = useMemo(() => build(a), [a]);
  const [hover, setHover] = useState<string | null>(null);
  const byId = Object.fromEntries(g.nodes.map((n) => [n.id, n]));

  const click = async (n: N) => {
    if (n.kind !== "action") return;
    try { onChange(await api.completeTask(n.id, n.status !== "done")); } catch { /* shown elsewhere */ }
  };
  return (
    <Card className="p-4">
      <p className="mb-3 text-sm text-slate-600">Input → requirements → dependent actions → deadlines → done. Click an action to mark it done. Dashed borders need verification.</p>
      <div className="overflow-x-auto rounded-xl bg-slate-50 p-2" role="img" aria-label="Action graph">
        <svg width={g.width} height={g.height + 22} viewBox={`0 0 ${g.width} ${g.height + 22}`}>
          <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#94a3b8" /></marker></defs>
          {g.heads.map((h, i) => <text key={i} x={PAD + i * (W + GX) + W / 2} y={12} textAnchor="middle" className="fill-slate-400" fontSize="11" fontWeight="600">{h.toUpperCase()}</text>)}
          <g transform="translate(0,22)">
            {g.edges.map((e, i) => {
              const f = byId[e.from], t = byId[e.to];
              if (!f || !t) return null;
              const x1 = f.x + W, y1 = f.y + H / 2, x2 = t.x, y2 = t.y + H / 2, mx = (x1 + x2) / 2;
              const hot = hover && (hover === e.from || hover === e.to);
              return <path key={i} d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`} fill="none" stroke={hot ? "#4f46e5" : "#cbd5e1"} strokeWidth={hot ? 2.2 : 1.4} strokeDasharray={e.dashed ? "4 4" : undefined} markerEnd="url(#arr)" />;
            })}
            {g.nodes.map((n) => {
              const done = n.status === "done";
              const strokeC = done ? "#10b981" : n.kind === "deadline" && n.tone === "red" ? "#e11d48" : stroke[n.kind];
              return (
                <g key={n.id} transform={`translate(${n.x},${n.y})`} onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)} onClick={() => click(n)} style={{ cursor: n.kind === "action" ? "pointer" : "default" }}>
                  <title>{n.label}</title>
                  <rect width={W} height={H} rx={12} fill={done ? "#ecfdf5" : fill[n.kind]} stroke={strokeC} strokeWidth={1.6} strokeDasharray={n.warn ? "5 3" : undefined} />
                  <foreignObject x={8} y={5} width={W - 16} height={H - 10}>
                    <div style={{ fontFamily: "inherit", lineHeight: 1.2 }}>
                      <div style={{ fontSize: 10, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: ".04em" }}>{done ? "✓ " : ""}{n.sub}</div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "#0f172a", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", textDecoration: done ? "line-through" : "none" }}>{n.label}</div>
                    </div>
                  </foreignObject>
                </g>
              );
            })}
          </g>
        </svg>
      </div>
    </Card>
  );
}
