import { useEffect, useState } from "react";
import { useParams, Link, useLocation } from "react-router-dom";
import { downloadWordReport, getResults, getStatus } from "../services/api";
import {
  FlaskConical,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Shield,
  Zap,
  TrendingUp,
  CheckCircle,
  Sparkles,
  Brain,
  Download,
} from "lucide-react";
import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

type RankedDrug = {
  rank?: number;
  score?: number;
  drug_name?: string;
  target_name?: string;
  molregno?: string;
  canonical_smiles?: string;
  mechanism?: string;
  evidence_level?: string;
  source?: string;
  max_phase?: number;
  best_activity?: number;
  activity_type?: string;
  confidence_label?: "HIGH" | "MEDIUM" | "LOW";
  priority?: "HIGH" | "MEDIUM" | "LOW";
  reasoning?: string;
};

type DiseaseInfo = {
  canonical_name?: string;
  description?: string;
  icd_code?: string;
};

type ResultsData = {
  task_id: string;
  disease_name: string;
  disease_info?: DiseaseInfo;
  top_k?: number;
  qubo_energy?: number;
  ranked_drugs?: RankedDrug[];
  ai_summary?: string;
  medical_summary?: string;
  ai_powered?: boolean;
  model_version?: string;
  message?: string;
  reason?: string;
  rejected_drugs?: { name: string; reason: string; molregno?: string; priority?: "HIGH" | "MEDIUM" | "LOW" }[];
  pipeline_summary?: {
    stage_genes: number;
    stage_targets: number;
    stage_candidates_raw: number;
    stage_hard_rejected: number;
    stage_passed: number;
    stage_ranked: number;
  };
};

const STATUS_LABEL: Record<string, string> = {
  loading: "Connecting…",
  queued: "Queued — waiting for worker…",
  running: "Pipeline running…",
  done: "Done",
  not_found: "Task not found",
  error: "Error",
  database_offline: "Database is offline. Loading cached results if available.",
};

