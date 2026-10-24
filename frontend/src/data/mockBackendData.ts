import { 
  VerificationRecord, 
  KnowledgeDocument, 
  Conversation, 
  AIProvider, 
  UserSettings, 
  ChartPoint, 
  NotificationItem,
  ModelLeaderboardEntry,
  ModelMetadata
} from '../types';

export const allEcosystemModels: ModelMetadata[] = [
  // 1. OpenAI (Proprietary Frontier)
  {
    id: 'gpt-5.6-sol',
    name: 'GPT-5.6 Sol',
    family: 'GPT',
    provider: 'OpenAI',
    modelType: 'proprietary',
    capabilities: ['text', 'vision', 'reasoning'],
    contextWindow: 1050000,
    maxOutputTokens: 16384,
    recommended: true,
    isConnected: true,
    tier: 'Frontier Flagship',
    description: 'Frontier high-intelligence reasoning flagship for deep claim deconstruction.'
  },
  {
    id: 'gpt-5.6-terra',
    name: 'GPT-5.6 Terra',
    family: 'GPT',
    provider: 'OpenAI',
    modelType: 'proprietary',
    capabilities: ['text', 'vision', 'reasoning'],
    contextWindow: 500000,
    maxOutputTokens: 8192,
    recommended: false,
    isConnected: true,
    tier: 'Balanced Frontier',
    description: 'Balanced frontier model optimized for high-throughput enterprise verification.'
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    family: 'GPT',
    provider: 'OpenAI',
    modelType: 'proprietary',
    capabilities: ['text', 'vision'],
    contextWindow: 128000,
    maxOutputTokens: 4096,
    recommended: true,
    isConnected: true,
    tier: 'Multimodal Baseline',
    description: 'Omni multimodal benchmark baseline for claim extraction.'
  },
  {
    id: 'gpt-oss-120b',
    name: 'GPT-OSS 120B',
    family: 'GPT',
    provider: 'OpenAI',
    modelType: 'open-weight',
    capabilities: ['text', 'coding'],
    contextWindow: 131072,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: true,
    tier: 'Open-Weight',
    description: 'OpenAI open-weight foundation model for transparent self-hosted benchmarking.'
  },

  // 2. Anthropic (Proprietary Frontier)
  {
    id: 'claude-3-5-sonnet',
    name: 'Claude 3.5 Sonnet',
    family: 'Claude',
    provider: 'Anthropic',
    modelType: 'proprietary',
    capabilities: ['text', 'vision', 'coding', 'reasoning'],
    contextWindow: 200000,
    maxOutputTokens: 8192,
    recommended: true,
    isConnected: true,
    tier: 'Frontier Reasoning',
    description: 'Frontier reasoning and factual nuance leader with high claim corroboration precision.'
  },
  {
    id: 'claude-3-opus',
    name: 'Claude 3 Opus',
    family: 'Claude',
    provider: 'Anthropic',
    modelType: 'proprietary',
    capabilities: ['text', 'vision', 'reasoning'],
    contextWindow: 200000,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: true,
    tier: 'Deep Synthesis',
    description: 'Deep synthetic analysis model for highly technical cross-examination.'
  },
  {
    id: 'claude-3-5-haiku',
    name: 'Claude 3.5 Haiku',
    family: 'Claude',
    provider: 'Anthropic',
    modelType: 'proprietary',
    capabilities: ['text', 'coding'],
    contextWindow: 200000,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: true,
    tier: 'Fast Triage',
    description: 'Ultra-fast proposition verification and initial snippet filtering.'
  },

  // 3. Google Gemini (Proprietary + Multimodal)
  {
    id: 'gemini-3.1-pro',
    name: 'Gemini 3.1 Pro',
    family: 'Gemini',
    provider: 'Google',
    modelType: 'proprietary',
    capabilities: ['text', 'vision', 'reasoning'],
    contextWindow: 2000000,
    maxOutputTokens: 8192,
    recommended: true,
    isConnected: true,
    tier: '2M Context Flagship',
    description: 'Deep multi-step reasoning flagship with 2M token context capability.'
  },
  {
    id: 'gemini-3.8-flash',
    name: 'Gemini 3.8 Flash',
    family: 'Gemini',
    provider: 'Google',
    modelType: 'proprietary',
    capabilities: ['text', 'vision', 'multimodal'],
    contextWindow: 1000000,
    maxOutputTokens: 8192,
    recommended: true,
    isConnected: true,
    tier: 'Fast Grounding',
    description: '1M+ token context window leader for full-document corpus grounding.'
  },
  {
    id: 'gemini-2.5-pro',
    name: 'Gemini 2.5 Pro',
    family: 'Gemini',
    provider: 'Google',
    modelType: 'proprietary',
    capabilities: ['text', 'multimodal'],
    contextWindow: 1000000,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: true,
    tier: 'Enterprise Grounding',
    description: 'Previous-generation enterprise grounding model.'
  },

  // 4. Groq (Ultra-Fast Inference Gateway)
  {
    id: 'llama-3.3-70b-versatile',
    name: 'Llama 3.3 70B (Groq)',
    family: 'Llama',
    provider: 'Groq',
    modelType: 'open-weight',
    capabilities: ['text', 'reasoning'],
    contextWindow: 128000,
    maxOutputTokens: 4096,
    recommended: true,
    isConnected: false,
    tier: 'LPU Ultra-Fast',
    description: 'Sub-second verification responses powered by Groq LPU silicon.'
  },
  {
    id: 'mixtral-8x7b-32768',
    name: 'Mixtral 8x7B MoE',
    family: 'Mistral',
    provider: 'Groq',
    modelType: 'open-weight',
    capabilities: ['text'],
    contextWindow: 32768,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: false,
    tier: 'High-Speed MoE',
    description: 'High-speed Mixture-of-Experts inference.'
  },

  // 5. OpenRouter / OmniRoute Gateway (DeepSeek, Qwen, Mistral, Cohere, Grok)
  {
    id: 'deepseek/deepseek-r1',
    name: 'DeepSeek R1',
    family: 'DeepSeek',
    provider: 'OpenRouter',
    modelType: 'open-weight',
    capabilities: ['text', 'reasoning'],
    contextWindow: 64000,
    maxOutputTokens: 8192,
    recommended: true,
    isConnected: false,
    tier: 'RL Reasoning Flagship',
    description: 'Reinforcement-learning reasoning model for deep contradiction proofing.'
  },
  {
    id: 'deepseek/deepseek-chat',
    name: 'DeepSeek V3',
    family: 'DeepSeek',
    provider: 'OpenRouter',
    modelType: 'open-weight',
    capabilities: ['text', 'coding'],
    contextWindow: 64000,
    maxOutputTokens: 8192,
    recommended: false,
    isConnected: false,
    tier: '671B MoE Core',
    description: '671B MoE architecture with exceptional factual retrieval fidelity.'
  },
  {
    id: 'qwen/qwen-2.5-72b-instruct',
    name: 'Qwen 2.5 72B',
    family: 'Qwen',
    provider: 'OpenRouter',
    modelType: 'open-weight',
    capabilities: ['text', 'coding', 'reasoning'],
    contextWindow: 131072,
    maxOutputTokens: 4096,
    recommended: true,
    isConnected: false,
    tier: 'Top Open-Weight',
    description: 'Top-tier open-weight reasoning model matching frontier proprietary baselines.'
  },
  {
    id: 'mistralai/mistral-large-2411',
    name: 'Mistral Large 3',
    family: 'Mistral',
    provider: 'OpenRouter',
    modelType: 'open-weight',
    capabilities: ['text', 'reasoning'],
    contextWindow: 128000,
    maxOutputTokens: 4096,
    recommended: true,
    isConnected: false,
    tier: 'EU Open Sovereign',
    description: 'European sovereign open-weight flagship with multi-lingual reasoning.'
  },
  {
    id: 'cohere/command-r-plus',
    name: 'Cohere Command R+',
    family: 'Cohere',
    provider: 'OpenRouter',
    modelType: 'proprietary',
    capabilities: ['text', 'reasoning', 'rerank'],
    contextWindow: 128000,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: false,
    tier: 'RAG Specialist',
    description: 'Specialized RAG and enterprise evidence retrieval foundation model.'
  },
  {
    id: 'x-ai/grok-2-1212',
    name: 'xAI Grok 2',
    family: 'Grok',
    provider: 'OpenRouter',
    modelType: 'proprietary',
    capabilities: ['text', 'vision'],
    contextWindow: 131072,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: false,
    tier: 'Independent Frontier',
    description: 'Independent proprietary baseline for non-consensus verification tests.'
  },

  // 6. Ollama / Local Self-Hosted (Air-Gapped & Private KB)
  {
    id: 'gemma4:12b',
    name: 'Gemma 4 12B (Local)',
    family: 'Gemma',
    provider: 'Ollama',
    modelType: 'local',
    capabilities: ['text', 'multimodal'],
    contextWindow: 262144,
    maxOutputTokens: 4096,
    recommended: true,
    isConnected: true,
    tier: 'Local 256K Context',
    description: 'Latest open-weight Gemma architecture running privately with 256K context.'
  },
  {
    id: 'phi4:14b',
    name: 'Phi-4 14B (Local)',
    family: 'Phi',
    provider: 'Ollama',
    modelType: 'local',
    capabilities: ['text', 'reasoning'],
    contextWindow: 16384,
    maxOutputTokens: 4096,
    recommended: true,
    isConnected: true,
    tier: 'Local Reasoning',
    description: 'Synthetic high-quality reasoning model suited for local air-gapped deployments.'
  },
  {
    id: 'llama3.3:8b',
    name: 'Llama 3.3 8B (Local)',
    family: 'Llama',
    provider: 'Ollama',
    modelType: 'local',
    capabilities: ['text'],
    contextWindow: 128000,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: true,
    tier: 'Local Lightweight',
    description: 'Lightweight local model for privacy-first proposition extraction.'
  },
  {
    id: 'deepseek-r1:14b',
    name: 'DeepSeek R1 14B (Local)',
    family: 'DeepSeek',
    provider: 'Ollama',
    modelType: 'local',
    capabilities: ['text', 'reasoning'],
    contextWindow: 64000,
    maxOutputTokens: 4096,
    recommended: false,
    isConnected: true,
    tier: 'Local Distill Reasoning',
    description: 'Locally hosted distilled reasoning model for offline verification checks.'
  }
];

