import {
  Bell, ChevronRight, FileText, GitCompare, LayoutDashboard, LogOut,
  MessageSquare, Search, ShieldCheck, Sparkles, UploadCloud,
} from "lucide-react";
import React from "react";
import { Link, NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useBilling } from "../context/BillingContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/contracts", label: "Contracts", icon: FileText },
  { to: "/upload", label: "Upload", icon: UploadCloud },
  { to: "/compliance", label: "Compliance", icon: ShieldCheck },
  { to: "/chat", label: "Chat with Contract", icon: MessageSquare },
  { to: "/comparison", label: "Comparison", icon: GitCompare },
];

const TITLES: Record<string, [string, string]> = {
  "/": ["Dashboard", "Portfolio-wide contract analytics and risk overview"],
  "/contracts": ["Contracts", "All ingested agreements and their review status"],
  "/upload": ["Upload", "Ingest new contracts for AI-powered analysis"],
  "/compliance": ["Compliance Audit", "Contracts checked against your corporate playbooks"],
  "/chat": ["Chat with Contract", "Ask natural-language questions, grounded in extracted clauses"],
  "/comparison": ["Contract Comparison", "Side-by-side redline between two versions"],
  "/profile": ["Profile", "Your account details, usage, and security settings"],
};

function UsagePanel() {
  const { status } = useBilling();
  if (!status) return null;

  if (status.plan === "premium") {
    return (
      <div className="rounded-lg p-3.5 bg-white/[0.05] border border-white/[0.08]">
        <div className="flex items-center gap-2">
          <Sparkles size={13} className="text-brass" />
          <span className="text-xs font-semibold text-[#F2E9D8]">Premium plan</span>
        </div>
        <p className="text-xs leading-relaxed text-slateLight mt-1">Unlimited contract uploads</p>
      </div>
    );
  }

  const used = status.uploads_used;
  const limit = status.uploads_limit ?? 30;
  const pct = Math.min(100, Math.round((used / limit) * 100));
  const near = pct >= 80;

  return (
    <div className="rounded-lg p-3.5 bg-white/[0.05] border border-white/[0.08]">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold text-[#F2E9D8]">Free plan</span>
        <span className="text-[11px] font-mono text-slateLight">{used} / {limit}</span>
      </div>
      <div className="w-full rounded-full h-1.5 bg-white/[0.08] mb-2">
        <div
          className="h-1.5 rounded-full"
          style={{ width: `${pct}%`, background: near ? "#B3271E" : "#A9822E" }}
        />
      </div>
      <Link
        to="/checkout"
        className="text-[11px] font-semibold text-brass"
      >
        {status.limit_reached ? "Upgrade to keep uploading \u2192" : "Upgrade to Premium \u2192"}
      </Link>
    </div>
  );
}

function Sidebar() {
  const { user, logout } = useAuth();
  const initials = (user?.full_name || "U").split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();

  return (
    <div className="h-full flex flex-col justify-between shrink-0 w-[232px] bg-ink">
      <div>
        <div className="flex items-center gap-2.5 px-5 pt-6 pb-7">
          <div className="flex items-center justify-center rounded w-7 h-7 bg-brass">
            <span className="font-serif text-ink text-[15px] font-bold">§</span>
          </div>
          <span className="font-serif text-[19px] tracking-wide text-paper">Covenant</span>
        </div>
        <nav className="flex flex-col gap-0.5 px-3">
          {NAV_ITEMS.map((it) => {
            const Icon = it.icon;
            return (
              <NavLink
                key={it.to}
                to={it.to}
                end={it.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-md text-left relative text-sm ${
                    isActive ? "bg-brass/[0.14] text-[#F2E9D8] font-semibold" : "text-[#AEB4C4] font-medium"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-r bg-brass" />}
                    <Icon size={17} strokeWidth={1.8} />
                    <span>{it.label}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>
      <div className="px-5 pb-6">
        <div className="flex items-center gap-1.5 mb-2 px-0.5">
          <Sparkles size={11} className="text-slateLight" />
          <span className="text-[10px] text-slateLight">Llama 3 8B via Ollama · localhost:11434</span>
        </div>
        <UsagePanel />
        <div className="flex items-center gap-2.5 mt-4 pt-4 border-t border-white/[0.08]">
          <Link to="/profile" className="flex items-center gap-2.5 flex-1 min-w-0">
            <div
              className="rounded-full flex items-center justify-center text-xs font-semibold w-[30px] h-[30px] bg-brass text-ink shrink-0"
            >
              {initials}
            </div>
            <div className="leading-tight min-w-0">
              <div className="text-xs font-medium text-[#F2E9D8] truncate">{user?.full_name}</div>
              <div className="text-[11px] text-slateLight capitalize">{user?.role}</div>
            </div>
          </Link>
          <button onClick={logout} title="Log out" className="shrink-0 p-1.5 rounded-md hover:bg-white/[0.06]">
            <LogOut size={15} className="text-slateLight" />
          </button>
        </div>
      </div>
    </div>
  );
}

function TopBar() {
  const location = useLocation();
  const [title, subtitle] = TITLES[location.pathname] || ["Covenant", ""];
  return (
    <div className="flex items-center justify-between px-8 py-5 shrink-0 border-b border-line">
      <div>
        <h1 className="font-serif text-[22px] text-ink font-semibold">{title}</h1>
        {subtitle && <p className="text-sm mt-0.5 text-slate">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-md px-3 py-2 bg-panel border border-line w-[260px]">
          <Search size={15} className="text-slateLight" />
          <input placeholder="Search contracts, clauses..." className="text-sm outline-none bg-transparent w-full text-ink" />
        </div>
        <button className="relative" aria-label="Notifications">
          <Bell size={19} className="text-slate" strokeWidth={1.8} />
          <span className="absolute -top-0.5 -right-0.5 rounded-full w-[7px] h-[7px] bg-redline" />
        </button>
      </div>
    </div>
  );
}

export default function AppLayout() {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="flex h-screen w-full bg-paper font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <Outlet />
      </div>
    </div>
  );
}
