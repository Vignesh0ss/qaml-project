import { useState } from "react";
import { motion } from "framer-motion";
import {
  Brain,
  Shield,
  Database,
  Sliders,
  CheckCircle,
  Info,
} from "lucide-react";

const MODEL_INFO = [
  { label: "AI Model", value: "Custom Trained Pharmaceutical AI" },
  { label: "Pipeline", value: "pipeline_v1" },
  { label: "QUBO Optimizer", value: "Simulated Annealing (500 reads)" },
  { label: "Data Sources", value: "ChEMBL 36 + ClinVar Gold Set + GNN Predictions" },
  { label: "Fingerprint Algorithm", value: "Morgan 2048-bit (RDKit)" },
  { label: "Audit Algorithm", value: "SHA-256 hash chain (tamper-evident)" },
];

export default function Settings() {
  const [topK, setTopK] = useState<number>(5);
  const [diseaseSensitivity, setDiseaseSensitivity] = useState<string>("auto");
  const [saved, setSaved] = useState(false);

  const save = () => {
    // Persist preferences to localStorage for the Query page to pick up
    localStorage.setItem(
      "qaml_prefs",
      JSON.stringify({ topK, diseaseSensitivity })
    );
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-primary-900">Settings</h1>
        <p className="text-slate-500 mt-1">
          Configure pipeline defaults and view system information.
        </p>
      </motion.div>

      {/* Pipeline Defaults */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl shadow-card border border-slate-100 p-6 space-y-6"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-accent-100 rounded-xl flex items-center justify-center">
            <Sliders className="w-5 h-5 text-accent-600" />
          </div>
          <h2 className="font-semibold text-slate-900 text-lg">Pipeline Defaults</h2>
        </div>

        {/* Top-K */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Default Top-K Candidates
          </label>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="flex-1 accent-accent-500"
            />
            <span className="w-8 text-center font-bold text-slate-800">{topK}</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            How many drug candidates the QUBO optimizer selects per query.
          </p>
        </div>

        {/* Disease Sensitivity */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Disease Recognition Mode
          </label>
          <select
            value={diseaseSensitivity}
            onChange={(e) => setDiseaseSensitivity(e.target.value)}
            className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-accent-500"
          >
            <option value="auto">Auto (AI + Database)</option>
            <option value="db_only">Database Only</option>
            <option value="ai_only">AI Suggestions Only</option>
          </select>
          <p className="text-xs text-slate-400 mt-1">
            "Auto" lets the AI canonicalise your input and fall back to AI
            suggestions if the database has no results.
          </p>
        </div>

        <button
          onClick={save}
          className="inline-flex items-center gap-2 bg-accent-500 hover:bg-accent-600 text-white px-6 py-2.5 rounded-xl font-semibold transition-all text-sm"
        >
          {saved ? <CheckCircle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4 opacity-0" />}
          {saved ? "Saved!" : "Save Preferences"}
        </button>
      </motion.div>

      {/* System Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl shadow-card border border-slate-100 p-6"
      >
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <Brain className="w-5 h-5 text-purple-600" />
          </div>
          <h2 className="font-semibold text-slate-900 text-lg">System Information</h2>
        </div>
        <div className="divide-y divide-slate-100">
          {MODEL_INFO.map((item) => (
            <div key={item.label} className="py-3 flex justify-between gap-4">
              <span className="text-sm text-slate-500 font-medium">{item.label}</span>
              <span className="text-sm text-slate-800 text-right">{item.value}</span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Security */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6"
      >
        <div className="flex items-center gap-3 mb-3">
          <Shield className="w-5 h-5 text-green-600" />
          <h2 className="font-semibold text-green-800 text-lg">Security & Audit</h2>
        </div>
        <ul className="space-y-2 text-sm text-green-700">
          <li className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
            SHA-256 hash chain: every audit entry is cryptographically linked to the previous one.
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
            All pipeline inputs and outputs are hashed and stored as immutable audit records.
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
            You can verify any result's integrity from its Audit Trail page.
          </li>
        </ul>
      </motion.div>

      {/* Data Sources */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="bg-white rounded-2xl shadow-card border border-slate-100 p-6"
      >
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <Database className="w-5 h-5 text-blue-600" />
          </div>
          <h2 className="font-semibold text-slate-900 text-lg">Data Sources</h2>
        </div>
        <div className="space-y-3 text-sm">
          {[
            { name: "ChEMBL 36 SQLite", desc: "Drug-target binding data and molecular profiles" },
            { name: "ClinVar Gold Set", desc: "Rare disease gene associations (clinvar_gold_set.tsv)" },
            { name: "GNN Predictions", desc: "GNN-generated pIC50 scores for top drug candidates" },
            { name: "Custom Pharmaceutical AI", desc: "Biomedical knowledge base for diseases with no local data" },
          ].map((src) => (
            <div key={src.name} className="flex gap-3 p-3 bg-slate-50 rounded-xl">
              <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
              <div>
                <p className="font-medium text-slate-800">{src.name}</p>
                <p className="text-slate-500">{src.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
