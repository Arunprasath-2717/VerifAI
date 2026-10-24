import React, { useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  User, 
  Shield, 
  Cpu, 
  Lock, 
  Palette, 
  Info, 
  Check, 
  AlertTriangle, 
  ExternalLink,
  RefreshCw,
  Trash2,
  Sun,
  Moon,
  Camera,
  Activity,
  Layers,
  Sliders,
  CheckCircle2,
  Key,
  Eye,
  EyeOff,
  Plus,
  X,
  Globe,
  Server,
  FolderKey,
  HelpCircle,
  Link as LinkIcon
} from 'lucide-react';
import { UserSettings, AIProvider } from '../types';
import { useTheme } from '../context/ThemeContext';
import { providersApi } from '../api/providers';

const SUPPORTED_PROVIDER_URLS: Record<string, string> = {
  openai: 'https://api.openai.com/v1',
  anthropic: 'https://api.anthropic.com/v1',
  google: 'https://generativelanguage.googleapis.com/v1beta',
  groq: 'https://api.groq.com/openai/v1',
  openrouter: 'https://openrouter.ai/api/v1',
  mistral: 'https://api.mistral.ai/v1',
  deepseek: 'https://api.deepseek.com',
  perplexity: 'https://api.perplexity.ai',
  nvidia: 'https://integrate.api.nvidia.com/v1',
  xai: 'https://api.x.ai/v1',
  together: 'https://api.together.xyz/v1',
  fireworks: 'https://api.fireworks.ai/inference/v1',
  cerebras: 'https://api.cerebras.ai/v1',
  deepinfra: 'https://api.deepinfra.com/v1/openai',
  sambanova: 'https://api.sambanova.ai/v1',
  moonshot: 'https://api.moonshot.ai/v1',
};

export const PROVIDER_PRESETS = [
  {
    id: 'openai',
    name: 'OpenAI',
    category: 'cloud' as const,
    placeholder: 'sk-proj-...',
    defaultModels: 'GPT-4o, GPT-4o-mini, o1-preview, o3-mini',
    docsUrl: 'https://platform.openai.com/api-keys',
    keyPrefix: 'sk-',
    desc: 'GPT-4o, mini & o1 reasoning engines'
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    category: 'cloud' as const,
    placeholder: 'sk-ant-api03-...',
    defaultModels: 'Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus',
    docsUrl: 'https://console.anthropic.com/settings/keys',
    keyPrefix: 'sk-ant-',
    desc: 'Claude 3.5 frontier reasoning models'
  },
  {
    id: 'google',
    name: 'Google Gemini',
    category: 'cloud' as const,
    placeholder: 'AIzaSy...',
    defaultModels: 'Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash',
    docsUrl: 'https://aistudio.google.com/apikey',
    keyPrefix: 'AIzaSy',
    desc: 'Gemini multimodal & ground-truth core'
  },
  {
    id: 'groq',
    name: 'Groq Cloud',
    category: 'cloud' as const,
    placeholder: 'gsk_...',
    defaultModels: 'Llama 3.3 70B Versatile, Mixtral 8x7B 32k',
    docsUrl: 'https://console.groq.com/keys',
    keyPrefix: 'gsk_',
    desc: 'Ultra-fast LPU inference engine'
  },
  {
    id: 'mistral',
    name: 'Mistral AI',
    category: 'cloud' as const,
    placeholder: '...',
    defaultModels: 'Mistral Large 2, Codestral, Pixtral Large',
    docsUrl: 'https://console.mistral.ai/api-keys',
    desc: 'European sovereign frontier LLM'
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    category: 'cloud' as const,
    placeholder: 'sk-...',
    defaultModels: 'DeepSeek-V3, DeepSeek-R1',
    docsUrl: 'https://platform.deepseek.com/api_keys',
    keyPrefix: 'sk-',
    desc: 'Open reasoning frontier models'
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    category: 'router' as const,
    placeholder: 'sk-or-v1-...',
    defaultModels: 'Mistral Large, Command R+, Qwen 2.5 72B',
    docsUrl: 'https://openrouter.ai/keys',
    keyPrefix: 'sk-or-',
    desc: 'Unified multi-provider LLM gateway'
  },
  {
    id: 'perplexity',
    name: 'Perplexity AI',
    category: 'cloud' as const,
    placeholder: 'pplx-...',
    defaultModels: 'Sonar Reasoning, Sonar Pro, Sonar',
    docsUrl: 'https://perplexity.ai/settings/api',
    keyPrefix: 'pplx-',
    desc: 'Search-augmented frontier models'
  },
  {
    id: 'xai',
    name: 'xAI Grok',
    category: 'cloud' as const,
    placeholder: 'xai-...',
    defaultModels: '',
    docsUrl: 'https://console.x.ai/',
    desc: 'Grok model access via xAI Cloud',
  },
  {
    id: 'together',
    name: 'Together AI',
    category: 'cloud' as const,
    placeholder: 'API key',
    defaultModels: '',
    docsUrl: 'https://api.together.ai/',
    desc: 'Hosted open models and inference',
  },
  {
    id: 'fireworks',
    name: 'Fireworks AI',
    category: 'cloud' as const,
    placeholder: 'API key',
    defaultModels: '',
    docsUrl: 'https://fireworks.ai/',
    desc: 'OpenAI-compatible Fireworks inference',
  },
  {
    id: 'cerebras',
    name: 'Cerebras',
    category: 'cloud' as const,
    placeholder: 'API key',
    defaultModels: '',
    docsUrl: 'https://cloud.cerebras.ai/',
    desc: 'Cerebras Cloud hosted models',
  },
  {
    id: 'deepinfra',
    name: 'DeepInfra',
    category: 'cloud' as const,
    placeholder: 'API key',
    defaultModels: '',
    docsUrl: 'https://deepinfra.com/',
    desc: 'Hosted inference API',
  },
  {
    id: 'sambanova',
    name: 'SambaNova',
    category: 'cloud' as const,
    placeholder: 'API key',
    defaultModels: '',
    docsUrl: 'https://cloud.sambanova.ai/',
    desc: 'SambaNova Cloud hosted models',
  },
  {
    id: 'moonshot',
    name: 'Moonshot AI',
    category: 'cloud' as const,
    placeholder: 'API key',
    defaultModels: '',
    docsUrl: 'https://platform.moonshot.ai/',
    desc: 'Moonshot API inference',
  },
  {
    id: 'custom',
    name: 'Custom OpenAI-Compatible API',
    category: 'cloud' as const,
    placeholder: 'sk-...',
    defaultModels: 'Custom-Model-v1',
    desc: 'Public HTTPS OpenAI-compatible inference endpoint'
  }
];

