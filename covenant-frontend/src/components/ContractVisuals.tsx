import React, { useMemo } from "react";
import {
  Cell, Pie, PieChart, ResponsiveContainer, Tooltip as RTooltip,
} from "recharts";
import type { ContractDetail } from "../lib/types";

const PALETTE = ["#14213D", "#A9822E", "#2F7A52", "#B3271E", "#5B6478", "#B8862E", "#8891A0"];
const SEVERITY_COLORS: Record<string, string> = { high: "#B3271E", medium: "#B8862E", low: "#2F7A52" };

function riskZone(score: number) {
  if (score >= 61) return { label: "High Risk", color: "#B3271E", note: "We'd recommend a closer legal review before signing." };
  if (score >= 31) return { label: "Medium Risk", color: "#B8862E", note: "A few clauses may be worth a second look." };
  return { label: "Low Risk", color: "#2F7A52", note: "No major concerns stood out in this contract." };
}

/**
 * Self-contained SVG gauge — deliberately NOT built from a recharts
 * ResponsiveContainer + externally-positioned text overlay. That combo is
 * exactly what caused the earlier overlap bug: the chart's rendered size
 * scales with its container while the "centered" text used a fixed
 * negative margin, so the two drifted out of sync at different widths.
 * Everything here lives in one fixed SVG coordinate system instead, so
 * the number and label are always exactly where the arc puts them.
 */
function RiskGauge({ score }: { score: number }) {
  const zone = riskZone(score);
  const clamped = Math.min(100, Math.max(0, score));

  const cx = 90;
  const cy = 88;
  const r = 64;
  const strokeWidth = 14;

  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const point = (deg: number) => ({ x: cx + r * Math.cos(toRad(deg)), y: cy - r * Math.sin(toRad(deg)) });
  const arcPath = (startDeg: number, endDeg: number) => {
    const start = point(startDeg);
    const end = point(endDeg);
    const largeArc = Math.abs(startDeg - endDeg) > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
  };

  const scoreAngle = 180 - (clamped / 100) * 180;

  return (
    <div className="flex flex-col items-center h-full">
      <svg width="180" height="105" viewBox="0 0 180 105">
        <path d={arcPath(180, 0)} fill="none" stroke="#EAE8E1" strokeWidth={strokeWidth} strokeLinecap="round" />
        {clamped > 0 && (
          <path d={arcPath(180, scoreAngle)} fill="none" stroke={zone.color} strokeWidth={strokeWidth} strokeLinecap="round" />
        )}
        <text x={cx} y={cy - 12} textAnchor="middle" fontSize="28" fontWeight="700" fill={zone.color} fontFamily="'Source Serif 4', Georgia, serif">
          {clamped}
        </text>
        <text x={cx} y={cy + 6} textAnchor="middle" fontSize="9.5" fontWeight="600" fill={zone.color} letterSpacing="0.06em">
          {zone.label.toUpperCase()}
        </text>
      </svg>
      <p className="text-xs text-slate text-center mt-1 max-w-[210px]">{zone.note}</p>
    </div>
  );
}

export default function ContractVisuals({ contract }: { contract: ContractDetail }) {
  const clauseTypeData = useMemo(() => {
    const counts = new Map<string, number>();
    for (const cl of contract.clauses) {
      const label = cl.clause_type.replace(/_/g, " ");
      counts.set(label, (counts.get(label) || 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([name, value], i) => ({ name, value, color: PALETTE[i % PALETTE.length] }))
      .sort((a, b) => b.value - a.value);
  }, [contract.clauses]);

  const severityCounts = useMemo(() => {
    const counts = { high: 0, medium: 0, low: 0 };
    for (const cl of contract.clauses) counts[cl.risk_severity] += 1;
    return counts;
  }, [contract.clauses]);

  const total = contract.clauses.length;
  const topClauseType = clauseTypeData[0];
  const flaggedCount = severityCounts.high + severityCounts.medium;

  if (total === 0) return null;

  return (
    <div className="rounded-lg p-6 bg-panel border border-line mb-4">
      <h3 className="text-sm font-semibold mb-1 text-ink">Visual Overview</h3>
      <p className="text-xs text-slateLight mb-5">A plain-language snapshot of this contract &mdash; no legal background needed.</p>

      <div className="grid grid-cols-3 gap-4 items-stretch">
        {/* Overall risk gauge */}
        <div className="rounded-lg border border-line p-4 flex flex-col items-center justify-center">
          <RiskGauge score={contract.risk_score} />
        </div>

        {/* Clause type breakdown */}
        <div className="rounded-lg border border-line p-4 flex flex-col items-center">
          <ResponsiveContainer width="100%" height={130}>
            <PieChart>
              <Pie data={clauseTypeData} dataKey="value" nameKey="name" innerRadius={32} outerRadius={54} paddingAngle={2}>
                {clauseTypeData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Pie>
              <RTooltip contentStyle={{ borderRadius: 8, border: "1px solid #E4E2DB", fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <p className="text-xs text-slate text-center mt-2 max-w-[210px]">
            {topClauseType
              ? <>This contract is mostly made up of <b className="text-ink">{topClauseType.name}</b> clauses ({Math.round((topClauseType.value / total) * 100)}%), across {total} clauses total.</>
              : "No clauses to summarize."}
          </p>
        </div>

        {/* Severity breakdown, in plain bars */}
        <div className="rounded-lg border border-line p-4 flex flex-col justify-center gap-3">
          {(["high", "medium", "low"] as const).map((sev) => {
            const count = severityCounts[sev];
            const pct = total ? Math.round((count / total) * 100) : 0;
            const label = sev === "high" ? "Need attention" : sev === "medium" ? "Worth reviewing" : "Look fine";
            return (
              <div key={sev}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate">{label}</span>
                  <span className="font-mono font-semibold text-ink">{count}</span>
                </div>
                <div className="w-full rounded-full h-2 bg-line overflow-hidden">
                  <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, background: SEVERITY_COLORS[sev] }} />
                </div>
              </div>
            );
          })}
          <p className="text-xs text-slate mt-1">
            {flaggedCount > 0
              ? <><b className="text-ink">{flaggedCount} of {total}</b> clauses were flagged as needing a closer look.</>
              : "No clauses were flagged \u2014 this contract looks straightforward."}
          </p>
        </div>
      </div>
    </div>
  );
}
