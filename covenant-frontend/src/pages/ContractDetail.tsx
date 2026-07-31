import { AlertTriangle, CheckCircle2, Download, Sparkles, X } from "lucide-react";
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ContractVisuals from "../components/ContractVisuals";
import {
  downloadContractReport, getComplianceResults, getContract, getErrorMessage,
  runComplianceAudit, suggestRedline, updateContractStatus,
} from "../lib/api";
import { Pill, RiskDial, statusLabel, statusTone } from "../components/ui";
import type { Clause, ComplianceResult, ContractDetail as ContractDetailType, ContractStatus } from "../lib/types";

const TABS = ["Summary", "Clauses", "Risk", "Redline", "Compliance"] as const;
type Tab = (typeof TABS)[number];

const STATUS_OPTIONS: ContractStatus[] = ["draft", "pending_review", "reviewed", "approved", "rejected"];

function RedlinePanel({ clause }: { clause: Clause | null }) {
  const [result, setResult] = useState<{ suggested_text: string; reason: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    if (!clause) return;
    setLoading(true);
    setError(null);
    try {
      const res = await suggestRedline(clause.id);
      setResult(res);
    } catch (err: any) {
      setError(
        err?.response?.status === 503
          ? "Ollama isn't running locally. Start it with `ollama serve` to generate redlines."
          : getErrorMessage(err, "Couldn't generate a redline suggestion.")
      );
    } finally {
      setLoading(false);
    }
  };

  if (!clause) {
    return <p className="text-sm text-slate">No flagged clauses found to redline — this contract has no high or medium risk clauses.</p>;
  }

  return (
    <div className="rounded-lg p-6 bg-ink">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={14} className="text-brass" />
        <span className="text-xs font-semibold tracking-wide text-brass">
          AI-SUGGESTED REDLINE · §{clause.clause_number} {clause.clause_type.replace(/_/g, " ")}
        </span>
      </div>
      <p className="text-sm leading-relaxed" style={{ color: "#C7CCDA", fontFamily: "Georgia, serif" }}>
        {clause.text}
      </p>

      {!result && (
        <button
          onClick={generate} disabled={loading}
          className="mt-5 text-xs font-medium px-3 py-1.5 rounded bg-brass text-ink disabled:opacity-60"
        >
          {loading ? "Generating via Ollama..." : "Generate redline suggestion"}
        </button>
      )}

      {error && <p className="text-xs text-redline mt-3">{error}</p>}

      {result && (
        <div className="mt-5 pt-4 border-t border-white/10">
          <p className="text-xs uppercase tracking-wide text-brass mb-2">Suggested revision</p>
          <p className="text-sm leading-relaxed" style={{ color: "#A9E0BF", fontFamily: "Georgia, serif" }}>{result.suggested_text}</p>
          <p className="text-xs mt-3 text-slateLight">{result.reason}</p>
        </div>
      )}
    </div>
  );
}