export default function Results() {
  const { taskId } = useParams<{ taskId: string }>();
  const location = useLocation();
  const offlineData = location.state?.offlineResults;

  const [data, setData] = useState<ResultsData | null>(null);
  const [status, setStatus] = useState<string>("loading");
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const summaryText = data?.medical_summary ?? data?.ai_summary ?? "";

  useEffect(() => {
    if (!taskId) return;
    let cancelled = false;

    if (offlineData) {
      setStatus("done");
      setData(offlineData as ResultsData);
      return;
    }

    const poll = async () => {
      try {
        const s = await getStatus(taskId);
        if (cancelled) return;
        setStatus(s.status);

        if (s.status === "done") {
          const res = await getResults(taskId);
          if (!cancelled) setData(res as ResultsData);
          return;
        }
        if (s.status === "not_found") {
          setError("Task not found. It may have expired.");
          return;
        }
        setTimeout(poll, 500);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load results.");
      }
    };

    poll();
    return () => { cancelled = true; };
  }, [taskId, offlineData]);

  useEffect(() => {
    if (!taskId || !data) return;
    const currentSummary = (data.medical_summary ?? data.ai_summary ?? "").trim().toLowerCase();
    if (currentSummary !== "summary generation in progress...") return;

    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 20;

    const refreshSummary = async () => {
      if (cancelled || attempts >= maxAttempts) return;
      attempts += 1;
      try {
        const latest = (await getResults(taskId)) as ResultsData;
        if (cancelled) return;
        setData(latest);
        const latestSummary = (latest.medical_summary ?? latest.ai_summary ?? "").trim().toLowerCase();
        if (latestSummary === "summary generation in progress...") {
          setTimeout(refreshSummary, 1500);
        }
      } catch {
        setTimeout(refreshSummary, 1500);
      }
    };

    const timer = window.setTimeout(refreshSummary, 1200);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [taskId, data]);

  /* ── Error state ── */
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-xl mx-auto mt-16 bg-red-50 border border-red-200 rounded-2xl p-8 text-center"
      >
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-red-800 mb-2">Something went wrong</h2>
        <p className="text-red-600 mb-6">{error}</p>
        <Link
          to="/query"
          className="inline-flex items-center gap-2 bg-red-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-red-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Try Again
        </Link>
        <p className="text-xs text-slate-400 mt-4">
          Back to <Link to="/results" className="underline hover:text-accent-600">results</Link>
        </p>
      </motion.div>
    );
  }

  /* ── Loading / polling state ── */
  if (status !== "done" || !data) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-xl mx-auto mt-24 text-center space-y-6"
      >
        <div className="inline-flex items-center justify-center w-20 h-20 bg-accent-100 rounded-full mx-auto">
          <Loader2 className="w-10 h-10 text-accent-600 animate-spin" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-primary-900">Processing Query</h2>
          <p className="text-slate-500 mt-2">{STATUS_LABEL[status] ?? status}</p>
        </div>
        <div className="flex items-center justify-center gap-2">
          {["Pipeline", "QUBO"].map((step, i) => (
            <span
              key={step}
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                i === 0
                  ? "bg-accent-500 text-white animate-pulse"
                  : "bg-slate-200 text-slate-500"
              }`}
            >
              {step}
            </span>
          ))}
        </div>
      </motion.div>
    );
  }

  /* ── Results ── */
  const chartData = (data.ranked_drugs ?? []).map((d) => ({
    name: String(d.drug_name ?? d.target_name ?? d.molregno ?? `Drug ${d.rank}`).slice(0, 14),
    score: Math.round((d.score ?? 0) * 100),
  }));

  const isAiPowered = Boolean(data.ai_powered);
  const ps = data.pipeline_summary;

  async function handleDownloadWord() {
    if (!taskId) return;
    setDownloading(true);
    try {
      const blob = await downloadWordReport(taskId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `qaml-report-${taskId}.doc`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to download report.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <p className="text-sm text-slate-500 mb-1 flex items-center gap-1">
            <ArrowLeft className="w-3 h-3" />
            <Link to="/query" className="hover:text-accent-600 transition-colors">
              Back to query
            </Link>
          </p>
          <h1 className="text-3xl font-bold text-primary-900">Results</h1>
          <p className="text-slate-500 mt-1">
            <span className="font-semibold text-slate-700">
              {data.disease_info?.canonical_name || data.disease_name}
            </span>{" "}
            · {data.ranked_drugs?.length ?? 0} candidates selected
          </p>
          {data.disease_info?.description && (
            <p className="text-sm text-slate-400 mt-1 max-w-xl italic">{data.disease_info.description}</p>
          )}
        </div>
        <div className="flex gap-3">
          {isAiPowered && (
            <span className="inline-flex items-center gap-1.5 bg-purple-100 text-purple-700 border border-purple-200 px-4 py-2.5 rounded-xl text-sm font-semibold">
              <Sparkles className="w-4 h-4" />
              AI-Powered Suggestions
            </span>
          )}
          <Link
            to={`/audit/${taskId}`}
            className="inline-flex items-center gap-2 bg-primary-800 hover:bg-primary-700 text-white px-5 py-2.5 rounded-xl font-semibold transition-all text-sm"
          >
            <Shield className="w-4 h-4" /> View Audit Trail
          </Link>
          <button
            onClick={handleDownloadWord}
            disabled={downloading}
            className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white px-5 py-2.5 rounded-xl font-semibold transition-all text-sm"
          >
            <Download className="w-4 h-4" />
            {downloading ? "Downloading..." : "Download Word"}
          </button>
        </div>
      </motion.div>

      {/* AI Disease Info Card */}
      {isAiPowered && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl p-5"
        >
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-5 h-5 text-purple-600" />
            <span className="font-semibold text-purple-800">AI-Powered Drug Discovery Mode</span>
          </div>
          <p className="text-sm text-purple-700">
            Your disease was not found in our local biomedical database.{" "}
            <strong>Our AI used its biomedical knowledge</strong> to suggest drug repurposing candidates based on known disease mechanisms, pathways, and published literature.
          </p>
        </motion.div>
      )}

      {/* Pipeline Summary Funnel */}
      {ps && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12 }}
          className="bg-slate-50 border border-slate-200 rounded-2xl p-5"
        >
          <div className="flex items-center gap-2 mb-3">
            <FlaskConical className="w-4 h-4 text-slate-500" />
            <span className="text-sm font-semibold text-slate-700">Pipeline Funnel</span>
            <span className="ml-auto text-xs text-slate-400">v3 · Disease → Gene → Target → Drug</span>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-center">
            {([
              { label: "Genes", value: ps.stage_genes, color: "text-blue-600" },
              { label: "Targets", value: ps.stage_targets, color: "text-indigo-600" },
              { label: "Candidates", value: ps.stage_candidates_raw, color: "text-violet-600" },
              { label: "Rejected", value: ps.stage_hard_rejected, color: "text-red-500" },
              { label: "Passed", value: ps.stage_passed, color: "text-emerald-600" },
              { label: "Ranked", value: ps.stage_ranked, color: "text-accent-700" },
            ] as const).map((item) => (
              <div key={item.label} className="bg-white rounded-xl p-2 border border-slate-100">
                <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
                <p className="text-xs text-slate-500">{item.label}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Stat badges */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 sm:grid-cols-3 gap-4"
      >
        {[
          { icon: FlaskConical, label: "Candidates", value: data.ranked_drugs?.length ?? 0, color: "bg-purple-100 text-purple-700" },
          { icon: Zap, label: "QUBO Energy", value: (data.qubo_energy ?? 0).toFixed(3), color: "bg-accent-100 text-accent-700" },
          { icon: CheckCircle, label: "Status", value: "Complete", color: "bg-green-100 text-green-700" },
        ].map(({ icon: Icon, label, value, color }) => (
          <div
            key={label}
            className="bg-white rounded-2xl shadow-card border border-slate-100 p-5 flex items-center gap-4"
          >
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">{label}</p>
              <p className="text-xl font-bold text-slate-900">{value}</p>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Score chart */}
      {chartData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl shadow-card border border-slate-100 p-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-accent-600" />
            <h3 className="font-semibold text-slate-900">Candidate Scores</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
              <Tooltip
                formatter={(v) => [`${v}%`, "Relevance Score"]}
                contentStyle={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderRadius: 8 }}
              />
              <Bar dataKey="score" fill={isAiPowered ? "#9333ea" : "#06b6d4"} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* ── Side-by-side: Selected | Rejected ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* ── LEFT: Selected Candidates ── */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-bold text-slate-900">
              Selected Candidates
            </h2>
            <span className="ml-auto text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">
              {Math.min(10, data.ranked_drugs?.length ?? 0)} selected
            </span>
          </div>

          {(data.ranked_drugs ?? []).length === 0 && (
            <div className="text-center py-10 text-slate-400 bg-slate-50 rounded-2xl border border-slate-200">
              No valid candidates found
            </div>
          )}

          {(data.ranked_drugs ?? []).slice(0, 10).map((drug, idx) => (
            <motion.div
              key={drug.rank ?? idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + idx * 0.05 }}
              className="bg-white rounded-2xl border border-emerald-100 shadow-sm p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="inline-flex items-center justify-center w-7 h-7 text-white text-xs font-bold rounded-lg bg-emerald-500">
                  {drug.rank}
                </span>
                <span className="text-sm font-semibold text-slate-600">
                  {((drug.score ?? 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-1.5 bg-slate-100 rounded-full mb-3 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600"
                  style={{ width: `${Math.round((drug.score ?? 0) * 100)}%` }}
                />
              </div>
              <p className="font-semibold text-slate-800 text-sm">
                {drug.drug_name || drug.target_name || drug.molregno || "Unknown"}
              </p>
              {drug.target_name && drug.drug_name && (
                <p className="text-xs text-slate-500 mt-0.5">Target: {drug.target_name}</p>
              )}
              <div className="flex flex-wrap gap-1.5 mt-2">
                {drug.max_phase !== undefined && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    drug.max_phase === 4 ? "bg-green-100 text-green-700" :
                    drug.max_phase >= 2 ? "bg-blue-100 text-blue-700" :
                    "bg-slate-100 text-slate-600"
                  }`}>
                    Phase {drug.max_phase === 4 ? "4 ✓" : drug.max_phase}
                  </span>
                )}
                {drug.confidence_label && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    drug.confidence_label === "HIGH" ? "bg-emerald-500 text-white" :
                    drug.confidence_label === "MEDIUM" ? "bg-orange-400 text-white" :
                    "bg-slate-400 text-white"
                  }`}>
                    {drug.confidence_label}
                  </span>
                )}
                {drug.priority && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    drug.priority === "HIGH" ? "bg-red-500 text-white" :
                    drug.priority === "MEDIUM" ? "bg-amber-500 text-white" :
                    "bg-slate-500 text-white"
                  }`}>
                    Priority {drug.priority}
                  </span>
                )}
                {drug.source === "nvidia_ai" && (
                  <span className="text-xs bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full font-medium">
                    AI
                  </span>
                )}
              </div>
              {drug.reasoning && (
                <p className="text-xs text-slate-500 mt-2 italic line-clamp-2">{drug.reasoning}</p>
              )}
              {drug.canonical_smiles && (
                <p className="text-xs font-mono text-slate-400 truncate mt-1">{drug.canonical_smiles}</p>
              )}
            </motion.div>
          ))}
        </div>

        {/* ── RIGHT: Rejected Candidates ── */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <h2 className="text-base font-bold text-slate-900">
              Rejected Candidates
            </h2>
            <span className="ml-auto text-xs font-semibold bg-red-100 text-red-700 px-2.5 py-1 rounded-full">
              {Math.min(10, data.rejected_drugs?.length ?? 0)} rejected
            </span>
          </div>

          {(data.rejected_drugs ?? []).length === 0 && (
            <div className="text-center py-10 text-slate-400 bg-slate-50 rounded-2xl border border-slate-200">
              No rejections recorded
            </div>
          )}

          {(data.rejected_drugs ?? []).slice(0, 10).map((rd, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.04 }}
              className="bg-red-50 rounded-2xl border border-red-100 p-4"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold text-slate-800 text-sm capitalize">
                  {rd.name}
                </p>
                <span className="shrink-0 text-xs font-mono text-slate-400">{rd.molregno || ""}</span>
              </div>
              <p className="text-xs text-red-600 mt-1">{rd.reason}</p>
              {rd.priority && (
                <span className={`inline-flex mt-2 text-xs px-2 py-0.5 rounded-full font-bold ${
                  rd.priority === "HIGH" ? "bg-red-500 text-white" :
                  rd.priority === "MEDIUM" ? "bg-amber-500 text-white" :
                  "bg-slate-500 text-white"
                }`}>
                  Priority {rd.priority}
                </span>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* AI Medical Summary */}
      {summaryText && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-2xl shadow-card border border-slate-100 p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">AI Medical Analysis</h3>
              <p className="text-xs text-slate-400">Scientific reasoning for researchers</p>
            </div>
          </div>
          <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{summaryText}</p>
          </div>
        </motion.div>
      )}

      {/* Task ID */}
      <p className="text-xs text-slate-400 text-center font-mono">Task ID: {data.task_id}</p>
    </div>
  );
}
