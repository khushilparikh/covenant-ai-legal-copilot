import { ArrowUpRight } from "lucide-react";
import React, { useEffect, useState } from "react";
import { compareContracts, getErrorMessage, listContracts } from "../lib/api";
import type { ComparisonResult, ContractSummary } from "../lib/types";

export default function Comparison() {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [aId, setAId] = useState("");
  const [bId, setBId] = useState("");
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listContracts().then((cs) => {
      setContracts(cs);
      if (cs.length >= 2) { setAId(cs[1].id); setBId(cs[0].id); }
    });
  }, []);

  const run = async () => {
    if (!aId || !bId) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await compareContracts(aId, bId));
    } catch (err: any) {
      setError(getErrorMessage(err, "Couldn't compare these contracts."));
    } finally {
      setBusy(false);
    }
  };

  if (contracts.length < 2) {
    return <div className="flex-1 px-8 py-7 text-sm text-slate">Upload at least two contracts to compare them.</div>;
  }

  return (
    <div className="flex-1 overflow-y-auto px-8 py-7">
      <div className="flex items-center gap-3 mb-6">
        <select value={aId} onChange={(e) => setAId(e.target.value)} className="rounded-lg px-4 py-2.5 text-sm font-medium bg-panel border border-line text-ink">
          {contracts.map((c) => <option key={c.id} value={c.id}>{c.display_code} — {c.title}</option>)}
        </select>
        <ArrowUpRight size={16} className="text-slateLight" />
        <select value={bId} onChange={(e) => setBId(e.target.value)} className="rounded-lg px-4 py-2.5 text-sm font-medium bg-panel border border-line text-ink">
          {contracts.map((c) => <option key={c.id} value={c.id}>{c.display_code} — {c.title}</option>)}
        </select>
        <button onClick={run} disabled={busy} className="ml-auto text-sm font-medium px-4 py-2.5 rounded-lg bg-ink text-paper disabled:opacity-60">
          {busy ? "Comparing..." : "Compare"}
        </button>
      </div>

      {error && <p className="text-sm text-redline mb-4">{error}</p>}

      {result && (
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-lg p-5 bg-greenlnBg border border-line">
            <h3 className="text-xs font-semibold mb-3 uppercase tracking-wide text-greenln">Added ({result.added.length})</h3>
            {result.added.map((a) => <p key={a} className="text-sm mb-2 text-ink">+ {a}</p>)}
            {result.added.length === 0 && <p className="text-xs text-slateLight">No added clauses.</p>}
          </div>
          <div className="rounded-lg p-5 bg-redlineBg border border-line">
            <h3 className="text-xs font-semibold mb-3 uppercase tracking-wide text-redline">Removed ({result.removed.length})</h3>
            {result.removed.map((a) => <p key={a} className="text-sm mb-2 text-ink">− {a}</p>)}
            {result.removed.length === 0 && <p className="text-xs text-slateLight">No removed clauses.</p>}
          </div>
          <div className="rounded-lg p-5 bg-amberBg border border-line">
            <h3 className="text-xs font-semibold mb-3 uppercase tracking-wide text-amber">Modified ({result.modified.length})</h3>
            {result.modified.map((m) => (
              <div key={m.clause} className="text-sm mb-3">
                <div className="font-medium text-ink font-mono text-xs">{m.clause}</div>
                <div className="text-slate text-xs mt-1 line-through opacity-70">{m.a}</div>
                <div className="text-ink text-xs mt-1">{m.b}</div>
                {m.risk_change !== 0 && (
                  <div className={`text-xs mt-1 font-mono ${m.risk_change > 0 ? "text-redline" : "text-greenln"}`}>
                    Risk {m.risk_change > 0 ? "+" : ""}{m.risk_change}
                  </div>
                )}
              </div>
            ))}
            {result.modified.length === 0 && <p className="text-xs text-slateLight">No modified clauses detected.</p>}
          </div>
        </div>
      )}
    </div>
  );
}
