export interface AIModel {
  id: string;
  name: string;
  provider: string;
  description: string;
  isDefault?: boolean;
}

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  model?: string;
  verificationId?: string;
  verificationStatus?: 'unverified' | 'pending' | 'completed' | 'failed';
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  model: string;
  messages: Message[];
}

export type VerdictType = 'SUPPORTED' | 'REFUTED' | 'MIXED' | 'NOT_ENOUGH_INFO' | 'UNVERIFIED';

export interface VerificationResult {
  verification_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  verdict: VerdictType;
  trust_score: number;
  created_at: string;
  summary?: string;
  message_id?: string;
  conversation_id?: string;
}

export interface Claim {
  claim_id: string;
  verification_id: string;
  text: string;
  verdict: VerdictType;
  confidence: number;
}

export interface Evidence {
  evidence_id: string;
  claim_id: string;
  source_title: string;
  source_url: string;
  snippet: string;
  relevance_score: number;
  supports_claim: boolean;
}

export interface ExtensionCapturePayload {
  captured_text: string;
  url?: string;
  page_title?: string;
  source_app?: string;
  selector?: string;
}

export interface ExtensionConfig {
  version: string;
  api_endpoint: string;
  auto_capture_enabled: boolean;
  min_selection_length: number;
}

export interface CaptureReportPayload {
  url?: string;
  page_title?: string;
  reason: string;
  html_snippet?: string;
  timestamp: string;
}