interface SettingsPageProps {
  userSettings: UserSettings;
  onUpdateUserSettings: (newSettings: UserSettings) => void;
  providers: AIProvider[];
  onSaveProviderKey?: (provId: string, data: { 
    apiKey: string; 
    keyMasked: string; 
    baseUrl?: string; 
    organizationId?: string; 
    keyLabel?: string; 
    name?: string; 
    models?: string[];
    category?: 'cloud' | 'local' | 'router';
  }) => Promise<void>;
  onUnlinkProvider?: (provId: string) => Promise<void>;
  onRefreshProviders?: () => Promise<void>;
  onClearHistory: () => Promise<void>;
  theme?: 'light' | 'dark';
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  userSettings,
  onUpdateUserSettings,
  providers,
  onSaveProviderKey,
  onUnlinkProvider,
  onRefreshProviders,
  onClearHistory,
  theme: propTheme,
}) => {
  const { tab = 'profile' } = useParams<{ tab?: string }>();
  const navigate = useNavigate();
  const context = useTheme();
  
  // Resilient theme check: prioritize propTheme, fallback to context
  const isDark = (propTheme || context.theme) === 'dark';

  // Local state for forms
  const [fullName, setFullName] = useState(userSettings.profile.fullName);
  const [email, setEmail] = useState(userSettings.profile.email);
  const [organization, setOrganization] = useState(userSettings.profile.organization || 'VerifAI Intelligence Lab');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [providerActionError, setProviderActionError] = useState<string | null>(null);
  const [isSavingProvider, setIsSavingProvider] = useState(false);
  const [unlinkingProviderId, setUnlinkingProviderId] = useState<string | null>(null);

  // Verification settings
  const [defaultMode, setDefaultMode] = useState(userSettings.verification.defaultMode);
  const [evidenceDetail, setEvidenceDetail] = useState(userSettings.verification.evidenceDetailLevel);
  const [autoReverify, setAutoReverify] = useState(userSettings.verification.autoReverify || false);

  // Appearance settings
  const [activeThemeSetting, setActiveThemeSetting] = useState(userSettings.appearance.theme);
  const [density, setDensity] = useState(userSettings.appearance.density);
  const [motion, setMotion] = useState(userSettings.appearance.motion);

  // Destructive confirmation modal state
  const [showPurgeConfirm, setShowPurgeConfirm] = useState(false);
  const [purgeError, setPurgeError] = useState<string | null>(null);
  const [isPurging, setIsPurging] = useState(false);
  const [testingProvId, setTestingProvId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; text: string } | null>(null);
  const [avatarUpdated, setAvatarUpdated] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Provider API Key linking dialog box state
  const [isLinkingModalOpen, setIsLinkingModalOpen] = useState(false);
  const [selectedProviderToLink, setSelectedProviderToLink] = useState<AIProvider | null>(null);
  const [isCustomNewProvider, setIsCustomNewProvider] = useState(false);
  const [modalApiKey, setModalApiKey] = useState('');
  const [showKeySecret, setShowKeySecret] = useState(false);
  const [modalKeyLabel, setModalKeyLabel] = useState('');
  const [modalBaseUrl, setModalBaseUrl] = useState('');
  const [modalOrgId, setModalOrgId] = useState('');
  const [modalProviderName, setModalProviderName] = useState('');
  const [modalModels, setModalModels] = useState('');
  const [modalCategory, setModalCategory] = useState<'cloud' | 'local' | 'router'>('cloud');
  const [selectedPresetId, setSelectedPresetId] = useState('openai');
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [isTestingInModal, setIsTestingInModal] = useState(false);
  const [modalTestResult, setModalTestResult] = useState<{ status: 'success' | 'error'; message: string } | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);

  const handleTestConnection = async (provId: string) => {
    setTestingProvId(provId);
    setTestResult(null);
    try {
      const result = await providersApi.testConnection(provId);
      setTestResult({
        id: provId,
        text: result.success
          ? `Connection verified: ${result.message}${result.latency_ms != null ? ` · ${result.latency_ms}ms` : ''}`
          : `Connection failed: ${result.message}`,
      });
    } catch (err) {
      setTestResult({
        id: provId,
        text: `Connection failed: ${err instanceof Error ? err.message : 'Unable to reach provider'}`,
      });
    } finally {
      try { await onRefreshProviders?.(); } catch (err) {
        setProviderActionError(err instanceof Error ? err.message : 'Could not refresh provider status.');
      }
      setTestingProvId(null);
    }
  };

  // Open Dialog Box for an existing provider
  const handleOpenLinkModal = (prov: AIProvider) => {
    setSelectedProviderToLink(prov);
    setIsCustomNewProvider(false);
    setModalApiKey(prov.apiKey || '');
    setModalKeyLabel(prov.keyLabel || `${prov.name} Workspace Key`);
    setModalBaseUrl(prov.baseUrl || '');
    setModalOrgId(prov.organizationId || '');
    setModalProviderName(prov.name);
    setModalModels(prov.models.join(', '));
    setModalCategory(prov.category);
    setShowKeySecret(false);
    setModalTestResult(null);
    setModalError(null);
    setIsAdvancedOpen(Boolean(prov.baseUrl || prov.organizationId));
    setIsLinkingModalOpen(true);
  };

  // Open Dialog Box for creating a new 3rd party LLM connection
  const handleOpenNewProviderModal = () => {
    setSelectedProviderToLink(null);
    setIsCustomNewProvider(true);
    setSelectedPresetId('openai');
    const defaultPreset = PROVIDER_PRESETS[0];
    setModalApiKey('');
    setModalKeyLabel('Production LLM Key');
    setModalBaseUrl('');
    setModalOrgId('');
    setModalProviderName(defaultPreset.name);
    setModalModels(defaultPreset.defaultModels);
    setModalCategory(defaultPreset.category);
    setShowKeySecret(false);
    setModalTestResult(null);
    setModalError(null);
    setIsAdvancedOpen(false);
    setIsLinkingModalOpen(true);
  };

  // Open Dialog Box specifically for a Custom OpenAI-compatible provider
  const handleOpenCustomModal = () => {
    setSelectedProviderToLink(null);
    setIsCustomNewProvider(true);
    setSelectedPresetId('custom');
    setModalApiKey('');
    setModalKeyLabel('Custom API Endpoint Key');
    setModalBaseUrl('');
    setModalOrgId('');
    setModalProviderName('Custom OpenAI-Compatible API');
    setModalModels('Custom-Model-v1');
    setModalCategory('cloud');
    setShowKeySecret(false);
    setModalTestResult(null);
    setModalError(null);
    setIsAdvancedOpen(true);
    setIsLinkingModalOpen(true);
  };

  const handleSelectPreset = (presetId: string) => {
    setSelectedPresetId(presetId);
    const p = PROVIDER_PRESETS.find(x => x.id === presetId);
    if (p) {
      if (presetId === 'custom') {
        setModalProviderName('Custom OpenAI-Compatible API');
        setModalModels('Custom-Model-v1');
        setModalCategory('cloud');
        setModalBaseUrl('');
        setIsAdvancedOpen(true);
      } else {
        setModalProviderName(p.name);
        setModalModels(p.defaultModels);
        setModalCategory(p.category);
        setModalBaseUrl(SUPPORTED_PROVIDER_URLS[presetId] || '');
        setIsAdvancedOpen(false);
      }
    }
  };

  const handleTestKeyInModal = async () => {
    setModalError(null);
    setModalTestResult(null);
    if (!selectedProviderToLink || selectedProviderToLink.status !== 'Connected') {
      setModalError('Save this credential first, then test it using the saved provider connection.');
      return;
    }
    setIsTestingInModal(true);
    try {
      const result = await providersApi.testConnection(selectedProviderToLink.id);
      if (!result.success) {
        setModalError(result.message || 'The provider rejected the saved key.');
      } else {
        setModalTestResult({
          status: 'success',
          message: `${result.message}${result.latency_ms != null ? ` · Latency: ${result.latency_ms}ms` : ''}`,
        });
      }
    } catch (err) {
      setModalError(err instanceof Error ? err.message : 'Provider connection test failed.');
    } finally {
      try { await onRefreshProviders?.(); } catch (err) {
        setModalError(err instanceof Error ? err.message : 'Could not refresh provider status.');
      }
      setIsTestingInModal(false);
    }
  };

  const handleSubmitLinkModal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalApiKey.trim()) {
      setModalError('API key cannot be empty. Please enter a valid secret key or endpoint URL.');
      return;
    }

    const cleanKey = modalApiKey.trim();
    let masked = '';
    if (cleanKey.startsWith('http://') || cleanKey.startsWith('https://')) {
      masked = cleanKey;
    } else if (cleanKey.length > 12) {
      masked = `${cleanKey.slice(0, 7)}••••••••${cleanKey.slice(-4)}`;
    } else {
      masked = '••••••••••••';
    }

    const isCustom = isCustomNewProvider && (selectedPresetId === 'custom' || modalProviderName.toLowerCase().includes('custom'));
    const targetId = selectedProviderToLink 
      ? selectedProviderToLink.id 
      : isCustom
        ? `prov-custom-${modalProviderName.toLowerCase().replace(/[^a-z0-9]/g, '-') || 'api'}-${Date.now().toString().slice(-4)}`
        : `prov-${selectedPresetId || 'openai'}`;

    const modelsList = modalModels
      .split(',')
      .map(m => m.trim())
      .filter(Boolean);

    const payload = {
      apiKey: cleanKey,
      keyMasked: masked,
      baseUrl: modalBaseUrl.trim() || undefined,
      organizationId: modalOrgId.trim() || undefined,
      keyLabel: modalKeyLabel.trim() || `${modalProviderName} Workspace Key`,
      name: modalProviderName.trim() || (selectedProviderToLink ? selectedProviderToLink.name : 'Custom 3rd Party LLM'),
      models: modelsList.length > 0 ? modelsList : ['Custom Model v1'],
      category: modalCategory,
    };

    if (!onSaveProviderKey) {
      setModalError('Backend provider configuration is unavailable.');
      return;
    }
    setIsSavingProvider(true);
    setModalError(null);
    setProviderActionError(null);
    try {
      await onSaveProviderKey(targetId, payload);
      setModalApiKey('');
      setIsLinkingModalOpen(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setModalError(err instanceof Error ? err.message : 'Unable to save credential.');
    } finally {
      setIsSavingProvider(false);
    }
  };

  const handleUnlinkClick = async (prov: AIProvider) => {
    if (!onUnlinkProvider) {
      setProviderActionError('Provider unlinking is not configured.');
      return;
    }
    setUnlinkingProviderId(prov.id);
    setProviderActionError(null);
    try {
      await onUnlinkProvider(prov.id);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (err) {
      setProviderActionError(err instanceof Error ? err.message : 'Could not unlink provider.');
    } finally {
      setUnlinkingProviderId(null);
    }
  };

  const navItems = [
    { id: 'profile', label: 'Profile', icon: User, desc: 'Credentials & identity' },
    { id: 'verification', label: 'Verification', icon: Shield, desc: 'Defaults & thresholds' },
    { id: 'providers', label: 'AI Providers', icon: Cpu, desc: 'Model API keys' },
    { id: 'privacy', label: 'Privacy & Data', icon: Lock, desc: 'Zero-retention & purge' },
    { id: 'appearance', label: 'Appearance', icon: Palette, desc: 'Theme tokens & motion' },
    { id: 'about', label: 'About', icon: Info, desc: 'Provenance architecture' },
  ];

  const handleProfileSave = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdateUserSettings({
      ...userSettings,
      profile: {
        ...userSettings.profile,
        fullName,
        email,
        organization,
      }
    });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleVerificationSave = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdateUserSettings({
      ...userSettings,
      verification: {
        ...userSettings.verification,
        defaultMode,
        evidenceDetailLevel: evidenceDetail,
        autoReverify,
      }
    });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleAppearanceSave = (newTheme: 'light' | 'dark', newDensity: any, newMotion: any) => {
    setActiveThemeSetting(newTheme);
    setDensity(newDensity);
    setMotion(newMotion);
    context.setTheme(newTheme);
    onUpdateUserSettings({
      ...userSettings,
      appearance: {
        theme: newTheme,
        density: newDensity,
        motion: newMotion,
      }
    });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  return (
    <div className="space-y-6 pb-16 w-full">
      {/* Settings Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-[#1B4332] dark:text-white transition-colors">
              Workspace Settings
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold tracking-wide uppercase bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] dark:bg-[#14161C] dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30 dark:shadow-[0_0_10px_rgba(182,255,46,0.15)]">
              {isDark ? 'Dark Mode' : 'Light Mode'}
            </span>
          </div>
          <p className="text-xs md:text-sm font-medium text-[#356B52] dark:text-slate-300 transition-colors">
            Manage your authenticated profile, multi-model verification parameters, and visual theme tokens.
          </p>
        </div>

        {providerActionError && (
          <p role="alert" className="text-xs font-semibold text-rose-600 dark:text-rose-300">
            {providerActionError}
          </p>
        )}
        {saveSuccess && (
          <div className="inline-flex items-center gap-2 text-xs font-bold px-3 py-1.5 rounded-xl animate-in fade-in bg-[#74C69D]/30 text-[#1B4332] border border-[#74C69D] dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] dark:border-[#B6FF2E]/40 shadow-xs">
            <CheckCircle2 size={15} />
            <span>Changes saved to workspace</span>
          </div>
        )}
      </div>

      {/* 2-Column Settings Workspace */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        
        {/* Left Settings Navigation Menu (3 cols) */}
        <nav className="md:col-span-4 lg:col-span-3 rounded-2xl p-2.5 border shadow-xs space-y-1 transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = tab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => navigate(`/settings/${item.id}`)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all text-left cursor-pointer group ${
                  isActive
                    ? isDark 
                      ? 'bg-[#B6FF2E] text-[#12141A] font-black shadow-[0_0_14px_rgba(182,255,46,0.25)] ring-1 ring-[#B6FF2E]' 
                      : 'bg-[#1B4332] text-[#D8F3DC] shadow-xs'
                    : isDark
                      ? 'text-slate-400 hover:text-white hover:bg-[#23262F]'
                      : 'text-[#356B52] hover:text-[#1B4332] hover:bg-[#D8F3DC]'
                }`}
              >
                <div className={`p-1.5 rounded-lg transition-colors shrink-0 ${
                  isActive 
                    ? isDark ? 'bg-[#12141A]/10 text-[#12141A]' : 'bg-white/20 text-[#D8F3DC]'
                    : isDark ? 'text-slate-400 group-hover:text-white' : 'text-[#356B52] group-hover:text-[#1B4332]'
                }`}>
                  <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="leading-tight truncate">{item.label}</p>
                  <p className={`text-[10px] font-medium truncate mt-0.5 ${
                    isActive 
                      ? isDark ? 'text-[#12141A]/80' : 'text-[#D8F3DC]/80'
                      : isDark ? 'text-slate-500' : 'text-[#356B52]'
                  }`}>
                    {item.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </nav>

        {/* Right Content Workspace (8 or 9 cols) */}
        <div className="md:col-span-8 lg:col-span-9 rounded-3xl p-6 md:p-8 border shadow-lg transition-colors relative overflow-hidden bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340] text-[#1B4332] dark:text-white">
          
          {/* Ambient top specular border for dark mode */}
          {isDark && (
            <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent pointer-events-none" />
          )}

          {/* TAB: PROFILE */}
          {tab === 'profile' && (
            <form onSubmit={handleProfileSave} className="space-y-6">
              <div className="pb-3 border-b border-slate-100 dark:border-[#2E3340] flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base md:text-lg text-[#1B4332] dark:text-white">
                    Profile Information
                  </h3>
                  <p className="text-xs text-[#356B52] dark:text-slate-300 mt-0.5">
                    Your authenticated VerifAI identity used for cryptographically signed reports
                  </p>
                </div>
              </div>

              {/* Avatar Lockup */}
              <div className="flex items-center gap-4 p-4 rounded-xl border transition-colors bg-[#FFFFFF] border-slate-200 dark:bg-[#14161C] dark:border-[#2E3340]">
                <div className="w-14 h-14 rounded-xl flex items-center justify-center text-xl font-black font-mono shadow-xs bg-[#D8F3DC] text-[#1B4332] border-2 border-[#74C69D] dark:bg-[#1E2129] dark:text-[#B6FF2E] dark:border-[#B6FF2E]/40 dark:shadow-[0_0_15px_rgba(182,255,46,0.2)] shrink-0">
                  {fullName ? fullName.charAt(0).toUpperCase() : 'A'}
                </div>
                <div>
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setAvatarUpdated(true);
                        setTimeout(() => setAvatarUpdated(false), 3000);
                      }
                    }} 
                  />
                  <div className="flex items-center gap-2.5">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-3.5 py-1.5 rounded-lg font-bold text-xs transition-colors cursor-pointer border flex items-center gap-1.5 bg-[#D8F3DC] text-[#1B4332] border-[#74C69D] hover:bg-[#D8F3DC] dark:bg-[#23262F] dark:text-slate-200 dark:border-[#333742] dark:hover:bg-[#2A2E38]"
                    >
                      <Camera size={14} />
                      <span>Change Photo</span>
                    </button>
                    <span className="text-[11px] font-mono text-[#356B52] dark:text-slate-500">
                      JPG/PNG · Max 2MB
                    </span>
                  </div>
                  {avatarUpdated ? (
                    <p className="text-xs font-semibold mt-1.5 flex items-center gap-1.5 text-[#1B4332] dark:text-[#B6FF2E]">
                      <Check size={13} /> Avatar photo updated successfully
                    </p>
                  ) : (
                    <p className="text-[11px] text-[#356B52] dark:text-slate-400 mt-1">
                      Rendered on public verification certificates and ledger records.
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold block mb-1.5 text-[#1B4332] dark:text-slate-200">
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full max-w-lg rounded-xl px-3.5 py-2.5 text-xs font-medium outline-none border transition-all bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] focus:ring-1 focus:ring-[#1B4332]/20 dark:bg-[#14161C] dark:border-[#2E3340] dark:text-white dark:focus:border-[#B6FF2E] dark:focus:ring-1 dark:focus:ring-[#B6FF2E]/30"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold block mb-1.5 text-[#1B4332] dark:text-slate-200">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full max-w-lg rounded-xl px-3.5 py-2.5 text-xs font-medium outline-none border transition-all bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] focus:ring-1 focus:ring-[#1B4332]/20 dark:bg-[#14161C] dark:border-[#2E3340] dark:text-white dark:focus:border-[#B6FF2E] dark:focus:ring-1 dark:focus:ring-[#B6FF2E]/30"
                  />
                  <p className="text-[11px] text-[#356B52] dark:text-slate-500 mt-1">Used for cryptographic verification receipts and audit exports.</p>
                </div>

                <div>
                  <label className="text-xs font-bold block mb-1.5 text-[#1B4332] dark:text-slate-200">
                    Organization / Lab Name
                  </label>
                  <input
                    type="text"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    className="w-full max-w-lg rounded-xl px-3.5 py-2.5 text-xs font-medium outline-none border transition-all bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] focus:ring-1 focus:ring-[#1B4332]/20 dark:bg-[#14161C] dark:border-[#2E3340] dark:text-white dark:focus:border-[#B6FF2E] dark:focus:ring-1 dark:focus:ring-[#B6FF2E]/30"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-[#74C69D] dark:border-[#2E3340] flex justify-end">
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl font-bold text-xs shadow-xs transition-all cursor-pointer active:scale-95 bg-[#1B4332] hover:bg-[#163E2D] text-[#D8F3DC] dark:bg-[#B6FF2E] dark:hover:bg-[#A3E823] dark:text-[#12141A] dark:font-black dark:shadow-[0_0_16px_rgba(182,255,46,0.25)]"
                >
                  Save Profile Changes
                </button>
              </div>
            </form>
          )}

          {/* TAB: VERIFICATION */}
          {tab === 'verification' && (
            <form onSubmit={handleVerificationSave} className="space-y-6">
              <div className="pb-3 border-b border-slate-100 dark:border-[#2E3340] flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base md:text-lg text-[#1B4332] dark:text-white">
                    Verification Engine Defaults
                  </h3>
                  <p className="text-xs text-[#356B52] dark:text-slate-300 mt-0.5">Configure default proposition evaluation behaviors and ground-truth scope</p>
                </div>
              </div>

              <div className="space-y-5 text-xs">
                <div>
                  <label className="font-bold block mb-2 text-[#1B4332] dark:text-slate-200">
                    Default Ground-Truth Evidence Scope
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <label
                      onClick={() => setDefaultMode('PRIVATE_KB_ONLY')}
                      className={`p-3.5 rounded-xl border flex items-center gap-3 cursor-pointer transition-all ${
                        defaultMode === 'PRIVATE_KB_ONLY' 
                          ? isDark
                            ? 'bg-[#14161C] border-[#B6FF2E] text-white shadow-[0_0_12px_rgba(182,255,46,0.15)] ring-1 ring-[#B6FF2E]'
                            : 'bg-[#74C69D]/30 border-[#1B4332] text-[#1B4332] shadow-xs'
                          : isDark
                            ? 'bg-[#14161C] border-[#2E3340] text-slate-300 hover:border-slate-500'
                            : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] hover:border-[#1B4332]/40'
                      }`}
                    >
                      <input 
                        type="radio" 
                        name="defaultMode"
                        checked={defaultMode === 'PRIVATE_KB_ONLY'} 
                        onChange={() => setDefaultMode('PRIVATE_KB_ONLY')} 
                        className={`w-4 h-4 shrink-0 ${isDark ? 'accent-[#B6FF2E]' : 'accent-[#1B4332]'}`}
                      />
                      <div>
                        <span className="font-bold block text-xs">Private Knowledge Base Only</span>
                        <span className="text-[11px] text-[#356B52] dark:text-slate-400 mt-0.5 block">Restricts evidence strictly to indexed vault documents.</span>
                      </div>
                    </label>

                    <label
                      onClick={() => setDefaultMode('PRIVATE_KB_PLUS_WEB')}
                      className={`p-3.5 rounded-xl border flex items-center gap-3 cursor-pointer transition-all ${
                        defaultMode === 'PRIVATE_KB_PLUS_WEB' 
                          ? isDark
                            ? 'bg-[#14161C] border-[#B6FF2E] text-white shadow-[0_0_12px_rgba(182,255,46,0.15)] ring-1 ring-[#B6FF2E]'
                            : 'bg-[#74C69D]/30 border-[#1B4332] text-[#1B4332] shadow-xs'
                          : isDark
                            ? 'bg-[#14161C] border-[#2E3340] text-slate-300 hover:border-slate-500'
                            : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] hover:border-[#1B4332]/40'
                      }`}
                    >
                      <input 
                        type="radio" 
                        name="defaultMode"
                        checked={defaultMode === 'PRIVATE_KB_PLUS_WEB'} 
                        onChange={() => setDefaultMode('PRIVATE_KB_PLUS_WEB')} 
                        className={`w-4 h-4 shrink-0 ${isDark ? 'accent-[#B6FF2E]' : 'accent-[#1B4332]'}`}
                      />
                      <div>
                        <span className="font-bold block text-xs">Private KB + Web Corpus</span>
                        <span className="text-[11px] text-[#356B52] dark:text-slate-400 mt-0.5 block">Augments private files with authoritative web sources.</span>
                      </div>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="font-bold block mb-1.5 text-[#1B4332] dark:text-slate-200">
                    Evidence Detail Preference
                  </label>
                  <select
                    value={evidenceDetail}
                    onChange={(e) => setEvidenceDetail(e.target.value as any)}
                    className="w-full max-w-md rounded-xl px-3.5 py-2.5 text-xs font-semibold outline-none border transition-all bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] dark:bg-[#14161C] dark:border-[#2E3340] dark:text-white dark:focus:border-[#B6FF2E] cursor-pointer"
                  >
                    <option value="granular">Granular (Full citations, snippets, and confidence scores)</option>
                    <option value="summary">Summary (High-level consensus & verdict only)</option>
                  </select>
                </div>

                <div className="pt-1">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoReverify}
                      onChange={(e) => setAutoReverify(e.target.checked)}
                      className={`w-4 h-4 mt-0.5 rounded shrink-0 ${isDark ? 'accent-[#B6FF2E]' : 'accent-[#1B4332]'}`}
                    />
                    <div>
                      <span className="font-bold text-xs text-[#1B4332] dark:text-slate-200 block">
                        Auto-Reverify When Knowledge Base Changes
                      </span>
                      <span className="text-[11px] text-[#356B52] dark:text-slate-400 mt-0.5 block">
                        Automatically flag stale verifications when new documents are indexed into the vault.
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <div className="pt-3 border-t border-[#74C69D] dark:border-[#2E3340] flex justify-end">
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl font-bold text-xs shadow-xs transition-all cursor-pointer active:scale-95 bg-[#1B4332] hover:bg-[#163E2D] text-[#D8F3DC] dark:bg-[#B6FF2E] dark:hover:bg-[#A3E823] dark:text-[#12141A] dark:font-black dark:shadow-[0_0_16px_rgba(182,255,46,0.25)]"
                >
                  Save Verification Defaults
                </button>
              </div>
            </form>
          )}

          {/* TAB: AI PROVIDERS */}
          {tab === 'providers' && (
            <div className="space-y-6">
              {/* Header with Title and Add New Provider button */}
              <div className="pb-3 border-b border-slate-100 dark:border-[#2E3340] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="font-bold text-base md:text-lg text-[#1B4332] dark:text-white flex items-center gap-2">
                    <span>AI Provider Integrations (BYOK)</span>
                  </h3>
                  <p className="text-xs text-[#356B52] dark:text-slate-300 mt-0.5">
                    Connect 3rd-party LLM providers using private API keys linked to this workspace project.
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-start sm:self-auto flex-wrap">
                  <button
                    type="button"
                    onClick={handleOpenCustomModal}
                    className="px-3.5 py-2 rounded-xl font-bold text-xs cursor-pointer transition-all active:scale-95 flex items-center gap-1.5 border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] hover:bg-[#F2E4D2] dark:bg-[#14161C] dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30 dark:hover:bg-[#1E2129]"
                  >
                    <Plus size={14} strokeWidth={2.5} />
                    <span>+ Custom Provider</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleOpenNewProviderModal}
                    className="px-3.5 py-2 rounded-xl font-bold text-xs cursor-pointer transition-all active:scale-95 flex items-center gap-1.5 bg-[#1B4332] text-[#D8F3DC] hover:bg-[#163E2D] dark:bg-[#B6FF2E] dark:text-[#12141A] dark:hover:bg-[#A3E823] dark:font-black shadow-xs"
                  >
                    <Cpu size={14} strokeWidth={2.5} />
                    <span>Link Preset LLM</span>
                  </button>
                </div>
              </div>

              {/* Informational Guidance Banner */}
              <div className="p-3.5 rounded-xl border flex items-start gap-3 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#14161C] dark:border-[#2E3340]">
                <FolderKey size={18} className="text-[#1B4332] dark:text-[#B6FF2E] shrink-0 mt-0.5" />
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-[#1B4332] dark:text-white">Active Project Workspace:</span>
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-[#D8F3DC] text-[#1B4332] dark:bg-[#23262F] dark:text-[#B6FF2E]">
                      {organization}
                    </span>
                  </div>
                  <p className="text-[#356B52] dark:text-slate-300 leading-relaxed text-[11px] md:text-xs">
                    Link secret API keys for OpenAI, Anthropic, Google Gemini, Groq, Mistral, Ollama, DeepSeek, OpenRouter, or custom OpenAI-compatible endpoints below. For Groq and OpenRouter, test your saved key before the supported chat models become available in the Chat Workspace.
                  </p>
                </div>
              </div>

              {/* Provider Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {providers.map((prov) => {
                  const isConnected = prov.status === 'Connected';
                  const isLinked = Boolean(prov.keyMasked);
                  const categoryBadge = 
                    prov.category === 'cloud' ? 'Cloud API' :
                    prov.category === 'local' ? 'Local Daemon' :
                    prov.category === 'router' ? 'Router Gateway' : 'Custom Endpoint';

                  return (
                    <div
                      key={prov.id}
                      className={`p-4.5 rounded-2xl border flex flex-col justify-between space-y-3.5 transition-all h-full ${
                        isConnected 
                          ? 'bg-[#FFFFFF] border-[#74C69D] shadow-xs dark:bg-[#14161C] dark:border-[#2E3340]'
                          : 'bg-[#FFFFFF] border-slate-200/90 dark:bg-[#14161C]/60 dark:border-[#2E3340]/60'
                      }`}
                    >
                      <div className="space-y-3">
                        {/* Provider Header: Icon + Title/Category + Status Pill */}
                        <div className="flex items-center justify-between gap-2.5">
                          <div className="flex items-center gap-2.5 min-w-0 flex-1">
                            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                              isDark 
                                ? 'bg-[#1E2129] text-[#B6FF2E] border border-[#B6FF2E]/30' 
                                : 'bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D]'
                            }`}>
                              <Cpu size={18} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <h4 className="font-bold text-sm text-[#1B4332] dark:text-white leading-tight truncate" title={prov.name}>
                                {prov.name}
                              </h4>
                              <p className="text-[11px] font-medium text-[#356B52] dark:text-slate-400 capitalize truncate mt-0.5">
                                {categoryBadge}
                              </p>
                            </div>
                          </div>

                          {/* Sleek Dot Status Pill */}
                          {isLinked ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-700 dark:bg-[#B6FF2E]/15 dark:text-[#B6FF2E] border border-emerald-500/20 dark:border-[#B6FF2E]/30 shrink-0">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-[#B6FF2E]" />
                              <span>{isConnected ? 'Connected' : prov.status === 'Unavailable' ? 'Unavailable' : 'Key Saved'}</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-500 dark:bg-[#23262F] dark:text-slate-400 border border-slate-200/80 dark:border-white/5 shrink-0">
                              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500" />
                              <span>Not Connected</span>
                            </span>
                          )}
                        </div>

                        {/* Models List */}
                        <div className="text-xs leading-relaxed">
                          <span className="font-semibold text-[#1B4332] dark:text-slate-300">Models: </span>
                          <span className="text-[#356B52] dark:text-slate-400">
                            {prov.models.length ? prov.models.join(', ') : 'Discovered dynamically in AI Chat after key validation'}
                          </span>
                        </div>

                        {/* API Key Status Pill / Details */}
                        <div className="p-2.5 rounded-xl border text-xs min-h-[50px] flex flex-col justify-center bg-[#D8F3DC]/50 border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340]">
                          {isLinked ? (
                            <div className="space-y-1">
                              <div className="flex items-center justify-between gap-2">
                                <div className="flex items-center gap-1.5 min-w-0 font-mono font-bold text-xs text-[#1B4332] dark:text-[#B6FF2E]">
                                  <Key size={12} className="shrink-0" />
                                  <span className="truncate">{prov.keyMasked || '••••••••••••'}</span>
                                </div>
                                <span className="text-[11px] font-medium text-[#356B52] dark:text-slate-400 shrink-0">
                                  {prov.configuredAt ? `Linked ${prov.configuredAt}` : 'Active'}
                                </span>
                              </div>
                              {prov.keyLabel && (
                                <p className="text-[11px] text-[#356B52] dark:text-slate-400 truncate">
                                  Label: <span className="font-medium text-[#1B4332] dark:text-slate-200">{prov.keyLabel}</span>
                                </p>
                              )}
                              {prov.baseUrl && prov.baseUrl !== prov.keyMasked && (
                                <p className="text-[11px] font-mono text-[#356B52] dark:text-slate-500 truncate">
                                  Endpoint: {prov.baseUrl}
                                </p>
                              )}
                              {prov.name.toLowerCase().includes('nvidia') &&
                                prov.baseUrl?.includes('localhost:8000') && (
                                <p className="text-[11px] text-amber-700 dark:text-amber-300">
                                  Legacy endpoint detected. Test Ping will switch this to NVIDIA's hosted API after validation.
                                </p>
                              )}
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 text-xs text-[#356B52] dark:text-slate-400 py-0.5">
                              <Lock size={13} className="shrink-0" />
                              <span>No credential saved for this provider.</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Card Footer Actions */}
                      <div className="pt-2.5 border-t border-slate-200/60 dark:border-[#2E3340]">
                        {isLinked ? (
                          <div className="w-full flex items-center justify-between gap-2">
                            <button
                              type="button"
                              onClick={() => handleTestConnection(prov.id)}
                              disabled={testingProvId === prov.id}
                              className="font-bold flex items-center gap-1.5 cursor-pointer text-[#1B4332] hover:text-[#163E2D] hover:underline dark:text-[#B6FF2E] text-xs shrink-0"
                            >
                              <RefreshCw size={12} className={testingProvId === prov.id ? 'animate-spin' : ''} />
                              <span>Test Ping</span>
                            </button>

                            <div className="flex items-center gap-1.5 shrink-0">
                              <button
                                type="button"
                                onClick={() => handleOpenLinkModal(prov)}
                                className="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors cursor-pointer bg-[#FFFFFF] border-[#74C69D] text-[#1B4332] hover:bg-[#D8F3DC] dark:bg-[#23262F] dark:border-[#333742] dark:text-slate-200 dark:hover:bg-[#2A2E38]"
                              >
                                Edit Key
                              </button>
                              <button
                                type="button"
                                onClick={() => handleUnlinkClick(prov)}
                                disabled={unlinkingProviderId === prov.id}
                                className="px-2.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors bg-rose-500/10 text-rose-500 hover:bg-rose-500/20 border border-rose-500/30"
                              >
                                Unlink
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleOpenLinkModal(prov)}
                            className="w-full py-2 px-3.5 rounded-xl text-xs font-bold cursor-pointer transition-all active:scale-[0.99] flex items-center justify-center gap-2 bg-[#1B4332] text-[#D8F3DC] hover:bg-[#163E2D] dark:bg-[#B6FF2E] dark:text-[#12141A] dark:hover:bg-[#A3E823] dark:font-black shadow-xs"
                          >
                            <Key size={13} />
                            <span>Link API Key with Project</span>
                          </button>
                        )}
                      </div>

                      {testResult && testResult.id === prov.id && (
                        <p className="text-[11px] font-mono p-2 rounded-lg bg-[#D8F3DC] dark:bg-[#1E2129] text-[#1B4332] dark:text-[#B6FF2E] border border-[#74C69D] dark:border-[#B6FF2E]/30 animate-in fade-in">
                          {testResult.text}
                        </p>
                      )}
                    </div>
                  );
                })}

                {/* Dedicated Add Custom Provider Card */}
                <div
                  onClick={handleOpenCustomModal}
                  className="p-5 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center text-center space-y-3 transition-all cursor-pointer group hover:scale-[1.01] bg-[#FFFFFF]/60 border-[#74C69D] hover:border-[#1B4332] dark:bg-[#14161C]/40 dark:border-[#2E3340] dark:hover:border-[#B6FF2E]/60 min-h-[220px]"
                >
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all ${
                    isDark ? 'bg-[#1E2129] text-[#B6FF2E] group-hover:scale-110 shadow-[0_0_12px_rgba(182,255,46,0.2)]' : 'bg-[#D8F3DC] text-[#1B4332] group-hover:scale-110'
                  }`}>
                    <Plus size={22} strokeWidth={2.5} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-[#1B4332] dark:text-white">
                      + Connect Custom API Endpoint
                    </h4>
                    <p className="text-[11px] text-[#356B52] dark:text-slate-400 mt-0.5 max-w-xs leading-relaxed">
                      Connect any OpenAI-compatible inference server, vLLM, Ollama remote, or internal proxy.
                    </p>
                  </div>
                  <span className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-colors ${
                    isDark ? 'bg-[#1E2129] text-[#B6FF2E] border-[#B6FF2E]/30' : 'bg-[#D8F3DC] text-[#1B4332] border-[#74C69D]'
                  }`}>
                    Configure Custom BYOK
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB: PRIVACY */}
          {tab === 'privacy' && (
            <div className="space-y-6">
              <div className="pb-3 border-b border-slate-100 dark:border-[#2E3340] flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base md:text-lg text-[#1B4332] dark:text-white">
                    Privacy & Data Governance
                  </h3>
                  <p className="text-xs text-[#356B52] dark:text-slate-300 mt-0.5">Zero-retention parameters and verifiable storage policy</p>
                </div>
              </div>

              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-xl border space-y-2 transition-colors bg-[#FFFFFF] border-slate-200 dark:bg-[#14161C] dark:border-[#2E3340]">
                  <div className="flex items-center gap-2 text-[#1B4332] dark:text-[#B6FF2E]">
                    <Shield size={16} strokeWidth={2.4} />
                    <h4 className="font-bold text-sm text-[#1B4332] dark:text-white">Zero-Retention Verification Guarantee</h4>
                  </div>
                  <p className="leading-relaxed text-[#356B52] dark:text-slate-300">
                    Prompts sent to third-party AI providers are subject to those providers’ privacy, retention and training policies. Check each provider’s terms before sharing sensitive information. API keys are encrypted in the backend.
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-[#2E3340] space-y-3">
                  <h4 className="font-bold text-sm text-rose-500 flex items-center gap-1.5">
                    <AlertTriangle size={15} />
                    <span>Danger Zone</span>
                  </h4>
                  <p className="text-[#356B52] dark:text-slate-400">
                    Permanently delete all verification records, claim evaluations, and cached evidence from this workspace.
                  </p>

                  <button
                    type="button"
                    onClick={() => setShowPurgeConfirm(true)}
                    className="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-500 dark:text-rose-400 font-bold text-xs transition-colors flex items-center gap-1.5 cursor-pointer active:scale-95"
                  >
                    <Trash2 size={14} />
                    <span>Purge Verification History</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB: APPEARANCE */}
          {tab === 'appearance' && (
            <div className="space-y-6">
              <div className="pb-3 border-b border-slate-100 dark:border-[#2E3340] flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base md:text-lg text-[#1B4332] dark:text-white">
                    Appearance & Theme Tokens
                  </h3>
                  <p className="text-xs text-[#356B52] dark:text-slate-300 mt-0.5">
                    Switch between Light and Dark interface appearance modes.
                  </p>
                </div>
              </div>

              <div className="space-y-5 text-xs">
                {/* Theme Selector with Live Cards */}
                <div>
                  <label className="font-bold block mb-2 text-[#1B4332] dark:text-slate-200">
                    Active Theme Mode
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    {/* Light Theme Card */}
                    <div
                      onClick={() => handleAppearanceSave('light', density, motion)}
                      className={`p-4 rounded-xl border-2 transition-all cursor-pointer relative ${
                        activeThemeSetting === 'light'
                          ? 'border-[#1B4332] shadow-sm ring-1 ring-[#1B4332]/20 bg-[#FFFFFF]'
                          : 'border-slate-200 dark:border-[#2E3340] bg-[#FFFFFF] dark:bg-[#14161C] opacity-75 hover:opacity-100'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Sun size={16} className="text-[#1B4332]" />
                          <h4 className="font-bold text-xs text-[#1B4332]">
                            Light Theme
                          </h4>
                        </div>
                        {activeThemeSetting === 'light' && (
                          <span className="w-2.5 h-2.5 rounded-full bg-[#1B4332]" />
                        )}
                      </div>
                      <p className="text-[11px] text-[#356B52] mb-2.5 leading-relaxed">
                        A bright white and pale-mint workspace with crisp black typography, olive (#40916C) actions, mint (#74C69D) highlights, and deep-green (#1B4332) accents.
                      </p>
                      <div className="flex items-center gap-1.5">
                        <span className="w-5 h-5 rounded-md bg-[#1B4332] border border-black/10" title="Deep Green (#1B4332)" />
                        <span className="w-5 h-5 rounded-md bg-[#74C69D] border border-black/10" title="Mint (#74C69D)" />
                        <span className="w-5 h-5 rounded-md bg-[#D8F3DC] border border-black/10" title="Pale Mint (#D8F3DC)" />
                      </div>
                    </div>

                    {/* Dark Theme Card */}
                    <div
                      onClick={() => handleAppearanceSave('dark', density, motion)}
                      className={`p-4 rounded-xl border-2 transition-all cursor-pointer relative ${
                        activeThemeSetting === 'dark'
                          ? 'border-[#B6FF2E] shadow-[0_0_16px_rgba(182,255,46,0.2)] ring-1 ring-[#B6FF2E]/40 bg-[#14161C]'
                          : 'border-slate-200 dark:border-[#2E3340] bg-white dark:bg-[#14161C] opacity-75 hover:opacity-100'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Moon size={16} className="text-[#B6FF2E]" />
                          <h4 className="font-bold text-xs text-white">
                            Dark Theme
                          </h4>
                        </div>
                        {activeThemeSetting === 'dark' && (
                          <span className="w-2.5 h-2.5 rounded-full bg-[#B6FF2E] shadow-[0_0_8px_#B6FF2E]" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-300 mb-2.5 leading-relaxed">
                        Deep obsidian graphite containers with high-contrast white text and radiant lime spark highlights.
                      </p>
                      <div className="flex items-center gap-1.5">
                        <span className="w-5 h-5 rounded-md bg-[#B6FF2E] border border-white/20" title="Lime Spark (#B6FF2E)" />
                        <span className="w-5 h-5 rounded-md bg-[#23262F] border border-white/20" title="Graphite Card (#23262F)" />
                        <span className="w-5 h-5 rounded-md bg-[#14161C] border border-white/20" title="Deep Midnight (#14161C)" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Display Density */}
                <div>
                  <label className="font-bold block mb-2 text-[#1B4332] dark:text-slate-200">
                    Display Density
                  </label>
                  <div className="flex gap-2.5">
                    {[
                      { id: 'comfortable', label: 'Comfortable' },
                      { id: 'compact', label: 'Compact' },
                    ].map((d) => (
                      <button
                        key={d.id}
                        type="button"
                        onClick={() => handleAppearanceSave(activeThemeSetting as any, d.id, motion)}
                        className={`px-4 py-2 rounded-xl font-bold border transition-all cursor-pointer text-xs ${
                          density === d.id 
                            ? isDark
                              ? 'bg-[#B6FF2E] text-[#12141A] font-black border-[#B6FF2E] shadow-[0_0_12px_rgba(182,255,46,0.25)]'
                              : 'bg-[#1B4332] text-[#D8F3DC] border-[#1B4332]'
                            : isDark
                              ? 'bg-[#14161C] border-[#2E3340] text-slate-300 hover:border-slate-500'
                              : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] hover:border-[#1B4332]/40'
                        }`}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Motion */}
                <div>
                  <label className="font-bold block mb-2 text-[#1B4332] dark:text-slate-200">
                    Animation & Transitions
                  </label>
                  <div className="flex gap-2.5">
                    {[
                      { id: 'full', label: 'Full Transitions' },
                      { id: 'reduced', label: 'Reduced Motion' },
                    ].map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => handleAppearanceSave(activeThemeSetting as any, density, m.id)}
                        className={`px-4 py-2 rounded-xl font-bold border transition-all cursor-pointer text-xs ${
                          motion === m.id 
                            ? isDark
                              ? 'bg-[#B6FF2E] text-[#12141A] font-black border-[#B6FF2E] shadow-[0_0_12px_rgba(182,255,46,0.25)]'
                              : 'bg-[#1B4332] text-[#D8F3DC] border-[#1B4332]'
                            : isDark
                              ? 'bg-[#14161C] border-[#2E3340] text-slate-300 hover:border-slate-500'
                              : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] hover:border-[#1B4332]/40'
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB: ABOUT */}
          {tab === 'about' && (
            <div className="space-y-6">
              <div className="pb-3 border-b border-slate-100 dark:border-[#2E3340] flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base md:text-lg text-[#1B4332] dark:text-white">
                    About VerifAI Platform
                  </h3>
                  <p className="text-xs text-[#356B52] dark:text-slate-300 mt-0.5">System architecture, cryptographic hashing, and ground-truth standards</p>
                </div>
              </div>

              <div className="space-y-4 text-xs leading-relaxed text-[#356B52] dark:text-slate-300">
                <p>
                  <strong className="text-[#1B4332] dark:text-white">VerifAI Engine Version:</strong>{' '}
                  <span className="font-mono font-bold text-xs text-[#1B4332] dark:text-[#B6FF2E] px-2.5 py-0.5 rounded-lg bg-[#D8F3DC] dark:bg-[#14161C] border border-[#74C69D] dark:border-[#B6FF2E]/30">v2.6.4-prod</span>
                </p>
                <p>
                  VerifAI is a high-assurance AI answer verification platform designed to evaluate model outputs against corroborating peer-reviewed publications, regulatory guidelines, and private institutional ground-truth documents.
                </p>
                <div className="p-4 rounded-xl border space-y-2 transition-colors bg-[#FFFFFF] border-[#74C69D] dark:bg-[#14161C] dark:border-[#2E3340]">
                  <h4 className="font-bold text-xs text-[#1B4332] dark:text-white">System Verification Pipeline</h4>
                  <ol className="list-decimal pl-4 space-y-1.5 text-[#356B52] dark:text-slate-300">
                    <li>Atomic proposition parsing using zero-shot semantic splitters.</li>
                    <li>Hybrid dense/sparse vector retrieval across connected ground-truth vaults.</li>
                    <li>Tri-model cross-examination with calibrated confidence scoring.</li>
                    <li>Cryptographic audit ledger hashing for institutional compliance.</li>
                  </ol>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* Confirmation Modal for Purging History */}
      {showPurgeConfirm && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="rounded-2xl max-w-md w-full p-6 space-y-3.5 border shadow-2xl animate-in zoom-in-95 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340] text-[#1B4332] dark:text-white">
            <div className="flex items-center gap-2.5 text-rose-500">
              <AlertTriangle size={20} />
              <h3 className="font-bold text-base text-[#1B4332] dark:text-white">
                Confirm History Purge
              </h3>
            </div>
            <p className="text-xs leading-relaxed text-[#356B52] dark:text-slate-300">
              This will permanently delete all verification runs and claim evaluations from your account. This action cannot be undone.
            </p>
            {purgeError && <p role="alert" className="text-xs text-rose-600 dark:text-rose-300">Purge failed: {purgeError}</p>}
            <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-100 dark:border-[#2E3340]">
              <button
                type="button"
                disabled={isPurging}
                onClick={() => setShowPurgeConfirm(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-[#14161C]"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isPurging}
                onClick={async () => {
                  setIsPurging(true);
                  setPurgeError(null);
                  try {
                    await onClearHistory();
                    setShowPurgeConfirm(false);
                  } catch (err) {
                    setPurgeError(err instanceof Error ? err.message : 'Purge could not be completed.');
                  } finally {
                    setIsPurging(false);
                  }
                }}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold cursor-pointer transition-all active:scale-95 shadow-xs disabled:opacity-50"
              >
                {isPurging ? 'Purging...' : 'Permanently Purge'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dialog Box: Link Provider API Key with Project */}
      {isLinkingModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="rounded-2xl max-w-lg w-full p-6 space-y-4 border shadow-2xl animate-in zoom-in-95 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#1E2129] dark:border-[#2E3340] text-[#1B4332] dark:text-white my-6">
            {/* Dialog Header */}
            <div className="flex items-start justify-between gap-3 pb-2.5 border-b border-slate-100 dark:border-[#2E3340]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#D8F3DC] text-[#1B4332] border border-[#74C69D] dark:bg-[#14161C] dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30 shadow-xs shrink-0">
                  <Key size={18} strokeWidth={2.4} />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-bold text-base text-[#1B4332] dark:text-white">
                      {isCustomNewProvider 
                        ? 'Link 3rd Party LLM Provider' 
                        : `Link ${selectedProviderToLink?.name || ''} API Key`}
                    </h3>
                  </div>
                  <p className="text-xs text-[#356B52] dark:text-slate-300 mt-0.5">
                    Connect secret credentials to project: <span className="font-bold text-[#1B4332] dark:text-[#B6FF2E]">{organization}</span>
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setIsLinkingModalOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-[#14161C] dark:hover:text-white transition-colors cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSubmitLinkModal} className="space-y-4 text-xs">
              {/* If adding new provider: Preset Selector */}
              {isCustomNewProvider && (
                <div>
                  <label className="text-xs font-bold block mb-1.5 text-[#1B4332] dark:text-slate-200">
                    Select 3rd-Party LLM Provider Preset
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {PROVIDER_PRESETS.map((preset) => {
                      const isSel = selectedPresetId === preset.id;
                      return (
                        <button
                          key={preset.id}
                          type="button"
                          onClick={() => handleSelectPreset(preset.id)}
                          className={`p-2 rounded-lg border text-left text-xs font-bold transition-all cursor-pointer ${
                            isSel
                              ? isDark
                                ? 'bg-[#14161C] border-[#B6FF2E] text-white ring-1 ring-[#B6FF2E]'
                                : 'bg-[#1B4332] text-[#D8F3DC] border-[#1B4332] shadow-xs'
                              : 'bg-[#FFFFFF] border-[#74C69D] text-[#356B52] hover:border-[#1B4332]/40 dark:bg-[#14161C] dark:border-[#2E3340] dark:text-slate-300'
                          }`}
                        >
                          <span className="block truncate">{preset.name}</span>
                          <span className={`text-[10px] block truncate font-normal mt-0.5 ${
                            isSel ? 'opacity-80' : 'text-[#356B52] dark:text-slate-500'
                          }`}>
                            {preset.category}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Provider Name, Base URL & Models (for custom or editing custom) */}
              {(selectedPresetId === 'custom' || selectedProviderToLink?.id?.startsWith('prov-custom')) && (
                <div className="space-y-3 p-3 rounded-xl border bg-[#FFFFFF] border-[#74C69D] dark:bg-[#14161C] dark:border-[#2E3340]">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div>
                      <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-200">
                        Custom Provider Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={modalProviderName}
                        onChange={(e) => setModalProviderName(e.target.value)}
                        placeholder="e.g. Together AI, Internal vLLM, DeepInfra"
                        className="w-full rounded-xl px-3 py-2 text-xs font-medium outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] dark:bg-[#1E2129] dark:border-[#2E3340] dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-200">
                        Deployment Type
                      </label>
                      <select
                        value={modalCategory}
                        onChange={(e) => setModalCategory(e.target.value as any)}
                        className="w-full rounded-xl px-3 py-2 text-xs font-medium outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] dark:bg-[#1E2129] dark:border-[#2E3340] dark:text-white"
                      >
                        <option value="cloud">Cloud Inference API</option>
                        <option value="local">Local Daemon / Self-Hosted</option>
                        <option value="router">Multi-Model Gateway / Router</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-200">
                      API Connection Base URL / Endpoint *
                    </label>
                    <input
                      type="text"
                      required
                      value={modalBaseUrl}
                      onChange={(e) => setModalBaseUrl(e.target.value)}
                      placeholder="e.g. http://localhost:8000/v1 or https://api.together.xyz/v1"
                      className="w-full rounded-xl px-3 py-2 text-xs font-mono font-medium outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] dark:bg-[#1E2129] dark:border-[#2E3340] dark:text-white"
                    />
                    <p className="text-[10px] text-[#356B52] dark:text-slate-400 mt-1">
                      Custom endpoints must expose OpenAI-compatible <span className="font-mono">/models</span> and <span className="font-mono">/chat/completions</span> over public HTTPS. Built-in providers use fixed official endpoints; Claude and Gemini use their native APIs.
                    </p>
                  </div>

                  <div>
                    <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-200">
                      Available Model Identifiers (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={modalModels}
                      onChange={(e) => setModalModels(e.target.value)}
                      placeholder="e.g. Meta-Llama-3-70B, Qwen-2.5-72B"
                      className="w-full rounded-xl px-3 py-2 text-xs font-medium outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] dark:bg-[#1E2129] dark:border-[#2E3340] dark:text-white"
                    />
                  </div>
                </div>
              )}

              {/* Secret API Key Input */}
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="font-bold text-[#1B4332] dark:text-slate-200 flex items-center gap-1.5">
                    <Key size={13} className="text-[#1B4332] dark:text-[#B6FF2E]" />
                    <span>Secret API Key or Endpoint URL *</span>
                  </label>
                  {(() => {
                    const preset = PROVIDER_PRESETS.find(p => 
                      p.name === (selectedProviderToLink ? selectedProviderToLink.name : modalProviderName) || 
                      p.id === selectedPresetId
                    );
                    const url = selectedProviderToLink?.docsUrl || preset?.docsUrl;
                    if (url) {
                      return (
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-[11px] flex items-center gap-1 text-[#1B4332] hover:underline dark:text-[#B6FF2E]"
                        >
                          <span>Get API Key</span>
                          <ExternalLink size={11} />
                        </a>
                      );
                    }
                    return null;
                  })()}
                </div>

                <div className="relative">
                  <input
                    type={showKeySecret ? 'text' : 'password'}
                    required
                    value={modalApiKey}
                    onChange={(e) => {
                      setModalApiKey(e.target.value);
                      if (modalError) setModalError(null);
                    }}
                    placeholder={
                      (() => {
                        const preset = PROVIDER_PRESETS.find(p => 
                          p.name === (selectedProviderToLink ? selectedProviderToLink.name : modalProviderName) || 
                          p.id === selectedPresetId
                        );
                        return preset?.placeholder || 'sk-...';
                      })()
                    }
                    className="w-full rounded-xl px-3.5 py-2.5 pr-10 text-xs font-mono font-medium outline-none border transition-all bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] focus:ring-1 focus:ring-[#1B4332]/20 dark:bg-[#14161C] dark:border-[#2E3340] dark:text-white dark:focus:border-[#B6FF2E]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKeySecret(!showKeySecret)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white cursor-pointer"
                    title={showKeySecret ? 'Hide secret key' : 'Show secret key'}
                  >
                    {showKeySecret ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>

                <p className="text-[10px] text-[#356B52] dark:text-slate-400">
                  Keys are encrypted and stored by the backend. Saving does not verify provider connectivity.
                </p>
              </div>

              {/* Key Nickname / Label */}
              <div>
                <label className="font-bold text-xs block mb-1 text-[#1B4332] dark:text-slate-200">
                  Key Label / Environment (Optional)
                </label>
                <input
                  type="text"
                  value={modalKeyLabel}
                  onChange={(e) => setModalKeyLabel(e.target.value)}
                  placeholder="e.g. Primary Production Key, Team Lab Key"
                  className="w-full rounded-xl px-3 py-2 text-xs font-medium outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] focus:border-[#1B4332] dark:bg-[#14161C] dark:border-[#2E3340] dark:text-white"
                />
              </div>

              {/* Advanced toggle */}
              <div className="pt-0.5">
                <button
                  type="button"
                  onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
                  className="text-xs font-bold flex items-center gap-1.5 text-[#1B4332] dark:text-[#B6FF2E] hover:underline cursor-pointer"
                >
                  <Sliders size={12} />
                  <span>{isAdvancedOpen ? 'Hide Advanced Options' : 'Show Advanced Options (Base URL, Org ID)'}</span>
                </button>

                {isAdvancedOpen && (
                  <div className="mt-2.5 p-3 rounded-xl border space-y-2.5 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#14161C] dark:border-[#2E3340] text-xs">
                    <div>
                      <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-200">
                        Custom Base URL / Proxy Endpoint (Optional)
                      </label>
                      <input
                        type="text"
                        value={modalBaseUrl}
                        onChange={(e) => setModalBaseUrl(e.target.value)}
                        placeholder="e.g. https://api.openai.com/v1 or http://localhost:11434"
                        className="w-full rounded-lg px-2.5 py-1.5 font-mono text-xs outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] dark:bg-[#1E2129] dark:border-[#2E3340] dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="font-bold block mb-1 text-[#1B4332] dark:text-slate-200">
                        Organization ID / Project Header (Optional)
                      </label>
                      <input
                        type="text"
                        value={modalOrgId}
                        onChange={(e) => setModalOrgId(e.target.value)}
                        placeholder="e.g. org-verifai-labs-2026"
                        className="w-full rounded-lg px-2.5 py-1.5 font-mono text-xs outline-none border bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] dark:bg-[#1E2129] dark:border-[#2E3340] dark:text-white"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Handshake Verification Ping Test */}
              <div className="p-3 rounded-xl border flex items-center justify-between gap-3 bg-[#FFFFFF] border-[#74C69D] dark:bg-[#14161C] dark:border-[#2E3340]">
                <div>
                  <span className="font-bold block text-xs text-[#1B4332] dark:text-white">Test Saved Credential</span>
                  <span className="text-[11px] text-[#356B52] dark:text-slate-400">Tests the previously saved key. Save changes before testing a new key.</span>
                </div>
                <button
                  type="button"
                  onClick={handleTestKeyInModal}
                  disabled={isTestingInModal || isSavingProvider}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors cursor-pointer flex items-center gap-1.5 shrink-0 bg-[#D8F3DC] border-[#74C69D] text-[#1B4332] hover:bg-[#D8F3DC] dark:bg-[#23262F] dark:border-[#333742] dark:text-slate-200"
                >
                  <RefreshCw size={11} className={isTestingInModal ? 'animate-spin' : ''} />
                  <span>{isTestingInModal ? 'Testing...' : 'Test Connection'}</span>
                </button>
              </div>

              {modalTestResult && (
                <div className="p-2.5 rounded-xl text-xs font-mono bg-emerald-50 dark:bg-[#1E2129] text-emerald-800 dark:text-[#B6FF2E] border border-emerald-200 dark:border-[#B6FF2E]/40 flex items-center gap-2">
                  <CheckCircle2 size={15} className="shrink-0" />
                  <span>{modalTestResult.message}</span>
                </div>
              )}

              {modalError && (
                <div className="p-2.5 rounded-xl text-xs bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900/50 flex items-center gap-2">
                  <AlertTriangle size={14} className="shrink-0" />
                  <span>{modalError}</span>
                </div>
              )}

              {/* Security Banner */}
              <div className="p-3 rounded-xl border flex items-start gap-2 bg-[#D8F3DC]/60 border-[#74C69D] dark:bg-[#14161C] dark:border-[#2E3340] text-[11px] text-[#356B52] dark:text-slate-400">
                <Shield size={14} className="text-[#1B4332] dark:text-[#B6FF2E] shrink-0 mt-0.5" />
                <p>
                  <strong className="text-[#1B4332] dark:text-white">Credential handling:</strong> Keys are sent to the backend for encrypted storage; the frontend receives only a masked hint.
                </p>
              </div>

              {/* Dialog Actions */}
              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100 dark:border-[#2E3340]">
                <button
                  type="button"
                  onClick={() => setIsLinkingModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-[#14161C]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingProvider}
                  className="px-5 py-2 rounded-xl font-bold text-xs cursor-pointer transition-all active:scale-95 shadow-xs flex items-center gap-1.5 bg-[#1B4332] hover:bg-[#163E2D] text-[#D8F3DC] dark:bg-[#B6FF2E] dark:hover:bg-[#A3E823] dark:text-[#12141A] dark:font-black disabled:opacity-50"
                >
                  <LinkIcon size={14} />
                  <span>{isSavingProvider ? 'Saving...' : 'Save API Key'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default SettingsPage;
