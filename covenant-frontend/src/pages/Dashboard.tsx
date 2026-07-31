import { AlertTriangle, ChevronRight } from "lucide-react";
import React, { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip as RTooltip, XAxis, YAxis,
} from "recharts";
import { Link } from "react-router-dom";
import { getDashboardSummary, getErrorMessage, listContracts } from "../lib/api";
import type { ContractSummary, DashboardSummary } from "../lib/types";

const PALETTE = ["#14213D", "#A9822E", "#B3271E", "#2F7A52", "#8891A0", "#B8862E"];

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [attention, setAttention] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, contracts] = await Promise.all([getDashboardSummary(), listContracts()]);
        setSummary(s);
        setAttention(contracts.filter((c) => c.risk_score >= 55).slice(0, 6));
      } catch (err: any) {
        setError(getErrorMessage(err, "Couldn't load dashboard data."));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="flex-1 px-8 py-7 text-sm text-slate">Loading dashboard...</div>;
  if (error) return <div className="flex-1 px-8 py-7 text-sm text-redline">{error}</div>;
  if (!summary) return null;

  const riskDist = Object.entries(summary.risk_distribution).map(([band, count]) => ({ band, count }));
  const clauseDist = Object.entries(summary.clause_distribution).map(([name, value], i) => ({
    name, value, color: PALETTE[i % PALETTE.length],
  }));

  const stats = [
    { label: "Contracts Reviewed", value: summary.contracts_reviewed },
    { label: "Compliance Rate", value: `${summary.compliance_rate}%` },
    { label: "Avg. Risk Score", value: summary.average_risk_score },
    { label: "Pending Review", value: summary.pending_review },
  ];

  return (
    <div className="flex-1 overflow-y-auto px-8 py-7">
      <div className="grid grid-cols-4 gap-4 mb-7">
        {stats.map((s) => (
          <div key={s.label} className="rounded-lg p-5 bg-panel border border-line">
            <div className="text-xs font-medium mb-2 text-slate">{s.label}</div>
            <span className="font-serif text-[30px] text-ink font-semibold">{s.value}</span>
          </div>
        ))}
      </div>

      {summary.contracts_reviewed === 0 ? (
        <div className="rounded-lg p-10 bg-panel border border-line text-center">
          <p className="text-sm text-slate">
            No contracts uploaded yet.{" "}
            <Link to="/upload" className="text-brass font-medium">Upload your first contract</Link> to see analytics here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-lg p-5 bg-panel border border-line">
            <h3 className="text-sm font-semibold mb-4 text-ink">Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={riskDist} layout="vertical" margin={{ left: 10 }}>
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="band" tick={{ fontSize: 11, fill: "#5B6478" }} axisLine={false} tickLine={false} width={70} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={16}>
                  {riskDist.map((entry, i) => (
                    <Cell key={i} fill={entry.band === "high" ? "#B3271E" : entry.band === "medium" ? "#B8862E" : "#2F7A52"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-lg p-5 bg-panel border border-line">
            <h3 className="text-sm font-semibold mb-4 text-ink">Clause Distribution</h3>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={clauseDist} dataKey="value" nameKey="name" innerRadius={38} outerRadius={62} paddingAngle={2}>
                  {clauseDist.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <RTooltip contentStyle={{ borderRadius: 8, border: "1px solid #E4E2DB", fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-lg p-5 bg-panel border border-line">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-ink">Needs Attention</h3>
              <Link to="/contracts" className="text-xs font-medium flex items-center gap-1 text-brass">
                View all <ChevronRight size={13} />
              </Link>
            </div>
            <div className="flex flex-col divide-y divide-line">
              {attention.length === 0 && <p className="text-xs text-slateLight py-3">No high-risk contracts right now.</p>}
              {attention.map((c) => (
                <Link key={c.id} to={`/contracts/${c.id}`} className="flex items-center justify-between py-2.5">
                  <div className="min-w-0">
                    <div className="text-xs font-medium text-ink truncate">{c.title}</div>
                    <div className="text-[11px] mt-0.5 text-slateLight font-mono">{c.display_code}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <AlertTriangle size={13} className={c.risk_score >= 61 ? "text-redline" : "text-amber"} />
                    <span className="text-sm font-semibold font-mono" style={{ color: c.risk_score >= 61 ? "#B3271E" : "#B8862E" }}>
                      {c.risk_score}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
