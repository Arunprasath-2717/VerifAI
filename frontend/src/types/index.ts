export type VerificationStatus = 'SUPPORTED' | 'CONTRADICTED' | 'UNKNOWN' | 'UNAVAILABLE' | 'FAILED';

export interface ClaimItem {
  id: string;
  statement: string;
  status: VerificationStatus;
  confidence: number; // 0 to 1
  evidenceSnippet?: string;
  sourceTitle?: string;
  sourceUrl?: string;
  contradictionReason?: string;
  domain?: string;
  retrievedAt?: string;
}

export interface VerificationRecord {
  id: string;
  query: string;
  originalAnswer?: string;
  summary: string;
  status: VerificationStatus;
  timestamp: string;
  dateFormatted?: string;
  claimsCount: number;
  supportedCount: number;
  contradictedCount: number;
  unknownCount: number;
  evidenceCount: number;
  model: string;
  modelsUsed?: string[];
  claims?: ClaimItem[];
  verificationMode?: 'PRIVATE_KB_ONLY' | 'PRIVATE_KB_PLUS_WEB';
}

export interface ChartPoint {
  name: string;
  claims: number;
  evidence: number;
  verifications: number;
  formattedDate?: string;
}

export interface KnowledgeDocument {
  id: string;
  name: string;
  type: 'PDF' | 'DOCX' | 'CSV' | 'TXT' | 'MD';
  size: string;
  status: 'Indexed' | 'Processing' | 'Failed';
  uploadedDate: string;
  chunksCount?: number;
  category?: string;
  reliabilityScore?: number;
  description?: string;
}

export interface ModelResponse {
  model: string;
  provider: string;
  text: string;
  status: 'Waiting' | 'Running' | 'Completed' | 'Failed' | 'Unavailable';
  latencyMs?: number;
  tokensUsed?: number;
  claimsCount?: number;
  errorReason?: string;
}

export interface ClaimComparisonItem {
  id: string;
  statement: string;
  modelAgreement: {
    agreeCount: number;
    totalModels: number;
    consensusNote: string;
  };
  evidenceSourcesCount: number;
  verificationVerdict: VerificationStatus;
  confidence: number;
  evidenceList: {
    source: string;
    title: string;
    domain: string;
    url: string;
    retrievedTime: string;
    excerpt: string;
    type: 'Primary Research' | 'Government/Regulatory' | 'Benchmark Report' | 'Internal KB';
  }[];
  modelJudgments: {
    model: string;
    verdict: VerificationStatus;
    reasoning: string;
  }[];
}

export interface ChatEvaluation {
  id: string;
  overallDecision: VerificationStatus;
  claimsAnalyzed: number;
  evidenceSourcesCount: number;
  modelsEvaluatedCount: number;
  decisionRationale: string;
  claims: ClaimComparisonItem[];
  modelJudgmentsSummary: {
    model: string;
    verdict: VerificationStatus;
    notes: string;
  }[];
  finalVerifaiDecision: VerificationStatus;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  modelResponses?: ModelResponse[];
  evaluation?: ChatEvaluation;
  verifiedRecordId?: string;
}

export interface Conversation {
  id: string;
  title: string;
  updatedAt: string;
  messageCount: number;
  models: string[];
  messages: ChatMessage[];
}

export interface ModelLeaderboardEntry {
  rank: number;
  model: string;
  provider: string;
  version: string;
  overallScore: number;
  categories: {
    factualSupport: number;
    evidenceSupport: number;
    contradictionDetection: number;
    unknownHandling: number;
    claimVerification: number;
  };
  evaluationsCount: number;
  lastEvaluated: string;
  strengths: string[];
  limitations: string[];
}

export interface ModelMetadata {
  id: string;
  name: string;
  family: string;
  provider: string;
  modelType: 'proprietary' | 'open-weight' | 'local';
  capabilities: string[];
  contextWindow: number;
  maxOutputTokens?: number;
  recommended: boolean;
  description?: string;
  isConnected: boolean;
  tier?: string;
}

export interface ProviderCatalog {
  provider: string;
  name: string;
  category: 'cloud' | 'local' | 'router';
  status: 'connected' | 'not_configured' | 'available';
  docsUrl: string;
  models: ModelMetadata[];
}

export interface AIProvider {
  id: string;
  name: string;
  category: 'cloud' | 'local' | 'router';
  status: 'Connected' | 'Not Connected' | 'Unavailable' | 'Error';
  models: string[];
  configuredAt?: string;
  keyMasked?: string;
  apiKey?: string;
  baseUrl?: string;
  organizationId?: string;
  keyLabel?: string;
  docsUrl?: string;
}

export interface UserSettings {
  profile: {
    fullName: string;
    email: string;
    avatarUrl?: string;
    organization: string;
  };
  verification: {
    defaultMode: 'PRIVATE_KB_ONLY' | 'PRIVATE_KB_PLUS_WEB';
    defaultModels: string[];
    evidenceDetailLevel: 'summary' | 'granular';
    autoReverify: boolean;
  };
  appearance: {
    theme: 'light' | 'dark' | 'system';
    density: 'comfortable' | 'compact';
    motion: 'full' | 'reduced';
  };
}

export interface NotificationItem {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  read: boolean;
  type: 'verification' | 'alert' | 'system';
  link?: string;
}

export interface UserProfile {
  name: string;
  email: string;
  role?: string;
  plan?: string;
  avatarSeed?: string;
  verificationsLimit?: number;
  verificationsUsed?: number;
}

export type KnowledgeSource = KnowledgeDocument;
