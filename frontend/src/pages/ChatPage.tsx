import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowRight, CheckCircle2, CircleAlert, Clock3,
  ExternalLink, Eye, EyeOff, KeyRound, LoaderCircle, LockKeyhole,
  MessageSquareText, Plus, RefreshCw, Search, Send, ShieldCheck,
  Sparkles, Trash2
} from 'lucide-react';
import type { ChatMessage, Conversation, ModelResponse } from '../types';
import {
  providersApi,
  type ConnectedChatModel,
  type ConnectedChatModelsResponse,
} from '../api/providers';
import { chatApi, adaptBackendConversation, verificationApi } from '../api';

interface ChatPageProps {
  conversations: Conversation[];
  onAddConversation: (conv: Conversation) => void;
  onUpdateConversation: (conv: Conversation) => void;
  onDeleteConversation: (conversationId: string) => Promise<void>;
  onProvidersChanged?: () => Promise<void>;
  selected: string[];
  setSelected: React.Dispatch<React.SetStateAction<string[]>>;
  testedModels: Record<string, 'working' | 'failed'>;
  setTestedModels: React.Dispatch<React.SetStateAction<Record<string, 'working' | 'failed'>>>;
  theme?: 'light' | 'dark';
}

type ProviderId = 'prov-groq' | 'prov-openrouter' | 'prov-nvidia';
const PROVIDER_DETAILS: {
  id: ProviderId;
  label: string;
  hint: string;
  keyUrl: string;
}[] = [
  {
    id: 'prov-groq',
    label: 'Groq',
    hint: 'Low-latency models · account free-tier limits apply',
    keyUrl: 'https://console.groq.com/keys',
  },
  {
    id: 'prov-openrouter',
    label: 'OpenRouter',
    hint: 'Explicitly free :free model routes · rate limited',
    keyUrl: 'https://openrouter.ai/settings/keys',
  },
  {
    id: 'prov-nvidia',
    label: 'NVIDIA NIM',
    hint: 'Official hosted NVIDIA API · account usage and pricing apply',
    keyUrl: 'https://build.nvidia.com/',
  },
];

const palette = {
  card: 'rounded-2xl border border-[#74C69D] bg-[#FFFFFF] dark:border-[#333742] dark:bg-[#1E2129]',
  muted: 'text-[#356B52] dark:text-slate-400',
  heading: 'text-[#1B4332] dark:text-[#F7F9FC]',
  primary: 'bg-[#74C69D] text-[#102D21] hover:bg-[#8FD9B4] dark:bg-[#B6FF2E] dark:text-[#14161C] dark:hover:bg-[#a1e528]',
  outline: 'border border-[#74C69D] bg-[#D8F3DC] text-[#1B4332] hover:border-[#1B4332]/50 dark:border-[#333742] dark:bg-[#151820] dark:text-[#E7EEF7] dark:hover:border-[#B6FF2E]/50',
};

function modelKey(model: ConnectedChatModel): string {
  return model.provider + ':' + model.id;
}

function shortDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
}