export default function ContractDetail() {
  const { id } = useParams<{ id: string }>();
  const [contract, setContract] = useState<ContractDetailType | null>(null);
  const [tab, setTab] = useState<Tab>("Summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [compliance, setCompliance] = useState<ComplianceResult[] | null>(null);
  const [complianceBusy, setComplianceBusy] = useState(false);
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getContract(id)
      .then(setContract)
      .catch((err) => setError(getErrorMessage(err, "Couldn't load this contract.")))
      .finally(() => setLoading(false));
    getComplianceResults(id).then(setCompliance).catch(() => setCompliance([]));
  }, [id]);

  const changeStatus = async (status: ContractStatus) => {
    if (!contract) return;
    const updated = await updateContractStatus(contract.id, status);
    setContract(updated);
  };

  const runAudit = async () => {
    if (!contract) return;
    setComplianceBusy(true);
    try {
      const results = await runComplianceAudit(contract.id);
      setCompliance(results);
    } finally {
      setComplianceBusy(false);
    }
  };

  const handleDownload = async () => {
    if (!contract) return;
    setDownloadBusy(true);
    setDownloadError(null);
    try {
      await downloadContractReport(contract.id, contract.display_code);
    } catch (err: any) {
      setDownloadError(getErrorMessage(err, "Couldn't generate the report."));
    } finally {
      setDownloadBusy(false);
    }
  };

  if (loading) return <div className="flex-1 px-8 py-7 text-sm text-slate">Loading contract...</div>;
  if (error || !contract) return <div className="flex-1 px-8 py-7 text-sm text-redline">{error || "Not found."}</div>;

  const riskiestClause = [...contract.clauses].sort((a, b) => b.risk_score - a.risk_score)[0] || null;

  return (
    <div className="flex-1 overflow-y-auto px-8 py-7">
      <Link to="/contracts" className="text-xs text-brass mb-4 inline-block">← Back to Contracts</Link>

      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="flex items-center gap-2 text-xs mb-1.5 text-slateLight font-mono">
            <span>{contract.display_code}</span><span>·</span><span>{contract.page_count} pages</span>
            <span>·</span><span>{new Date(contract.created_at).toLocaleDateString()}</span>
          </div>
          <h2 className="font-serif text-2xl text-ink font-semibold">{contract.title}</h2>
        </div>
        <div className="flex items-center gap-3">
          <RiskDial score={contract.risk_score} />
          <select
            value={contract.status}
            onChange={(e) => changeStatus(e.target.value as ContractStatus)}
            className="text-xs font-medium rounded-full px-2.5 py-1 border border-line bg-panel"
          >
            {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{statusLabel(s)}</option>)}
          </select>
          <button
            onClick={handleDownload}
            disabled={downloadBusy}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-ink text-paper disabled:opacity-60"
          >
            <Download size={13} />
            {downloadBusy ? "Preparing PDF..." : "Download Report"}
          </button>
        </div>
      </div>

      {downloadError && <p className="text-xs text-redline mb-4">{downloadError}</p>}

      <div className="flex gap-1 mb-6 border-b border-line">
        {TABS.map((t) => (
          <button
            key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium relative -mb-px ${tab === t ? "text-ink" : "text-slate"}`}
          >
            {t}
            {tab === t && <span className="absolute left-0 right-0 -bottom-px h-0.5 bg-brass" />}
          </button>
        ))}
      </div>

      {tab === "Summary" && (
        <>
          <ContractVisuals contract={contract} />
          <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 rounded-lg p-6 bg-panel border border-line">
            <h3 className="text-sm font-semibold mb-3 text-ink">Executive Summary</h3>
            <p className="text-sm leading-relaxed text-slate">{contract.executive_summary || "No summary generated."}</p>
            <div className="grid grid-cols-2 gap-4 mt-5 pt-5 border-t border-line">
              {[
                ["Effective Date", contract.effective_date], ["Expiry Date", contract.expiry_date],
                ["Governing Law", contract.governing_law], ["Payment Terms", contract.payment_terms],
              ].map(([k, v]) => (
                <div key={k}>
                  <div className="text-xs mb-1 text-slateLight">{k}</div>
                  <div className="text-sm font-medium text-ink font-mono">{v || "—"}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-lg p-6 bg-panel border border-line">
            <h3 className="text-sm font-semibold mb-3 text-ink">Key Risks</h3>
            <div className="flex flex-col gap-3">
              {contract.clauses.flatMap((cl) => cl.risk_flags.map((f, i) => (
                <div key={`${cl.id}-${i}`} className="flex gap-2.5">
                  <AlertTriangle size={15} className={`shrink-0 mt-0.5 ${f.severity === "high" ? "text-redline" : "text-amber"}`} />
                  <div>
                    <div className="text-xs font-medium text-ink">{f.reason}</div>
                    <div className="text-xs mt-0.5 text-slateLight font-mono">§{cl.clause_number}</div>
                  </div>
                </div>
              )))}
              {contract.clauses.every((c) => c.risk_flags.length === 0) && (
                <p className="text-xs text-slateLight">No risk flags raised for this contract.</p>
              )}
            </div>
          </div>
        </div>
        </>
      )}

      {tab === "Clauses" && (
        <div className="flex flex-col gap-3">
          {contract.clauses.map((cl) => (
            <div key={cl.id} className="rounded-lg p-5 flex gap-4 bg-panel border border-line">
              <div className="shrink-0 w-16 text-sm font-semibold font-mono text-brass">§{cl.clause_number}</div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Pill tone="ink">{cl.clause_type.replace(/_/g, " ")}</Pill>
                  <span className="text-xs text-slateLight font-mono">{cl.classification_confidence}% confidence</span>
                  <Pill tone={cl.risk_severity === "high" ? "red" : cl.risk_severity === "medium" ? "amber" : "green"}>
                    {cl.risk_severity} risk
                  </Pill>
                </div>
                <p className="text-sm leading-relaxed text-slate" style={{ fontFamily: "Georgia, serif" }}>{cl.text}</p>
              </div>
            </div>
          ))}
          {contract.clauses.length === 0 && <p className="text-sm text-slateLight">No clauses were extracted from this document.</p>}
        </div>
      )}

      {tab === "Risk" && (
        <div className="flex flex-col gap-3">
          {contract.clauses.flatMap((cl) => cl.risk_flags.map((f, i) => (
            <div key={`${cl.id}-${i}`} className={`rounded-lg p-5 border border-line ${f.severity === "high" ? "bg-redlineBg" : "bg-amberBg"}`}>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={15} className={f.severity === "high" ? "text-redline" : "text-amber"} />
                <span className="text-sm font-semibold text-ink">{f.reason}</span>
                <span className="text-xs ml-auto text-slateLight font-mono">§{cl.clause_number}</span>
              </div>
              <p className="text-sm text-slate">Clause type: {cl.clause_type.replace(/_/g, " ")} · Risk score {cl.risk_score}</p>
            </div>
          )))}
          {contract.clauses.every((c) => c.risk_flags.length === 0) && (
            <p className="text-sm text-slateLight">No risk flags raised for this contract.</p>
          )}
        </div>
      )}

      {tab === "Redline" && <RedlinePanel clause={riskiestClause && riskiestClause.risk_score >= 31 ? riskiestClause : null} />}

      {tab === "Compliance" && (
        <div className="rounded-lg p-6 bg-panel border border-line">
          <div className="flex items-center justify-between mb-5">
            <span className="text-sm font-semibold text-ink">Compliance vs. active playbook rules</span>
            <button
              onClick={runAudit} disabled={complianceBusy}
              className="text-xs font-medium px-3 py-1.5 rounded bg-ink text-paper disabled:opacity-60"
            >
              {complianceBusy ? "Running audit..." : "Run compliance audit"}
            </button>
          </div>
          {compliance === null && <p className="text-sm text-slate">Loading...</p>}
          {compliance && compliance.length === 0 && (
            <p className="text-sm text-slateLight">No audit has been run yet — click "Run compliance audit" above.</p>
          )}
          <div className="flex flex-col divide-y divide-line">
            {compliance?.map((r, i) => (
              <div key={i} className="flex items-start gap-3 py-2.5">
                {r.status === "compliant" ? <CheckCircle2 size={16} className="text-greenln mt-0.5" /> : <X size={16} className="text-redline mt-0.5" />}
                <div>
                  <div className="text-sm text-ink font-medium">{r.rule_name}</div>
                  <div className="text-xs text-slate mt-0.5">{r.reasoning}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