export const initialUserSettings: UserSettings = {
  profile: {
    fullName: 'Arun Prasath',
    email: 'arun@example.com',
    organization: 'VerifAI Intelligence Lab',
  },
  verification: {
    defaultMode: 'PRIVATE_KB_PLUS_WEB',
    defaultModels: ['GPT-4o', 'Claude 3.5', 'Gemini 1.5'],
    evidenceDetailLevel: 'granular',
    autoReverify: false,
  },
  appearance: {
    theme: 'light',
    density: 'comfortable',
    motion: 'full',
  },
};

export const weeklyChartData: ChartPoint[] = [
  { name: 'Sep 12', claims: 14, evidence: 48, verifications: 8 },
  { name: 'Sep 13', claims: 24, evidence: 82, verifications: 14 },
  { name: 'Sep 14', claims: 18, evidence: 65, verifications: 11 },
  { name: 'Sep 15', claims: 38, evidence: 135, verifications: 22 },
  { name: 'Sep 16', claims: 28, evidence: 98, verifications: 17 },
  { name: 'Sep 17', claims: 12, evidence: 40, verifications: 6 },
  { name: 'Sep 18', claims: 19, evidence: 56, verifications: 9 },
];

export const monthlyChartData: ChartPoint[] = [
  { name: 'Week 1', claims: 120, evidence: 410, verifications: 68 },
  { name: 'Week 2', claims: 185, evidence: 640, verifications: 94 },
  { name: 'Week 3', claims: 240, evidence: 890, verifications: 138 },
  { name: 'Week 4', claims: 210, evidence: 780, verifications: 116 },
];

