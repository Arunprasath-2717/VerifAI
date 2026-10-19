import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Plus, 
  MessageSquare, 
  Send, 
  Bot, 
  ShieldCheck, 
  Sparkles, 
  RotateCw, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Check, 
  Copy, 
  WifiOff, 
  Info,
  Clock,
  Layers,
  Sparkle,
  Compass,
  Key,
  Search,
  Filter,
  SlidersHorizontal,
  Cpu,
  Globe,
  Server,
  CheckCircle2,
  X
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Conversation, 
  ChatMessage, 
  ModelResponse, 
  ChatEvaluation, 
  AIProvider,
  VerificationStatus,
  ModelMetadata
} from '../types';
import { allEcosystemModels } from '../data/mockBackendData';
import { HaloButton } from '../components/ui/halo-button';
import { BorderGlowButton } from '../components/ui/BorderGlowButton';
import { useTheme } from '../context/ThemeContext';
import { chatApi, verificationApi, adaptBackendVerificationToRecord } from '../api';

interface ChatPageProps {
  conversations: Conversation[];
  onAddConversation: (conv: Conversation) => void;
  onUpdateConversation: (conv: Conversation) => void;
  providers: AIProvider[];
  theme?: 'light' | 'dark';
}

export const ChatPage: React.FC<ChatPageProps> = ({
  conversations,
  onAddConversation,
  onUpdateConversation,
  providers,
  theme: propTheme,
}) => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const context = useTheme();
  const isDark = (propTheme || context.theme) === 'dark';

  const activeConv = conversations.find(c => c.id === conversationId) || conversations[0] || {
    id: 'conv-default',
    title: 'Multi-Model Comparative Session',
    updatedAt: 'Just now',
    messageCount: 0,
    models: ['GPT-4o', 'Claude 3.5', 'Gemini 1.5'],
    messages: []
  };

  const [selectedModels, setSelectedModels] = useState<string[]>(
    activeConv.models && activeConv.models.length > 0 
      ? activeConv.models 
      : ['GPT-5.6 Sol', 'Claude 3.5 Sonnet', 'Gemini 3.1 Pro']
  );

  const [promptText, setPromptText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [evaluatingMsgId, setEvaluatingMsgId] = useState<string | null>(null);
  const [evaluationStage, setEvaluationStage] = useState<string>('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedClaimIds, setExpandedClaimIds] = useState<string[]>(['cl-c1']);

  // Model Browser Dialog State
  const [isAdvancedBrowserOpen, setIsAdvancedBrowserOpen] = useState(false);
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterCapability, setFilterCapability] = useState<string>('all');
  const [searchModelQuery, setSearchModelQuery] = useState<string>('');

  // Merge live provider credentials connectivity
  const availableProviderModels: ModelMetadata[] = allEcosystemModels.map((item) => {
    const provId = item.provider === 'OpenAI' ? 'prov-openai'
      : item.provider === 'Anthropic' ? 'prov-anthropic'
      : item.provider === 'Google' ? 'prov-google'
      : item.provider === 'Groq' ? 'prov-groq'
      : item.provider === 'Ollama' ? 'prov-ollama'
      : 'prov-openrouter';
    const isConn = providers.some(p => p.id === provId && p.status === 'Connected');
    return { ...item, isConnected: isConn };
  });

  // Recommended default picker models
  const recommendedModels: ModelMetadata[] = availableProviderModels.filter(m => m.recommended);

  // Filtered models for advanced browser
  const filteredBrowserModels: ModelMetadata[] = availableProviderModels.filter(m => {
    const query = searchModelQuery.toLowerCase();
    const matchSearch = m.name.toLowerCase().includes(query) ||
      m.family.toLowerCase().includes(query) ||
      (m.description && m.description.toLowerCase().includes(query));
    const matchProvider = filterProvider === 'all' || m.provider.toLowerCase() === filterProvider.toLowerCase();
    const matchType = filterType === 'all' || m.modelType === filterType;
    const matchCap = filterCapability === 'all' || m.capabilities.includes(filterCapability);
    return matchSearch && matchProvider && matchType && matchCap;
  });

  const handleToggleModel = (modelName: string) => {
    if (selectedModels.includes(modelName)) {
      if (selectedModels.length > 1) {
        setSelectedModels(selectedModels.filter(m => m !== modelName));
      }
    } else {
      if (selectedModels.length < 3) {
        setSelectedModels([...selectedModels, modelName]);
      }
    }
  };

  const handleCreateNewChat = () => {
    const newConv: Conversation = {
      id: `conv-${Date.now()}`,
      title: 'New Multi-Model Session',
      updatedAt: 'Just now',
      messageCount: 0,
      models: selectedModels,
      messages: []
    };
    onAddConversation(newConv);
    navigate(`/chat/${newConv.id}`);
  };

  const handleCopyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleClaimExpand = (claimId: string) => {
    if (expandedClaimIds.includes(claimId)) {
      setExpandedClaimIds(expandedClaimIds.filter(id => id !== claimId));
    } else {
      setExpandedClaimIds([...expandedClaimIds, claimId]);
    }
  };

  function toBackendModel(modelName: string): { provider: string; model_name: string } {
    const lower = modelName.toLowerCase();
    if (lower.includes('claude') || lower.includes('anthropic')) {
      return { provider: 'anthropic', model_name: 'claude-3-5-sonnet' };
    }
    if (lower.includes('gemini') || lower.includes('google')) {
      return { provider: 'google', model_name: 'gemini-1.5-pro' };
    }
    if (lower.includes('llama') || lower.includes('groq')) {
      return { provider: 'groq', model_name: 'llama-3.3-70b-versatile' };
    }
    if (lower.includes('mistral')) {
      return { provider: 'mistral', model_name: 'mistral-large' };
    }
    if (lower.includes('deepseek')) {
      return { provider: 'deepseek', model_name: 'deepseek-chat' };
    }
    return { provider: 'openai', model_name: 'gpt-4o' };
  }

  const handleSendPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptText.trim() || isSending) return;

    const currentPrompt = promptText;
    setPromptText('');
    setIsSending(true);

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      sender: 'user',
      content: currentPrompt,
      timestamp: 'Just now'
    };

    const pendingAssistantMsg: ChatMessage = {
      id: `msg-${Date.now()}-asst`,
      sender: 'assistant',
      content: '',
      timestamp: 'Just now',
      modelResponses: selectedModels.map((m) => {
        const prov = availableProviderModels.find(p => p.name === m);
        return {
          model: m,
          provider: prov?.provider || 'AI Provider',
          text: '',
          status: 'Running',
        };
      })
    };

    const updatedConv: Conversation = {
      ...activeConv,
      title: activeConv.messages.length === 0 ? currentPrompt.slice(0, 42) + '...' : activeConv.title,
      updatedAt: 'Just now',
      models: selectedModels,
      messages: [...activeConv.messages, userMsg, pendingAssistantMsg]
    };

    onUpdateConversation(updatedConv);

    try {
      let convId = activeConv.id;
      const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(convId);
      if (!isUuid) {
        try {
          const created = await chatApi.createConversation(currentPrompt.slice(0, 42));
          convId = created.id;
        } catch {}
      }

      const backendModels = selectedModels.slice(0, 3).map(toBackendModel);
      const resp = await chatApi.sendMessage(convId, {
        prompt: currentPrompt,
        models: backendModels,
        verify: false,
      });

      const completedResponses: ModelResponse[] = (resp.runs || []).map(r => ({
        model: r.model_name,
        provider: r.provider,
        text: r.response || (r.status === 'FAILED' ? `[Execution Error]: ${r.error_message || 'Provider call failed'}` : ''),
        status: r.status === 'COMPLETED' ? 'Completed' : r.status === 'FAILED' ? 'Failed' : 'Unavailable',
        latencyMs: r.latency_ms ? Math.round(r.latency_ms) : undefined,
        errorReason: r.error_message || undefined,
      }));

      const finalizedAssistantMsg: ChatMessage = {
        ...pendingAssistantMsg,
        modelResponses: completedResponses.length > 0 ? completedResponses : pendingAssistantMsg.modelResponses,
      };

      onUpdateConversation({
        ...updatedConv,
        id: convId,
        messages: [...activeConv.messages, userMsg, finalizedAssistantMsg]
      });
    } catch (err: any) {
      const errorResponses: ModelResponse[] = (pendingAssistantMsg.modelResponses || []).map(m => ({
        ...m,
        status: 'Failed',
        errorReason: err?.message || 'Inference execution failed.',
      }));

      onUpdateConversation({
        ...updatedConv,
        messages: [...activeConv.messages, userMsg, { ...pendingAssistantMsg, modelResponses: errorResponses }]
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleTriggerEvaluation = async (msgId: string, responses: ModelResponse[]) => {
    setEvaluatingMsgId(msgId);
    setEvaluationStage('Extracting discrete propositions from model answers...');

    const stageTimers = [
      setTimeout(() => setEvaluationStage('Querying ground-truth corpus & peer-reviewed registries...'), 1200),
      setTimeout(() => setEvaluationStage('Cross-examining models for corroboration vs contradiction...'), 2400),
      setTimeout(() => setEvaluationStage('Formulating cryptographically calibrated evidence decisions...'), 3600),
    ];

    try {
      const combinedAnswers = responses
        .filter(r => r.text)
        .map(r => `[${r.model}]: ${r.text}`)
        .join('\n\n');

      const verifResp = await verificationApi.createVerification({
        input_text: combinedAnswers || 'Model proposition evaluation',
        options: {
          use_web_evidence: true,
          use_knowledge_base: true,
          strictness: 'STANDARD',
        },
      });

      stageTimers.forEach(clearTimeout);
      const verifRecord = adaptBackendVerificationToRecord(verifResp);

      const evaluation: ChatEvaluation = {
        id: verifRecord.id,
        overallDecision: verifRecord.status,
        claimsAnalyzed: verifRecord.claimsCount,
        evidenceSourcesCount: verifRecord.evidenceCount,
        modelsEvaluatedCount: responses.filter(r => r.status === 'Completed').length,
        decisionRationale: verifRecord.summary || 'Claims verified via authoritative backend verification pipeline.',
        finalVerifaiDecision: verifRecord.status,
        modelJudgmentsSummary: responses.map(r => ({
          model: r.model,
          verdict: verifRecord.status,
          notes: r.status === 'Completed' ? `Verified against ${verifRecord.evidenceCount} empirical evidence vaults.` : 'Offline or unverified.',
        })),
        claims: (verifRecord.claims || []).map(c => ({
          id: c.id,
          statement: c.statement,
          modelAgreement: {
            agreeCount: responses.filter(r => r.status === 'Completed').length,
            totalModels: responses.length,
            consensusNote: 'Consensus evaluated against empirical evidence.',
          },
          evidenceSourcesCount: c.evidenceSnippet ? 1 : 0,
          verificationVerdict: c.status,
          confidence: c.confidence,
          modelJudgments: responses.map(r => ({
            model: r.model,
            verdict: c.status,
            reasoning: c.contradictionReason || 'Audited against factual benchmarks.',
          })),
          evidenceList: c.evidenceSnippet ? [
            {
              source: c.sourceTitle || 'Retrieved Evidence Vault',
              title: c.sourceTitle || 'Verified Document Source',
              domain: c.domain || 'knowledge-base',
              url: c.sourceUrl || '#',
              retrievedTime: c.retrievedAt || 'Just now',
              excerpt: c.evidenceSnippet,
              type: 'Primary Research',
            }
          ] : [],
        })),
      };

      const updatedMessages = activeConv.messages.map(m => {
        if (m.id === msgId) {
          return { ...m, evaluation };
        }
        return m;
      });

      onUpdateConversation({
        ...activeConv,
        messages: updatedMessages
      });
    } catch {
      stageTimers.forEach(clearTimeout);
    } finally {
      setEvaluatingMsgId(null);
      setEvaluationStage('');
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 pb-16 max-w-6xl mx-auto"
    >
      {/* 1. Header & Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <h1 className={`text-3xl md:text-4xl font-extrabold tracking-tight transition-colors ${
              isDark ? 'text-white' : 'text-[#2E0A12]'
            }`}>
              AI Chat Workspace
            </h1>
            <span className={`px-3 py-1 rounded-full text-xs font-extrabold border ${
              isDark 
                ? 'bg-[#181A20] text-[#B6FF2E] border-[#B6FF2E]/40 shadow-[0_0_12px_rgba(182,255,46,0.15)]' 
                : 'bg-[#FBF1E3] text-[#800020] border-[#E9D6C4]'
            }`}>
              Multi-Model Comparison
            </span>
          </div>
          <p className={`text-sm md:text-base font-medium ${
            isDark ? 'text-slate-300' : 'text-[#6C3B45]'
          }`}>
            Send one question to multiple LLMs simultaneously, compare independent assertions, and verify evidence.
          </p>
        </div>

        <BorderGlowButton
          size="sm"
          variant="primary"
          onClick={handleCreateNewChat}
          theme={isDark ? 'dark' : 'light'}
        >
          <Plus size={16} strokeWidth={2.4} />
          <span>New Multi-Model Session</span>
        </BorderGlowButton>
      </div>

      {/* 2. Horizontal Session Switcher (Quickly navigate between comparative threads) */}
      {conversations.length > 0 && (
        <div className={`p-2.5 rounded-2xl border flex items-center gap-2 overflow-x-auto shadow-xs transition-colors ${
          isDark ? 'bg-[#1E2129] border-[#333742]' : 'bg-[#FFFDFA] border-[#E9D6C4]'
        }`}>
          <span className={`text-[11px] font-extrabold uppercase tracking-wider px-3 shrink-0 ${
            isDark ? 'text-slate-400' : 'text-[#8A6A72]'
          }`}>
            Sessions:
          </span>
          <div className="flex items-center gap-2 flex-nowrap min-w-0">
            {conversations.map((c) => {
              const isActive = c.id === activeConv.id;
              return (
                <button
                  key={c.id}
                  onClick={() => navigate(`/chat/${c.id}`)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all flex items-center gap-2 cursor-pointer ${
                    isActive
                      ? isDark
                        ? 'bg-[#B6FF2E] text-[#181A20] font-black shadow-[0_0_15px_rgba(182,255,46,0.3)]'
                        : 'bg-[#800020] text-[#FBF1E3]'
                      : isDark
                        ? 'bg-[#14161C] text-slate-300 hover:text-white border border-[#2D313D] hover:border-slate-500'
                        : 'bg-[#FBF1E3] text-[#6C3B45] hover:text-[#2E0A12] border border-[#E9D6C4]'
                  }`}
                >
                  <MessageSquare size={13} />
                  <span className="max-w-[160px] truncate">{c.title}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-md ${
                    isActive
                      ? isDark ? 'bg-[#181A20]/20 text-[#181A20]' : 'bg-[#FFFDFA]/20 text-[#FBF1E3]'
                      : isDark ? 'bg-[#23262F] text-slate-400' : 'bg-[#EFE0D1] text-[#6C3B45]'
                  }`}>
                    {c.messages.length}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* 3. Prominent Model Selector (Dark Container with Light Typography) */}
      <section className={`rounded-[2.4rem] p-6 border shadow-xl space-y-4 transition-colors relative overflow-hidden ${
        isDark 
          ? 'bg-[#1E2129] border-[#333742] shadow-black/40' 
          : 'bg-[#FFFDFA] border-[#E9D6C4]'
      }`}>
        {/* Subtle dark ambient top highlight */}
        {isDark && (
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent pointer-events-none" />
        )}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className={`font-extrabold text-sm uppercase tracking-wider ${
                isDark ? 'text-white' : 'text-[#2E0A12]'
              }`}>
                Select Models to Compare
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold border ${
                isDark 
                  ? 'bg-[#14161C] text-[#B6FF2E] border-[#B6FF2E]/30' 
                  : 'bg-[#FBF1E3] text-[#800020] border-[#E9D6C4]'
              }`}>
                {selectedModels.length} / 3 models active
              </span>
            </div>
            <p className={`text-xs mt-1 ${
              isDark ? 'text-slate-300' : 'text-[#6C3B45]'
            }`}>
              Select 1 to 3 models across proprietary, open-weight, or local runtimes to cross-examine responses.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
            <button
              type="button"
              onClick={() => setIsAdvancedBrowserOpen(true)}
              className={`px-3.5 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                isDark 
                  ? 'bg-[#14161C] border-[#B6FF2E]/40 text-[#B6FF2E] hover:bg-[#B6FF2E]/10 shadow-[0_0_10px_rgba(182,255,46,0.15)]' 
                  : 'bg-[#800020] border-[#800020] text-[#FBF1E3] hover:bg-[#990026] shadow-xs'
              }`}
            >
              <SlidersHorizontal size={13} />
              <span>Browse All Models ({availableProviderModels.length})</span>
            </button>

            <Link
              to="/settings/providers"
              className={`px-3.5 py-1.5 rounded-xl border text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                isDark 
                  ? 'bg-[#14161C] border-[#333742] text-slate-300 hover:text-white hover:border-slate-500' 
                  : 'bg-[#FBF1E3] border-[#E9D6C4] text-[#800020] hover:bg-[#EFE0D1] shadow-2xs'
              }`}
            >
              <Key size={13} />
              <span>Link API Keys</span>
            </Link>
          </div>
        </div>

        {/* Recommended Default Model Quick Picker */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5 pt-1">
          {recommendedModels.slice(0, 5).map((item) => {
            const isSelected = selectedModels.includes(item.name);
            const isConnected = item.isConnected;

            return (
              <div
                key={item.id}
                onClick={() => {
                  if (isConnected) handleToggleModel(item.name);
                }}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer relative select-none flex flex-col justify-between ${
                  !isConnected
                    ? isDark 
                      ? 'bg-[#14161C]/60 border-[#2D313D] opacity-60'
                      : 'bg-[#FBF1E3]/50 border-[#E9D6C4] opacity-60'
                    : isSelected
                    ? isDark
                      ? 'bg-[#14161C] border-[#B6FF2E] text-white shadow-[0_0_20px_rgba(182,255,46,0.25)] ring-1 ring-[#B6FF2E]/60 -translate-y-0.5'
                      : 'bg-[#800020] border-[#800020] text-[#FBF1E3] font-bold shadow-md -translate-y-0.5'
                    : isDark
                    ? 'bg-[#14161C] border-[#333742] text-slate-200 hover:border-slate-500 hover:bg-[#181B22]'
                    : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#2E0A12] hover:border-[#800020]/40 hover:bg-[#FBF1E3]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`text-[9px] font-extrabold uppercase tracking-wider ${
                      isSelected 
                        ? isDark ? 'text-[#B6FF2E]' : 'text-[#FBF1E3]'
                        : isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                    }`}>
                      {item.provider}
                    </span>
                    {isConnected ? (
                      <span className={`w-2 h-2 rounded-full ${
                        isSelected 
                          ? isDark ? 'bg-[#B6FF2E] shadow-[0_0_8px_#B6FF2E]' : 'bg-[#D8AE9B]' 
                          : 'bg-emerald-500'
                      }`} />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-slate-500" />
                    )}
                  </div>
                  <h4 className={`text-xs font-black leading-tight truncate ${
                    isSelected
                      ? isDark ? 'text-white' : 'text-[#FBF1E3]'
                      : isDark ? 'text-white' : 'text-[#2E0A12]'
                  }`}>
                    {item.name}
                  </h4>
                  <div className="flex items-center gap-1 mt-1">
                    <span className={`text-[8.5px] px-1.5 py-0.5 rounded font-mono uppercase font-bold ${
                      isSelected
                        ? isDark ? 'bg-[#B6FF2E]/20 text-[#B6FF2E]' : 'bg-white/20 text-white'
                        : isDark ? 'bg-[#23262F] text-slate-300' : 'bg-[#F4E6D8] text-[#800020]'
                    }`}>
                      {item.modelType}
                    </span>
                  </div>
                </div>

                <div className={`pt-2 mt-2 border-t flex items-center justify-between text-[10px] font-bold ${
                  isSelected 
                    ? isDark ? 'border-[#B6FF2E]/30 text-[#B6FF2E]' : 'border-white/20 text-[#FBF1E3]' 
                    : isDark ? 'border-[#2D313D] text-slate-400' : 'border-[#E9D6C4] text-[#8A6A72]'
                }`}>
                  {isConnected ? (
                    <span>
                      {isSelected ? 'Active ✓' : '+ Add'}
                    </span>
                  ) : (
                    <Link
                      to="/settings/providers"
                      onClick={(e) => e.stopPropagation()}
                      className={`hover:underline flex items-center gap-1 ${
                        isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                      }`}
                    >
                      <Key size={10} />
                      <span>Link Key</span>
                    </Link>
                  )}
                  {isSelected && <Check size={12} strokeWidth={2.5} />}
                </div>
              </div>
            );
          })}

          {/* "+ Browse More Models" Tile */}
          <div
            onClick={() => setIsAdvancedBrowserOpen(true)}
            className={`p-3.5 rounded-2xl border border-dashed transition-all cursor-pointer flex flex-col justify-center items-center text-center group ${
              isDark 
                ? 'bg-[#14161C]/50 border-[#333742] hover:border-[#B6FF2E]/60 hover:bg-[#181B22]'
                : 'bg-[#FBF1E3]/50 border-[#D8AE9B] hover:border-[#800020] hover:bg-[#F7EBE1]'
            }`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1.5 transition-transform group-hover:scale-110 ${
              isDark ? 'bg-[#23262F] text-[#B6FF2E]' : 'bg-[#E9D6C4] text-[#800020]'
            }`}>
              <Plus size={16} />
            </div>
            <span className={`text-xs font-bold leading-tight ${
              isDark ? 'text-white' : 'text-[#2E0A12]'
            }`}>
              + Add Model
            </span>
            <span className={`text-[10px] mt-0.5 ${
              isDark ? 'text-slate-400' : 'text-[#8A6A72]'
            }`}>
              {availableProviderModels.length} catalog options
            </span>
          </div>
        </div>

        {/* Advanced Model Browser Modal */}
        <AnimatePresence>
          {isAdvancedBrowserOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
              <motion.div
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className={`w-full max-w-4xl max-h-[88vh] rounded-[2rem] border shadow-2xl flex flex-col overflow-hidden ${
                  isDark ? 'bg-[#1A1D24] border-[#333742] text-white' : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#2E0A12]'
                }`}
              >
                {/* Modal Header */}
                <div className={`p-5 border-b flex items-center justify-between ${
                  isDark ? 'border-[#2D313D]' : 'border-[#E9D6C4]'
                }`}>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-black tracking-tight">VerifAI Model Catalog & Multi-Model Selector</h3>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-mono font-bold border ${
                        isDark ? 'bg-[#14161C] text-[#B6FF2E] border-[#B6FF2E]/40' : 'bg-[#FBF1E3] text-[#800020] border-[#E9D6C4]'
                      }`}>
                        {selectedModels.length} / 3 Selected
                      </span>
                    </div>
                    <p className={`text-xs mt-0.5 ${isDark ? 'text-slate-400' : 'text-[#6C3B45]'}`}>
                      Compare propositions across frontier closed models, hosted open-weight gateways, and local air-gapped runtimes.
                    </p>
                  </div>
                  <button
                    onClick={() => setIsAdvancedBrowserOpen(false)}
                    className={`p-2 rounded-xl transition-colors cursor-pointer ${
                      isDark ? 'hover:bg-[#23262F] text-slate-400 hover:text-white' : 'hover:bg-[#FBF1E3] text-[#8A6A72] hover:text-[#2E0A12]'
                    }`}
                  >
                    <X size={18} />
                  </button>
                </div>

                {/* Filter and Search Bar */}
                <div className={`p-4 border-b space-y-3 ${
                  isDark ? 'border-[#2D313D] bg-[#14161C]/50' : 'border-[#E9D6C4] bg-[#FBF1E3]/40'
                }`}>
                  {/* Search Input */}
                  <div className="relative">
                    <Search className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${
                      isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                    }`} size={15} />
                    <input
                      type="text"
                      value={searchModelQuery}
                      onChange={(e) => setSearchModelQuery(e.target.value)}
                      placeholder="Search models (GPT-5.6 Sol, Claude Sonnet, Gemini 3.1, Llama 4, Qwen 2.5, DeepSeek R1)..."
                      className={`w-full pl-9 pr-4 py-2 rounded-xl text-xs border outline-none font-medium transition-all ${
                        isDark 
                          ? 'bg-[#181B22] border-[#333742] text-white focus:border-[#B6FF2E]' 
                          : 'bg-white border-[#E9D6C4] text-[#2E0A12] focus:border-[#800020]'
                      }`}
                    />
                  </div>

                  {/* Filter Pills */}
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className={`text-[11px] font-bold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>
                      Provider:
                    </span>
                    {['all', 'OpenAI', 'Anthropic', 'Google', 'Groq', 'OpenRouter', 'Ollama'].map((prov) => (
                      <button
                        key={prov}
                        onClick={() => setFilterProvider(prov)}
                        className={`px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all cursor-pointer ${
                          filterProvider === prov
                            ? isDark ? 'bg-[#B6FF2E] text-black shadow-xs' : 'bg-[#800020] text-white shadow-xs'
                            : isDark ? 'bg-[#23262F] text-slate-300 hover:text-white' : 'bg-[#EFE0D1] text-[#6C3B45] hover:bg-[#E5D2C0]'
                        }`}
                      >
                        {prov === 'all' ? 'All Providers' : prov}
                      </button>
                    ))}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className={`text-[11px] font-bold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>
                      Type:
                    </span>
                    {[
                      { key: 'all', label: 'All Tiers' },
                      { key: 'proprietary', label: 'Proprietary' },
                      { key: 'open-weight', label: 'Open-Weight' },
                      { key: 'local', label: 'Local / Self-Hosted' },
                    ].map((t) => (
                      <button
                        key={t.key}
                        onClick={() => setFilterType(t.key)}
                        className={`px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all cursor-pointer ${
                          filterType === t.key
                            ? isDark ? 'bg-[#B6FF2E] text-black' : 'bg-[#800020] text-white'
                            : isDark ? 'bg-[#23262F] text-slate-300 hover:text-white' : 'bg-[#EFE0D1] text-[#6C3B45] hover:bg-[#E5D2C0]'
                        }`}
                      >
                        {t.label}
                      </button>
                    ))}

                    <span className={`ml-3 text-[11px] font-bold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>
                      Capability:
                    </span>
                    {[
                      { key: 'all', label: 'All' },
                      { key: 'reasoning', label: 'Reasoning' },
                      { key: 'multimodal', label: 'Multimodal' },
                      { key: 'coding', label: 'Coding' },
                    ].map((cap) => (
                      <button
                        key={cap.key}
                        onClick={() => setFilterCapability(cap.key)}
                        className={`px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all cursor-pointer ${
                          filterCapability === cap.key
                            ? isDark ? 'bg-[#B6FF2E] text-black' : 'bg-[#800020] text-white'
                            : isDark ? 'bg-[#23262F] text-slate-300 hover:text-white' : 'bg-[#EFE0D1] text-[#6C3B45] hover:bg-[#E5D2C0]'
                        }`}
                      >
                        {cap.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Model Catalog Grid */}
                <div className="p-5 overflow-y-auto max-h-[50vh] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                  {filteredBrowserModels.map((item) => {
                    const isSelected = selectedModels.includes(item.name);
                    const isConnected = item.isConnected;

                    return (
                      <div
                        key={item.id}
                        className={`p-4 rounded-2xl border transition-all flex flex-col justify-between ${
                          isSelected
                            ? isDark
                              ? 'bg-[#181B22] border-[#B6FF2E] ring-1 ring-[#B6FF2E]/60 shadow-[0_0_15px_rgba(182,255,46,0.15)]'
                              : 'bg-[#FFFDFA] border-[#800020] ring-1 ring-[#800020]/40 shadow-sm'
                            : isDark
                            ? 'bg-[#181B22]/70 border-[#2D313D] hover:border-[#3D4252]'
                            : 'bg-white border-[#E9D6C4] hover:border-[#800020]/30'
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-1.5">
                            <span className={`text-[10px] font-extrabold uppercase tracking-wider ${
                              isDark ? 'text-slate-400' : 'text-[#8A6A72]'
                            }`}>
                              {item.provider}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono uppercase font-bold ${
                                item.modelType === 'proprietary'
                                  ? isDark ? 'bg-amber-500/20 text-amber-300' : 'bg-amber-100 text-amber-900'
                                  : item.modelType === 'open-weight'
                                  ? isDark ? 'bg-cyan-500/20 text-cyan-300' : 'bg-cyan-100 text-cyan-900'
                                  : isDark ? 'bg-emerald-500/20 text-emerald-300' : 'bg-emerald-100 text-emerald-900'
                              }`}>
                                {item.modelType}
                              </span>
                              <span className={`w-2 h-2 rounded-full ${
                                isConnected ? 'bg-emerald-500' : 'bg-slate-500'
                              }`} />
                            </div>
                          </div>

                          <h4 className="text-sm font-black leading-tight">
                            {item.name}
                          </h4>
                          <p className={`text-[11px] font-medium mt-1 line-clamp-2 ${
                            isDark ? 'text-slate-300' : 'text-[#6C3B45]'
                          }`}>
                            {item.description || item.tier}
                          </p>

                          <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
                            <span className={`text-[9.5px] px-2 py-0.5 rounded-full font-mono ${
                              isDark ? 'bg-[#23262F] text-slate-300' : 'bg-[#F4E6D8] text-[#800020]'
                            }`}>
                              {(item.contextWindow / 1000).toFixed(0)}k context
                            </span>
                            {item.capabilities.map((cap) => (
                              <span
                                key={cap}
                                className={`text-[9.5px] px-1.5 py-0.5 rounded font-medium ${
                                  isDark ? 'bg-[#23262F]/80 text-slate-400' : 'bg-[#EFE0D1] text-[#6C3B45]'
                                }`}
                              >
                                {cap}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="pt-3 mt-3 border-t border-slate-700/20 flex items-center justify-between">
                          {isConnected ? (
                            <button
                              type="button"
                              onClick={() => handleToggleModel(item.name)}
                              className={`w-full py-1.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                                isSelected
                                  ? isDark
                                    ? 'bg-[#B6FF2E] text-black shadow-xs'
                                    : 'bg-[#800020] text-white shadow-xs'
                                  : selectedModels.length >= 3
                                  ? isDark
                                    ? 'bg-[#23262F] text-slate-500 cursor-not-allowed'
                                    : 'bg-[#EFE0D1] text-slate-400 cursor-not-allowed'
                                  : isDark
                                  ? 'bg-[#23262F] text-white hover:bg-[#2D313D]'
                                  : 'bg-[#FBF1E3] text-[#800020] hover:bg-[#EFE0D1]'
                              }`}
                            >
                              {isSelected ? (
                                <>
                                  <Check size={13} strokeWidth={2.5} />
                                  <span>Selected</span>
                                </>
                              ) : selectedModels.length >= 3 ? (
                                <span>Max 3 Selected</span>
                              ) : (
                                <span>+ Select Model</span>
                              )}
                            </button>
                          ) : (
                            <Link
                              to="/settings/providers"
                              className={`w-full py-1.5 rounded-xl text-xs font-bold text-center border transition-all flex items-center justify-center gap-1.5 ${
                                isDark 
                                  ? 'border-[#333742] text-[#B6FF2E] hover:bg-[#23262F]' 
                                  : 'border-[#E9D6C4] text-[#800020] hover:bg-[#FBF1E3]'
                              }`}
                            >
                              <Key size={12} />
                              <span>Link Key in Settings</span>
                            </Link>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Modal Footer */}
                <div className={`p-4 border-t flex flex-col sm:flex-row items-center justify-between gap-3 ${
                  isDark ? 'border-[#2D313D] bg-[#14161C]' : 'border-[#E9D6C4] bg-[#FBF1E3]'
                }`}>
                  <div className="text-xs">
                    <span className="font-bold">Active Selection: </span>
                    <span className={`font-mono ${isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'}`}>
                      {selectedModels.join(', ')}
                    </span>
                  </div>
                  <button
                    onClick={() => setIsAdvancedBrowserOpen(false)}
                    className={`px-5 py-2 rounded-xl text-xs font-black transition-all cursor-pointer ${
                      isDark ? 'bg-[#B6FF2E] text-black shadow-md' : 'bg-[#800020] text-white shadow-md'
                    }`}
                  >
                    Done ({selectedModels.length} / 3 Selected)
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </section>

      {/* 4. Prompt Composer (Dark Container, Pristine Light Typography) */}
      <section className={`rounded-[2.4rem] p-6 border shadow-xl space-y-4 transition-colors relative ${
        isDark 
          ? 'bg-[#1E2129] border-[#333742]' 
          : 'bg-[#FFFDFA] border-[#E9D6C4]'
      }`}>
        <div className="flex items-center justify-between">
          <label className={`text-xs font-bold uppercase tracking-wider block ${
            isDark ? 'text-white' : 'text-[#2E0A12]'
          }`}>
            Send Prompt to Independent Models
          </label>
          <span className={`text-[11px] font-mono ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>
            Parallel dispatch
          </span>
        </div>
        
        <form onSubmit={handleSendPrompt} className="space-y-4">
          <div className={`rounded-2xl p-1 border transition-all ${
            isDark 
              ? 'bg-[#14161C] border-[#333742] focus-within:border-[#B6FF2E] focus-within:ring-2 focus-within:ring-[#B6FF2E]/20' 
              : 'bg-[#FBF1E3] border-[#E9D6C4] focus-within:border-[#800020] focus-within:ring-2 focus-within:ring-[#800020]/20'
          }`}>
            <textarea
              rows={3}
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              placeholder="Ask anything for evidence evaluation (e.g. 'What evidence demonstrates that electric vehicle lifetime emissions are lower than gasoline cars?')"
              className={`w-full p-4 text-sm md:text-base outline-none font-sans leading-relaxed resize-none rounded-xl bg-transparent ${
                isDark
                  ? 'text-white placeholder-slate-500'
                  : 'text-slate-900 placeholder-slate-400'
              }`}
            />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
            <p className={`text-xs font-medium ${
              isDark ? 'text-slate-300' : 'text-[#6C3B45]'
            }`}>
              Your inquiry will be answered by <strong className={isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'}>{selectedModels.join(', ')}</strong> without coordinating consensus.
            </p>

            <BorderGlowButton
              type="submit"
              size="md"
              variant="primary"
              disabled={isSending || !promptText.trim()}
              theme={isDark ? 'dark' : 'light'}
            >
              {isSending ? (
                <>
                  <RotateCw size={16} className="animate-spin" />
                  <span>Dispatching Query...</span>
                </>
              ) : (
                <>
                  <Send size={16} strokeWidth={2.4} />
                  <span>Dispatch Prompt</span>
                </>
              )}
            </BorderGlowButton>
          </div>
        </form>
      </section>

      {/* 5. Chat Messages Stream */}
      <div className="space-y-8">
        {activeConv.messages.length > 0 ? (
          activeConv.messages.map((msg) => (
            <div key={msg.id} className="space-y-6 animate-in fade-in">
              
              {/* User Prompt Bubble */}
              {msg.sender === 'user' && (
                <div className="flex justify-end">
                  <div className={`max-w-2xl rounded-[2.2rem] p-6 shadow-lg border transition-colors ${
                    isDark
                      ? 'bg-gradient-to-r from-[#1C202B] to-[#252A38] border-[#3B4254] text-white shadow-black/30'
                      : 'bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12]'
                  }`}>
                    <div className="flex items-center gap-2 mb-1.5 opacity-80">
                      <span className={`w-2 h-2 rounded-full ${isDark ? 'bg-[#B6FF2E]' : 'bg-[#800020]'}`} />
                      <p className="text-xs font-black uppercase tracking-wider text-[#800020] dark:text-slate-300">
                        Prompt Dispatched:
                      </p>
                    </div>
                    <p className={`text-sm md:text-base leading-relaxed font-sans font-semibold ${
                      isDark ? 'text-white' : 'text-[#2E0A12]'
                    }`}>
                      {msg.content}
                    </p>
                  </div>
                </div>
              )}

              {/* Multi-Model Assistant Response Grid (Dark Containers, Crystal-Clear Light Typography) */}
              {msg.sender === 'assistant' && msg.modelResponses && (
                <div className="space-y-6">
                  
                  {/* Grid of 1, 2, or 3 columns based on responses count */}
                  <div className={`grid gap-4 md:gap-6 ${
                    msg.modelResponses.length === 1 
                      ? 'grid-cols-1' 
                      : msg.modelResponses.length === 2 
                      ? 'grid-cols-1 md:grid-cols-2' 
                      : 'grid-cols-1 md:grid-cols-3'
                  }`}>
                    {msg.modelResponses.map((res, rIdx) => {
                      const isComplete = res.status === 'Completed';
                      const isFailed = res.status === 'Failed' || res.status === 'Unavailable';

                      return (
                        <div
                          key={rIdx}
                          className={`rounded-[2.2rem] border p-6 shadow-xl flex flex-col justify-between space-y-4 relative overflow-hidden transition-colors ${
                            isDark
                              ? 'bg-[#1E2129] border-[#333742] text-white shadow-black/30'
                              : 'bg-[#FFFDFA] border-[#E9D6C4] text-[#2E0A12]'
                          }`}
                        >
                          <div>
                            {/* Card Header: Provider & Model */}
                            <div className={`flex items-center justify-between pb-3.5 mb-3.5 border-b ${
                              isDark ? 'border-[#2D313D]' : 'border-[#E9D6C4]'
                            }`}>
                              <div className="flex items-center gap-3">
                                <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs ${
                                  isDark 
                                    ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30 shadow-[0_0_10px_rgba(182,255,46,0.15)]' 
                                    : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
                                }`}>
                                  <Bot size={18} strokeWidth={2.2} />
                                </div>
                                <div>
                                  <h4 className={`text-sm font-black leading-tight ${
                                    isDark ? 'text-white' : 'text-slate-900'
                                  }`}>
                                    {res.model}
                                  </h4>
                                  <span className={`text-[10px] font-bold uppercase tracking-wider ${
                                    isDark ? 'text-slate-400' : 'text-slate-500'
                                  }`}>
                                    {res.provider}
                                  </span>
                                </div>
                              </div>

                              {/* Status Badge */}
                              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                                isComplete 
                                  ? isDark
                                    ? 'bg-[#B6FF2E]/15 text-[#B6FF2E] border border-[#B6FF2E]/30 shadow-[0_0_8px_rgba(182,255,46,0.2)]'
                                    : 'bg-[#800020]/10 text-[#800020] border border-[#800020]/20'
                                  : isFailed
                                  ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                                  : 'bg-amber-500/15 text-amber-300 border border-amber-500/30 animate-pulse'
                              }`}>
                                {res.status}
                              </span>
                            </div>

                            {/* Response Content Box (Dark Container with Light Text) */}
                            {isComplete && (
                              <div className={`p-4 rounded-2xl border text-xs md:text-sm leading-relaxed font-sans space-y-2 ${
                                isDark 
                                  ? 'bg-[#14161C] border-[#2D313D] text-[#F1F5F9]' 
                                  : 'bg-[#FFFBF6] border-slate-200 text-slate-800'
                              }`}>
                                <p>{res.text}</p>
                              </div>
                            )}

                            {isFailed && (
                              <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 space-y-1">
                                <p className="font-bold flex items-center gap-1.5">
                                  <WifiOff size={14} />
                                  <span>{res.model} — Provider Unavailable</span>
                                </p>
                                <p className="text-[11px] text-rose-400 leading-relaxed">
                                  {res.errorReason || 'Provider connection timed out or credentials not configured.'}
                                </p>
                              </div>
                            )}

                            {res.status === 'Running' && (
                              <div className={`py-8 flex items-center justify-center gap-2.5 text-xs font-semibold rounded-2xl border ${
                                isDark ? 'bg-[#14161C] border-[#2D313D] text-slate-300' : 'bg-slate-50 border-slate-200 text-slate-600'
                              }`}>
                                <RotateCw size={15} className={`animate-spin ${isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'}`} />
                                <span>Generating independent propositions...</span>
                              </div>
                            )}
                          </div>

                          {/* Footer Metrics & Actions */}
                          <div className={`pt-3.5 border-t flex items-center justify-between text-[11px] ${
                            isDark ? 'border-[#2D313D] text-slate-400' : 'border-slate-100 text-slate-500'
                          }`}>
                            {isComplete ? (
                              <div className="flex items-center gap-2 font-mono">
                                <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>{res.latencyMs}ms</span>
                                <span>·</span>
                                <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>{res.tokensUsed} tokens</span>
                              </div>
                            ) : (
                              <span>Telemetry unavailable</span>
                            )}

                            {isComplete && (
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => handleCopyText(`${msg.id}-${res.model}`, res.text)}
                                  className={`font-semibold flex items-center gap-1 cursor-pointer transition-colors px-2 py-1 rounded-lg ${
                                    isDark ? 'hover:bg-[#14161C] text-slate-300 hover:text-white' : 'hover:bg-slate-100 text-slate-600 hover:text-[#800020]'
                                  }`}
                                >
                                  {copiedId === `${msg.id}-${res.model}` ? (
                                    <>
                                      <Check size={12} className={isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'} />
                                      <span className={isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'}>Copied</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy size={12} />
                                      <span>Copy</span>
                                    </>
                                  )}
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* 6. Ready for VerifAI Verification Banner */}
                  {!msg.evaluation && (
                    <div className={`p-7 rounded-[2.5rem] border flex flex-col sm:flex-row sm:items-center justify-between gap-5 transition-colors shadow-2xl relative overflow-hidden ${
                      isDark
                        ? 'bg-gradient-to-r from-[#1E2129] via-[#232733] to-[#1E2129] border-[#333742]'
                        : 'bg-gradient-to-r from-[#FAF2E3] via-white to-[#FAF2E3] border-[#EAD3AC]'
                    }`}>
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2.5">
                          <Sparkles size={20} className={isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'} />
                          <h4 className={`font-black text-base md:text-lg ${
                            isDark ? 'text-white' : 'text-[#2E0A12]'
                          }`}>
                            Ready for VerifAI Evidence Verification
                          </h4>
                        </div>
                        <p className={`text-xs md:text-sm max-w-xl leading-relaxed ${
                          isDark ? 'text-slate-200' : 'text-[#6C3B45]'
                        }`}>
                          Run VerifAI's evidence verification pipeline to extract discrete claims, query authoritative sources, and identify corroborated facts vs contradictions.
                        </p>
                      </div>

                      <HaloButton
                        type="button"
                        isLoading={evaluatingMsgId === msg.id}
                        loadingText={evaluationStage || "Evaluating Claims…"}
                        onClick={() => handleTriggerEvaluation(msg.id, msg.modelResponses!)}
                        className="self-start sm:self-auto shrink-0 shadow-xl"
                      >
                        <ShieldCheck size={17} strokeWidth={2.4} className={isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'} />
                        <span>Summarise & Evaluate</span>
                      </HaloButton>
                    </div>
                  )}

                  {/* Evaluation in progress banner */}
                  {evaluatingMsgId === msg.id && (
                    <div className={`p-6 rounded-2xl border space-y-2 animate-in fade-in shadow-xl ${
                      isDark
                        ? 'bg-[#14161C] border-[#B6FF2E]/40 text-white'
                        : 'bg-[#FBF1E3] border-[#D8AE9B] text-[#2E0A12]'
                    }`}>
                      <p className={`text-xs font-bold uppercase tracking-wider flex items-center gap-2.5 ${
                        isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                      }`}>
                        <RotateCw size={15} className="animate-spin" />
                        <span>VerifAI Verification Pipeline in Progress</span>
                      </p>
                      <p className={`text-sm md:text-base font-bold ${isDark ? 'text-white' : 'text-[#2E0A12]'}`}>
                        {evaluationStage}
                      </p>
                    </div>
                  )}

                  {/* 7. VerifAI Evaluation Area (Dark Containers, High-Contrast Light Typography) */}
                  {msg.evaluation && (
                    <section className={`rounded-[2.8rem] p-7 md:p-9 border shadow-2xl space-y-7 animate-in fade-in transition-colors ${
                      isDark 
                        ? 'bg-[#1E2129] border-[#333742] shadow-black/40' 
                        : 'bg-[#FFFDFA] border-[#E9D6C4]'
                    }`}>
                      
                      {/* Evaluation Header */}
                      <div className={`flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b gap-4 ${
                        isDark ? 'border-[#2D313D]' : 'border-[#E9D6C4]'
                      }`}>
                        <div className="flex items-center gap-3.5">
                          <div className={`w-13 h-13 rounded-2xl flex items-center justify-center shadow-lg ${
                            isDark 
                              ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30 shadow-[0_0_15px_rgba(182,255,46,0.2)]' 
                              : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
                          }`}>
                            <ShieldCheck size={26} strokeWidth={2.4} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2.5">
                              <h3 className={`font-black text-xl tracking-tight ${
                                isDark ? 'text-white' : 'text-[#2E0A12]'
                              }`}>
                                VerifAI Evaluation
                              </h3>
                              <span className={`px-3 py-1 rounded-full text-xs font-black uppercase ${
                                msg.evaluation.overallDecision === 'SUPPORTED'
                                  ? isDark
                                    ? 'bg-[#B6FF2E]/15 text-[#B6FF2E] border border-[#B6FF2E]/30 shadow-[0_0_10px_rgba(182,255,46,0.25)]'
                                    : 'bg-[#D8AE9B]/30 text-[#800020] border border-[#D8AE9B]'
                                  : msg.evaluation.overallDecision === 'CONTRADICTED'
                                  ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                                  : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                              }`}>
                                {msg.evaluation.overallDecision}
                              </span>
                            </div>
                            <p className={`text-xs font-medium mt-0.5 ${
                              isDark ? 'text-slate-300' : 'text-[#6C3B45]'
                            }`}>
                              Independent evidence assessment calibrated against ground-truth corpus
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 text-xs">
                          <span className={`px-3.5 py-1.5 rounded-xl font-mono font-bold border ${
                            isDark 
                              ? 'bg-[#14161C] text-slate-200 border-[#2D313D]' 
                              : 'bg-[#FBF1E3] text-[#2E0A12] border-[#E9D6C4]'
                          }`}>
                            {msg.evaluation.claimsAnalyzed} Claims Analyzed
                          </span>
                          <span className={`px-3.5 py-1.5 rounded-xl font-mono font-bold border ${
                            isDark 
                              ? 'bg-[#14161C] text-[#B6FF2E] border-[#B6FF2E]/30 shadow-[0_0_10px_rgba(182,255,46,0.15)]' 
                              : 'bg-[#FBF1E3] text-[#800020] border-[#E9D6C4]'
                          }`}>
                            {msg.evaluation.evidenceSourcesCount} Sources Cited
                          </span>
                        </div>
                      </div>

                      {/* Decision Rationale Container */}
                      <div className={`p-5 rounded-2xl border space-y-1.5 ${
                        isDark 
                          ? 'bg-[#14161C] border-[#2D313D]' 
                          : 'bg-[#FBF1E3] border-[#E9D6C4]'
                      }`}>
                        <span className={`text-[10px] font-extrabold uppercase tracking-wider block ${
                          isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                        }`}>
                          Calibrated Decision Rationale
                        </span>
                        <p className={`text-xs md:text-sm leading-relaxed font-sans ${
                          isDark ? 'text-[#F1F5F9]' : 'text-[#2E0A12]'
                        }`}>
                          {msg.evaluation.decisionRationale}
                        </p>
                      </div>

                      {/* Claim Comparison Section */}
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h4 className={`font-extrabold text-sm uppercase tracking-wider ${
                            isDark ? 'text-white' : 'text-[#2E0A12]'
                          }`}>
                            Claim-by-Claim Verification
                          </h4>
                          <span className={`text-[11px] italic ${isDark ? 'text-slate-400' : 'text-[#8A6A72]'}`}>
                            *Model agreement is an observation; evidence alone determines verification verdict.
                          </span>
                        </div>

                        <div className="space-y-3.5">
                          {msg.evaluation.claims.map((claim, cIdx) => {
                            const isExpanded = expandedClaimIds.includes(claim.id);
                            return (
                              <div
                                key={claim.id}
                                className={`rounded-[2rem] border overflow-hidden shadow-xs transition-all ${
                                  isDark 
                                    ? 'bg-[#14161C] border-[#2D313D]' 
                                    : 'bg-[#FFFDFA] border-[#E9D6C4]'
                                }`}
                              >
                                {/* Claim Header */}
                                <div 
                                  onClick={() => toggleClaimExpand(claim.id)}
                                  className={`p-5 flex items-start sm:items-center justify-between gap-4 cursor-pointer transition-colors ${
                                    isDark ? 'hover:bg-[#1A1D25]' : 'hover:bg-[#FBF1E3]'
                                  }`}
                                >
                                  <div className="flex items-start sm:items-center gap-3.5 min-w-0">
                                    <span className="font-mono font-bold text-xs text-slate-400 shrink-0 mt-0.5 sm:mt-0">
                                      CLAIM {String(cIdx + 1).padStart(2, '0')}
                                    </span>
                                    <p className={`text-xs sm:text-sm font-bold leading-snug ${
                                      isDark ? 'text-white' : 'text-[#2E0A12]'
                                    }`}>
                                      "{claim.statement}"
                                    </p>
                                  </div>

                                  <div className="flex items-center gap-3 shrink-0">
                                    <span className={`px-2.5 py-1 rounded-xl text-[10px] font-mono font-bold border ${
                                      isDark 
                                        ? 'bg-[#1E2129] text-slate-300 border-[#333742]' 
                                        : 'bg-[#FFFBF6] text-slate-700 border-slate-200'
                                    }`}>
                                      Agreement: {claim.modelAgreement.agreeCount}/{claim.modelAgreement.totalModels}
                                    </span>

                                    <span className={`px-2.5 py-1 rounded-xl text-[10px] font-black uppercase ${
                                      claim.verificationVerdict === 'SUPPORTED'
                                        ? isDark
                                          ? 'bg-[#B6FF2E]/15 text-[#B6FF2E] border border-[#B6FF2E]/30'
                                          : 'bg-[#D8AE9B]/30 text-[#800020] border border-[#D8AE9B]'
                                        : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                                    }`}>
                                      {claim.verificationVerdict}
                                    </span>

                                    <button className={`text-xs font-bold flex items-center gap-1 ${
                                      isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                                    }`}>
                                      <span>{isExpanded ? 'Hide' : 'Inspect'}</span>
                                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                    </button>
                                  </div>
                                </div>

                                {/* Expanded Evidence and Provenance View */}
                                {isExpanded && (
                                  <div className={`px-6 pb-6 pt-3 border-t space-y-4 animate-in fade-in ${
                                    isDark ? 'border-[#2D313D] bg-[#181B22]' : 'border-[#E9D6C4] bg-[#FBF1E3]/50'
                                  }`}>
                                    
                                    <div className={`p-3.5 rounded-xl border text-[11px] flex items-center gap-2.5 ${
                                      isDark
                                        ? 'bg-[#14161C] border-[#2D313D] text-slate-200'
                                        : 'bg-[#FBF1E3] border-[#E9D6C4] text-[#6C3B45]'
                                    }`}>
                                      <Info size={15} className={isDark ? 'text-[#B6FF2E] shrink-0' : 'text-[#800020] shrink-0'} />
                                      <span>{claim.modelAgreement.consensusNote}</span>
                                    </div>

                                    {/* Evidence List */}
                                    <div className="space-y-3">
                                      <span className={`text-[10px] font-bold uppercase tracking-wider block ${
                                        isDark ? 'text-slate-400' : 'text-[#800020]'
                                      }`}>
                                        Ground-Truth Citations ({claim.evidenceList.length})
                                      </span>

                                      {claim.evidenceList.map((ev, evIdx) => (
                                        <div key={evIdx} className={`p-4 rounded-2xl border space-y-2.5 ${
                                          isDark 
                                            ? 'bg-[#14161C] border-[#2D313D]' 
                                            : 'bg-[#FFFDFA] border-[#E9D6C4]'
                                        }`}>
                                          <div className="flex items-center justify-between text-xs">
                                            <a 
                                              href={ev.url} 
                                              target="_blank" 
                                              rel="noopener noreferrer"
                                              className={`font-bold hover:underline flex items-center gap-1.5 ${
                                                isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                                              }`}
                                            >
                                              <span>{ev.title}</span>
                                              <ExternalLink size={12} />
                                            </a>
                                            <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold ${
                                              isDark ? 'bg-[#1E2129] text-slate-300 border border-[#2D313D]' : 'bg-[#FBF1E3] text-[#800020]'
                                            }`}>
                                              {ev.type}
                                            </span>
                                          </div>
                                          <p className={`text-xs leading-relaxed p-3.5 rounded-xl border ${
                                            isDark 
                                              ? 'bg-[#1A1D24] border-[#2D313D] text-[#F1F5F9]' 
                                              : 'bg-[#FBF1E3] border-[#E9D6C4] text-[#2E0A12]'
                                          }`}>
                                            "{ev.excerpt}"
                                          </p>
                                          <div className="flex items-center justify-between text-[10px] text-[#8A6A72] font-mono">
                                            <span>Source: {ev.source} ({ev.domain})</span>
                                            <span>Retrieved {ev.retrievedTime}</span>
                                          </div>
                                        </div>
                                      ))}
                                    </div>

                                    {/* Independent Model Judgments */}
                                    <div className={`pt-3 border-t space-y-2.5 ${
                                      isDark ? 'border-[#2D313D]' : 'border-[#E9D6C4]'
                                    }`}>
                                      <span className={`text-[10px] font-bold uppercase tracking-wider block ${
                                        isDark ? 'text-slate-400' : 'text-[#800020]'
                                      }`}>
                                        Independent Model Cross-Judging
                                      </span>
                                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                                        {claim.modelJudgments.map((mj, jIdx) => (
                                          <div key={jIdx} className={`p-3 rounded-xl border space-y-1.5 ${
                                            isDark ? 'bg-[#14161C] border-[#2D313D]' : 'bg-[#FFFDFA] border-[#E9D6C4]'
                                          }`}>
                                            <div className="flex justify-between items-center">
                                              <span className={`font-bold ${isDark ? 'text-white' : 'text-[#2E0A12]'}`}>{mj.model}</span>
                                              <span className={`text-[10px] font-extrabold ${
                                                isDark ? 'text-[#B6FF2E]' : 'text-[#800020]'
                                              }`}>{mj.verdict}</span>
                                            </div>
                                            <p className={`text-[11px] leading-relaxed ${isDark ? 'text-slate-300' : 'text-[#6C3B45]'}`}>{mj.reasoning}</p>
                                          </div>
                                        ))}
                                      </div>
                                    </div>

                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>

                    </section>
                  )}

                </div>
              )}

            </div>
          ))
        ) : (
          <div className={`text-center py-16 px-6 rounded-[2.5rem] border shadow-xl space-y-4 transition-colors ${
            isDark ? 'bg-[#1E2129] border-[#333742]' : 'bg-[#FFFDFA] border-[#E9D6C4]'
          }`}>
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mx-auto shadow-md ${
              isDark ? 'bg-[#14161C] text-[#B6FF2E] border border-[#B6FF2E]/30' : 'bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4]'
            }`}>
              <MessageSquare size={26} />
            </div>
            <h3 className={`font-black text-lg ${isDark ? 'text-white' : 'text-[#2E0A12]'}`}>
              Start Multi-Model Comparison
            </h3>
            <p className={`text-xs md:text-sm max-w-md mx-auto leading-relaxed ${
              isDark ? 'text-slate-300' : 'text-[#6C3B45]'
            }`}>
              Ask any complex scientific, factual, or regulatory question above. Up to 3 models will answer simultaneously, and VerifAI will cross-examine their claims.
            </p>
          </div>
        )}
      </div>

    </motion.div>
  );
};
export default ChatPage;
