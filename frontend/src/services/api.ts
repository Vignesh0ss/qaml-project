import axios from "axios";

const rawBase =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, "").trim() || "";
const api = axios.create({
  baseURL: rawBase || "/api/v1",
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

// Add request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("qaml_token");
    if (token && token !== "undefined" && token !== "null") {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Surface server-side error messages properly
api.interceptors.response.use(
  (res) => res,
  (err) => {
    // If token is expired or invalid (401), clear auth
    if (err?.response?.status === 401) {
      localStorage.removeItem("qaml_token");
      localStorage.removeItem("qaml_user");
      if (!window.location.pathname.includes("/login") && !window.location.pathname.includes("/signup")) {
        window.location.href = "/login";
      }
    }
    const serverMsg = err?.response?.data?.error || err?.response?.data?.msg;
    if (serverMsg) {
      return Promise.reject(new Error(serverMsg));
    }
    const code = err?.code as string | undefined;
    const isNetwork =
      code === "ERR_NETWORK" ||
      code === "ECONNREFUSED" ||
      (!err.response && err.message?.toLowerCase().includes("network"));
    if (isNetwork) {
      const hint =
        rawBase && !rawBase.startsWith("/")
          ? `Cannot reach API at ${rawBase}. Check the URL and CORS.`
          : "Cannot reach the backend API. Start the Flask server (port 5000) and use the Vite dev server so /api is proxied, or set VITE_API_BASE_URL to your API root (e.g. http://127.0.0.1:5000/api/v1).";
      return Promise.reject(new Error(hint));
    }
    return Promise.reject(err);
  }
);

export interface SubmitQueryPayload {
  disease_name: string;
  top_k?: number;
  constraints?: Record<string, unknown>;
}

export async function submitQuery(payload: SubmitQueryPayload) {
  const { data } = await api.post<{ task_id: string; status: string; results?: unknown }>("/query", payload);
  return data;
}

export async function getStatus(taskId: string) {
  const { data } = await api.get<{ task_id: string; status: string }>(`/query/${taskId}/status`);
  return data;
}

export async function getResults(taskId: string) {
  const { data } = await api.get<{
    task_id: string;
    disease_name: string;
    top_k: number;
    qubo_energy: number;
    ranked_drugs: Array<{ rank: number; score: number; molregno: string; canonical_smiles?: string; target_name?: string }>;
  }>(`/results/${taskId}`);
  return data;
}

export async function getAudit(taskId: string) {
  const { data } = await api.get<{ task_id: string; entries: Array<Record<string, unknown>> }>(`/audit/${taskId}`);
  return data;
}

export async function verifyAudit(taskId: string) {
  const { data } = await api.get<{ task_id: string; valid: boolean; message: string }>(`/audit/verify/${taskId}`);
  return data;
}

export async function getAuditHistory() {
  const { data } = await api.get<{
    items: Array<{
      task_id: string;
      disease_name: string;
      status: string;
      reason?: string;
      created_at?: string;
      completed_at?: string;
    }>;
  }>("/audit/history");
  return data;
}

export async function downloadWordReport(taskId: string) {
  const response = await api.get(`/reports/${taskId}/word`, { responseType: "blob" });
  return response.data as Blob;
}

export async function health() {
  const { data } = await api.get<{ status: string; service?: string }>("/health");
  return data;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  username?: string;
  message?: string;
}

export interface LoginPayload {
  username?: string;
  email?: string;
  password?: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export async function login(payload: LoginPayload) {
  const { data } = await api.post<AuthResponse>("/auth/login", payload);
  return data;
}

export async function register(payload: RegisterPayload) {
  const { data } = await api.post<AuthResponse>("/auth/register", payload);
  return data;
}

export interface StatsData {
  total_queries: number;
  completed: number;
  drugs_analyzed: number;
  audit_entries: number;
  recent: Array<{
    task_id: string;
    query: string;
    status: string;
    drugs: number;
    time: string;
  }>;
  history?: Array<{
    task_id: string;
    disease_name: string;
    status: string;
    reason?: string;
    created_at?: string;
  }>;
}

export async function getStats(): Promise<StatsData> {
  const { data } = await api.get<StatsData>("/stats");
  return data;
}

export interface ExperimentalSuggestPayload {
  age?: number;
  gender?: string;
  blood_group?: string;
  duration_days?: number;
  symptoms: string[];
  gene_patterns?: string[];
  lab_results?: {
    blood_test?: Record<string, number | string>;
    urine_test?: Record<string, number>;
    other_tests?: Record<string, number>;
  };
  notes?: string;
}

export interface ExperimentalSuggestResponse {
  run_id: string;
  mode: "experimental";
  predicted_diseases: Array<{ disease: string; prob: number }>;
  recommended_drugs: Array<{
    drug_name: string;
    final_score: number;
    source_diseases: string[];
    target: string;
    confidence: string;
  }>;
  summary: string;
  warnings: string[];
}

export async function experimentalSuggest(payload: ExperimentalSuggestPayload, experimentalApiKey?: string) {
  const headers = experimentalApiKey
    ? { "X-Experimental-Nvidia-Key": experimentalApiKey }
    : undefined;
  const { data } = await api.post<ExperimentalSuggestResponse>("/experimental/suggest", payload, { headers });
  return data;
}

export async function downloadExperimentalWordReport(runId: string) {
  const response = await api.get(`/experimental/report/${runId}/word`, { responseType: "blob" });
  return response.data as Blob;
}
