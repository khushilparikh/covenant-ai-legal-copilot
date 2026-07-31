export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "reviewer" | "user";
  plan: "free" | "premium";
  company_name: string | null;
  job_title: string | null;
  phone_number: string | null;
  created_at: string;
}

export interface BillingStatus {
  plan: "free" | "premium";
  uploads_used: number;
  uploads_limit: number | null;
  remaining: number | null;
  limit_reached: boolean;
  price_inr_monthly: number;
  price_inr_yearly: number;
}

export interface FakeOrder {
  order_id: string;
  amount_inr: number;
  billing_cycle: "monthly" | "yearly";
}

export interface RiskFlag {
  severity: "low" | "medium" | "high";
  reason: string;
}

export interface Clause {
  id: string;
  clause_number: string;
  page_number: number | null;
  text: string;
  clause_type: string;
  classification_confidence: number;
  risk_score: number;
  risk_severity: "low" | "medium" | "high";
  risk_flags: RiskFlag[];
}

export type ContractStatus = "draft" | "pending_review" | "reviewed" | "approved" | "rejected";

export interface ContractSummary {
  id: string;
  display_code: string;
  title: string;
  contract_type: string;
  counterparty: string | null;
  status: ContractStatus;
  risk_score: number;
  page_count: number;
  created_at: string;
}

export interface ContractDetail extends ContractSummary {
  effective_date: string | null;
  expiry_date: string | null;
  governing_law: string | null;
  payment_terms: string | null;
  parties: string[] | null;
  monetary_values: string[] | null;
  executive_summary: string | null;
  clauses: Clause[];
}

export interface ComplianceResult {
  rule_name: string;
  status: "compliant" | "non_compliant" | "needs_review";
  reasoning: string;
}

export interface ChatMessage {
  role: "user" | "ai";
  content: string;
  sources: string[] | null;
  created_at: string;
}

export interface ComparisonResult {
  added: string[];
  removed: string[];
  modified: { clause: string; a: string; b: string; similarity: number; risk_change: number }[];
}

export interface DashboardSummary {
  contracts_reviewed: number;
  compliance_rate: number;
  average_risk_score: number;
  pending_review: number;
  status_breakdown: Record<string, number>;
  risk_distribution: Record<string, number>;
  clause_distribution: Record<string, number>;
}