export const initialVerifications: VerificationRecord[] = [
  {
    id: 'ver-ev-01',
    query: 'Safety of electric vehicles and carbon emissions parity',
    originalAnswer: 'Electric vehicles are better for the environment because they produce zero emissions and have a lower carbon footprint compared to gasoline cars.',
    summary: 'Analyzed 4 discrete claims across lifecycle emissions, tailpipe metrics, and battery production.',
    status: 'SUPPORTED',
    timestamp: '2 hours ago',
    dateFormatted: 'Sep 18, 2026',
    claimsCount: 4,
    supportedCount: 3,
    contradictedCount: 1,
    unknownCount: 0,
    evidenceCount: 12,
    model: 'GPT-4o & Claude 3.5',
    modelsUsed: ['GPT-4o', 'Claude 3.5'],
    verificationMode: 'PRIVATE_KB_PLUS_WEB',
    claims: [
      {
        id: 'c-101',
        statement: 'Electric vehicles produce zero emissions during direct operation.',
        status: 'SUPPORTED',
        confidence: 0.99,
        evidenceSnippet: 'Battery electric powertrains emit no tailpipe pollutants, carbon monoxide, or NOx during road driving.',
        sourceTitle: 'EPA Clean Air Act Compliance Guidelines 2026',
        sourceUrl: 'https://epa.gov/transportation-air-pollution-and-climate-change',
        domain: 'epa.gov',
        retrievedAt: 'Sep 18, 2026 10:14 AM'
      },
      {
        id: 'c-102',
        statement: 'Electric vehicles have a lower lifetime carbon footprint than gasoline cars.',
        status: 'SUPPORTED',
        confidence: 0.94,
        evidenceSnippet: 'Across 95% of world energy grids, lifecycle greenhouse gas emissions of EVs are 42% to 70% lower than comparable internal combustion engine vehicles.',
        sourceTitle: 'International Council on Clean Transportation (ICCT) Lifecycle Assessment',
        sourceUrl: 'https://theicct.org/publications/global-LCA-passenger-cars-2026',
        domain: 'theicct.org',
        retrievedAt: 'Sep 18, 2026 10:14 AM'
      },
      {
        id: 'c-103',
        statement: 'Electric vehicle batteries are more polluting than gasoline engines over entire vehicle lifespan.',
        status: 'CONTRADICTED',
        confidence: 0.96,
        evidenceSnippet: 'While battery production has a higher upfront carbon debt, breakeven is typically achieved within 12,000 to 18,000 miles of driving.',
        sourceTitle: 'Argonne National Laboratory GREET Model 2026',
        sourceUrl: 'https://greet.anl.gov',
        domain: 'anl.gov',
        retrievedAt: 'Sep 18, 2026 10:15 AM'
      },
      {
        id: 'c-104',
        statement: 'Electric vehicles are always more environmentally friendly in all scenarios.',
        status: 'UNKNOWN',
        confidence: 0.62,
        evidenceSnippet: 'In isolated regions relying 100% on legacy coal-fired generation with very low mileage use, lifecycle emissions can approach parity with ultra-efficient hybrids.',
        sourceTitle: 'MIT Energy Initiative Mobility Study',
        sourceUrl: 'https://energy.mit.edu',
        domain: 'mit.edu',
        retrievedAt: 'Sep 18, 2026 10:15 AM'
      }
    ]
  },
  {
    id: 'ver-climate-02',
    query: 'Is climate change causing more extreme weather events?',
    originalAnswer: 'Anthropogenic global warming has led to an observed increase in the frequency and intensity of heavy precipitation and heatwaves globally.',
    summary: 'Corroborated against IPCC AR6 Assessment Report and WMO Global Climate State reports.',
    status: 'SUPPORTED',
    timestamp: '2 hours ago',
    dateFormatted: 'Sep 18, 2026',
    claimsCount: 4,
    supportedCount: 4,
    contradictedCount: 0,
    unknownCount: 0,
    evidenceCount: 12,
    model: 'Gemini 1.5 & GPT-4o',
    modelsUsed: ['Gemini 1.5', 'GPT-4o'],
    verificationMode: 'PRIVATE_KB_PLUS_WEB',
    claims: [
      {
        id: 'c-201',
        statement: 'Global frequency of heatwaves has increased significantly since 1950.',
        status: 'SUPPORTED',
        confidence: 0.98,
        evidenceSnippet: 'Human-induced climate change is the main driver of more frequent and more intense heat extremes.',
        sourceTitle: 'IPCC Working Group I Sixth Assessment Report',
        sourceUrl: 'https://ipcc.ch/report/ar6/wg1',
        domain: 'ipcc.ch'
      }
    ]
  },
  {
    id: 'ver-fasting-03',
    query: 'Benefits of intermittent fasting on cellular autophagy',
    originalAnswer: '16:8 intermittent fasting induces complete cellular autophagy in humans within 14 hours and cures metabolic resistance.',
    summary: 'Clinical studies confirm partial metabolic switching but refute unvalidated curative claims.',
    status: 'UNKNOWN',
    timestamp: '1 day ago',
    dateFormatted: 'Sep 17, 2026',
    claimsCount: 6,
    supportedCount: 3,
    contradictedCount: 1,
    unknownCount: 2,
    evidenceCount: 18,
    model: 'Claude 3.5',
    modelsUsed: ['Claude 3.5'],
    verificationMode: 'PRIVATE_KB_PLUS_WEB',
    claims: [
      {
        id: 'c-301',
        statement: '16-hour fasting induces measurable autophagy in human peripheral blood mononuclear cells.',
        status: 'UNKNOWN',
        confidence: 0.55,
        evidenceSnippet: 'Direct human in vivo measurements of tissue autophagy during short fasts remain limited and methodologically contested.',
        sourceTitle: 'Cell Metabolism Clinical Monograph',
        sourceUrl: 'https://cell.com/cell-metabolism'
      }
    ]
  },
  {
    id: 'ver-ai-safety-04',
    query: 'Impact of AI on white-collar employment transition',
    originalAnswer: 'GenAI tools replace 80% of entry-level corporate analyst jobs while doubling productivity across mid-market accounting.',
    summary: 'Industry survey datasets show task acceleration rather than direct 80% head-count substitution.',
    status: 'CONTRADICTED',
    timestamp: '2 days ago',
    dateFormatted: 'Sep 16, 2026',
    claimsCount: 5,
    supportedCount: 1,
    contradictedCount: 3,
    unknownCount: 1,
    evidenceCount: 9,
    model: 'GPT-4o',
    modelsUsed: ['GPT-4o'],
    verificationMode: 'PRIVATE_KB_ONLY',
    claims: [
      {
        id: 'c-401',
        statement: '80% of entry-level analyst positions have been eliminated by generative models.',
        status: 'CONTRADICTED',
        confidence: 0.95,
        evidenceSnippet: 'Bureau of Labor Statistics and OECD 2026 labor data demonstrate restructuring and job enrichment rather than 80% headcount reduction.',
        sourceTitle: 'OECD Employment Outlook 2026',
        sourceUrl: 'https://oecd.org'
      }
    ]
  },
  {
    id: 'ver-renew-05',
    query: 'Renewable energy vs fossil fuels LCOE metrics',
    originalAnswer: 'Utility-scale solar and onshore wind maintain a lower Levelized Cost of Energy than new natural gas combined cycle plants.',
    summary: 'Corroborated by Lazard LCOE v18.0 across global benchmarks.',
    status: 'SUPPORTED',
    timestamp: '1 week ago',
    dateFormatted: 'Sep 11, 2026',
    claimsCount: 4,
    supportedCount: 4,
    contradictedCount: 0,
    unknownCount: 0,
    evidenceCount: 12,
    model: 'Gemini 1.5',
    modelsUsed: ['Gemini 1.5'],
    verificationMode: 'PRIVATE_KB_PLUS_WEB'
  },
  {
    id: 'ver-space-06',
    query: 'Space exploration benefits to earth-bound materials science',
    originalAnswer: 'Microgravity protein crystal growth enables novel pharmaceutical formulations with high stability.',
    summary: 'Corroborated by ISS National Laboratory research archives.',
    status: 'SUPPORTED',
    timestamp: '1 week ago',
    dateFormatted: 'Sep 10, 2026',
    claimsCount: 6,
    supportedCount: 5,
    contradictedCount: 0,
    unknownCount: 1,
    evidenceCount: 18,
    model: 'Claude 3.5',
    modelsUsed: ['Claude 3.5'],
    verificationMode: 'PRIVATE_KB_ONLY'
  }
];

