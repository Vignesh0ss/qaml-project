import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getAudit, verifyAudit } from "../services/api";
import {
  Shield,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowLeft,
  Lock,
  Hash,
  Clock,
} from "lucide-react";
import { motion } from "framer-motion";

type AuditEntry = Record<string, unknown>;

export default function Audit() {
  const { taskId } = useParams<{ taskId: string }>();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [verified, setVerified] = useState<{ valid: boolean; message: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!taskId) return;

    Promise.allSettled([
      getAudit(taskId),
      verifyAudit(taskId),
    ]).then(([auditResult, verifyResult]) => {
      if (auditResult.status === "fulfilled") {
        setEntries(auditResult.value.entries || []);
      } else {
        setError("Failed to load audit entries.");
      }
      if (verifyResult.status === "fulfilled") {
        setVerified({ valid: verifyResult.value.valid, message: verifyResult.value.message });
      } else {
        setVerified({ valid: false, message: "Chain verification failed." });
      }
      setLoading(false);
    });
  }, [taskId]);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-xl mx-auto mt-24 text-center space-y-4"
      >
        <Loader2 className="w-10 h-10 text-accent-600 animate-spin mx-auto" />
        <p className="text-slate-500">Loading audit trail…</p>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-xl mx-auto mt-16 bg-red-50 border border-red-200 rounded-2xl p-8 text-center"
      >
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-700 font-semibold">{error}</p>
        <Link
          to={`/results/${taskId}`}
          className="mt-6 inline-flex items-center gap-2 text-accent-600 font-medium hover:underline"
        >
          <ArrowLeft className="w-4 h-4" /> Back to results
        </Link>
      </motion.div>
    );
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
            <Link to={`/results/${taskId}`} className="hover:text-accent-600 transition-colors">
              Back to results
            </Link>
          </p>
          <h1 className="text-3xl font-bold text-primary-900">Audit Trail</h1>
          <p className="text-slate-500 mt-1 font-mono text-xs">Task: {taskId}</p>
        </div>
        {/* Chain validity badge */}
        {verified && (
          <div
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm ${
              verified.valid
                ? "bg-green-100 text-green-700 border border-green-200"
                : "bg-red-100 text-red-700 border border-red-200"
            }`}
          >
            {verified.valid ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <AlertCircle className="w-4 h-4" />
            )}
            {verified.valid ? "Chain Valid" : "Chain Broken"}
          </div>
        )}
      </motion.div>

      {/* Integrity summary card */}
      {verified && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className={`rounded-2xl border p-6 ${
            verified.valid
              ? "bg-green-50 border-green-200"
              : "bg-red-50 border-red-200"
          }`}
        >
          <div className="flex items-start gap-4">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                verified.valid ? "bg-green-200" : "bg-red-200"
              }`}
            >
              {verified.valid ? (
                <Shield className="w-6 h-6 text-green-700" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-700" />
              )}
            </div>
            <div>
              <h3 className={`font-bold ${verified.valid ? "text-green-900" : "text-red-900"}`}>
                {verified.valid ? "Audit Chain Verified" : "Integrity Check Failed"}
              </h3>
              <p className={`text-sm mt-1 ${verified.valid ? "text-green-700" : "text-red-700"}`}>
                {verified.message}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Entries */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="space-y-3"
      >
        <h2 className="text-lg font-bold text-slate-900">
          Log Entries
          <span className="ml-2 text-sm font-normal text-slate-400">({entries.length})</span>
        </h2>

        {entries.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-card border border-slate-100 p-12 text-center">
            <Lock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-400">No audit entries recorded for this task.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.25 + i * 0.05 }}
                className="bg-white rounded-2xl shadow-card border border-slate-100 p-5"
              >
                {/* Entry header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 bg-primary-100 text-primary-700 rounded-lg flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </span>
                    <span className="font-semibold text-slate-800 text-sm">
                      {String(entry.event_type ?? "EVENT")}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-400 text-xs">
                    <Clock className="w-3 h-3" />
                    {String(entry.timestamp ?? "").replace("T", " ").split(".")[0]}
                  </div>
                </div>

                {/* Hash row */}
                <div className="bg-slate-50 rounded-xl p-3 space-y-1.5">
                  {Boolean(entry.entry_hash) && (
                    <div className="flex items-start gap-2">
                      <Hash className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs font-medium text-slate-500">entry_hash </span>
                        <span className="font-mono text-xs text-slate-700 break-all">
                          {String(entry.entry_hash).slice(0, 32)}…
                        </span>
                      </div>
                    </div>
                  )}
                  {Boolean(entry.previous_hash) && (
                    <div className="flex items-start gap-2">
                      <Hash className="w-3.5 h-3.5 text-slate-300 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs font-medium text-slate-400">prev_hash </span>
                        <span className="font-mono text-xs text-slate-400 break-all">
                          {String(entry.previous_hash).slice(0, 32)}…
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Model & user badges */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {Boolean(entry.model_version) && (
                    <span className="px-2 py-0.5 bg-accent-50 text-accent-700 text-xs rounded-full font-medium">
                      model: {String(entry.model_version)}
                    </span>
                  )}
                  {Boolean(entry.user_id) && (
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-full font-medium">
                      user: {String(entry.user_id)}
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Footer */}
      <div className="flex items-center justify-center gap-2 text-slate-400 text-sm">
        <Shield className="w-4 h-4" />
        <span>Tamper-evident Audit Trail — every entry is cryptographically linked</span>
      </div>
    </div>
  );
}
