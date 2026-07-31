import axios from "axios";
import type {
  BillingStatus,
  ChatMessage,
  ComparisonResult,
  ComplianceResult,
  ContractDetail,
  ContractStatus,
  ContractSummary,
  DashboardSummary,
  FakeOrder,
  User,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE_URL });

export function getErrorMessage(err: any, fallback = "Something went wrong. Please try again."): string {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI/Pydantic validation errors: [{type, loc, msg, input, ctx}, ...]
    return detail.map((d) => d?.msg || JSON.stringify(d)).join("; ");
  }
  return fallback;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("covenant_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("covenant_token");
      localStorage.removeItem("covenant_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// --- Auth -----------------------------------------------------------
export async function login(email: string, password: string) {
  const { data } = await api.post<{ access_token: string; user: User }>("/api/auth/login", { email, password });
  return data;
}

export async function register(email: string, password: string, full_name: string) {
  const { data } = await api.post<{ access_token: string; user: User }>("/api/auth/register", {
    email, password, full_name,
  });
  return data;
}

export async function getMyProfile() {
  const { data } = await api.get<User>("/api/auth/me");
  return data;
}

export async function updateMyProfile(payload: {
  full_name?: string;
  company_name?: string;
  job_title?: string;
  phone_number?: string;
}) {
  const { data } = await api.patch<User>("/api/auth/me", payload);
  return data;
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const { data } = await api.post<{ detail: string }>("/api/auth/me/change-password", {
    current_password: currentPassword, new_password: newPassword,
  });
  return data;
}

// --- Contracts --------------------------------------------------------
export async function listContracts(statusFilter?: string) {
  const { data } = await api.get<ContractSummary[]>("/api/contracts", {
    params: statusFilter ? { status_filter: statusFilter } : {},
  });
  return data;
}

export async function getContract(id: string) {
  const { data } = await api.get<ContractDetail>(`/api/contracts/${id}`);
  return data;
}

export async function uploadContract(file: File, onProgress?: (pct: number) => void) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<ContractDetail>("/api/contracts/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
    },
  });
  return data;
}

export async function updateContractStatus(id: string, status: ContractStatus) {
  const { data } = await api.patch<ContractDetail>(`/api/contracts/${id}/status`, { status });
  return data;
}

// --- Compliance -------------------------------------------------------
export async function runComplianceAudit(contractId: string) {
  const { data } = await api.post<ComplianceResult[]>(`/api/compliance/${contractId}/run`);
  return data;
}

export async function getComplianceResults(contractId: string) {
  const { data } = await api.get<ComplianceResult[]>(`/api/compliance/${contractId}`);
  return data;
}

// --- Chat ---------------------------------------------------------------
export async function askContract(contractId: string, question: string) {
  const { data } = await api.post<{ answer: string; sources: string[] }>("/api/chat/ask", {
    contract_id: contractId, question,
  });
  return data;
}

export async function getChatHistory(contractId: string) {
  const { data } = await api.get<ChatMessage[]>(`/api/chat/${contractId}/history`);
  return data;
}

// --- Comparison -----------------------------------------------------
export async function compareContracts(contractAId: string, contractBId: string) {
  const { data } = await api.post<ComparisonResult>("/api/comparison", {
    contract_a_id: contractAId, contract_b_id: contractBId,
  });
  return data;
}

// --- Dashboard --------------------------------------------------------
export async function getDashboardSummary() {
  const { data } = await api.get<DashboardSummary>("/api/dashboard/summary");
  return data;
}

// --- Redline ------------------------------------------------------------
export async function suggestRedline(clauseId: string) {
  const { data } = await api.post(`/api/redline/${clauseId}`);
  return data as { clause_id: string; original_text: string; suggested_text: string; reason: string; source: string };
}

// --- Billing ------------------------------------------------------------
export async function getBillingStatus() {
  const { data } = await api.get<BillingStatus>("/api/billing/status");
  return data;
}

export async function createFakeOrder(billingCycle: "monthly" | "yearly") {
  const { data } = await api.post<FakeOrder>("/api/billing/checkout/create-order", { billing_cycle: billingCycle });
  return data;
}

export interface PayOrderPayload {
  order_id: string;
  method: "card" | "upi" | "netbanking" | "qr";
  card_number?: string;
  card_name?: string;
  expiry?: string;
  cvv?: string;
  upi_id?: string;
  bank_name?: string;
}

export async function payFakeOrder(payload: PayOrderPayload) {
  const { data } = await api.post<BillingStatus>("/api/billing/checkout/pay", payload);
  return data;
}
// --- Search -------------------------------------------------------------
export async function downloadContractReport(contractId: string, displayCode: string) {
  const response = await api.get(`/api/contracts/${contractId}/export/pdf`, { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `${displayCode}_report.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function semanticSearch(query: string, contractId?: string) {
  const { data } = await api.get("/api/search/semantic", { params: { q: query, contract_id: contractId } });
  return data as { text: string; metadata: Record<string, any>; score: number }[];
}