export const initialDocuments: KnowledgeDocument[] = [
  {
    id: 'doc-01',
    name: 'Company Policy.pdf',
    type: 'PDF',
    size: '2.4 MB',
    status: 'Indexed',
    uploadedDate: 'Sep 18, 2026',
    chunksCount: 142,
    category: 'Internal Governance',
    reliabilityScore: 99,
    description: 'Corporate ethics, factual claims governance, and regulatory disclosure standards.'
  },
  {
    id: 'doc-02',
    name: 'Research Paper.pdf',
    type: 'PDF',
    size: '1.8 MB',
    status: 'Indexed',
    uploadedDate: 'Sep 16, 2026',
    chunksCount: 88,
    category: 'Academic Research',
    reliabilityScore: 96,
    description: 'Peer-reviewed evidence on semiconductor thermal dissipation and cryo-quench dynamics.'
  },
  {
    id: 'doc-03',
    name: 'Technology Report.docx',
    type: 'DOCX',
    size: '3.1 MB',
    status: 'Processing',
    uploadedDate: 'Sep 14, 2026',
    chunksCount: 112,
    category: 'Technical Specs',
    reliabilityScore: 92,
    description: 'Transformer kv-cache quantization latency benchmarks on NVIDIA H100 clusters.'
  },
  {
    id: 'doc-04',
    name: 'Dataset.csv',
    type: 'CSV',
    size: '5.6 MB',
    status: 'Indexed',
    uploadedDate: 'Sep 12, 2026',
    chunksCount: 340,
    category: 'Raw Empirical Data',
    reliabilityScore: 100,
    description: 'EPA emissions logs and fuel economy test cycles across 450 vehicle models.'
  },
  {
    id: 'doc-05',
    name: 'User Guide.pdf',
    type: 'PDF',
    size: '1.2 MB',
    status: 'Failed',
    uploadedDate: 'Sep 10, 2026',
    chunksCount: 0,
    category: 'Documentation',
    reliabilityScore: 0,
    description: 'Corrupted font encoding prevented text vectorization. Re-upload required.'
  },
  {
    id: 'doc-06',
    name: 'Whitepaper.pdf',
    type: 'PDF',
    size: '4.3 MB',
    status: 'Indexed',
    uploadedDate: 'Sep 8, 2026',
    chunksCount: 204,
    category: 'Industry Whitepaper',
    reliabilityScore: 95,
    description: 'Zero-knowledge verification protocols for multi-model consensus.'
  }
];

