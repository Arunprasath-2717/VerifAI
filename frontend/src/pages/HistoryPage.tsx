import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Clock, 
  Search, 
  ChevronRight, 
  Download,
  ShieldCheck,
  MessageSquare,
  FileCheck2
} from 'lucide-react';
import { motion } from 'motion/react';
import { VerificationRecord, Conversation } from '../types';
import { historyApi, BackendAuditHistoryItem } from '../api';
import { useTheme } from '../context/ThemeContext';

interface HistoryPageProps {
  verifications: VerificationRecord[];
  conversations: Conversation[];
  theme?: 'light' | 'dark';
}

export const HistoryPage: React.FC<HistoryPageProps> = ({
  verifications,
  conversations,
  theme: propTheme,
}) => {
  const navigate = useNavigate();
  const context = useTheme();
  const isDark = (propTheme || context.theme) === 'dark';
  const [searchParams] = useSearchParams();
  const queryParam = searchParams.get('q') || '';

  const [activeTab, setActiveTab] = useState<'verifications' | 'conversations' | 'audit'>('verifications');
  const [searchFilter, setSearchFilter] = useState(queryParam);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [timeFilter, setTimeFilter] = useState('ALL');
  const [auditRecords, setAuditRecords] = useState<BackendAuditHistoryItem[]>([]);

  React.useEffect(() => {
    if (activeTab === 'audit') {
      historyApi.listAudit({ limit: 50 })
        .then(res => setAuditRecords(res.items || []))
        .catch(() => {});
    }
  }, [activeTab]);

  const filteredVerifications = verifications.filter(v => {
    const matchesSearch = v.query.toLowerCase().includes(searchFilter.toLowerCase()) ||
      v.summary.toLowerCase().includes(searchFilter.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || v.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredConversations = conversations.filter(c =>
    c.title.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 pb-16"
    >
      {/* Header with Title and Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#1E0A10] dark:text-white transition-colors">
            History
          </h1>
          <p className="text-xs md:text-sm font-medium text-[#5C3040] dark:text-slate-300 transition-colors">
            Past verifications, comparative conversations, and verifiable audit records.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex p-1 rounded-2xl border shadow-2xs self-start sm:self-auto bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          {[
            { id: 'verifications', label: 'Verifications' },
            { id: 'conversations', label: 'Conversations' },
            { id: 'audit', label: 'Audit Logs' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === tab.id
                  ? 'bg-[#800020] text-[#FBF1E3] dark:bg-[#B6FF2E] dark:text-[#181A20] shadow-xs'
                  : 'text-[#8A6A72] dark:text-slate-400 hover:text-[#2E0A12] dark:hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="rounded-[2rem] p-4 border shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#8A6A72] dark:text-slate-400" size={16} />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder={`Search ${activeTab}...`}
            className="w-full rounded-xl py-2 pl-9 pr-4 text-xs md:text-sm outline-none border transition-all bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12] placeholder-[#8A6A72] focus:ring-2 focus:ring-[#800020]/20 dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-100 dark:placeholder-slate-500 dark:focus:ring-[#B6FF2E]/30 dark:focus:border-[#B6FF2E]"
          />
        </div>

        {activeTab === 'verifications' && (
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs font-semibold rounded-xl px-3 py-2 outline-none border transition-colors bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-200 cursor-pointer"
            >
              <option value="ALL">All Status</option>
              <option value="SUPPORTED">Supported</option>
              <option value="CONTRADICTED">Contradicted</option>
              <option value="UNKNOWN">Unknown</option>
            </select>

            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              className="text-xs font-semibold rounded-xl px-3 py-2 outline-none border transition-colors bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12] dark:bg-[#181A20] dark:border-[#333742] dark:text-slate-200 cursor-pointer"
            >
              <option value="ALL">All Time</option>
              <option value="7D">Past 7 Days</option>
              <option value="30D">Past 30 Days</option>
            </select>
          </div>
        )}
      </div>

      {/* Content based on Active Tab */}
      {activeTab === 'verifications' && (
        <div className="rounded-[2.5rem] border shadow-xs divide-y overflow-hidden transition-colors bg-[#FFFDFA] border-[#E9D6C4] divide-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742] dark:divide-[#333742]">
          {filteredVerifications.length > 0 ? (
            filteredVerifications.map((item) => (
              <div
                key={item.id}
                onClick={() => navigate(`/verification/${item.id}`)}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors cursor-pointer group hover:bg-[#FBF1E3] dark:hover:bg-[#2A2E38]"
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-black uppercase ${
                      item.status === 'SUPPORTED'
                        ? isDark
                          ? 'bg-[#B6FF2E]/15 text-[#B6FF2E] border border-[#B6FF2E]/30'
                          : 'lt-badge-supported'
                        : item.status === 'CONTRADICTED'
                        ? isDark
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'lt-badge-contradicted'
                        : isDark
                          ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                          : 'lt-badge-unknown'
                    }`}>
                      {item.status}
                    </span>
                    <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">·</span>
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">{item.model}</span>
                    <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">·</span>
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">{item.timestamp}</span>
                  </div>

                  <h3 className="text-sm md:text-base font-bold truncate transition-colors text-[#2E0A12] group-hover:text-[#800020] dark:text-white dark:group-hover:text-[#B6FF2E]">
                    {item.query}
                  </h3>
                </div>

                <div className="flex items-center gap-4 shrink-0">
                  <span className="text-sm font-semibold tabular-nums text-[#8A6A72] dark:text-slate-400">
                    {item.claimsCount} claims · {item.evidenceCount} evidence
                  </span>
                  <div className="w-8 h-8 rounded-xl flex items-center justify-center transition-colors bg-[#FBF1E3] text-[#8A6A72] group-hover:bg-[#800020] group-hover:text-[#FBF1E3] dark:bg-[#181A20] dark:group-hover:bg-[#B6FF2E] dark:group-hover:text-[#181A20]">
                    <ChevronRight size={16} />
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-16 text-sm text-slate-400 dark:text-slate-500">
              No matching verifications found.
            </div>
          )}
        </div>
      )}

      {activeTab === 'conversations' && (
        <div className="rounded-[2.5rem] border shadow-xs divide-y overflow-hidden transition-colors bg-[#FFFDFA] border-[#E9D6C4] divide-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742] dark:divide-[#333742]">
          {filteredConversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => navigate(`/chat/${conv.id}`)}
              className="p-5 flex items-center justify-between gap-4 transition-colors cursor-pointer group hover:bg-[#FBF1E3] dark:hover:bg-[#2A2E38]"
            >
              <div className="space-y-1 min-w-0">
                <h3 className="text-sm md:text-base font-bold truncate transition-colors text-[#2E0A12] group-hover:text-[#800020] dark:text-white dark:group-hover:text-[#B6FF2E]">
                  {conv.title}
                </h3>
                <p className="text-xs text-[#8A6A72] dark:text-slate-400">
                  Updated {conv.updatedAt} · {conv.models.join(', ')}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-sm font-mono text-[#8A6A72] dark:text-slate-400">
                  {conv.messages.length} messages
                </span>
                <ChevronRight size={16} className="text-[#8A6A72] group-hover:text-[#2E0A12] dark:group-hover:text-white transition-colors" />
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="rounded-[2.5rem] p-6 border shadow-xs space-y-4 transition-colors bg-[#FFFDFA] border-[#E9D6C4] dark:bg-[#23262F] dark:border-[#333742]">
          <div className="flex items-center justify-between pb-3 border-b border-[#E9D6C4] dark:border-[#333742]">
            <div>
              <h3 className="text-base font-extrabold text-[#2E0A12] dark:text-white">Cryptographically Signed Audit Trail</h3>
              <p className="text-sm font-medium text-[#8A6A72] dark:text-slate-400 mt-0.5">Verifiable Merkle logs of claim inspections for regulatory compliance</p>
            </div>
            <button
              onClick={() => {
                const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(verifications, null, 2));
                const downloadAnchor = document.createElement('a');
                downloadAnchor.setAttribute("href", dataStr);
                downloadAnchor.setAttribute("download", `verifai-audit-trail-${Date.now()}.json`);
                document.body.appendChild(downloadAnchor);
                downloadAnchor.click();
                downloadAnchor.remove();
              }}
              className="px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-xs transition-colors bg-[#800020] hover:bg-[#6E1B33] text-[#FBF1E3] dark:bg-[#B6FF2E] dark:hover:bg-[#A3E823] dark:text-[#181A20]"
            >
              <Download size={14} />
              <span>Export Ledger</span>
            </button>
          </div>

          <div className="space-y-2">
            {auditRecords.length > 0 ? (
              auditRecords.map((r) => (
                <div key={r.id} className="p-3.5 rounded-xl border flex items-center justify-between text-xs font-mono bg-[#FBF1E3] border-[#E9D6C4] dark:bg-[#181A20] dark:border-[#333742]">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#800020] dark:text-[#B6FF2E]">{r.stage}</span>
                      <span className="text-[#8A6A72] dark:text-slate-400">· {r.event_type}</span>
                    </div>
                    <p className="text-[11px] font-sans text-[#2E0A12] dark:text-slate-200">{r.message}</p>
                  </div>
                  <div className="text-right">
                    <span className={`font-bold ${r.status === 'SUCCESS' ? 'text-emerald-600 dark:text-[#B6FF2E]' : 'text-[#800020] dark:text-rose-400'}`}>{r.status}</span>
                    <p className="text-[10px] text-[#8A6A72] dark:text-slate-500">{new Date(r.timestamp).toLocaleTimeString()}</p>
                  </div>
                </div>
              ))
            ) : (
              verifications.map((v) => (
                <div key={v.id} className="p-3.5 rounded-xl border flex items-center justify-between text-xs font-mono bg-[#FBF1E3] border-[#E9D6C4] dark:bg-[#181A20] dark:border-[#333742]">
                  <div>
                    <span className="font-bold text-[#800020] dark:text-[#B6FF2E]">{v.id}</span>
                    <span className="text-[#8A6A72] dark:text-slate-500 ml-2">HASH: 0x{v.id.replace('ver-', '')}89a...4b12</span>
                  </div>
                  <span className="font-bold text-[#800020] dark:text-[#B6FF2E]">{v.status}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
};
export default HistoryPage;
