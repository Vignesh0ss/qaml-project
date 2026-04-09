import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { health, getStats, StatsData } from "../services/api";
import {
  Activity,
  Search,
  Database,
  Shield,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  FlaskConical,
  Microscope,
  RefreshCw,
  PlugZap,
} from "lucide-react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function Dashboard() {
  const navigate = useNavigate();
  const [ok, setOk] = useState<boolean | null>(null);
  const [apiLoading, setApiLoading] = useState(true);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState("");

  const loadStats = () => {
    setStatsLoading(true);
    setStatsError("");
    getStats()
      .then((data) => {
        setStats(data);
        // Cache locally so offline refreshes show last known data
        localStorage.setItem("qaml_last_stats", JSON.stringify(data));
      })
      .catch(() => {
        // Try loading cached stats
        const cached = localStorage.getItem("qaml_last_stats");
        if (cached) {
          try { setStats(JSON.parse(cached)); } catch { /**/ }
        } else {
          setStatsError("Database offline — stats unavailable");
        }
      })
      .finally(() => setStatsLoading(false));
  };

  useEffect(() => {
    health()
      .then(() => setOk(true))
      .catch(() => setOk(false))
      .finally(() => setApiLoading(false));
    loadStats();

    // Auto-refresh stats every 20 seconds
    const interval = setInterval(loadStats, 20000);
    return () => clearInterval(interval);
  }, []);

  const statCards = [
    {
      label: "Total Queries",
      value: statsLoading ? "…" : String(stats?.total_queries ?? 0),
      icon: Search,
      color: "bg-blue-500",
    },
    {
      label: "Completed",
      value: statsLoading ? "…" : String(stats?.completed ?? 0),
      icon: CheckCircle,
      color: "bg-green-500",
    },
    {
      label: "Drugs Analyzed",
      value: statsLoading ? "…" : String(stats?.drugs_analyzed ?? 0),
      icon: FlaskConical,
      color: "bg-purple-500",
    },
    {
      label: "Audit Entries",
      value: statsLoading ? "…" : String(stats?.audit_entries ?? 0),
      icon: Shield,
      color: "bg-orange-500",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-primary-900">Dashboard</h1>
          <p className="text-slate-500 mt-1">
            Quantum-Assisted ML Framework for Drug Repurposing in Rare Diseases
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={loadStats}
            className="inline-flex items-center gap-2 bg-white border border-slate-200 text-slate-600 px-4 py-3 rounded-xl font-semibold hover:bg-slate-50 transition-all text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <Link
            to="/custom-query"
            className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white px-5 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
          >
            <PlugZap className="w-5 h-5" />
            Custom Query
          </Link>
          <Link
            to="/query"
            className="inline-flex items-center gap-2 bg-accent-500 hover:bg-accent-600 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
          >
            <Search className="w-5 h-5" />
            New Query
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/disease-drug-classification"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
          >
            <Microscope className="w-5 h-5" />
            Disease and Drug Classification
          </Link>
        </div>
      </motion.div>

      {/* Status Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl shadow-card p-6 border border-slate-100"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                ok === null
                  ? "bg-slate-100"
                  : ok
                  ? "bg-green-100"
                  : "bg-red-100"
              }`}
            >
              {apiLoading ? (
                <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
              ) : ok ? (
                <Activity className="w-6 h-6 text-green-600" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-600" />
              )}
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">API Status</h3>
              <p className="text-sm text-slate-500">
                {apiLoading
                  ? "Checking connection..."
                  : ok
                  ? "Connected to backend services"
                  : "Unable to connect"}
              </p>
            </div>
          </div>
          <div
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              ok === null
                ? "bg-slate-100 text-slate-600"
                : ok
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-700"
            }`}
          >
            {apiLoading ? "Checking..." : ok ? "● Online" : "● Offline"}
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
            className="bg-white rounded-2xl shadow-card p-6 border border-slate-100 hover:shadow-card-hover transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">{stat.label}</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  {stat.value}
                </p>
              </div>
              <div
                className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center`}
              >
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Completion Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-2xl shadow-card p-6 border border-slate-100"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-slate-900">Query Overview</h3>
            <TrendingUp className="w-5 h-5 text-slate-400" />
          </div>
          {statsLoading ? (
            <div className="flex items-center justify-center h-[200px]">
              <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={[
                  { name: "Total", value: stats?.total_queries ?? 0 },
                  { name: "Done", value: stats?.completed ?? 0 },
                  { name: "Drugs", value: stats?.drugs_analyzed ?? 0 },
                  { name: "Audit", value: stats?.audit_entries ?? 0 },
                ]}
              >
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#028090" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#028090" stopOpacity={0.3} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} axisLine={false} tickLine={false} dy={10} />
                <YAxis stroke="#94a3b8" fontSize={12} axisLine={false} tickLine={false} dx={-10} />
                <Tooltip
                  cursor={{ fill: "#f8fafc" }}
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "none",
                    borderRadius: "12px",
                    boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                    padding: "12px",
                  }}
                  itemStyle={{ color: "#028090", fontWeight: "bold" }}
                />
                <Bar dataKey="value" fill="url(#barGradient)" radius={[6, 6, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        {/* Recent Queries */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="bg-white rounded-2xl shadow-card p-6 border border-slate-100"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-slate-900">Recent Queries</h3>
            <Database className="w-5 h-5 text-slate-400" />
          </div>
          {statsLoading ? (
            <div className="flex items-center justify-center h-[200px]">
              <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
            </div>
          ) : statsError ? (
            <p className="text-sm text-red-500">{statsError}</p>
          ) : !stats?.recent?.length ? (
            <p className="text-sm text-slate-400 text-center py-8">
              No queries yet. Submit your first query!
            </p>
          ) : (
            <div className="space-y-3 max-h-[220px] overflow-y-auto">
              {stats.recent.map((activity, index) => (
                <div
                  key={index}
                  onClick={() =>
                    activity.task_id &&
                    navigate(`/results/${activity.task_id}`)
                  }
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        activity.status === "done"
                          ? "bg-green-500"
                          : "bg-yellow-500 animate-pulse"
                      }`}
                    />
                    <div>
                      <p className="font-medium text-slate-900 group-hover:text-accent-600 transition-colors">
                        {activity.query}
                      </p>
                      <p className="text-xs text-slate-500">{activity.time}</p>
                    </div>
                  </div>
                  <span className="text-sm text-slate-500">
                    {activity.drugs} drugs
                  </span>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      {/* Audit History Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.38 }}
        className="bg-white rounded-2xl shadow-card p-6 border border-slate-100"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Audit History</h3>
          <Shield className="w-5 h-5 text-slate-400" />
        </div>
        {statsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-accent-500" />
          </div>
        ) : !(stats?.history?.length) ? (
          <p className="text-sm text-slate-400">No audit history available yet.</p>
        ) : (
          <div className="space-y-2 max-h-[260px] overflow-y-auto">
            {stats.history.slice(0, 25).map((h, idx) => (
              <div
                key={`${h.task_id}-${idx}`}
                onClick={() => h.task_id && navigate(`/audit/${h.task_id}`)}
                className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-medium text-slate-800 truncate">{h.disease_name}</p>
                    <p className="text-xs text-slate-500 font-mono truncate">{h.task_id}</p>
                    {h.reason ? (
                      <p className="text-xs text-red-500 truncate">Reason: {h.reason}</p>
                    ) : null}
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-semibold ${
                      h.status === "done"
                        ? "bg-green-100 text-green-700"
                        : h.status === "failed"
                        ? "bg-red-100 text-red-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {h.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* CTA */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gradient-to-r from-primary-800 to-primary-700 rounded-2xl p-8 text-white"
      >
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-xl font-bold">Start Your Research</h3>
            <p className="text-white/70 mt-1">
              Submit a disease query to discover potential drug candidates using
              AI + Quantum optimisation, or connect your own databases for custom pipelines.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
            <Link
              to="/custom-query"
              className="inline-flex items-center justify-center gap-2 bg-white/15 border border-white/30 text-white px-6 py-3 rounded-xl font-semibold hover:bg-white/20 transition-colors"
            >
              <PlugZap className="w-5 h-5" />
              Custom Query
            </Link>
            <Link
              to="/query"
              className="inline-flex items-center justify-center gap-2 bg-white text-primary-900 px-6 py-3 rounded-xl font-semibold hover:bg-white/90 transition-colors"
            >
              <Search className="w-5 h-5" />
              Begin Query
            </Link>
          </div>
        </div>
      </motion.div>

      {/* Security Badge */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="flex items-center justify-center gap-2 text-slate-400"
      >
        <Shield className="w-4 h-4" />
        <span className="text-sm">
          Secure Data Audit • All queries are encrypted
        </span>
      </motion.div>
    </div>
  );
}