export const initialConversations: Conversation[] = [
  {
    id: 'conv-01',
    title: 'Climate change analysis',
    updatedAt: '2 hours ago',
    messageCount: 8,
    models: ['GPT-4o', 'Claude 3.5', 'Gemini 1.5'],
    messages: [
      {
        id: 'msg-1',
        sender: 'user',
        content: 'What are the main causes of climate change and what evidence supports anthropogenic greenhouse gas forcing?',
        timestamp: '10:15 AM'
      },
      {
        id: 'msg-2',
        sender: 'assistant',
        content: 'Comparative evaluation across 3 independent models.',
        timestamp: '10:16 AM',
        modelResponses: [
          {
            model: 'GPT-4o',
            provider: 'OpenAI',
            text: 'Current observational data and ice-core isotope ratios confirm atmospheric CO2 has exceeded 420 ppm primarily due to fossil fuel combustion, cement production, and deforestation.',
            status: 'Completed',
            latencyMs: 780,
            tokensUsed: 420,
            claimsCount: 3
          },
          {
            model: 'Claude 3.5',
            provider: 'Anthropic',
            text: 'Multiple independent lines of empirical evidence corroborate radiative forcing from anthropogenic greenhouse gases, matching global climate model projections over six decades.',
            status: 'Completed',
            latencyMs: 910,
            tokensUsed: 395,
            claimsCount: 2
          },
          {
            model: 'Gemini 1.5',
            provider: 'Google',
            text: 'Paleoclimate records and satellite spectroscopic measurements directly observe the reduction in outgoing infrared radiation corresponding precisely to CO2 and methane absorption bands.',
            status: 'Completed',
            latencyMs: 640,
            tokensUsed: 410,
            claimsCount: 3
          }
        ],
        evaluation: {
          id: 'eval-conv-01',
          overallDecision: 'SUPPORTED',
          claimsAnalyzed: 3,
          evidenceSourcesCount: 14,
          modelsEvaluatedCount: 3,
          decisionRationale: 'All extracted propositions regarding radiative forcing and atmospheric greenhouse concentration are strongly substantiated by peer-reviewed IPCC and NASA climate monitoring data.',
          finalVerifaiDecision: 'SUPPORTED',
          modelJudgmentsSummary: [
            { model: 'GPT-4o', verdict: 'SUPPORTED', notes: 'Isotope ratio claims verified against Law Dome ice core logs.' },
            { model: 'Claude 3.5', verdict: 'SUPPORTED', notes: 'Radiative forcing matching climate observations confirmed.' },
            { model: 'Gemini 1.5', verdict: 'SUPPORTED', notes: 'Spectroscopic absorption measurements corroborated by satellite data.' }
          ],
          claims: [
            {
              id: 'cl-c1',
              statement: 'Atmospheric CO2 has exceeded 420 ppm primarily from fossil fuel combustion and industrial emissions.',
              modelAgreement: {
                agreeCount: 3,
                totalModels: 3,
                consensusNote: 'All 3 models explicitly asserted this factual benchmark.'
              },
              evidenceSourcesCount: 5,
              verificationVerdict: 'SUPPORTED',
              confidence: 0.99,
              modelJudgments: [
                { model: 'GPT-4o', verdict: 'SUPPORTED', reasoning: 'Matches NOAA ESRL global baseline.' },
                { model: 'Claude 3.5', verdict: 'SUPPORTED', reasoning: 'Direct match with IPCC AR6 data.' },
                { model: 'Gemini 1.5', verdict: 'SUPPORTED', reasoning: 'Affirmed by satellite spectroscopy.' }
              ],
              evidenceList: [
                {
                  source: 'NOAA Global Monitoring Laboratory',
                  title: 'Trends in Atmospheric Carbon Dioxide (Mauna Loa Observatory)',
                  domain: 'gml.noaa.gov',
                  url: 'https://gml.noaa.gov/ccgg/trends/',
                  retrievedTime: '2 hours ago',
                  excerpt: 'Monthly mean CO2 mole fractions at Mauna Loa surpassed 424 ppm in recent seasonal measurements.',
                  type: 'Government/Regulatory'
                },
                {
                  source: 'Nature Geoscience',
                  title: 'Decadal trends in carbon isotope signatures across terrestrial reservoirs',
                  domain: 'nature.com',
                  url: 'https://nature.com/articles/ngeo3214',
                  retrievedTime: '2 hours ago',
                  excerpt: 'Suess effect measurements of declining 13C/12C ratios uniquely identify fossil carbon as the dominant source.',
                  type: 'Primary Research'
                }
              ]
            },
            {
              id: 'cl-c2',
              statement: 'Satellite spectroscopic measurements directly observe the reduction in outgoing infrared radiation corresponding to CO2 and methane absorption bands.',
              modelAgreement: {
                agreeCount: 2,
                totalModels: 3,
                consensusNote: 'Asserted by Gemini 1.5 and Claude 3.5; omitted by GPT-4o.'
              },
              evidenceSourcesCount: 4,
              verificationVerdict: 'SUPPORTED',
              confidence: 0.96,
              modelJudgments: [
                { model: 'Claude 3.5', verdict: 'SUPPORTED', reasoning: 'Confirmed by Harries et al. and CERES satellite data.' },
                { model: 'Gemini 1.5', verdict: 'SUPPORTED', reasoning: 'Direct spectroscopic absorption match.' },
                { model: 'GPT-4o', verdict: 'UNKNOWN', reasoning: 'Did not evaluate satellite absorption bands.' }
              ],
              evidenceList: [
                {
                  source: 'NASA Earth Observatory & CERES Team',
                  title: 'Direct Observation of Earth\'s Outgoing Longwave Radiation Spectrum',
                  domain: 'nasa.gov',
                  url: 'https://ceres.larc.nasa.gov',
                  retrievedTime: '2 hours ago',
                  excerpt: 'Clear-sky outgoing longwave radiation shows marked flux reductions at 667 cm-1, verifying the greenhouse gas forcing mechanism in situ.',
                  type: 'Government/Regulatory'
                }
              ]
            },
            {
              id: 'cl-c3',
              statement: 'Observed radiative forcing matches predictive multi-decadal climate model projections within standard error margins.',
              modelAgreement: {
                agreeCount: 3,
                totalModels: 3,
                consensusNote: 'All 3 models concurred on predictive model calibration.'
              },
              evidenceSourcesCount: 5,
              verificationVerdict: 'SUPPORTED',
              confidence: 0.94,
              modelJudgments: [
                { model: 'GPT-4o', verdict: 'SUPPORTED', reasoning: 'CMIP6 calibration confirmed.' },
                { model: 'Claude 3.5', verdict: 'SUPPORTED', reasoning: 'Hausfather et al. historical evaluation corroborated.' },
                { model: 'Gemini 1.5', verdict: 'SUPPORTED', reasoning: 'Concurred with historical model fidelity.' }
              ],
              evidenceList: [
                {
                  source: 'Geophysical Research Letters',
                  title: 'Evaluating the Performance of Past Climate Model Projections',
                  domain: 'agu.org',
                  url: 'https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/2019GL085378',
                  retrievedTime: '2 hours ago',
                  excerpt: 'Climate models published between 1970 and 2007 were skillfully able to project subsequent global warming.',
                  type: 'Primary Research'
                }
              ]
            }
          ]
        }
      }
    ]
  },
  {
    id: 'conv-02',
    title: 'Electric vehicles carbon parity',
    updatedAt: '1 day ago',
    messageCount: 4,
    models: ['GPT-4o', 'Claude 3.5'],
    messages: [
      {
        id: 'msg-3',
        sender: 'user',
        content: 'Do electric vehicles actually produce less carbon when factoring in battery manufacturing?',
        timestamp: 'Yesterday'
      },
      {
        id: 'msg-4',
        sender: 'assistant',
        content: 'Comparative evaluation across 2 models.',
        timestamp: 'Yesterday',
        modelResponses: [
          {
            model: 'GPT-4o',
            provider: 'OpenAI',
            text: 'Yes, despite higher manufacturing emissions, the operational efficiency of EVs overcomes this delta after 1 to 2 years of standard driving.',
            status: 'Completed',
            latencyMs: 820,
            tokensUsed: 310,
            claimsCount: 2
          },
          {
            model: 'Claude 3.5',
            provider: 'Anthropic',
            text: 'Lifecycle assessments across Europe and North America show battery electric vehicles have 50-70% lower lifetime emissions than internal combustion equivalents.',
            status: 'Completed',
            latencyMs: 760,
            tokensUsed: 290,
            claimsCount: 2
          }
        ]
      }
    ]
  }
];

