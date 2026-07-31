import { ChevronRight } from "lucide-react";
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getErrorMessage, listContracts } from "../lib/api";
import { Pill, statusLabel, statusTone } from "../components/ui";
import type { ContractSummary } from "../lib/types";

export default function ContractsList() {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listContracts()
      .then(setContracts)
      .catch((err) => setError(getErrorMessage(err, "Couldn't load contracts.")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-7">
      {loading && <p className="text-sm text-slate">Loading contracts...</p>}
      {error && <p className="text-sm text-redline">{error}</p>}

      {!loading && !error && contracts.length === 0 && (
        <div className="rounded-lg p-10 bg-panel border border-line text-center">
          <p className="text-sm text-slate">
            No contracts uploaded yet. <Link to="/upload" className="text-brass font-medium">Upload one</Link> to get started.
          </p>
        </div>
      )}

      {!loading && !error && contracts.length > 0 && (
        <div className="rounded-lg overflow-hidden bg-panel border border-line">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-paper border-b border-line">
                {["Contract", "Type", "Status", "Risk", "Pages", "Uploaded", ""].map((h) => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-semibold text-slate">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contracts.map((c) => (
                <tr key={c.id} className="border-b border-line last:border-0 hover:bg-black/[0.015]">
                  <td className="px-5 py-4">
                    <Link to={`/contracts/${c.id}`} className="font-medium text-ink hover:text-brass">{c.title}</Link>
                    <div className="text-xs mt-0.5 text-slateLight font-mono">{c.display_code}</div>
                  </td>
                  <td className="px-5 py-4 text-slate">{c.contract_type}</td>
                  <td className="px-5 py-4"><Pill tone={statusTone(c.status)}>{statusLabel(c.status)}</Pill></td>
                  <td className="px-5 py-4">
                    <span className="font-semibold font-mono" style={{
                      color: c.risk_score >= 61 ? "#B3271E" : c.risk_score >= 31 ? "#B8862E" : "#2F7A52",
                    }}>
                      {c.risk_score}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate font-mono">{c.page_count}</td>
                  <td className="px-5 py-4 text-slate font-mono">{new Date(c.created_at).toLocaleDateString()}</td>
                  <td className="px-5 py-4">
                    <Link to={`/contracts/${c.id}`}><ChevronRight size={16} className="text-slateLight" /></Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
