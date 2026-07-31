import React from "react";

const TONE_CLASSES: Record<string, string> = {
  slate: "bg-[#EEF0F3] text-slate",
  red: "bg-redlineBg text-redline",
  green: "bg-greenlnBg text-greenln",
  amber: "bg-amberBg text-amber",
  ink: "bg-[#EBEEF5] text-ink",
};

export function Pill({ children, tone = "slate" }: { children: React.ReactNode; tone?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium font-mono tracking-wide ${TONE_CLASSES[tone]}`}>
      {children}
    </span>
  );
}

export function statusTone(status: string): string {
  if (status === "approved" || status === "compliant" || status === "reviewed") return "green";
  if (status === "non_compliant" || status === "rejected") return "red";
  if (status === "needs_review" || status === "pending_review") return "amber";
  return "slate";
}

export function statusLabel(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function RiskDial({ score }: { score: number }) {
  const tone = score >= 61 ? "#B3271E" : score >= 31 ? "#B8862E" : "#2F7A52";
  const pct = Math.min(100, Math.max(0, score)) / 100;
  const r = 26;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative flex items-center justify-center" style={{ width: 64, height: 64 }}>
      <svg width="64" height="64" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={r} fill="none" stroke="#EAE8E1" strokeWidth="6" />
        <circle
          cx="32" cy="32" r={r} fill="none" stroke={tone} strokeWidth="6"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)} strokeLinecap="round"
          transform="rotate(-90 32 32)"
        />
      </svg>
      <span className="absolute text-sm font-semibold font-mono" style={{ color: tone }}>{score}</span>
    </div>
  );
}