export const initialLeaderboard: ModelLeaderboardEntry[] = [
  {
    rank: 1,
    model: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    version: '20241022',
    overallScore: 94,
    categories: {
      factualSupport: 95,
      evidenceSupport: 96,
      contradictionDetection: 92,
      unknownHandling: 94,
      claimVerification: 93
    },
    evaluationsCount: 148,
    lastEvaluated: 'Oct 3, 2026',
    strengths: [
      'High calibration on uncertain propositions, avoiding false affirmative claims',
      'Strong source attribution when citing regulatory and academic monographs',
      'Superior performance on handling ambiguous medical and clinical claims'
    ],
    limitations: [
      'Occasionally conservative on emerging pre-print scientific developments',
      'Slightly higher latency on multi-turn claim decomposition'
    ]
  },
  {
    rank: 2,
    model: 'Gemini 1.5 Pro',
    provider: 'Google',
    version: '002',
    overallScore: 92,
    categories: {
      factualSupport: 93,
      evidenceSupport: 94,
      contradictionDetection: 90,
      unknownHandling: 89,
      claimVerification: 94
    },
    evaluationsCount: 132,
    lastEvaluated: 'Oct 2, 2026',
    strengths: [
      'Rapid retrieval and alignment across long document contexts (2M tokens)',
      'High accuracy on technical math, physics, and empirical table data',
      'Fast response generation with consistent structured JSON extraction'
    ],
    limitations: [
      'Occasionally omits domain constraints unless specifically prompted in system instructions'
    ]
  },
  {
    rank: 3,
    model: 'GPT-4o',
    provider: 'OpenAI',
    version: '2024-11-20',
    overallScore: 91,
    categories: {
      factualSupport: 94,
      evidenceSupport: 91,
      contradictionDetection: 91,
      unknownHandling: 85,
      claimVerification: 94
    },
    evaluationsCount: 164,
    lastEvaluated: 'Oct 4, 2026',
    strengths: [
      'Extensive broad-domain factual knowledge and historical benchmark coverage',
      'Effective at direct contradiction identification on refuted physical claims',
      'Strong natural language synthesis for executive summaries'
    ],
    limitations: [
      'Higher tendency to attempt confident answers on propositions with insufficient evidence rather than classifying as UNKNOWN'
    ]
  },
  {
    rank: 4,
    model: 'Llama 3.3 70B',
    provider: 'Ollama (Local)',
    version: 'Instruct-q8',
    overallScore: 86,
    categories: {
      factualSupport: 88,
      evidenceSupport: 85,
      contradictionDetection: 87,
      unknownHandling: 82,
      claimVerification: 88
    },
    evaluationsCount: 84,
    lastEvaluated: 'Sep 29, 2026',
    strengths: [
      'Runs locally with zero cloud telemetry, preserving strict organizational data sovereignty',
      'Strong logical deduction on closed-world private document extraction'
    ],
    limitations: [
      'Lower citation specificity compared to frontier cloud providers',
      'Requires calibrated prompt engineering to prevent superficial consensus'
    ]
  },
  {
    rank: 5,
    model: 'Mistral Large',
    provider: 'OpenRouter',
    version: '2411',
    overallScore: 85,
    categories: {
      factualSupport: 86,
      evidenceSupport: 84,
      contradictionDetection: 85,
      unknownHandling: 83,
      claimVerification: 87
    },
    evaluationsCount: 72,
    lastEvaluated: 'Sep 28, 2026',
    strengths: [
      'Excellent multilingual factual grounding across French, German, and Spanish documents',
      'Cost-effective high-throughput comparative evaluation'
    ],
    limitations: [
      'Modest gap on complex medical dosage and regulatory precision compared to Sonnet'
    ]
  }
];


