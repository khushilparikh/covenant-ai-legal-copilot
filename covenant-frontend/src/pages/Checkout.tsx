import {
  AlertTriangle, Building2, Check, CreditCard, Landmark, Lock, QrCode,
  ShieldCheck, Smartphone,
} from "lucide-react";
import React, { useMemo, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useBilling } from "../context/BillingContext";
import { createFakeOrder, getErrorMessage, payFakeOrder } from "../lib/api";
import type { PayOrderPayload } from "../lib/api";

type Step = "form" | "processing" | "success" | "declined";
type Method = "card" | "upi" | "netbanking" | "qr";

const BANKS = [
  "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank",
  "Kotak Mahindra Bank", "Punjab National Bank", "Test Bank (Always Declines)",
];

function formatCardNumber(value: string) {
  const digits = value.replace(/\D/g, "").slice(0, 19);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

function formatExpiry(value: string) {
  const digits = value.replace(/\D/g, "").slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}/${digits.slice(2)}`;
}

/** Purely decorative pseudo-QR pattern for the QR payment tab — not a
 * real scannable code, just a deterministic grid that looks like one so
 * the "scan to pay" flow reads visually rather than showing empty space. */
function PseudoQR({ seed }: { seed: string }) {
  const GRID = 21;
  const cells = useMemo(() => {
    let h = 0;
    for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
    const rand = () => {
      h = (h * 1103515245 + 12345) >>> 0;
      return (h >>> 16) % 100;
    };
    const isFinder = (r: number, c: number) =>
      (r < 7 && c < 7) || (r < 7 && c >= GRID - 7) || (r >= GRID - 7 && c < 7);
    const grid: boolean[][] = [];
    for (let r = 0; r < GRID; r++) {
      const row: boolean[] = [];
      for (let c = 0; c < GRID; c++) {
        row.push(isFinder(r, c) ? false : rand() < 45);
      }
      grid.push(row);
    }
    const finderPattern = (grid_: boolean[][], r0: number, c0: number) => {
      for (let r = 0; r < 7; r++) {
        for (let c = 0; c < 7; c++) {
          const border = r === 0 || r === 6 || c === 0 || c === 6;
          const center = r >= 2 && r <= 4 && c >= 2 && c <= 4;
          grid_[r0 + r][c0 + c] = border || center;
        }
      }
    };
    finderPattern(grid, 0, 0);
    finderPattern(grid, 0, GRID - 7);
    finderPattern(grid, GRID - 7, 0);
    return grid;
  }, [seed]);

  const cellSize = 7;
  const size = GRID * cellSize;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="rounded-md border border-line">
      <rect width={size} height={size} fill="#FFFFFF" />
      {cells.map((row, r) =>
        row.map((on, c) =>
          on ? <rect key={`${r}-${c}`} x={c * cellSize} y={r * cellSize} width={cellSize} height={cellSize} fill="#14213D" /> : null
        )
      )}
    </svg>
  );
}

export default function Checkout() {
  const { user } = useAuth();
  const { status, refresh } = useBilling();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const initialCycle = params.get("cycle") === "yearly" ? "yearly" : "monthly";

  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">(initialCycle);
  const [method, setMethod] = useState<Method>("card");
  const [step, setStep] = useState<Step>("form");
  const [error, setError] = useState<string | null>(null);

  // Card fields
  const [cardType, setCardType] = useState<"credit" | "debit">("credit");
  const [cardNumber, setCardNumber] = useState("");
  const [cardName, setCardName] = useState(user?.full_name || "");
  const [expiry, setExpiry] = useState("");
  const [cvv, setCvv] = useState("");

  // UPI field
  const [upiId, setUpiId] = useState("");

  // Netbanking field
  const [bankName, setBankName] = useState(BANKS[0]);

  if (!user) return <Navigate to="/login" replace />;
  if (!status) return null;

  const price = billingCycle === "monthly" ? status.price_inr_monthly : status.price_inr_yearly;

  const runPayment = async (extra: Partial<PayOrderPayload>) => {
    setError(null);
    setStep("processing");
    try {
      const order = await createFakeOrder(billingCycle);
      await new Promise((r) => setTimeout(r, 900));
      await payFakeOrder({ order_id: order.order_id, method, ...extra });
      await refresh();
      setStep("success");
    } catch (err: any) {
      if (err?.response?.status === 402) {
        setStep("declined");
      } else {
        setError(getErrorMessage(err, "Something went wrong. Please try again."));
        setStep("form");
      }
    }
  };

  const submitCard = (e: React.FormEvent) => {
    e.preventDefault();
    runPayment({ card_number: cardNumber, card_name: cardName, expiry, cvv });
  };

  const submitUpi = (e: React.FormEvent) => {
    e.preventDefault();
    runPayment({ upi_id: upiId });
  };

  const submitNetbanking = (e: React.FormEvent) => {
    e.preventDefault();
    runPayment({ bank_name: bankName });
  };

  const submitQr = () => {
    runPayment({});
  };

  const METHOD_TABS: { id: Method; label: string; icon: React.ElementType }[] = [
    { id: "card", label: "Card", icon: CreditCard },
    { id: "upi", label: "UPI", icon: Smartphone },
    { id: "netbanking", label: "Netbanking", icon: Landmark },
    { id: "qr", label: "QR Code", icon: QrCode },
  ];

  return (
    <div className="min-h-screen w-full bg-ink flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-3xl">
        <div className="flex items-center gap-2.5 justify-center mb-8">
          <div className="flex items-center justify-center rounded w-8 h-8 bg-brass">
            <span className="font-serif text-ink text-lg font-bold">§</span>
          </div>
          <span className="font-serif text-2xl text-paper">Covenant Pay</span>
        </div>

        <div className="bg-panel rounded-lg border border-line overflow-hidden grid grid-cols-5">
          {/* Order summary */}
          <div className="col-span-2 bg-paper p-6 border-r border-line">
            <h3 className="text-xs font-semibold text-slateLight uppercase tracking-wide mb-4">Order Summary</h3>

            <div className="flex items-center gap-1 mb-5">
              {(["monthly", "yearly"] as const).map((c) => (
                <button
                  key={c}
                  disabled={step !== "form"}
                  onClick={() => setBillingCycle(c)}
                  className={`flex-1 text-xs font-medium py-1.5 rounded-md border capitalize disabled:opacity-60 ${
                    billingCycle === c ? "bg-ink text-paper border-ink" : "border-line text-slate bg-panel"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate">Covenant Premium</span>
              <span className="text-ink font-medium">&#8377;{price.toLocaleString("en-IN")}</span>
            </div>
            <div className="text-xs text-slateLight mb-4">Billed {billingCycle}</div>

            <div className="border-t border-line pt-4 flex items-center justify-between">
              <span className="text-sm font-semibold text-ink">Total due today</span>
              <span className="font-serif text-xl font-semibold text-ink">&#8377;{price.toLocaleString("en-IN")}</span>
            </div>

            <ul className="text-xs text-slate flex flex-col gap-2 mt-6">
              <li className="flex items-center gap-2"><Check size={13} className="text-greenln shrink-0" /> Unlimited contract uploads</li>
              <li className="flex items-center gap-2"><Check size={13} className="text-greenln shrink-0" /> Full ML/NLP analysis</li>
              <li className="flex items-center gap-2"><Check size={13} className="text-greenln shrink-0" /> Priority processing</li>
            </ul>

            <div className="mt-6 flex items-center gap-1.5 text-[11px] text-slateLight">
              <ShieldCheck size={13} />
              <span>Simulated checkout &mdash; no real card, UPI, or bank data leaves this demo.</span>
            </div>
          </div>

          {/* Payment form / result */}
          <div className="col-span-3 p-6">
            {step === "form" && (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-4 gap-1.5">
                  {METHOD_TABS.map((m) => {
                    const Icon = m.icon;
                    return (
                      <button
                        key={m.id}
                        onClick={() => setMethod(m.id)}
                        className={`flex flex-col items-center gap-1 py-2.5 rounded-md border text-[11px] font-medium ${
                          method === m.id ? "bg-ink text-paper border-ink" : "border-line text-slate"
                        }`}
                      >
                        <Icon size={15} />
                        {m.label}
                      </button>
                    );
                  })}
                </div>

                {error && <p className="text-xs text-redline">{error}</p>}

                {method === "card" && (
                  <form onSubmit={submitCard} className="flex flex-col gap-3.5">
                    <div className="flex items-center gap-1.5">
                      {(["credit", "debit"] as const).map((t) => (
                        <button
                          key={t} type="button" onClick={() => setCardType(t)}
                          className={`flex-1 text-xs font-medium py-1.5 rounded-md border capitalize ${
                            cardType === t ? "bg-paper text-ink border-brass" : "border-line text-slate"
                          }`}
                        >
                          {t} card
                        </button>
                      ))}
                    </div>

                    <div>
                      <label className="text-xs font-medium text-slate">Card number</label>
                      <input
                        value={cardNumber}
                        onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                        placeholder="4111 1111 1111 1111"
                        inputMode="numeric"
                        required
                        className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass font-mono"
                      />
                    </div>

                    <div>
                      <label className="text-xs font-medium text-slate">Name on card</label>
                      <input
                        value={cardName}
                        onChange={(e) => setCardName(e.target.value)}
                        required
                        className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-medium text-slate">Expiry</label>
                        <input
                          value={expiry}
                          onChange={(e) => setExpiry(formatExpiry(e.target.value))}
                          placeholder="MM/YY"
                          inputMode="numeric"
                          required
                          className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-slate">CVV</label>
                        <input
                          value={cvv}
                          onChange={(e) => setCvv(e.target.value.replace(/\D/g, "").slice(0, 4))}
                          placeholder="123"
                          inputMode="numeric"
                          required
                          className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass font-mono"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="mt-1 flex items-center justify-center gap-2 rounded-md bg-brass text-ink text-sm font-semibold py-2.5"
                    >
                      <Lock size={13} /> Pay &#8377;{price.toLocaleString("en-IN")}
                    </button>

                    <p className="text-[11px] text-slateLight leading-relaxed">
                      Use <span className="font-mono text-ink">4111 1111 1111 1111</span> for a successful payment,
                      or <span className="font-mono text-ink">4000 0000 0000 0002</span> to see the decline flow.
                      Any name, future expiry, and 3&ndash;4 digit CVV work.
                    </p>
                  </form>
                )}

                {method === "upi" && (
                  <form onSubmit={submitUpi} className="flex flex-col gap-3.5">
                    <div>
                      <label className="text-xs font-medium text-slate">UPI ID</label>
                      <input
                        value={upiId}
                        onChange={(e) => setUpiId(e.target.value)}
                        placeholder="yourname@bank"
                        required
                        className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass font-mono"
                      />
                    </div>
                    <button
                      type="submit"
                      className="mt-1 flex items-center justify-center gap-2 rounded-md bg-brass text-ink text-sm font-semibold py-2.5"
                    >
                      <Lock size={13} /> Verify &amp; Pay &#8377;{price.toLocaleString("en-IN")}
                    </button>
                    <p className="text-[11px] text-slateLight leading-relaxed">
                      Use any ID like <span className="font-mono text-ink">name@bank</span> to succeed, or{" "}
                      <span className="font-mono text-ink">decline@upi</span> to see the decline flow.
                    </p>
                  </form>
                )}

                {method === "netbanking" && (
                  <form onSubmit={submitNetbanking} className="flex flex-col gap-3.5">
                    <div>
                      <label className="text-xs font-medium text-slate">Select your bank</label>
                      <select
                        value={bankName}
                        onChange={(e) => setBankName(e.target.value)}
                        className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass bg-panel"
                      >
                        {BANKS.map((b) => <option key={b} value={b}>{b}</option>)}
                      </select>
                    </div>
                    <button
                      type="submit"
                      className="mt-1 flex items-center justify-center gap-2 rounded-md bg-brass text-ink text-sm font-semibold py-2.5"
                    >
                      <Building2 size={13} /> Proceed to Bank &mdash; &#8377;{price.toLocaleString("en-IN")}
                    </button>
                    <p className="text-[11px] text-slateLight leading-relaxed">
                      Pick "Test Bank (Always Declines)" to see the decline flow &mdash; any other bank succeeds.
                    </p>
                  </form>
                )}

                {method === "qr" && (
                  <div className="flex flex-col items-center gap-3.5">
                    <PseudoQR seed={`${billingCycle}-${price}-${user.id}`} />
                    <p className="text-xs text-slate text-center">Scan with any UPI app &mdash; Google Pay, PhonePe, Paytm, or your bank's app.</p>
                    <button
                      onClick={submitQr}
                      className="w-full flex items-center justify-center gap-2 rounded-md bg-brass text-ink text-sm font-semibold py-2.5"
                    >
                      <Lock size={13} /> I've completed the payment
                    </button>
                    <p className="text-[11px] text-slateLight leading-relaxed text-center">
                      This is a simulated code &mdash; nothing to actually scan. Click above once you've "paid" to continue the demo.
                    </p>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => navigate(-1)}
                  className="text-xs text-slate text-center"
                >
                  Cancel and go back
                </button>
              </div>
            )}

            {step === "processing" && (
              <div className="h-full flex flex-col items-center justify-center py-16">
                <div className="w-8 h-8 rounded-full border-2 border-line border-t-brass animate-spin mb-4" />
                <p className="text-sm text-ink font-medium">Processing your payment...</p>
                <p className="text-xs text-slateLight mt-1">Please don't close this window.</p>
              </div>
            )}

            {step === "success" && (
              <div className="h-full flex flex-col items-center justify-center py-14 text-center">
                <div className="rounded-full w-14 h-14 flex items-center justify-center bg-greenlnBg mb-4">
                  <Check size={28} className="text-greenln" />
                </div>
                <p className="text-base font-semibold text-ink mb-1">Payment successful</p>
                <p className="text-sm text-slate mb-6">
                  You're now on the Premium plan &mdash; unlimited contract uploads are unlocked.
                </p>
                <button
                  onClick={() => navigate("/")}
                  className="text-sm font-medium px-5 py-2.5 rounded-md bg-ink text-paper"
                >
                  Continue to Dashboard
                </button>
              </div>
            )}

            {step === "declined" && (
              <div className="h-full flex flex-col items-center justify-center py-14 text-center">
                <div className="rounded-full w-14 h-14 flex items-center justify-center bg-redlineBg mb-4">
                  <AlertTriangle size={26} className="text-redline" />
                </div>
                <p className="text-base font-semibold text-ink mb-1">Payment declined</p>
                <p className="text-sm text-slate mb-6">
                  That test detail is scripted to always decline. Adjust it (or switch method) to complete the demo.
                </p>
                <button
                  onClick={() => setStep("form")}
                  className="text-sm font-medium px-5 py-2.5 rounded-md bg-ink text-paper"
                >
                  Try again
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
