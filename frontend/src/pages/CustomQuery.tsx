import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Database,
  Dna,
  Pill,
  Activity,
  Share2,
  PlugZap,
  Cpu,
  TreePine,
  GitBranch,
  Network,
  Atom,
  CheckCircle2,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";

type Workflow = "simulation" | "repurposing";

const ML_MODELS = [
  {
    id: "random_forest",
    name: "Random Forest",
    description: "Ensemble bagging; strong baseline on tabular gene–drug features.",
    icon: TreePine,
  },
  {
    id: "xgboost",
    name: "XGBoost",
    description: "Gradient boosting; often best accuracy on structured omics stacks.",
    icon: GitBranch,
  },
  {
    id: "lightgbm",
    name: "LightGBM",
    description: "Fast training on high-dimensional sparse molecular descriptors.",
    icon: GitBranch,
  },
  {
    id: "gnn",
    name: "Graph Neural Network",
    description: "Learn on drug–target–disease graphs and polypharmacy edges.",
    icon: Network,
  },
  {
    id: "svm",
    name: "Support Vector Machine",
    description: "Kernel methods when sample size is moderate and features are rich.",
    icon: Cpu,
  },
  {
    id: "quantum_ranking",
    name: "Quantum-assisted ranking",
    description: "Use with the built-in QAML QUBO layer after classical pre-scoring.",
    icon: Atom,
  },
] as const;

type ModelId = (typeof ML_MODELS)[number]["id"];

