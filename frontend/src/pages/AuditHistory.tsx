import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getAuditHistory } from "../services/api";
import { AlertCircle, ArrowLeft, CheckCircle, Clock, Filter, Loader2, Search, Shield } from "lucide-react";
import { motion } from "framer-motion";

type HistoryItem = {
  task_id: string;
  disease_name: string;
  status: string;
  reason?: string;
  created_at?: string;
  completed_at?: string;
};

type StatusFilter = "all" | "done" | "failed";

export default function AuditHistory() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [query, setQuery] = useState("");

  useEffect(() => {
    getAuditHistory()
      .then((res) => setItems(res.items || []))
      .catch(() => setError("Failed to load audit history."))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((i) => {
      if (statusFilter !== "all" && i.status !== statusFilter) return false;
      if (!q) return true;
      return i.disease_name.toLowerCase().includes(q) || i.task_id.toLowerCase().includes(q);
    });
  }, [items, statusFilter, query]);

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <p className="text-sm text-slate-500 mb-1 flex items-center gap-1">
            <ArrowLeft className="w-3 h-3" />
            <Link to="/" className="hover:text-accent-600 transition-colors">
              Back to dashboard
            </Link>
          </p>
          <h1 className="text-3xl font-bold text-primary-900">Audit History</h1>
          <p className="text-slate-500 mt-1">Completed/failed query history with reasons and task IDs.</p>
        </div>
      </motion.div>

      <div className="bg-white rounded-2xl shadow-card border border-slate-100 p-4 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search disease or task ID..."
            className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:border-accent-500 focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          {(["all", "done", "failed"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-2 rounded-lg text-sm font-semibold ${
                statusFilter === s ? "bg-accent-500 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {s === "all" ? "All" : s === "done" ? "Completed" : "Failed"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-accent-500 mx-auto" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-card border border-slate-100 p-10 text-center text-slate-400">
          No matching history entries.
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((h, idx) => (
            <motion.div
              key={`${h.task_id}-${idx}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(0.02 * idx, 0.2) }}
              className="bg-white rounded-2xl shadow-card border border-slate-100 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-semibold text-slate-800 truncate">{h.disease_name}</p>
                  <p className="text-xs text-slate-500 font-mono truncate">{h.task_id}</p>
                  {h.reason ? <p className="text-xs text-red-500 mt-1">Reason: {h.reason}</p> : null}
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-bold inline-flex items-center gap-1 ${
                      h.status === "done"
                        ? "bg-green-100 text-green-700"
                        : h.status === "failed"
                        ? "bg-red-100 text-red-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {h.status === "done" ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                    {h.status}
                  </span>
                  <Link to={`/audit/${h.task_id}`} className="text-xs text-accent-600 hover:underline">
                    Open audit log
                  </Link>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      <div className="flex items-center justify-center gap-2 text-slate-400 text-sm">
        <Shield className="w-4 h-4" />
        <Clock className="w-4 h-4" />
        <span>Task status history with reason tracking</span>
      </div>
    </div>
  );
}

