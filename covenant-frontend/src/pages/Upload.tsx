import { FileUp, Lock, Paperclip, Sparkles } from "lucide-react";
import React, { useCallback, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useBilling } from "../context/BillingContext";
import { getErrorMessage, uploadContract } from "../lib/api";

interface QueueItem {
  name: string;
  progress: number;
  stage: "uploading" | "analyzing" | "done" | "error";
  contractId?: string;
  error?: string;
}

function PaywallBlock() {
  const { status } = useBilling();
  return (
    <div className="rounded-lg flex flex-col items-center justify-center gap-3 py-20 mb-6 border-2 border-dashed border-line bg-panel">
      <div className="rounded-full w-12 h-12 flex items-center justify-center bg-amberBg">
        <Lock size={20} className="text-amber" />
      </div>
      <p className="text-sm font-semibold text-ink">You've used all {status?.uploads_limit} free contract uploads</p>
      <p className="text-xs text-slateLight max-w-sm text-center">
        Upgrade to Premium for unlimited uploads &mdash; everything else (ML analysis, chat, compliance, comparison) stays the same.
      </p>
      <Link
        to="/checkout"
        className="mt-2 flex items-center gap-1.5 text-sm font-medium px-4 py-2 rounded-md bg-brass text-ink"
      >
        <Sparkles size={14} /> Upgrade to Premium
      </Link>
    </div>
  );
}

export default function Upload() {
  const [dragging, setDragging] = useState(false);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const navigate = useNavigate();
  const { status, refresh } = useBilling();

  const limitReached = status?.plan === "free" && status?.limit_reached;

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((file) => {
      if (!/\.(pdf|docx)$/i.test(file.name)) return;

      const item: QueueItem = { name: file.name, progress: 0, stage: "uploading" };
      setQueue((q) => [item, ...q]);

      uploadContract(file, (pct) => {
        setQueue((q) => q.map((it) => (it.name === file.name && it.stage === "uploading" ? { ...it, progress: pct } : it)));
        if (pct === 100) {
          setQueue((q) => q.map((it) => (it.name === file.name ? { ...it, stage: "analyzing", progress: 100 } : it)));
        }
      })
        .then((contract) => {
          setQueue((q) => q.map((it) => (it.name === file.name ? { ...it, stage: "done", contractId: contract.id } : it)));
          refresh();
        })
        .catch((err) => {
          if (err?.response?.status === 402) {
            setQueue((q) => q.map((it) => (it.name === file.name
              ? { ...it, stage: "error", error: "Free plan limit reached." }
              : it)));
            refresh();
            navigate("/checkout");
            return;
          }
          setQueue((q) => q.map((it) => (it.name === file.name
            ? { ...it, stage: "error", error: getErrorMessage(err, "Upload failed.") }
            : it)));
        });
    });
  }, [refresh, navigate]);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-7">
      {limitReached ? (
        <PaywallBlock />
      ) : (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
          className={`rounded-lg flex flex-col items-center justify-center gap-3 py-20 mb-6 border-2 border-dashed transition-colors ${
            dragging ? "bg-amberBg border-brass" : "bg-panel border-line"
          }`}
        >
          <FileUp size={30} className="text-brass" strokeWidth={1.5} />
          <p className="text-sm font-medium text-ink">Drag and drop contracts here, or click to browse</p>
          <p className="text-xs text-slateLight">Supports PDF, DOCX &middot; OCR enabled for scanned documents &middot; Bulk upload supported</p>
          {status?.plan === "free" && status.uploads_limit && (
            <p className="text-xs text-slateLight">{status.remaining} of {status.uploads_limit} free uploads remaining</p>
          )}
          <label className="mt-2 text-sm font-medium px-4 py-2 rounded-md bg-ink text-paper cursor-pointer">
            Browse files
            <input type="file" accept=".pdf,.docx" multiple hidden onChange={(e) => handleFiles(e.target.files)} />
          </label>
        </div>
      )}

      {queue.length > 0 && (
        <>
          <h3 className="text-sm font-semibold mb-3 text-ink">Processing Queue</h3>
          <div className="flex flex-col gap-2.5">
            {queue.map((f) => (
              <button
                key={f.name}
                disabled={f.stage !== "done"}
                onClick={() => f.contractId && navigate(`/contracts/${f.contractId}`)}
                className="rounded-lg p-4 flex items-center gap-4 bg-panel border border-line text-left disabled:cursor-default"
              >
                <Paperclip size={16} className="text-slateLight shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-ink truncate">{f.name}</span>
                    <span className={`text-xs ${f.stage === "done" ? "text-greenln" : f.stage === "error" ? "text-redline" : "text-slate"}`}>
                      {f.stage === "uploading" && "Uploading..."}
                      {f.stage === "analyzing" && "Running ML pipeline (classify, score, extract)..."}
                      {f.stage === "done" && "Complete - click to view"}
                      {f.stage === "error" && (f.error || "Failed")}
                    </span>
                  </div>
                  <div className="w-full rounded-full h-1.5 bg-line">
                    <div
                      className="h-1.5 rounded-full transition-all"
                      style={{
                        width: `${f.stage === "done" ? 100 : f.stage === "analyzing" ? 90 : f.progress}%`,
                        background: f.stage === "done" ? "#2F7A52" : f.stage === "error" ? "#B3271E" : "#A9822E",
                      }}
                    />
                  </div>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
