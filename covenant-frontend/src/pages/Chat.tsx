import { FileText, Send } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { askContract, getChatHistory, listContracts } from "../lib/api";
import { Pill } from "../components/ui";
import type { ChatMessage, ContractSummary } from "../lib/types";

export default function Chat() {
  const [contracts, setContracts] = useState<ContractSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listContracts().then((cs) => {
      setContracts(cs);
      if (cs.length) setSelectedId(cs[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    getChatHistory(selectedId).then(setMessages);
  }, [selectedId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || !selectedId || busy) return;
    const question = input;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: question, sources: null, created_at: new Date().toISOString() }]);
    setBusy(true);
    try {
      const res = await askContract(selectedId, question);
      setMessages((m) => [...m, { role: "ai", content: res.answer, sources: res.sources, created_at: new Date().toISOString() }]);
    } catch {
      setMessages((m) => [...m, { role: "ai", content: "Something went wrong answering that — please try again.", sources: null, created_at: new Date().toISOString() }]);
    } finally {
      setBusy(false);
    }
  };

  const selected = contracts.find((c) => c.id === selectedId);

  return (
    <div className="flex-1 flex flex-col px-8 py-7 overflow-hidden">
      {contracts.length === 0 ? (
        <p className="text-sm text-slate">Upload a contract first to chat with it.</p>
      ) : (
        <>
          <div className="flex items-center gap-2 mb-4">
            <FileText size={14} className="text-amber" />
            <select
              value={selectedId}
              onChange={(e) => { setSelectedId(e.target.value); setMessages([]); }}
              className="text-sm border border-line rounded-md px-2 py-1.5 bg-panel"
            >
              {contracts.map((c) => <option key={c.id} value={c.id}>{c.display_code} — {c.title}</option>)}
            </select>
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-4 pr-2">
            {messages.length === 0 && (
              <p className="text-sm text-slateLight">
                Ask anything about {selected?.title} — termination terms, payment schedule, obligations, or risk exposure.
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`rounded-lg px-4 py-3 max-w-[70%] text-sm leading-relaxed ${
                  m.role === "user" ? "bg-ink text-paper" : "bg-panel border border-line text-ink"
                }`}>
                  {m.content}
                  {m.sources && m.sources.length > 0 && (
                    <div className="mt-2 flex gap-1.5 flex-wrap">
                      {m.sources.map((s) => <Pill key={s} tone="ink">§{s}</Pill>)}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div className="flex items-center gap-2 mt-4 rounded-lg px-3 py-2.5 bg-panel border border-line">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask about payment terms, obligations, risks..."
              className="flex-1 text-sm outline-none bg-transparent text-ink"
              disabled={busy}
            />
            <button onClick={send} disabled={busy} className="p-1.5 rounded bg-brass disabled:opacity-60">
              <Send size={14} className="text-ink" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
