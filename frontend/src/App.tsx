import { Link, NavLink, Route, Routes } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./api";
import type { Health } from "./types";
import Landing from "./pages/Landing";
import Analyze from "./pages/Analyze";
import Results from "./pages/Results";
import Privacy from "./pages/Privacy";

function Header() {
  const link = ({ isActive }: { isActive: boolean }) => `rounded-lg px-3 py-1.5 text-sm font-medium ${isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-100"}`;
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="flex items-center gap-2 font-bold text-slate-900"><ShieldCheck className="h-6 w-6 text-indigo-600" />LifeOps <span className="text-indigo-600">AI</span></Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/analyze" className={link}>Analyze</NavLink>
          <NavLink to="/privacy" className={link}>Privacy</NavLink>
        </nav>
      </div>
    </header>
  );
}

export function useHealth() {
  const [h, setH] = useState<Health | null>(null);
  useEffect(() => { api.health().then(setH).catch(() => setH(null)); }, []);
  return h;
}

export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/analysis/:id" element={<Results />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="*" element={<div className="py-20 text-center"><p className="text-lg font-semibold">Page not found</p><Link className="text-indigo-600 underline" to="/">Go home</Link></div>} />
        </Routes>
      </main>
      <footer className="mx-auto max-w-6xl px-4 pb-8 text-center text-xs text-slate-400">Built by Tushar for WCC Launchpad 30. LifeOps AI organises information to help you act; it is not legal, medical, financial or other professional advice.</footer>
    </div>
  );
}
