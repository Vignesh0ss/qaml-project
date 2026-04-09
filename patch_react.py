import re

FILE = 'frontend/src/pages/Results.tsx'

with open(FILE, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update Types
type_patch = '''type ResultsData = {
  task_id: string;
  disease_name: string;
  disease_info?: DiseaseInfo;
  top_k?: number;
  qubo_energy?: number;
  ranked_drugs?: RankedDrug[];
  gemini_summary?: string;
  gemini_powered?: boolean;
  model_version?: string;
  message?: string;
  reason?: string;
  rejected_drugs?: { name: string; reason: string; molregno?: string }[];
};'''

code = re.sub(r'type ResultsData = \{.*?model_version\?: string;\n\};', type_patch, code, flags=re.DOTALL)

# 2. Add Rejected UI Block
rejected_ui = '''      {/* Rejected Candidates Section */}
      {(data.rejected_drugs && data.rejected_drugs.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-8 border border-red-100 rounded-2xl overflow-hidden bg-white shadow-sm"
        >
          <div className="bg-red-50 px-6 py-4 flex items-center justify-between border-b border-red-100">
            <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <h3 className="font-bold text-red-900">Rejected Candidates</h3>
            </div>
            <span className="text-sm font-semibold text-red-700 bg-red-100 px-3 py-1 rounded-full">{data.rejected_drugs.length} Excluded</span>
          </div>
          <div className="p-0 max-h-96 overflow-y-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 sticky top-0 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold text-slate-700">Drug / Target Name</th>
                  <th className="px-6 py-3 font-semibold text-slate-700">Database ID</th>
                  <th className="px-6 py-3 font-semibold text-slate-700">Rejection Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.rejected_drugs.map((rd, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3 font-medium text-slate-900 capitalize">{rd.name}</td>
                    <td className="px-6 py-3 font-mono text-xs">{rd.molregno || '-'}</td>
                    <td className="px-6 py-3 text-red-600">{rd.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Task ID */}'''

code = code.replace('{/* Task ID */}', rejected_ui)

# 3. Add Early Abort / 0 Valid State
empty_state = '''  /* -- Results -- */
  if (data.message && (!data.ranked_drugs || data.ranked_drugs.length === 0)) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div className="max-w-xl mx-auto mt-16 bg-amber-50 border border-amber-200 rounded-2xl p-8 text-center">
            <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-amber-800 mb-2">{data.message}</h2>
            <p className="text-amber-700 mb-6">{data.reason}</p>
            <Link
            to="/query"
            className="inline-flex items-center gap-2 bg-amber-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-amber-700 transition-colors"
            >
            <ArrowLeft className="w-4 h-4" /> Try a Different Query
            </Link>
        </div>
        
        {/* Rejected Candidates Section */}
        {(data.rejected_drugs && data.rejected_drugs.length > 0) && (
            <div className="max-w-4xl mx-auto border border-red-100 rounded-2xl overflow-hidden bg-white shadow-sm">
            <div className="bg-red-50 px-6 py-4 flex items-center justify-between border-b border-red-100">
                <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-600" />
                    <h3 className="font-bold text-red-900">Rejected Candidates</h3>
                </div>
                <span className="text-sm font-semibold text-red-700 bg-red-100 px-3 py-1 rounded-full">{data.rejected_drugs.length} Excluded</span>
            </div>
            <div className="p-0 max-h-96 overflow-y-auto">
                <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 sticky top-0 border-b border-slate-200">
                    <tr>
                    <th className="px-6 py-3 font-semibold text-slate-700">Drug / Target Name</th>
                    <th className="px-6 py-3 font-semibold text-slate-700">Rejection Reason</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {data.rejected_drugs.map((rd, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-3 font-medium text-slate-900 capitalize">{rd.name}</td>
                        <td className="px-6 py-3 text-red-600">{rd.reason}</td>
                    </tr>
                    ))}
                </tbody>
                </table>
            </div>
            </div>
        )}
      </motion.div>
    );
  }

  const chartData'''

code = code.replace('  /* -- Results -- */\n  const chartData', empty_state)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(code)

print('React patched successfully.')
