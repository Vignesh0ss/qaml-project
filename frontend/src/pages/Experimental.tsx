import { useState } from "react";
import { AlertTriangle, Brain, Download, FlaskConical, Loader2, Microscope, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { downloadExperimentalWordReport, experimentalSuggest, ExperimentalSuggestResponse } from "../services/api";

function parseGenes(input: string): string[] {
  return input
    .split(",")
    .map((x) => x.trim().toUpperCase())
    .filter(Boolean);
}

function parseSymptoms(input: string): string[] {
  return input
    .split(",")
    .map((x) => x.trim().toLowerCase())
    .filter(Boolean);
}

export default function Experimental() {
  const [age, setAge] = useState<number | "">("");
  const [gender, setGender] = useState("unknown");
  const [bloodGroup, setBloodGroup] = useState("");
  const [durationDays, setDurationDays] = useState<number | "">("");
  const [symptomsText, setSymptomsText] = useState("");
  const [genesText, setGenesText] = useState("");
  const [hemoglobin, setHemoglobin] = useState<number | "">("");
  const [redBloodCells, setRedBloodCells] = useState("");
  const [wbc, setWbc] = useState<number | "">("");
  const [platelets, setPlatelets] = useState<number | "">("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ExperimentalSuggestResponse | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const symptoms = parseSymptoms(symptomsText);
    if (symptoms.length === 0) {
      setError("At least one symptom is required.");
      return;
    }
    setLoading(true);
    try {
      const res = await experimentalSuggest(
        {
          age: age === "" ? undefined : Number(age),
          gender,
          blood_group: bloodGroup || undefined,
          duration_days: durationDays === "" ? undefined : Number(durationDays),
          symptoms,
          gene_patterns: parseGenes(genesText),
          lab_results: {
            blood_test: {
              ...(hemoglobin === "" ? {} : { hemoglobin: Number(hemoglobin) }),
              ...(redBloodCells.trim() === "" ? {} : { red_blood_cells: redBloodCells.trim() }),
              ...(wbc === "" ? {} : { wbc: Number(wbc) }),
              ...(platelets === "" ? {} : { platelets: Number(platelets) }),
            },
          },
          notes: notes || undefined,
        }
      );
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run experimental suggestion.");
    } finally {
      setLoading(false);
    }
  }

  async function onDownload() {
    if (!result?.run_id) return;
    setDownloading(true);
    try {
      const blob = await downloadExperimentalWordReport(result.run_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `qaml-experimental-report-${result.run_id}.doc`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download report.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl bg-white border border-slate-100 p-6 shadow-card">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Disease and Drug Classification</h1>
            <p className="text-sm text-slate-600 mt-1">
              Rule-based disease scoring from symptoms, genes, and labs; ChEMBL-backed drug names; deterministic report text (no LLM).
            </p>
            <p className="text-xs text-amber-700 mt-2 font-semibold">Not medical advice. For research exploration only.</p>
          </div>
        </div>
      </motion.div>

      <form onSubmit={onSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2"><Microscope className="w-4 h-4" /> Research Input</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input className="border border-slate-200 rounded-xl px-3 py-2 text-sm" placeholder="Age" type="number" value={age} onChange={(e) => setAge(e.target.value === "" ? "" : Number(e.target.value))} />
            <select className="border border-slate-200 rounded-xl px-3 py-2 text-sm" value={gender} onChange={(e) => setGender(e.target.value)}>
              <option value="unknown">Gender (Unknown)</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
            <input className="border border-slate-200 rounded-xl px-3 py-2 text-sm" placeholder="Blood group (e.g., O+)" value={bloodGroup} onChange={(e) => setBloodGroup(e.target.value)} />
            <input className="border border-slate-200 rounded-xl px-3 py-2 text-sm" placeholder="Duration (days)" type="number" value={durationDays} onChange={(e) => setDurationDays(e.target.value === "" ? "" : Number(e.target.value))} />
          </div>
          <textarea className="border border-slate-200 rounded-xl px-3 py-2 text-sm w-full min-h-[90px]" placeholder="Symptoms (comma separated): fever, fatigue, joint pain" value={symptomsText} onChange={(e) => setSymptomsText(e.target.value)} />
          <input className="border border-slate-200 rounded-xl px-3 py-2 text-sm w-full" placeholder="Common gene patterns (comma separated): HBB, LMNA" value={genesText} onChange={(e) => setGenesText(e.target.value)} />
          <div>
            <p className="text-xs text-slate-500 mb-2">Blood test values</p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              <input className="border border-slate-200 rounded-xl px-3 py-2 text-sm" placeholder="Hemoglobin" type="number" step="any" value={hemoglobin} onChange={(e) => setHemoglobin(e.target.value === "" ? "" : Number(e.target.value))} />
              <input
                className="border border-slate-200 rounded-xl px-3 py-2 text-sm"
                placeholder="Red blood cells (e.g. 4.5, 4.5 million/µL)"
                type="text"
                value={redBloodCells}
                onChange={(e) => setRedBloodCells(e.target.value)}
              />
              <input className="border border-slate-200 rounded-xl px-3 py-2 text-sm" placeholder="WBC" type="number" step="any" value={wbc} onChange={(e) => setWbc(e.target.value === "" ? "" : Number(e.target.value))} />
              <input className="border border-slate-200 rounded-xl px-3 py-2 text-sm" placeholder="Platelets" type="number" step="any" value={platelets} onChange={(e) => setPlatelets(e.target.value === "" ? "" : Number(e.target.value))} />
            </div>
          </div>
          <textarea className="border border-slate-200 rounded-xl px-3 py-2 text-sm w-full min-h-[70px]" placeholder="Optional notes / family history" value={notes} onChange={(e) => setNotes(e.target.value)} />
          <div className="flex gap-3">
            <button type="submit" disabled={loading} className="inline-flex items-center gap-2 bg-accent-600 text-white px-5 py-2.5 rounded-xl font-semibold disabled:bg-slate-300">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
              Run Classification
            </button>
            {result?.run_id && (
              <button type="button" onClick={onDownload} disabled={downloading} className="inline-flex items-center gap-2 bg-emerald-600 text-white px-5 py-2.5 rounded-xl font-semibold disabled:bg-slate-300">
                <Download className="w-4 h-4" />
                {downloading ? "Downloading..." : "Download Report"}
              </button>
            )}
          </div>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
        </div>

        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2"><Brain className="w-4 h-4" /> Disease Probabilities</h2>
          {!result?.predicted_diseases?.length ? (
            <p className="text-sm text-slate-500">Run inference to see top disease matches.</p>
          ) : (
            <div className="space-y-2">
              {result.predicted_diseases.map((d) => (
                <div key={d.disease} className="rounded-xl bg-slate-50 border border-slate-100 p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-800">{d.disease}</span>
                    <span className="font-semibold text-slate-700">{(d.prob * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </form>

      {result && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-5">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2"><Sparkles className="w-4 h-4" /> Drug Recommendations</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {result.recommended_drugs.map((d, idx) => (
              <div key={`${d.drug_name}-${idx}`} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center justify-between">
                  <p className="font-semibold text-slate-800">{d.drug_name}</p>
                  <span className="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700 font-bold">{d.confidence}</span>
                </div>
                <p className="text-sm text-slate-600 mt-1">Score: {d.final_score}</p>
                <p className="text-xs text-slate-500 mt-1">Sources: {d.source_diseases.join(", ")}</p>
              </div>
            ))}
          </div>
          <div className="rounded-xl border border-purple-100 bg-purple-50 p-4">
            <p className="text-sm font-semibold text-purple-900 mb-1">Summary</p>
            <p className="text-sm text-purple-800 leading-relaxed">{result.summary}</p>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
            {result.warnings.map((w, i) => (
              <p key={i} className="text-xs text-amber-800 font-medium">{w}</p>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

