import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listContracts } from "../lib/api";
import { Pill, statusLabel, statusTone } from "../components/ui";
import type { ContractSummary } from "../lib/types";

export default function Compliance() {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listContracts().then(setContracts).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex-1 px-8 py-7 text-sm text-slate">Loading...</div>;

  return (
    <div className="flex-1 overflow-y-auto px-8 py-7">
      {contracts.length === 0 ? (
        <div className="rounded-lg p-10 bg-panel border border-line text-center">
          <p className="text-sm text-slate">
            No contracts to audit yet. <Link to="/upload" className="text-brass font-medium">Upload one</Link> first.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {contracts.map((c) => (
            <Link key={c.id} to={`/contracts/${c.id}`} className="rounded-lg p-5 bg-panel border border-line block">
              <div className="mb-3">
                <div className="text-xs mb-1 text-slateLight font-mono">{c.display_code}</div>
                <div className="text-sm font-medium text-ink">{c.title}</div>
              </div>
              <Pill tone={statusTone(c.status)}>{statusLabel(c.status)}</Pill>
              <div className="mt-4 pt-4 flex items-center justify-between border-t border-line">
                <span className="text-xs text-slateLight">Risk score</span>
                <span className="text-xs font-semibold font-mono text-ink">{c.risk_score}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
