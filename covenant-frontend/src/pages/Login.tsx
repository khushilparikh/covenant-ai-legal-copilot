import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getErrorMessage } from "../lib/api";

export default function Login() {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const switchMode = (next: "login" | "register") => {
    setMode(next);
    setError(null);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, fullName);
      navigate("/");
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-ink">
      <div className="w-[380px]">
        <div className="flex items-center gap-2.5 justify-center mb-8">
          <div className="flex items-center justify-center rounded w-8 h-8 bg-brass">
            <span className="font-serif text-ink text-lg font-bold">§</span>
          </div>
          <span className="font-serif text-2xl text-paper">Covenant</span>
        </div>

        <div className="bg-panel rounded-lg border border-line overflow-hidden">
          <div className="grid grid-cols-2">
            <button
              onClick={() => switchMode("login")}
              className={`py-3 text-sm font-semibold transition-colors ${
                mode === "login" ? "bg-panel text-ink" : "bg-paper text-slate hover:text-ink"
              }`}
              style={mode === "login" ? { boxShadow: "inset 0 -2px 0 #A9822E" } : undefined}
            >
              Sign In
            </button>
            <button
              onClick={() => switchMode("register")}
              className={`py-3 text-sm font-semibold transition-colors ${
                mode === "register" ? "bg-panel text-ink" : "bg-paper text-slate hover:text-ink"
              }`}
              style={mode === "register" ? { boxShadow: "inset 0 -2px 0 #A9822E" } : undefined}
            >
              Sign Up
            </button>
          </div>

          <div className="p-7">
            <h2 className="font-serif text-xl text-ink font-semibold mb-1">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h2>
            <p className="text-sm text-slate mb-6">
              {mode === "login"
                ? "Sign in to your contract workspace."
                : "Free plan includes 30 contract uploads — no card required."}
            </p>

            <form onSubmit={submit} className="flex flex-col gap-3.5">
              {mode === "register" && (
                <div>
                  <label className="text-xs font-medium text-slate">Full name</label>
                  <input
                    value={fullName} onChange={(e) => setFullName(e.target.value)} required
                    className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
                  />
                </div>
              )}
              <div>
                <label className="text-xs font-medium text-slate">Email</label>
                <input
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                  className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate">Password</label>
                <input
                  type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                  className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm outline-none focus:border-brass"
                />
              </div>

              {error && <p className="text-xs text-redline">{error}</p>}

              <button
                type="submit" disabled={busy}
                className="mt-2 rounded-md bg-ink text-paper text-sm font-medium py-2.5 disabled:opacity-60"
              >
                {busy ? "Please wait..." : mode === "login" ? "Sign in" : "Create free account"}
              </button>
            </form>

            <p className="text-xs text-slate mt-5 text-center">
              {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
              <button
                onClick={() => switchMode(mode === "login" ? "register" : "login")}
                className="text-brass font-medium"
              >
                {mode === "login" ? "Sign up free" : "Sign in"}
              </button>
            </p>
          </div>
        </div>

        <p className="text-xs text-slateLight text-center mt-5">
          Demo login: admin@covenant.dev / ChangeMe123! (after running <code>python -m app.db.seed</code>)
        </p>
      </div>
    </div>
  );
}
