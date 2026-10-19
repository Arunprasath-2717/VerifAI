import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Trophy, 
  Search, 
  Bot, 
  ChevronRight, 
  Info, 
  X,
  ArrowLeft,
  Sparkles,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Award
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { ModelLeaderboardEntry } from '../types';
import { modelsApi } from '../api';

interface ModelLeaderboardPageProps {
  leaderboardData: ModelLeaderboardEntry[];
  theme?: 'light' | 'dark';
}

export const ModelLeaderboardPage: React.FC<ModelLeaderboardPageProps> = ({
  leaderboardData,
  theme = 'light',
}) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [inspectedModel, setInspectedModel] = useState<ModelLeaderboardEntry | null>(null);
  const [liveData, setLiveData] = useState<ModelLeaderboardEntry[]>([]);

  React.useEffect(() => {
    modelsApi.getModelLeaderboard()
      .then(res => setLiveData(res))
      .catch(() => {});
  }, []);

  const isDark = theme === 'dark';
  const effectiveData = liveData.length > 0 ? liveData : leaderboardData;

  const filteredData = effectiveData.filter(entry => {
    const matchesSearch = entry.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.provider.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesProvider = selectedProvider === 'all' || entry.provider.toLowerCase().includes(selectedProvider.toLowerCase());
    return matchesSearch && matchesProvider;
  });

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 pb-16 max-w-6xl mx-auto"
    >
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link 
              to="/reports" 
              className={`text-xs font-semibold flex items-center gap-1 transition-colors ${
                isDark ? 'text-slate-400 hover:text-white' : 'text-[#8A6A72] hover:text-[#2E0A12]'
              }`}
            >
              <ArrowLeft size={13} />
              <span>Back to Reports</span>
            </Link>
          </div>
          <h1 className={`text-2xl md:text-3xl font-extrabold tracking-tight transition-colors ${
            isDark ? 'text-white' : 'text-[#2E0A12]'
          }`}>
            Model Performance Leaderboard
          </h1>
          <p className={`text-xs md:text-sm font-medium transition-colors ${
            isDark ? 'text-slate-300' : 'text-[#6C3B45]'
          }`}>
            Empirical accuracy rankings, hallucination resistance, and citation precision across frontier LLMs.
          </p>
        </div>

        {/* Navigation Switcher */}
        <div className={`flex p-1 rounded-2xl border shadow-2xs self-start sm:self-auto ${
          isDark 
            ? 'bg-[#23262F] border-[#333742]' 
            : 'bg-[#FFFDFA] border-[#E9D6C4]'
        }`}>
          <button
            onClick={() => navigate('/reports')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
              isDark ? 'text-slate-400 hover:text-white' : 'text-[#8A6A72] hover:text-[#2E0A12]'
            }`}
          >
            Verification Analytics
          </button>
          <button
            className={`px-4 py-2 rounded-xl text-xs font-bold shadow-xs cursor-pointer ${
              isDark 
                ? 'bg-[#B6FF2E] text-[#181A20]' 
                : 'bg-[#800020] text-[#FBF1E3]'
            }`}
          >
            Model Leaderboard
          </button>
        </div>
      </div>

      {/* Disclaimers & Methodology Notice */}
      <div className={`p-5 rounded-2xl border flex items-start gap-3.5 text-xs transition-colors ${
        isDark 
          ? 'bg-[#181A20] border-[#333742] text-slate-200' 
          : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#2E0A12]'
      }`}>
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
          isDark ? 'bg-[#23262F] text-[#B6FF2E]' : 'bg-[#EFE0D1] text-[#800020]'
        }`}>
          <Info size={18} />
        </div>
        <div className="space-y-1">
          <p className={`font-bold ${isDark ? 'text-white' : 'text-[#2E0A12]'}`}>
            Multi-Round Ground-Truth Calibration Methodology
          </p>
          <p className={`leading-relaxed text-[11px] ${isDark ? 'text-slate-300' : 'text-[#6C3B45]'}`}>
            Rankings reflect top observed performance across atomic fact deconstruction, cross-examination against verified document repositories, and citation specificity. Scores are calibrated regularly across diverse scientific, economic, and technical propositions.
          </p>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className={`rounded-[2rem] p-4 border shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4 transition-colors ${
        isDark 
          ? 'bg-[#23262F] border-[#333742]' 
          : 'bg-[#FFFDFA] border-[#E9D6C4]'
      }`}>
        <div className="relative flex-1 w-full max-w-md">
          <Search className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${
            isDark ? 'text-slate-400' : 'text-[#8A6A72]'
          }`} size={16} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search models (Sonnet, GPT-4o, Gemini, Llama)..."
            className={`w-full rounded-xl py-2 pl-9 pr-4 text-xs md:text-sm outline-none border transition-all ${
              isDark 
                ? 'bg-[#181A20] border-[#333742] text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-[#B6FF2E]/30 focus:border-[#B6FF2E]' 
                : 'bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12] placeholder-[#8A6A72] focus:ring-2 focus:ring-[#800020]/20 focus:border-[#800020]'
            }`}
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className={`text-xs font-semibold rounded-xl px-3 py-2 outline-none border transition-colors cursor-pointer ${
              isDark 
                ? 'bg-[#181A20] border-[#333742] text-slate-200' 
                : 'bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12]'
            }`}
          >
            <option value="all">All Providers</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama (Local)</option>
            <option value="openrouter">OpenRouter</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className={`text-xs font-semibold rounded-xl px-3 py-2 outline-none border transition-colors cursor-pointer ${
              isDark 
                ? 'bg-[#181A20] border-[#333742] text-slate-200' 
                : 'bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12]'
            }`}
          >
            <option value="all">All Categories</option>
            <option value="evidenceSupport">Evidence Support</option>
            <option value="factualSupport">Factual Support</option>
            <option value="unknownHandling">Unknown Handling</option>
            <option value="contradictionDetection">Contradiction Detection</option>
          </select>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className={`rounded-[2.5rem] border shadow-xs overflow-hidden transition-colors ${
        isDark 
          ? 'bg-[#23262F] border-[#333742]' 
          : 'bg-[#FFFDFA] border-[#E9D6C4]'
      }`}>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className={`border-b uppercase text-xs font-bold tracking-wider ${
                isDark 
                  ? 'border-[#333742] bg-[#181A20]/80 text-slate-400' 
                  : 'border-[#E9D6C4] bg-[#FBF1E3] text-[#8A6A72]'
              }`}>
                <th className="py-4 px-6">Rank</th>
                <th className="py-4 px-4">Model</th>
                <th className="py-4 px-4">Provider</th>
                <th className="py-4 px-4 text-center">Overall Score</th>
                <th className="py-4 px-4">Top Strengths</th>
                <th className="py-4 px-4">Evaluations</th>
                <th className="py-4 px-4">Last Audited</th>
                <th className="py-4 px-6 text-right">Details</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-[#333742]' : 'divide-[#E9D6C4]'}`}>
              {filteredData.map((item) => (
                <tr
                  key={item.model}
                  onClick={() => setInspectedModel(item)}
                  className={`transition-colors cursor-pointer group ${
                    isDark ? 'hover:bg-[#181A20]' : 'hover:bg-[#FBF1E3]'
                  }`}
                >
                  <td className="py-4 px-6 font-mono font-bold">
                    <span className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-sm ${
                      item.rank === 1 
                        ? isDark ? 'bg-[#B6FF2E]/20 text-[#B6FF2E]' : 'bg-[#800020] text-[#FBF1E3]'
                        : item.rank === 2 
                        ? isDark ? 'bg-amber-400/20 text-amber-300' : 'bg-[#D8AE9B] text-[#2E0A12]'
                        : item.rank === 3 
                        ? isDark ? 'bg-slate-700 text-slate-300' : 'bg-[#E5E0D7] text-[#6C3B45]'
                        : isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                    }`}>
                      #{item.rank}
                    </span>
                  </td>

                  <td className={`py-4 px-4 text-sm font-bold transition-colors ${
                    isDark 
                      ? 'text-white group-hover:text-[#B6FF2E]' 
                      : 'text-[#2E0A12] group-hover:text-[#800020]'
                  }`}>
                    <div className="flex items-center gap-2">
                      <Bot size={17} className={`shrink-0 ${
                        isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                      }`} />
                      <span>{item.model}</span>
                    </div>
                  </td>

                  <td className={`py-4 px-4 text-xs font-semibold ${
                    isDark ? 'text-slate-300' : 'text-[#6C3B45]'
                  }`}>
                    {item.provider}
                  </td>

                  <td className="py-4 px-4 text-center">
                    <span className={`font-mono font-extrabold text-sm px-2.5 py-1 rounded-lg ${
                      isDark 
                        ? 'bg-[#181A20] text-[#B6FF2E]' 
                        : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
                    }`}>
                      {item.overallScore}%
                    </span>
                  </td>

                  <td className="py-4 px-4">
                    <div className="flex flex-wrap gap-1.5 text-xs">
                      <span className={`px-2 py-0.5 rounded-md font-semibold ${
                        isDark 
                          ? 'bg-[#181A20] text-blue-300 border border-blue-500/30' 
                          : 'bg-[#FBF1E3] text-[#6C3B45] border border-[#E9D6C4]'
                      }`}>
                        Evidence: {item.categories.evidenceSupport}%
                      </span>
                      <span className={`px-2 py-0.5 rounded-md font-semibold ${
                        isDark 
                          ? 'bg-[#181A20] text-[#B6FF2E] border border-[#B6FF2E]/30' 
                          : 'bg-[#D8AE9B]/30 text-[#2E0A12] border border-[#D8AE9B]/60'
                      }`}>
                        Unknowns: {item.categories.unknownHandling}%
                      </span>
                    </div>
                  </td>

                  <td className={`py-4 px-4 font-mono font-semibold text-xs ${
                    isDark ? 'text-slate-300' : 'text-[#6C3B45]'
                  }`}>
                    {item.evaluationsCount} cases
                  </td>

                  <td className={`py-4 px-4 font-medium ${
                    isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                  }`}>
                    {item.lastEvaluated}
                  </td>

                  <td className="py-4 px-6 text-right">
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ml-auto ${
                      isDark 
                        ? 'bg-[#181A20] text-slate-400 group-hover:bg-[#B6FF2E] group-hover:text-[#181A20]' 
                        : 'bg-[#FBF1E3] text-[#8A6A72] group-hover:bg-[#800020] group-hover:text-[#FBF1E3]'
                    }`}>
                      <ChevronRight size={16} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Detail Modal */}
      <AnimatePresence>
        {inspectedModel && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`rounded-[2.5rem] w-full max-w-2xl p-6 md:p-8 border shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto transition-colors ${
                isDark 
                  ? 'bg-[#23262F] border-[#333742] text-white' 
                  : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#2E0A12]'
              }`}
            >
              
              {/* Header */}
              <div className={`flex items-start justify-between pb-4 border-b ${
                isDark ? 'border-[#333742]' : 'border-[#E9D6C4]'
              }`}>
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                    isDark 
                      ? 'bg-[#181A20] text-[#B6FF2E] border border-[#B6FF2E]/30' 
                      : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
                  }`}>
                    <Bot size={24} />
                  </div>
                  <div>
                    <h3 className={`font-extrabold text-lg ${
                      isDark ? 'text-white' : 'text-[#2E0A12]'
                    }`}>
                      {inspectedModel.model}
                    </h3>
                    <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>
                      {inspectedModel.provider} · Version: {inspectedModel.version}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setInspectedModel(null)}
                  className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                    isDark 
                      ? 'bg-[#181A20] hover:bg-[#2A2E38] text-slate-300' 
                      : 'bg-[#FBF1E3] hover:bg-[#EFE0D1] text-[#6C3B45]'
                  }`}
                >
                  <X size={16} />
                </button>
              </div>

              {/* Performance Summary Banner */}
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className={`p-3.5 rounded-2xl border ${
                  isDark ? 'bg-[#181A20] border-[#333742]' : 'bg-[#FBF1E3] border-[#E9D6C4]'
                }`}>
                  <span className={`text-xs uppercase font-bold block ${
                    isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                  }`}>
                    Overall Score
                  </span>
                  <span className={`text-2xl font-black font-mono mt-1 block ${
                    isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                  }`}>
                    {inspectedModel.overallScore}%
                  </span>
                </div>
                <div className={`p-3.5 rounded-2xl border ${
                  isDark ? 'bg-[#181A20] border-[#333742]' : 'bg-[#FBF1E3] border-[#E9D6C4]'
                }`}>
                  <span className={`text-xs uppercase font-bold block ${
                    isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                  }`}>
                    Evaluated Runs
                  </span>
                  <span className={`text-2xl font-black font-mono mt-1 block ${
                    isDark ? 'text-white' : 'text-[#2E0A12]'
                  }`}>
                    {inspectedModel.evaluationsCount}
                  </span>
                </div>
                <div className={`p-3.5 rounded-2xl border ${
                  isDark ? 'bg-[#181A20] border-[#333742]' : 'bg-[#FBF1E3] border-[#E9D6C4]'
                }`}>
                  <span className={`text-xs uppercase font-bold block ${
                    isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                  }`}>
                    Last Audited
                  </span>
                  <span className={`text-sm font-bold font-mono block mt-2 ${
                    isDark ? 'text-slate-300' : 'text-[#6C3B45]'
                  }`}>
                    {inspectedModel.lastEvaluated}
                  </span>
                </div>
              </div>

              {/* Category Scores */}
              <div className="space-y-2.5 text-xs">
                <h4 className={`font-bold uppercase tracking-wider text-xs ${
                  isDark ? 'text-slate-200' : 'text-[#2E0A12]'
                }`}>
                  Category Calibration
                </h4>
                <div className="space-y-2">
                  {[
                    { label: 'Factual Support', val: inspectedModel.categories.factualSupport },
                    { label: 'Evidence Support', val: inspectedModel.categories.evidenceSupport },
                    { label: 'Contradiction Detection', val: inspectedModel.categories.contradictionDetection },
                    { label: 'Unknown Handling', val: inspectedModel.categories.unknownHandling },
                    { label: 'Claim Verification Accuracy', val: inspectedModel.categories.claimVerification },
                  ].map((c) => (
                    <div key={c.label} className="space-y-1">
                      <div className={`flex justify-between font-semibold ${
                        isDark ? 'text-slate-300' : 'text-[#6C3B45]'
                      }`}>
                        <span>{c.label}</span>
                        <span className={`font-mono font-bold ${
                          isDark ? 'text-white' : 'text-[#2E0A12]'
                        }`}>{c.val}%</span>
                      </div>
                      <div className={`h-2 w-full rounded-full overflow-hidden ${
                        isDark ? 'bg-[#181A20]' : 'bg-[#E9D6C4]'
                      }`}>
                        <div 
                          className={`h-full rounded-full ${
                            isDark ? 'bg-[#B6FF2E]' : 'bg-[#800020]'
                          }`} 
                          style={{ width: `${c.val}%` }} 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className={`pt-3 border-t flex justify-end gap-3 ${
                isDark ? 'border-[#333742]' : 'border-[#E9D6C4]'
              }`}>
                <button
                  onClick={() => {
                    setInspectedModel(null);
                    navigate('/chat');
                  }}
                  className={`px-4 py-2.5 rounded-xl font-bold text-xs cursor-pointer border ${
                    isDark 
                      ? 'bg-[#181A20] text-white border-[#333742] hover:border-[#B6FF2E]' 
                      : 'bg-[#FBF1E3] text-[#2E0A12] border-[#E9D6C4] hover:bg-[#EFE0D1]'
                  }`}
                >
                  Test in Multi-Model Chat
                </button>
                <button
                  onClick={() => setInspectedModel(null)}
                  className={`px-5 py-2.5 rounded-xl font-bold text-xs cursor-pointer shadow-xs ${
                    isDark 
                      ? 'bg-[#B6FF2E] text-[#181A20]' 
                      : 'bg-[#800020] text-[#FBF1E3]'
                  }`}
                >
                  Close Details
                </button>
              </div>

            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </motion.div>
  );
};
export default ModelLeaderboardPage;