export default function CustomQuery() {
  const [workflow, setWorkflow] = useState<Workflow>("repurposing");
  const [geneDb, setGeneDb] = useState("");
  const [drugDb, setDrugDb] = useState("");
  const [diseaseDb, setDiseaseDb] = useState("");
  const [interactionDb, setInteractionDb] = useState("");
  const [selectedModel, setSelectedModel] = useState<ModelId>("xgboost");
  const [savedNotice, setSavedNotice] = useState(false);

  function handlePreviewConnect(e: React.FormEvent) {
    e.preventDefault();
    setSavedNotice(true);
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-4"
      >
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-accent-600 w-fit"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to dashboard
        </Link>
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-accent-600 flex items-center justify-center shadow-lg">
            <PlugZap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-primary-900">Custom Query</h1>
            <p className="text-slate-600 mt-1 max-w-2xl">
              Connect <strong>your</strong> databases to drive drug simulation and repurposing runs. This page
              collects connection targets and model choices; wire the fields to your backend when you are ready
              to execute.
            </p>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="rounded-2xl border border-amber-200 bg-amber-50/90 p-4 text-sm text-amber-950"
      >
        <p className="font-semibold flex items-center gap-2">
          <Database className="w-4 h-4 shrink-0" />
          Connect your database to run the query
        </p>
        <p className="mt-1 text-amber-900/85">
          Provide JDBC/URI connection strings or host, port, and database name for each source. Nothing is sent to
          a server from this preview—fields are for your integration checklist only.
        </p>
      </motion.div>

      <form onSubmit={handlePreviewConnect} className="space-y-8">
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl border border-slate-100 shadow-card p-6 space-y-4"
        >
          <h2 className="font-semibold text-slate-900 text-lg">Workflow</h2>
          <p className="text-sm text-slate-500">Choose what you want to simulate against your linked data.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setWorkflow("simulation")}
              className={cn(
                "rounded-xl border-2 p-4 text-left transition-all",
                workflow === "simulation"
                  ? "border-accent-500 bg-accent-50/50 ring-2 ring-accent-500/20"
                  : "border-slate-200 hover:border-slate-300 bg-slate-50/50",
              )}
            >
              <p className="font-semibold text-slate-900">Drug simulation</p>
              <p className="text-xs text-slate-600 mt-1">
                Virtual screening, response curves, and interaction checks using your compound and target tables.
              </p>
            </button>
            <button
              type="button"
              onClick={() => setWorkflow("repurposing")}
              className={cn(
                "rounded-xl border-2 p-4 text-left transition-all",
                workflow === "repurposing"
                  ? "border-accent-500 bg-accent-50/50 ring-2 ring-accent-500/20"
                  : "border-slate-200 hover:border-slate-300 bg-slate-50/50",
              )}
            >
              <p className="font-semibold text-slate-900">Drug repurposing</p>
              <p className="text-xs text-slate-600 mt-1">
                Rank approved or investigational drugs for new indications from your disease and gene maps.
              </p>
            </button>
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-white rounded-2xl border border-slate-100 shadow-card p-6 space-y-5"
        >
          <h2 className="font-semibold text-slate-900 text-lg">Your data sources</h2>
          <p className="text-sm text-slate-500">
            Four slots for typical QAML-style stacks. Use full connection URIs or paste DSN details.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="space-y-2 block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500 flex items-center gap-2">
                <Dna className="w-3.5 h-3.5 text-teal-600" />
                Gene database
              </span>
              <input
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-accent-500/30 focus:border-accent-500 outline-none"
                placeholder="postgresql://user:pass@host:5432/genes"
                value={geneDb}
                onChange={(e) => setGeneDb(e.target.value)}
                autoComplete="off"
              />
            </label>
            <label className="space-y-2 block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500 flex items-center gap-2">
                <Pill className="w-3.5 h-3.5 text-purple-600" />
                Drug / compound database
              </span>
              <input
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-accent-500/30 focus:border-accent-500 outline-none"
                placeholder="mongodb://host:27017/chemvault"
                value={drugDb}
                onChange={(e) => setDrugDb(e.target.value)}
                autoComplete="off"
              />
            </label>
            <label className="space-y-2 block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500 flex items-center gap-2">
                <Activity className="w-3.5 h-3.5 text-rose-600" />
                Disease / phenotype database
              </span>
              <input
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-accent-500/30 focus:border-accent-500 outline-none"
                placeholder="mysql://host:3306/ontology"
                value={diseaseDb}
                onChange={(e) => setDiseaseDb(e.target.value)}
                autoComplete="off"
              />
            </label>
            <label className="space-y-2 block">
              <span className="text-xs font-bold uppercase tracking-wide text-slate-500 flex items-center gap-2">
                <Share2 className="w-3.5 h-3.5 text-indigo-600" />
                Interaction / pathway database
              </span>
              <input
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-accent-500/30 focus:border-accent-500 outline-none"
                placeholder="neo4j://host:7687/pathways"
                value={interactionDb}
                onChange={(e) => setInteractionDb(e.target.value)}
                autoComplete="off"
              />
            </label>
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl border border-slate-100 shadow-card p-6 space-y-4"
        >
          <h2 className="font-semibold text-slate-900 text-lg">Model</h2>
          <p className="text-sm text-slate-500">Pick the classical or graph learner for your custom pipeline.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {ML_MODELS.map((m) => {
              const Icon = m.icon;
              const active = selectedModel === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedModel(m.id)}
                  className={cn(
                    "rounded-xl border-2 p-4 text-left transition-all flex gap-3",
                    active
                      ? "border-accent-500 bg-accent-50/60 ring-2 ring-accent-500/15"
                      : "border-slate-200 hover:border-slate-300",
                  )}
                >
                  <div
                    className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center shrink-0",
                      active ? "bg-accent-500 text-white" : "bg-slate-100 text-slate-600",
                    )}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900 text-sm">{m.name}</p>
                    <p className="text-xs text-slate-600 mt-0.5 leading-snug">{m.description}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </motion.section>

        <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
          <p className="text-xs text-slate-500">
            Next step: expose an API that accepts these fields and starts your job runner.
          </p>
          <button
            type="submit"
            className="inline-flex justify-center items-center gap-2 bg-accent-600 hover:bg-accent-700 text-white px-6 py-3 rounded-xl font-semibold shadow-lg transition-colors"
          >
            <PlugZap className="w-5 h-5" />
            Save configuration
          </button>
        </div>
      </form>

      {savedNotice ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-950"
        >
          <p className="font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            Preview configuration captured
          </p>
          <ul className="mt-3 space-y-1 text-emerald-900/90 font-mono text-xs">
            <li>workflow: {workflow}</li>
            <li>model: {selectedModel}</li>
            <li>gene_db: {geneDb || "(empty)"}</li>
            <li>drug_db: {drugDb || "(empty)"}</li>
            <li>disease_db: {diseaseDb || "(empty)"}</li>
            <li>interaction_db: {interactionDb || "(empty)"}</li>
          </ul>
        </motion.div>
      ) : null}
    </div>
  );
}
