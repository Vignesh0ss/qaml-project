import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitQuery } from "../services/api";
import type { AxiosError } from "axios";
import {
  Search, 
  Loader2, 
  ArrowRight, 
  AlertCircle,
  Sparkles,
  FlaskConical
} from "lucide-react";
import { motion } from "framer-motion";

const diseaseSuggestions = [
  "Progeria",
  "Huntington's Disease",
  "ALS (Amyotrophic Lateral Sclerosis)",
  "Duchenne Muscular Dystrophy",
  "Cystic Fibrosis",
  "Sickle Cell Anemia",
  "Rare Disease: Fibrodysplasia Ossificans Progressiva",
  "Menkes Disease",
  "Pompe Disease",
  "Friedreich's Ataxia"
];

export default function Query() {
  const [disease, setDisease] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const navigate = useNavigate();
  type ApiError = { error?: string; msg?: string };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!disease.trim()) {
      setError("Disease name is required");
      return;
    }
    setLoading(true);
    try {
      const res = await submitQuery({ disease_name: disease.trim(), top_k: 10 });
      navigate(`/results/${res.task_id}`, { state: { offlineResults: res.results } });
    } catch (err: unknown) {
      const apiErr = err as AxiosError<ApiError>;
      const backendError = apiErr.response?.data?.error || apiErr.response?.data?.msg;
      setError(backendError || apiErr.message || "Submit failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="inline-flex items-center justify-center w-16 h-16 bg-accent-100 rounded-2xl mb-4">
          <Search className="w-8 h-8 text-accent-600" />
        </div>
        <h1 className="text-3xl font-bold text-primary-900">New Query</h1>
        <p className="text-slate-500 mt-2">
          Submit a rare disease to discover potential drug candidates using quantum-optimized ML
        </p>
      </motion.div>

      {/* Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl shadow-card p-8 border border-slate-100"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Disease Input */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-slate-700">
              <Sparkles className="w-4 h-4 inline-block mr-1 text-accent-500" />
              Disease Name
            </label>
            <div className="relative">
              <input
                type="text"
                value={disease}
                onChange={(e) => {
                  setDisease(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder="e.g. Progeria, Huntington's Disease"
                className="w-full px-4 py-3 text-lg border-2 border-slate-200 rounded-xl focus:border-accent-500 focus:outline-none transition-colors"
              />
              {showSuggestions && disease && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden">
                  {diseaseSuggestions
                    .filter(d => d.toLowerCase().includes(disease.toLowerCase()))
                    .slice(0, 5)
                    .map((suggestion) => (
                      <button
                        key={suggestion}
                        type="button"
                        onMouseDown={(e) => {
                          e.preventDefault(); // Prevent input from losing focus immediately
                          setDisease(suggestion);
                          setShowSuggestions(false);
                        }}
                        className="w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                </div>
              )}
            </div>
          </div>

          <div className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
            This query runs with a fixed output of top 10 selected and top 10 rejected candidates.
          </div>

          {/* Error Message */}
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              {error}
            </motion.div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-accent-500 hover:bg-accent-600 disabled:bg-slate-300 text-white px-6 py-4 rounded-xl font-semibold text-lg transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 disabled:translate-y-0 disabled:shadow-none"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing Query...
              </>
            ) : (
              <>
                <FlaskConical className="w-5 h-5" />
                Run Analysis
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </form>
      </motion.div>

    </div>
  );
}