function ProviderCard({
  config, status, onChanged,
}: {
  config: (typeof PROVIDER_DETAILS)[number];
  status?: ConnectedChatModelsResponse['providers'][number];
  onChanged: () => Promise<void>;
}) {
  const [expanded, setExpanded] = useState(false);
  const [secret, setSecret] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [pending, setPending] = useState<'saving' | 'testing' | 'removing' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const linked = Boolean(status?.keyMasked);
  const connected = status?.status === 'Connected';

  const saveAndCheck = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!secret.trim()) return;
    setPending('saving');
    setError(null);
    setFeedback(null);
    let saved = false;
    try {
      await providersApi.saveKey(config.id, { api_key: secret.trim() });
      saved = true;
      setSecret('');
      setShowSecret(false);
      setPending('testing');
      const result = await providersApi.testConnection(config.id);
      if (!result.success) {
        setError(result.message || 'Provider rejected the key.');
      } else {
        setFeedback('Key accepted. Connected models have been refreshed.');
        setExpanded(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save or verify the key.');
    } finally {
      if (saved) {
        // If validation fails, show the honest "Saved/Unavailable" state.
        await onChanged();
      }
      setPending(null);
    }
  };

  const testSaved = async () => {
    setPending('testing');
    setError(null);
    setFeedback(null);
    try {
      const result = await providersApi.testConnection(config.id);
      if (result.success) setFeedback('Connection verified.');
      else setError(result.message || 'Connection test failed.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not test this credential.');
    } finally {
      await onChanged();
      setPending(null);
    }
  };

  const remove = async () => {
    if (!window.confirm('Remove the saved ' + config.label + ' API key?')) return;
    setPending('removing');
    setError(null);
    try {
      await providersApi.unlinkKey(config.id);
      await onChanged();
      setFeedback('Key removed. This provider can no longer be used.');
      setExpanded(false);
      setSecret('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove the key.');
    } finally {
      setPending(null);
    }
  };

  return (
    <section className="rounded-xl border border-[#74C69D] bg-white/75 p-3.5 dark:border-[#343844] dark:bg-[#161922]">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className={'font-extrabold text-sm ' + palette.heading}>{config.label}</h3>
          <p className={'text-[11px] leading-relaxed mt-1 ' + palette.muted}>{config.hint}</p>
        </div>
        <span className={
          'text-[10px] font-bold rounded-full px-2 py-1 shrink-0 ' +
          (connected
            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-400/15 dark:text-emerald-300'
            : linked
              ? 'bg-amber-100 text-amber-800 dark:bg-amber-400/15 dark:text-amber-300'
              : 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-300')
        }>
          {connected ? 'Verified' : linked ? status?.status === 'Saved' ? 'Key saved' : 'Needs attention' : 'Not linked'}
        </span>
      </div>
      <p className={'mt-2 text-[11px] ' + palette.muted}>
        {connected
          ? String(status?.modelsCount ?? 0) + ' eligible models in catalog'
          : linked ? 'Credential stored; a successful test is required.' : 'Bring your own key to enable models.'}
      </p>
      {linked && <p className={'font-mono text-[11px] mt-1 ' + palette.muted}>Key: {status?.keyMasked}</p>}
      {status?.message && <p className="text-xs text-amber-700 dark:text-amber-300 mt-2">{status.message}</p>}
      {error && <p role="alert" className="text-xs text-rose-700 dark:text-rose-300 mt-2">{error}</p>}
      {feedback && <p role="status" className="text-xs text-emerald-700 dark:text-emerald-300 mt-2">{feedback}</p>}
      <div className="flex flex-wrap items-center gap-2 mt-3">
        <button
          type="button"
          disabled={Boolean(pending)}
          onClick={() => { setExpanded(!expanded); setError(null); }}
          className={'rounded-lg px-3 py-1.5 text-[11px] font-bold disabled:opacity-50 ' + palette.outline}
        >
          {linked ? 'Replace key' : 'Add API key'}
        </button>
        {linked && (
          <button type="button" disabled={Boolean(pending)} onClick={testSaved}
            className="text-[11px] font-bold text-[#1B4332] dark:text-[#B6FF2E] disabled:opacity-50">
            {pending === 'testing' ? 'Checking…' : 'Test'}
          </button>
        )}
        {linked && (
          <button type="button" disabled={Boolean(pending)} onClick={remove}
            aria-label={'Remove ' + config.label + ' API key'}
            className="text-rose-600 dark:text-rose-300 disabled:opacity-50">
            <Trash2 size={14} />
          </button>
        )}
      </div>
      {expanded && (
        <form onSubmit={saveAndCheck} className="space-y-2.5 mt-3 pt-3 border-t border-[#74C69D] dark:border-[#333742]">
          <label htmlFor={'key-' + config.id} className={'text-[11px] font-bold block ' + palette.heading}>
            {config.label} secret key
          </label>
          <div className="relative">
            <input
              id={'key-' + config.id} value={secret} required maxLength={512}
              type={showSecret ? 'text' : 'password'} autoComplete="off"
              onChange={event => setSecret(event.target.value)}
              placeholder="Paste your provider key"
              className="w-full bg-[#D8F3DC] border border-[#74C69D] dark:bg-[#101319] dark:border-[#404450] rounded-lg py-2 pl-2.5 pr-9 text-xs text-[#1B4332] dark:text-white outline-none focus:border-[#1B4332] dark:focus:border-[#B6FF2E]"
            />
            <button type="button" onClick={() => setShowSecret(!showSecret)} aria-label={showSecret ? 'Hide key' : 'Show key'}
              className="absolute right-2 top-2 text-slate-500 dark:text-slate-400">
              {showSecret ? <EyeOff size={15}/> : <Eye size={15}/>}
            </button>
          </div>
          <p className={'text-[10px] leading-relaxed ' + palette.muted}>
            Encrypted by the backend. Never included in model listings or chat responses.
          </p>
          <div className="flex items-center justify-between gap-2">
            <a href={config.keyUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[11px] text-[#1B4332] dark:text-[#B6FF2E] font-bold">
              Get a key <ExternalLink size={11}/>
            </a>
            <button type="submit" disabled={Boolean(pending) || !secret.trim()}
              className={'rounded-lg px-3 py-2 text-[11px] font-bold disabled:opacity-50 ' + palette.primary}>
              {pending ? 'Connecting…' : 'Save & test'}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}

export const ChatPage: React.FC<ChatPageProps> = ({
  conversations, onAddConversation, onUpdateConversation, onDeleteConversation,
  onProvidersChanged,
  selected, setSelected, testedModels, setTestedModels,
}) => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const [catalog, setCatalog] = useState<ConnectedChatModelsResponse | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [probeErrors, setProbeErrors] = useState<Record<string, string>>({});
  const [probingModel, setProbingModel] = useState<string | null>(null);
  const [autoSelecting, setAutoSelecting] = useState(false);
  const [autoFeedback, setAutoFeedback] = useState<string | null>(null);
  const [expandedResponse, setExpandedResponse] = useState<string | null>(null);
  const [modelSearch, setModelSearch] = useState('');
  const [freeOnly, setFreeOnly] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [sending, setSending] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState<string | null>(null);
  const [summarizing, setSummarizing] = useState<string | null>(null);
  const [verifiedForMessage, setVerifiedForMessage] = useState<Record<string, string>>({});
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const createdSessionIds = useRef(new Set<string>());
  const onProvidersChangedRef = useRef(onProvidersChanged);
  onProvidersChangedRef.current = onProvidersChanged;
  const testedModelsRef = useRef(testedModels);
  testedModelsRef.current = testedModels;

  const active = conversationId
    ? conversations.find(conv => conv.id === conversationId)
    : undefined;
  const models = catalog?.models || [];
  const known = useMemo(() => new Map(models.map(model => [modelKey(model), model])), [models]);
  const selectedModels = selected.map(key => known.get(key)).filter((model): model is ConnectedChatModel => Boolean(model));

  // Rank currently-discovered candidates, never invented or stale model IDs.
  // A successful live probe (not ranking alone) determines whether one is usable.
  const modelRank = (model: ConnectedChatModel): number => {
    const id = model.id.toLowerCase();
    const health = testedModels[modelKey(model)];
    const proven = health === 'working' ? 10000 : health === 'failed' ? -10000 : 0;
    const knownBest: Record<string, number> = {
      'openai/gpt-oss-120b': 950,
      'openai/gpt-oss-20b': 900,
      'qwen/qwen3.8-27b': 860,
      'google/gemma-4-31b-it:free': 830,
      'google/gemma-4-26b-a4b-it:free': 820,
      'nvidia/nemotron-3.5-lightning:free': 790,
      'meta/llama-3.3-70b-instruct': 760,
    };
    const retired = ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'].includes(id);
    return proven + (retired ? -2000 : 0) + (knownBest[id] || 0)
      + Math.min(model.contextWindow || 0, 131072) / 65536
      + (model.provider === 'groq' ? 60 : 0);
  };
  const eligibleModels = models.filter(model => !freeOnly || model.isFree);
  const shownModels = eligibleModels
    .filter(model => (model.name + ' ' + model.id + ' ' + model.provider)
      .toLowerCase().includes(modelSearch.toLowerCase()))
    .sort((a, b) => modelRank(b) - modelRank(a));
  const verifiedProviders = (catalog?.providers || []).filter(provider => provider.status === 'Connected').length;
  const displayProvider = (model: { provider: string; providerId?: string }) =>
    catalog?.providers.find(provider => provider.providerId === (model.providerId || model.provider))?.name
      || model.provider;
  const visibleMessages = active?.messages || [];

  const refreshModels = useCallback(async (clearTests = false) => {
    setAutoFeedback(null);
    setCatalogLoading(true);
    setCatalogError(null);
    try {
      const response = await providersApi.getConnectedChatModels();
      setCatalog(response);
      // Preserve working probes only across route changes for this logged-in
      // owner. User-initiated refresh or key changes require fresh probes.
      const valid = new Set(response.models.map(modelKey));
      if (clearTests) {
        setTestedModels({});
        setSelected([]);
      } else {
        const previouslyWorking = testedModelsRef.current;
        setTestedModels(current =>
          Object.fromEntries(Object.entries(current).filter(([key]) => valid.has(key)))
        );
        setSelected(current =>
          current.filter(key => valid.has(key) && previouslyWorking[key] === 'working')
        );
      }
      setProbeErrors({});
      // A secondary settings refresh must not erase an already valid catalog.
      try {
        await onProvidersChangedRef.current?.();
      } catch (err) {
        console.warn('Could not refresh provider settings:', err instanceof Error ? err.message : 'unknown error');
      }
    } catch (err) {
      setCatalogError(err instanceof Error ? err.message : 'Could not load connected models.');
    } finally {
      setCatalogLoading(false);
    }
  }, []);

  useEffect(() => { void refreshModels(); }, [refreshModels]);

  // A route loaded directly from History may have only a summary in memory.
  useEffect(() => {
    if (!conversationId || createdSessionIds.current.has(conversationId)) return;
    let valid = true;
    if (active && active.messages.length > 0) return;
    setLoadingHistory(true);
    setError(null);
    chatApi.getConversation(conversationId)
      .then(detail => { if (valid) onUpdateConversation(adaptBackendConversation(detail)); })
      .catch(err => { if (valid) setError(err instanceof Error ? err.message : 'Conversation not found.'); })
      .finally(() => { if (valid) setLoadingHistory(false); });
    return () => { valid = false; };
    // Load on navigation, not after each pending message update.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  const findWorkingModels = async () => {
    if (autoSelecting || sending || probingModel || catalogLoading) return;
    setAutoSelecting(true);
    setAutoFeedback(null);
    setError(null);
    // First sample providers independently; if some cannot answer, fill the
    // remaining lanes with other proven models on healthy providers.
    // Bounded at seven small, opt-in inference probes (quota may apply).
    const byProvider = new Map<string, ConnectedChatModel[]>();
    for (const model of [...eligibleModels].sort((a, b) => modelRank(b) - modelRank(a))) {
      if (testedModels[modelKey(model)] === 'failed') continue;
      const group = byProvider.get(model.provider) || [];
      if (group.length < 3) group.push(model);
      byProvider.set(model.provider, group);
    }
    const passed: ConnectedChatModel[] = [];
    const errors: string[] = [];
    const blockedProviders = new Set<string>();
    let probeCount = 0;
    try {
      for (let round = 0; round < 3 && passed.length < 3 && probeCount < 7; round++) {
        const candidates = [...byProvider.entries()]
          .sort(([a], [b]) => Number(passed.some(m => m.provider === b))
                                  - Number(passed.some(m => m.provider === a)))
          .filter(([provider]) => !blockedProviders.has(provider))
          .map(([, group]) => group[round])
          .filter((model): model is ConnectedChatModel => Boolean(model));
        for (let offset = 0; offset < candidates.length && passed.length < 3 && probeCount < 7; offset += 2) {
          const batch = candidates.slice(offset, offset + Math.min(2, 7 - probeCount));
          probeCount += batch.length;
          const tested = await Promise.all(batch.map(async model => {
            const key = modelKey(model);
            if (testedModels[key] === 'working') {
              return { model, working: true, message: '', errorCode: '' };
            }
            try {
              const result = await providersApi.probeChatModel(model);
              return {
                model, working: result.working, message: result.message || '',
                errorCode: result.error_code || '',
              };
            } catch (err) {
              return {
                model, working: false,
                message: err instanceof Error ? err.message : 'Probe unavailable.',
                errorCode: 'PROBE_REQUEST_FAILED',
              };
            }
          }));
          for (const item of tested) {
            const key = modelKey(item.model);
            setTestedModels(current => ({ ...current, [key]: item.working ? 'working' : 'failed' }));
            if (item.working) {
              passed.push(item.model);
            } else {
              setProbeErrors(current => ({ ...current, [key]: item.message }));
              errors.push(item.model.provider + ': ' + item.message);
              const providerWide = ['HTTP_401', 'HTTP_402', 'HTTP_403', 'HTTP_429',
                'NETWORK_FAILURE', 'CREDENTIAL_UNREADABLE', 'PROBE_REQUEST_FAILED'].includes(item.errorCode)
                || /rate.limit|quota|network|credential|cannot be reached/i.test(item.message);
              if (providerWide) blockedProviders.add(item.model.provider);
            }
          }
        }
      }
      const best = passed.sort((a, b) => modelRank(b) - modelRank(a)).slice(0, 3);
      setSelected(best.map(modelKey));
      const summary = best.length
        ? best.length + ' working model' + (best.length === 1 ? '' : 's')
          + ' selected after real inference checks. Only these models will receive your chat prompt.'
        : 'No models passed inference testing. Check your provider quotas, endpoint access and the failures below.';
      setAutoFeedback(summary);
      if (!best.length && errors.length) setError(errors.slice(0, 3).join(' · '));
    } finally {
      setAutoSelecting(false);
    }
  };

  const toggleModel = async (key: string) => {
    if (probingModel || autoSelecting || sending) return;
    if (selected.includes(key)) {
      setSelected(current => current.filter(item => item !== key));
      return;
    }
    if (selected.length >= 3) {
      setError('Remove a selected model before adding another.');
      return;
    }
    const model = known.get(key);
    if (!model) return;
    // Only an actual, nonempty completion counts as a working model.
    if (testedModels[key] === 'working') {
      setSelected(current => current.length < 3 ? [...current, key] : current);
      return;
    }
    setProbingModel(key);
    setError(null);
    setProbeErrors(current => ({ ...current, [key]: '' }));
    try {
      const result = await providersApi.probeChatModel(model);
      if (!result.working) {
        setTestedModels(current => ({ ...current, [key]: 'failed' }));
        setProbeErrors(current => ({
          ...current, [key]: result.message || 'Model could not generate a response.',
        }));
        return;
      }
      setTestedModels(current => ({ ...current, [key]: 'working' }));
      setSelected(current => current.includes(key) || current.length >= 3
        ? current : [...current, key]);
    } catch (err) {
      setTestedModels(current => ({ ...current, [key]: 'failed' }));
      setProbeErrors(current => ({
        ...current, [key]: err instanceof Error ? err.message : 'Model test failed.',
      }));
    } finally {
      setProbingModel(null);
    }
  };

  const deleteConversation = async (id: string) => {
    if (sending || deleting || !window.confirm('Permanently delete this chat and all its saved messages?')) return;
    setDeleting(id);
    setError(null);
    try {
      await onDeleteConversation(id);
      createdSessionIds.current.delete(id);
      if (conversationId === id) navigate('/chat', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete the conversation.');
    } finally {
      setDeleting(null);
    }
  };

  useEffect(() => {
    if (messagesEndRef.current && !loadingHistory) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [visibleMessages.length, loadingHistory]);

  const newConversation = async () => {
    if (sending || creating) return;
    setCreating(true);
    setError(null);
    try {
      const created = await chatApi.createConversation('New Multi-Model Session');
      createdSessionIds.current.add(created.id);
      onAddConversation({
        id: created.id, title: created.title, updatedAt: created.updated_at,
        messageCount: 0, models: selected, messages: [],
      });
      navigate('/chat/' + created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start a conversation.');
    } finally {
      setCreating(false);
    }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const text = prompt.trim();
    if (!text || sending || creating || summarizing) return;
    // Defensive UI check; the authoritative blocking gate runs in FastAPI.
    if (/-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:gsk_|nvapi-|sk-(?:or-v1-|proj-)?|gh[pousr]_|AIzaSy)[\w-]{12,}|\bBearer\s+[\w.-]{18,}|\b(?:api[_ -]?key|password|client[_ -]?secret|access[_ -]?token)\b\s*[:=]\s*[\w!@#$%^&*.-]{8,}/i.test(text)) {
      setError('Possible credential detected. Remove passwords, API keys and tokens before sending.');
      return;
    }
    if (catalogError) {
      setError('Refresh connected models successfully before sending a new prompt.');
      return;
    }
    if (!selectedModels.length) {
      setError('Connect and select at least one model before sending a prompt.');
      return;
    }
    setSending(true);
    setError(null);
    let base = active;
    let optimistic: Conversation | undefined;
    let attemptedSend = false;
    try {
      const backendModels = selectedModels.map(model => ({
        provider: model.provider, model_name: model.id,
      }));
      if (!base) {
        setCreating(true);
        const created = await chatApi.createConversation(text.slice(0, 58));
        base = {
          id: created.id, title: created.title, updatedAt: created.updated_at,
          messageCount: 0, models: selected, messages: [],
        };
        createdSessionIds.current.add(created.id);
        onAddConversation(base);
        navigate('/chat/' + created.id);
        setCreating(false);
      }

      const userMessage: ChatMessage = {
        id: 'pending-user-' + Date.now(), sender: 'user',
        content: text, timestamp: 'Just now',
      };
      const pendingMessage: ChatMessage = {
        id: 'pending-reply-' + Date.now(), sender: 'assistant',
        content: '', timestamp: 'Just now',
        modelResponses: selectedModels.map(model => ({
          model: model.name, provider: model.provider, text: '',
          status: 'Running' as const,
        })),
      };
      optimistic = {
        ...base, updatedAt: 'Just now', models: selected,
        title: base.messages.length ? base.title : text.slice(0, 58),
        messages: [...base.messages, userMessage, pendingMessage],
        messageCount: base.messages.length + 2,
      };
      onUpdateConversation(optimistic);
      setPrompt('');
      attemptedSend = true;
      const result = await chatApi.sendMessage(base.id, {
        prompt: text, models: backendModels,
        verify: true,
      });
      const responses: ModelResponse[] = result.runs.map(run => {
        const entry = selectedModels.find(model => model.id === run.model_name && model.provider === run.provider);
        return {
          model: entry?.name || run.model_name, provider: run.provider,
          text: run.response || '',
          status: run.status === 'COMPLETED' ? 'Completed' as const
            : run.status === 'FAILED' ? 'Failed' as const : 'Unavailable' as const,
          latencyMs: run.latency_ms == null ? undefined : Math.round(run.latency_ms),
          errorReason: run.error_message || undefined,
        };
      });
      // Do not keep silently resending to endpoints that just failed.
      const failedKeys = new Set(result.runs
        .filter(run => run.status !== 'COMPLETED' || !(run.response || '').trim())
        .map(run => run.provider + ':' + run.model_name));
      if (failedKeys.size) {
        setTestedModels(current => Object.fromEntries([
          ...Object.entries(current).filter(([key]) => !failedKeys.has(key)),
          ...[...failedKeys].map(key => [key, 'failed' as const]),
        ]));
        setSelected(current => current.filter(key => !failedKeys.has(key)));
        setAutoFeedback('Unresponsive models were removed from the active selection. Retest or use Find working models.');
      }
      const finalResponse: ChatMessage = {
        ...pendingMessage,
        id: result.user_message_id + '-responses',
        synthesis: result.synthesis || undefined,
        modelResponses: responses.length ? responses : [{
          model: 'Provider', provider: 'backend', text: '',
          status: 'Unavailable', errorReason: 'The backend returned no model results.',
        }],
      };
      onUpdateConversation({
        ...optimistic,
        messages: [...optimistic.messages.slice(0, -1), finalResponse],
      });
    } catch (err) {
      const detail = err instanceof Error ? err.message : 'Prompt generation failed.';
      setError(detail);
      if (!attemptedSend) setPrompt(text);
      else if (optimistic) {
        onUpdateConversation({
          ...optimistic,
          messages: optimistic.messages.map((message, index) => (
            index === optimistic!.messages.length - 1
              ? {
                  ...message,
                  modelResponses: (message.modelResponses || []).map(model => ({
                    ...model, status: 'Failed' as const, errorReason: detail,
                  })),
                }
              : message
          )),
        });
      }
    } finally {
      setSending(false);
      setCreating(false);
    }
  };

  const summarizeResponse = async (message: ChatMessage) => {
    if (summarizing || sending || !active || !message.id.endsWith('-responses') || message.synthesis) return;
    const successful = (message.modelResponses || []).some(model =>
      model.status === 'Completed' && model.text.trim());
    if (!successful) return;
    setSummarizing(message.id);
    setError(null);
    try {
      const summary = await chatApi.summarizeResponses(
        active.id, message.id.slice(0, -'-responses'.length),
      );
      // Update this response in-place; other model answers remain unchanged.
      onUpdateConversation({
        ...active,
        messages: active.messages.map(item =>
          item.id === message.id ? { ...item, synthesis: summary } : item),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to summarize these responses.');
    } finally {
      setSummarizing(null);
    }
  };

  const verifyResponse = async (message: ChatMessage) => {
    if (verifying) return;
    const responses = (message.modelResponses || [])
      .filter(model => model.status === 'Completed' && model.text.trim());
    if (!responses.length) return;
    setVerifying(message.id);
    setError(null);
    try {
      const result = await verificationApi.createVerification({
        input_text: responses.map(model => model.provider + '/' + model.model + ': ' + model.text).join('\n\n'),
        options: { use_knowledge_base: true, use_web_evidence: true },
      });
      setVerifiedForMessage(current => ({ ...current, [message.id]: result.id }));
      navigate('/verification/' + result.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to verify this response.');
    } finally {
      setVerifying(null);
    }
  };

  return (
    <div data-testid="chat-workspace-root" className="space-y-5 pb-12 w-full min-w-0 max-w-none">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className={'uppercase text-[11px] font-extrabold tracking-[.16em] mb-1.5 ' + palette.muted}>
            Workspace / Multi-model intelligence
          </p>
          <div className="flex flex-wrap gap-3 items-center">
            <h1 className={'text-2xl md:text-3xl tracking-tight font-black ' + palette.heading}>AI Chat Workspace</h1>
            <span className={'text-[11px] font-bold flex items-center gap-1.5 px-2.5 py-1 rounded-full ' +
              (verifiedProviders
                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300'
                : 'bg-[#F5EDE4] text-[#356B52] dark:bg-[#272B36] dark:text-slate-400')
            }>
              <span className={'w-1.5 h-1.5 rounded-full ' + (verifiedProviders ? 'bg-emerald-500' : 'bg-slate-400')} />
              {verifiedProviders ? verifiedProviders + ' verified providers' : 'No verified provider'}
            </span>
          </div>
          <p className={'mt-2 text-sm leading-relaxed ' + palette.muted}>
            Compare real model responses using your own encrypted provider keys.
          </p>
        </div>
        <button onClick={newConversation} disabled={sending || creating}
          className={'inline-flex items-center gap-2 rounded-xl px-4 py-2.5 font-extrabold text-xs disabled:opacity-50 ' + palette.primary}>
          {creating ? <LoaderCircle size={16} className="animate-spin"/> : <Plus size={16}/>}
          New Multi-Model Session
        </button>
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-300 bg-rose-50 dark:border-rose-700 dark:bg-rose-950/30 p-3 text-sm text-rose-800 dark:text-rose-200 flex items-start gap-2">
        <CircleAlert size={17} className="shrink-0 mt-0.5"/>{error}
      </div>}
      {catalogError && <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/30 p-3 text-xs text-amber-900 dark:text-amber-200 flex items-center justify-between gap-3">
        <span>Could not discover connected models: {catalogError}</span>
        <button onClick={() => void refreshModels(true)} className="font-bold underline">Retry</button>
      </div>}

      <div className="grid grid-cols-1 xl:grid-cols-[276px_minmax(0,1fr)] gap-5 items-start">
        <aside className="space-y-4 xl:sticky xl:top-20">
          <section className={palette.card + ' p-4'}>
            <div className="flex justify-between items-center gap-2 mb-3">
              <h2 className={'text-sm font-extrabold flex items-center gap-2 ' + palette.heading}>
                <MessageSquareText size={16}/> Conversations
              </h2>
              <span className={'text-xs font-mono ' + palette.muted}>{conversations.length}</span>
            </div>
            {conversations.length ? (
              <nav aria-label="Saved chat conversations" className="space-y-1 max-h-48 overflow-y-auto">
                {conversations.map(item => (
                  <div key={item.id} className={'group flex gap-1 items-center rounded-xl ' +
                    (conversationId === item.id
                      ? 'bg-[#1B4332] text-white dark:bg-[#B6FF2E] dark:text-[#14161C]'
                      : 'text-[#356B52] hover:bg-[#D8F3DC] dark:text-slate-300 dark:hover:bg-[#2A2E38]')}>
                    <Link to={'/chat/' + item.id}
                      className="min-w-0 flex-1 flex items-center gap-2 px-2.5 py-2 text-xs font-semibold">
                      <MessageSquareText size={14} className="shrink-0"/>
                      <span className="truncate">{item.title}</span>
                    </Link>
                    <button type="button" disabled={sending || Boolean(deleting)}
                      onClick={() => void deleteConversation(item.id)}
                      aria-label={'Delete conversation ' + item.title}
                      title="Delete conversation"
                      className="shrink-0 rounded-lg p-2 mx-1 opacity-60 hover:opacity-100 focus:opacity-100 disabled:opacity-30">
                      {deleting === item.id ? <LoaderCircle size={13} className="animate-spin"/> : <Trash2 size={13}/>}
                    </button>
                  </div>
                ))}
              </nav>
            ) : <p className={'text-xs leading-relaxed ' + palette.muted}>Your conversations will appear here once created.</p>}
          </section>

          <section className={palette.card + ' p-4 space-y-3'}>
            <div className="flex justify-between items-center gap-2">
              <h2 className={'text-sm font-extrabold flex items-center gap-2 ' + palette.heading}>
                <LockKeyhole size={16}/> BYOK connections
              </h2>
              <button onClick={() => void refreshModels(true)} aria-label="Refresh connected model list" title="Refresh connections"
                disabled={catalogLoading} className="p-1.5 rounded-md text-[#1B4332] dark:text-[#B6FF2E] disabled:opacity-50">
                <RefreshCw size={15} className={catalogLoading ? 'animate-spin' : ''}/>
              </button>
            </div>
            <p className={'text-[11px] leading-relaxed ' + palette.muted}>
              Verify your Groq, OpenRouter or NVIDIA/custom key before testing models.
            </p>
            {PROVIDER_DETAILS.map(config => (
              <ProviderCard
                key={config.id}
                config={config}
                status={catalog?.providers.find(item => item.providerId === config.id)}
                onChanged={() => refreshModels(true)}
              />
            ))}
            {(catalog?.providers || []).filter(item => item.providerId.startsWith('prov-custom-')).map(item => (
              <section key={item.providerId} className="rounded-xl border border-[#74C69D] bg-white/75 dark:border-[#343844] dark:bg-[#161922] p-3.5 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <strong className={'text-sm break-words ' + palette.heading}>{item.name}</strong>
                  <span className={'text-[10px] font-bold rounded-full px-2 py-1 ' +
                    (item.status === 'Connected' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800')}>
                    {item.status === 'Connected' ? 'Verified' : item.status}
                  </span>
                </div>
                <p className={'text-[11px] ' + palette.muted}>
                  {item.status === 'Connected'
                    ? item.modelsCount + ' supported models in catalog · test a model before use'
                    : item.message || 'Test this provider from Workspace Settings to enable models.'}
                </p>
                <Link to="/settings/providers" className="text-xs font-bold text-[#1B4332] dark:text-[#B6FF2E] inline-flex items-center gap-1">
                  Manage custom connection <ArrowRight size={12}/>
                </Link>
              </section>
            ))}
            {(catalog?.providers || [])
              .filter(item =>
                !['prov-groq', 'prov-openrouter', 'prov-nvidia'].includes(item.providerId) &&
                !item.providerId.startsWith('prov-custom-') &&
                item.status !== 'Not Connected'
              )
              .map(item => (
                <div key={item.providerId} className={'rounded-xl border p-3 ' + palette.outline}>
                  <div className="flex items-center justify-between gap-2">
                    <strong className={'text-xs break-words ' + palette.heading}>{item.name}</strong>
                    <span className={
                      'text-[10px] rounded-full px-2 py-0.5 font-bold ' +
                      (item.status === 'Connected' ? 'text-emerald-700 bg-emerald-100'
                        : 'text-amber-800 bg-amber-100')
                    }>{item.status}</span>
                  </div>
                  <p className={'mt-1 text-[11px] ' + palette.muted}>
                    {item.modelsCount} discovered models · only working tests are selectable
                  </p>
                </div>
              ))}
            <Link to="/settings/providers"
              className="flex items-center justify-center gap-2 rounded-lg py-2 text-[11px] font-bold text-[#1B4332] dark:text-[#B6FF2E]">
              Manage all providers <ArrowRight size={13}/>
            </Link>
          </section>
        </aside>

        <main className="space-y-4 min-w-0">
          <section className={palette.card + ' p-4 md:p-5 space-y-4'}>
            <div className="flex flex-wrap gap-3 justify-between items-start">
              <div>
                <h2 className={'text-base font-extrabold flex items-center gap-2 ' + palette.heading}>
                  <Sparkles size={17}/> Connected models
                </h2>
                <p className={'text-xs mt-1 ' + palette.muted}>
                  Probe real text completions, then chat with only working models. Provider quota and charges may apply.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button type="button" onClick={() => void findWorkingModels()}
                  disabled={autoSelecting || Boolean(probingModel) || sending || catalogLoading || !eligibleModels.length}
                  aria-label="Find working models"
                  className={'inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-bold disabled:opacity-50 ' + palette.primary}>
                  {autoSelecting ? <LoaderCircle size={14} className="animate-spin"/> : <ShieldCheck size={14}/>}
                  {autoSelecting ? 'Testing best models…' : 'Find working models'}
                </button>
                <span className={'rounded-full px-2.5 py-1 text-[11px] font-bold ' + palette.outline}>
                  {selectedModels.length} / 3 selected
                </span>
              </div>
            </div>
            {autoFeedback && <p role="status" className={'rounded-lg px-3 py-2 text-xs bg-[#D8F3DC] dark:bg-[#17251E] ' + palette.heading}>{autoFeedback}</p>}
            <div className="flex flex-wrap gap-2 items-center">
              <div className="relative flex-1 min-w-[150px]">
                <Search className="absolute left-3 top-2.5 text-slate-400" size={15}/>
                <input aria-label="Search connected models" value={modelSearch} onChange={event => setModelSearch(event.target.value)}
                  placeholder="Search connected models…"
                  className="w-full rounded-xl border border-[#74C69D] bg-[#D8F3DC] dark:border-[#333742] dark:bg-[#11151C] text-sm px-9 py-2 text-[#1B4332] dark:text-white outline-none focus:border-[#1B4332] dark:focus:border-[#B6FF2E]"/>
              </div>
              <label className={'inline-flex items-center gap-1.5 text-xs font-bold select-none ' + palette.muted}>
                <input type="checkbox" checked={freeOnly} onChange={event => setFreeOnly(event.target.checked)}
                  className="accent-[#1B4332] dark:accent-[#B6FF2E]"/>
                OpenRouter free only
              </label>
            </div>

            {catalogLoading ? <p role="status" className={'text-xs py-5 flex items-center gap-2 ' + palette.muted}>
              <LoaderCircle size={15} className="animate-spin"/> Discovering available models…
            </p> : shownModels.length ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 2xl:grid-cols-3 gap-2.5 max-h-[255px] overflow-y-auto pr-1">
                {shownModels.map(model => {
                  const key = modelKey(model);
                  const activeSelection = selected.includes(key);
                  const blocked = !activeSelection && (selected.length >= 3 || Boolean(probingModel) || sending);
                  const isTesting = probingModel === key;
                  const probeStatus = testedModels[key];
                  return (
                    <button
                      key={key} type="button" disabled={blocked}
                      onClick={() => void toggleModel(key)}
                      aria-pressed={activeSelection}
                      aria-label={(activeSelection ? 'Remove ' : probeStatus === 'working' ? 'Select ' : 'Test and select ') + model.name + ' from ' + model.provider}
                      className={
                        'rounded-xl border p-3 text-left transition-colors disabled:opacity-50 ' +
                        (activeSelection
                          ? 'border-[#1B4332] bg-[#F8E8E6] dark:border-[#B6FF2E] dark:bg-[#B6FF2E]/10'
                          : 'border-[#74C69D] hover:border-[#1B4332]/50 dark:border-[#3B404C] dark:hover:border-[#B6FF2E]/50')
                      }
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className={'uppercase tracking-wide text-[10px] font-black ' + palette.muted}>{displayProvider(model)}</span>
                        {isTesting ? <LoaderCircle size={15} className="animate-spin text-[#1B4332]"/>
                          : activeSelection ? <CheckCircle2 size={15} className="text-[#1B4332] dark:text-[#B6FF2E]"/>
                          : probeStatus === 'working' ? <ShieldCheck size={15} className="text-emerald-600"/>
                          : <span className="w-3.5 h-3.5 rounded-full border border-slate-400"/>}
                      </div>
                      <strong className={'mt-1.5 text-xs block break-words ' + palette.heading}>{model.name}</strong>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        {model.isFree ? <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-400/15 dark:text-emerald-300 text-[10px] font-black">FREE ROUTE</span>
                          : <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-400/15 dark:text-amber-300 text-[10px] font-bold">ACCOUNT QUOTA</span>}
                        {model.contextWindow > 0 && <span className={'text-[10px] ' + palette.muted}>{Math.round(model.contextWindow / 1000)}k context</span>}
                        <span className={'rounded px-1.5 py-0.5 text-[10px] font-extrabold ' +
                          (probeStatus === 'working' ? 'bg-emerald-100 text-emerald-800'
                            : probeStatus === 'failed' ? 'bg-rose-100 text-rose-800'
                            : 'bg-slate-100 text-slate-700')}>
                          {isTesting ? 'TESTING LIVE…' : activeSelection ? 'WORKING · SELECTED'
                            : probeStatus === 'working' ? 'WORKING · ADD'
                            : probeStatus === 'failed' ? 'FAILED · RETEST'
                            : 'TEST & SELECT'}
                        </span>
                      </div>
                      {probeErrors[key] && <p className="text-[11px] mt-2 text-rose-700 break-words">{probeErrors[key]}</p>}
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-[#D8BBAF] dark:border-[#3B404C] px-4 py-7 text-center">
                <KeyRound size={21} className="mx-auto text-[#1B4332] dark:text-[#B6FF2E] mb-2"/>
                <p className={'text-sm font-bold ' + palette.heading}>
                  {models.length ? 'No models match your filter' : 'Connect your first model'}
                </p>
                <p className={'text-xs mt-1 ' + palette.muted}>
                  {models.length
                    ? 'Change the search or free-route filter.'
                    : 'Connect Groq, OpenRouter or NVIDIA NIM, then test a model.'}
                </p>
              </div>
            )}
            <p className={'text-[11px] leading-relaxed ' + palette.muted}>
              Model availability and quotas may change. Selected third-party providers receive your prompts and return their responses according to their own terms; do not submit secrets. A verified key does not guarantee unlimited free inference.
            </p>
          </section>

          <section data-testid="selected-models-workspace" className={palette.card + ' p-4 md:p-5 space-y-3'}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className={'text-base font-extrabold flex items-center gap-2 ' + palette.heading}>
                  <ShieldCheck size={18}/> Selected & tested models
                </h2>
                <p className={'text-xs mt-1 ' + palette.muted}>
                  Dedicated inference lanes for one prompt. Each added model passed a real completion check.
                </p>
              </div>
              <span className={'rounded-full px-3 py-1.5 text-xs font-bold ' + palette.outline}>
                {selectedModels.length} of 3 ready
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {Array.from({ length: 3 }, (_, index) => {
                const model = selectedModels[index];
                return (
                  <div key={modelKey(model || { provider: 'groq', id: 'empty-'+index } as ConnectedChatModel)}
                    className={'min-w-0 rounded-xl border p-4 ' + (model
                      ? 'border-emerald-300 bg-emerald-50/70 dark:bg-emerald-900/15 dark:border-emerald-600/50'
                      : 'border-dashed border-[#DBD0C2] bg-[#FBF7F1]/60 dark:border-[#43434D] dark:bg-[#1A1D24]')}>
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className={'text-[10px] uppercase tracking-widest font-black ' + palette.muted}>MODEL {index+1}</span>
                      {model ? <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-300">TESTED · READY</span>
                        : <span className={'text-[10px] font-bold ' + palette.muted}>UNASSIGNED</span>}
                    </div>
                    {model ? <>
                      <strong className={'text-sm block break-words leading-snug ' + palette.heading}>{model.name}</strong>
                      <p className={'text-[11px] mt-1 uppercase ' + palette.muted}>{displayProvider(model)}</p>
                      <button type="button" onClick={() => void toggleModel(modelKey(model))}
                        disabled={sending} className="text-xs font-bold text-[#1B4332] dark:text-[#B6FF2E] mt-3 disabled:opacity-50">Remove</button>
                    </> : <p className={'text-xs leading-relaxed ' + palette.muted}>Test a model in the catalog above to place it here.</p>}
                  </div>
                );
              })}
            </div>
          </section>

          <section className={palette.card + ' overflow-hidden'}>
            <div className="px-4 md:px-5 py-3.5 border-b border-[#74C69D] dark:border-[#333742] flex items-center justify-between gap-2">
              <div className="min-w-0">
                <h2 className={'font-extrabold text-sm truncate ' + palette.heading}>
                  {active?.title || 'New conversation'}
                </h2>
                <p className={'text-[11px] mt-0.5 ' + palette.muted}>
                  {active ? 'Saved conversation · ' + shortDate(active.updatedAt) : 'Start a new, persistent session'}
                </p>
              </div>
              <span className={'flex items-center gap-1.5 text-[11px] font-semibold ' + palette.muted}>
                <LockKeyhole size={15}/> Encrypted BYOK
              </span>
            </div>

            <div aria-live="polite" className="min-h-[300px] max-h-[540px] overflow-y-auto px-4 md:px-5 py-5 space-y-5">
              {loadingHistory ? <p role="status" className={'flex items-center gap-2 text-sm ' + palette.muted}>
                <LoaderCircle size={16} className="animate-spin"/> Loading saved messages…
              </p> : visibleMessages.length ? visibleMessages.map(message => (
                <div key={message.id} className={message.sender === 'user' ? 'flex justify-end' : 'w-full'}>
                  {message.sender === 'user' ? (
                    <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-[#1B4332] dark:bg-[#B6FF2E] text-white dark:text-[#14161C] px-4 py-3">
                      <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">{message.content}</p>
                      <span className="block text-right text-[10px] opacity-70 mt-2">{message.timestamp}</span>
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      <p className={'font-extrabold text-[11px] flex items-center gap-1.5 ' + palette.muted}>
                        <Sparkles size={14}/> Model responses
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-3">
                        {(message.modelResponses || []).map((model, index) => (
                          <article key={message.id + '-' + index}
                            className={'rounded-xl border border-[#74C69D] bg-[#FBF7F1] dark:border-[#3A3E49] dark:bg-[#171B23] p-4 space-y-3 min-w-0 ' +
                              (expandedResponse === message.id + '-' + index
                                ? 'md:col-span-2 2xl:col-span-3' : '')}>
                            <div className="flex flex-wrap justify-between items-start gap-2">
                              <div>
                                <strong className={'text-xs block break-words ' + palette.heading}>
                        {known.get(model.provider + ':' + model.model)?.name || model.model}
                      </strong>
                                <span className={'text-[11px] uppercase font-bold tracking-wide ' + palette.muted}>{displayProvider(model)}</span>
                              </div>
                              <div className="flex items-center flex-wrap gap-2">
                                <button type="button"
                                  onClick={() => setExpandedResponse(
                                    current => current === message.id + '-' + index
                                      ? null : message.id + '-' + index
                                  )}
                                  aria-label={(expandedResponse === message.id + '-' + index
                                    ? 'Compact ' : 'Expand ') + model.model + ' model response'}
                                  className={'rounded-md px-2 py-1 text-[11px] font-bold ' + palette.outline}>
                                  {expandedResponse === message.id + '-' + index ? 'Compact' : 'Expand'}
                                </button>
                              <span className={
                                'rounded-full text-[10px] font-bold px-2 py-1 ' +
                                (model.status === 'Completed'
                                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300'
                                  : model.status === 'Running'
                                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-500/15 dark:text-blue-300'
                                    : 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300')
                              }>
                                {model.status === 'Running' ? 'Generating…' : model.status}
                              </span>
                              </div>
                            </div>
                            {model.text ? (
                              <p className={'text-sm whitespace-pre-wrap break-words leading-relaxed ' + palette.heading}>{model.text}</p>
                            ) : model.status === 'Running' ? (
                              <p role="status" className={'flex items-center gap-2 text-xs ' + palette.muted}><LoaderCircle size={14} className="animate-spin"/> Waiting for provider response…</p>
                            ) : <p className={'text-xs ' + palette.muted}>No response returned.</p>}
                            {model.errorReason && <p role="alert" className="text-xs text-rose-700 dark:text-rose-300 break-words">{model.errorReason}</p>}
                            {model.latencyMs != null && <span className={'text-[11px] flex items-center gap-1 ' + palette.muted}><Clock3 size={12}/>{model.latencyMs}ms</span>}
                          </article>
                        ))}
                      </div>
                      {message.synthesis && (
                        <section data-testid="combined-summary"
                          className="rounded-2xl border border-[#74C69D] bg-[#D8F3DC]/65 dark:border-[#8DB65D]/60 dark:bg-[#171F1A] p-4 md:p-5 space-y-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <h3 className={'text-base font-black flex items-center gap-2 ' + palette.heading}>
                              <Sparkles size={18}/> Combined summary
                            </h3>
                            <span className={'text-[10px] font-bold ' + palette.muted}>AI-generated · not independently verified</span>
                          </div>
                          <p className={'text-xs ' + palette.muted}>
                            Combined from {message.synthesis.source_models.length} completed model response(s).
                            Check important claims using Verify.
                          </p>
                          <div className={'whitespace-pre-wrap break-words text-sm leading-7 ' + palette.heading}>
                            {message.synthesis.text}
                          </div>
                        </section>
                      )}
                      {(message.modelResponses || []).some(model => model.status === 'Completed' && model.text.trim()) && (
                        <div className="flex flex-wrap items-center gap-2">
                          <button type="button" data-testid="summarize-response"
                            disabled={Boolean(summarizing) || sending || Boolean(message.synthesis) || !active}
                            onClick={() => void summarizeResponse(message)}
                            className={'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-bold disabled:opacity-50 ' + palette.outline}>
                            {summarizing === message.id ? <LoaderCircle size={14} className="animate-spin"/> : <Sparkles size={14}/>}
                            {summarizing === message.id ? 'Summarizing…' : message.synthesis ? 'Summarized' : 'Summarize'}
                          </button>
                          <button type="button" disabled={Boolean(verifying)} onClick={() => void verifyResponse(message)}
                            className={'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-bold disabled:opacity-50 ' + palette.outline}>
                            {verifying === message.id ? <LoaderCircle size={14} className="animate-spin"/> : <ShieldCheck size={14}/>}
                            {verifying === message.id ? 'Verifying…' : 'Verify this response'}
                          </button>
                          {verifiedForMessage[message.id] && (
                            <Link to={'/verification/' + verifiedForMessage[message.id]}
                              className="text-xs font-bold text-[#1B4332] dark:text-[#B6FF2E]">View verification <ArrowRight size={12} className="inline"/></Link>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )) : (
                <div className="min-h-[280px] flex flex-col justify-center items-center text-center px-4">
                  <div className="h-14 w-14 rounded-2xl flex items-center justify-center bg-[#F3E3DB] dark:bg-[#B6FF2E]/10 text-[#1B4332] dark:text-[#B6FF2E] mb-4">
                    <MessageSquareText size={26}/>
                  </div>
                  <h3 className={'text-lg font-extrabold ' + palette.heading}>One prompt. Independent responses.</h3>
                  <p className={'text-sm mt-2 max-w-md leading-relaxed ' + palette.muted}>
                    Choose one to three tested models and send your prompt. Compare their independent answers, then click Summarize to combine them whenever you want.
                  </p>
                </div>
              )}
              <div ref={messagesEndRef} aria-hidden="true" />
            </div>

            <form onSubmit={submit} className="px-4 md:px-5 py-4 border-t border-[#74C69D] dark:border-[#333742]">
              <label htmlFor="byok-chat-prompt" className={'text-xs font-extrabold block mb-2 ' + palette.heading}>
                Your message
              </label>
              <textarea
                id="byok-chat-prompt" aria-label="Chat prompt" value={prompt} maxLength={20000}
                onChange={event => setPrompt(event.target.value)}
                onKeyDown={event => {
                  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
                placeholder="Ask anything…"
                rows={3}
                className="w-full resize-y rounded-xl border border-[#74C69D] bg-[#D8F3DC] dark:border-[#333742] dark:bg-[#12161F] text-sm text-[#1B4332] dark:text-white p-3.5 outline-none focus:border-[#1B4332] dark:focus:border-[#B6FF2E]"
              />
              <div className="mt-3 flex flex-wrap justify-between items-center gap-3">
                <div className={'flex flex-wrap items-center gap-3 text-[11px] ' + palette.muted}>
                  <span>{prompt.length} / 20,000</span>
                  <span>Ctrl / ⌘ + Enter to send</span>
                </div>
                <button type="submit" disabled={sending || creating || Boolean(summarizing) || Boolean(catalogError) || !prompt.trim() || !selectedModels.length}
                  className={'rounded-xl px-5 py-2.5 text-xs font-black inline-flex gap-2 items-center disabled:opacity-50 disabled:cursor-not-allowed ' + palette.primary}>
                  {sending ? <LoaderCircle size={16} className="animate-spin"/> : <Send size={16}/>}
                  {sending ? 'Generating…' : 'Send to ' + selectedModels.length + (selectedModels.length === 1 ? ' model' : ' models')}
                </button>
              </div>
            </form>
          </section>
        </main>
      </div>
    </div>
  );
};

export default ChatPage;