export const initialProviders: AIProvider[] = [
  {
    id: 'prov-openai',
    name: 'OpenAI',
    category: 'cloud',
    status: 'Not Connected',
    models: ['GPT-4o', 'GPT-4o-mini', 'o1-preview', 'o3-mini'],
    docsUrl: 'https://platform.openai.com/api-keys'
  },
  {
    id: 'prov-anthropic',
    name: 'Anthropic',
    category: 'cloud',
    status: 'Not Connected',
    models: ['Claude 3.5 Sonnet', 'Claude 3.5 Haiku', 'Claude 3 Opus'],
    docsUrl: 'https://console.anthropic.com/settings/keys'
  },
  {
    id: 'prov-google',
    name: 'Google Gemini',
    category: 'cloud',
    status: 'Not Connected',
    models: ['Gemini 1.5 Pro', 'Gemini 1.5 Flash', 'Gemini 2.0 Flash'],
    docsUrl: 'https://aistudio.google.com/apikey'
  },
  {
    id: 'prov-groq',
    name: 'Groq Cloud (LPU)',
    category: 'cloud',
    status: 'Not Connected',
    models: ['Llama 3.3 70B (Groq)', 'Mixtral 8x7B MoE'],
    docsUrl: 'https://console.groq.com/keys'
  },
  {
    id: 'prov-mistral',
    name: 'Mistral AI',
    category: 'cloud',
    status: 'Not Connected',
    models: ['Mistral Large 2', 'Mistral Small', 'Codestral'],
    docsUrl: 'https://console.mistral.ai/api-keys'
  },
  {
    id: 'prov-deepseek',
    name: 'DeepSeek',
    category: 'cloud',
    status: 'Not Connected',
    models: ['DeepSeek R1', 'DeepSeek V3'],
    docsUrl: 'https://platform.deepseek.com/api_keys'
  },
  {
    id: 'prov-ollama',
    name: 'Ollama (Local / Air-Gapped)',
    category: 'local',
    status: 'Not Connected',
    models: ['Llama 3.3 8B (Local)', 'DeepSeek R1 14B (Local)', 'Phi-4 14B (Local)'],
    baseUrl: 'http://localhost:11434',
    docsUrl: 'https://ollama.com'
  },
  {
    id: 'prov-openrouter',
    name: 'OpenRouter / OmniRoute Gateway',
    category: 'router',
    status: 'Not Connected',
    models: ['DeepSeek R1', 'DeepSeek V3', 'Qwen 2.5 72B', 'Mistral Large 3'],
    docsUrl: 'https://openrouter.ai/keys'
  },
  {
    id: 'prov-custom',
    name: 'Custom OpenAI-Compatible API',
    category: 'cloud',
    status: 'Not Connected',
    models: ['Custom-Model-v1'],
    docsUrl: ''
  }
];

export const initialNotifications: NotificationItem[] = [
  {
    id: 'notif-1',
    title: 'Verification Complete: Electric vehicles lifecycle emissions',
    description: '3 claims supported, 1 contradicted by peer-reviewed ICCT data.',
    timestamp: '2 hours ago',
    read: false,
    type: 'verification',
    link: '/verification/ver-ev-01'
  },
  {
    id: 'notif-2',
    title: 'Knowledge Base Vector Indexing',
    description: 'Company Policy.pdf indexed 142 semantic chunks successfully.',
    timestamp: '4 hours ago',
    read: false,
    type: 'system',
    link: '/knowledge-base'
  },
  {
    id: 'notif-3',
    title: 'Evidence Consensus Threshold Reached',
    description: 'High-agreement consensus on Renewable energy grid LCOE.',
    timestamp: 'Yesterday',
    read: true,
    type: 'alert',
    link: '/history'
  }
];
