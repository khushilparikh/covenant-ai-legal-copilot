import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getBillingStatus } from "../lib/api";
import type { BillingStatus } from "../lib/types";
import { useAuth } from "./AuthContext";

interface BillingContextValue {
  status: BillingStatus | null;
  refresh: () => Promise<void>;
}

const BillingContext = createContext<BillingContextValue | undefined>(undefined);

export function BillingProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [status, setStatus] = useState<BillingStatus | null>(null);

  const refresh = useCallback(async () => {
    if (!user) return;
    try {
      const data = await getBillingStatus();
      setStatus(data);
    } catch {
      // silently ignore — billing display is non-critical, never blocks the app
    }
  }, [user]);

  useEffect(() => {
    if (user) refresh();
    else setStatus(null);
  }, [user, refresh]);

  return (
    <BillingContext.Provider value={{ status, refresh }}>
      {children}
    </BillingContext.Provider>
  );
}

export function useBilling() {
  const ctx = useContext(BillingContext);
  if (!ctx) throw new Error("useBilling must be used within BillingProvider");
  return ctx;
}
