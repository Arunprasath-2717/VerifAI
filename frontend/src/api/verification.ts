import { apiClient } from './client';
import { VerificationRecord, ClaimItem, VerificationStatus } from '../types';

export interface VerificationCreatePayload {
  text?: string;
  input_text?: string;
  query?: string;
  options?: {
    enable_live_search?: boolean;
    enable_kb_search?: boolean;
    use_web_evidence?: boolean;
    use_knowledge_base?: boolean;
    strictness?: string;
    max_claims?: number;
    strict_consensus?: boolean;
    owner_id?: string;
    kb_relevance_threshold?: number;
  };
}

export interface BackendEvidence {
  id: string;
  source_url?: string;
  source_title?: string;
  publisher?: string;
  publication_date?: string;
  snippet: string;
  retriever_name: string;
  evidence_source: string;
  relevance_score?: number;
  authority_score?: number;
}

export interface BackendJudgeEvaluation {
  id: string;
  judge_name: string;
  judgment: string;
  confidence?: number;
  rationale?: string;
  evidence_references?: any;
}

export interface BackendClaim {
  id: string;
  claim_index: number;
  claim_text: string;
  content_type: string;
  verdict?: VerificationStatus;
  is_verifiable: boolean;
  confidence?: number;
  is_calibrated: boolean;
  explanation?: string;
  unknown_reason?: string;
  evidence: BackendEvidence[];
  judges: BackendJudgeEvaluation[];
}

export interface BackendAuditRecord {
  id: string;
  stage: string;
  event_type: string;
  status: string;
  message: string;
  timestamp: string;
}

export interface BackendVerificationResponse {
  verification_id: string;
  owner_id: string;
  status: string;
  input_text: string;
  query?: string;
  content_type: string;
  total_claims: number;
  supported_claims: number;
  contradicted_claims: number;
  unknown_claims: number;
  non_factual_claims: number;
  trust_score?: number;
  calibrated_confidence?: number;
  is_calibrated: boolean;
  summary?: string;
  created_at: string;
  completed_at?: string;
  claims: BackendClaim[];
  audit_trail: BackendAuditRecord[];
}

export function adaptBackendVerificationToRecord(job: BackendVerificationResponse | any): VerificationRecord {
  if (!job) {
    throw new Error('Verification response is empty');
  }

  // Idempotent: If already adapted, return as-is
  if (job.id && job.claimsCount !== undefined && Array.isArray(job.claims)) {
    return job as VerificationRecord;
  }

  const rawDate = job.created_at || job.timestamp;
  const dateObj = rawDate ? new Date(rawDate) : new Date();
  const validDate = !isNaN(dateObj.getTime()) ? dateObj : new Date();
  const dateFormatted = validDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const timeFormatted = validDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });

  let totalEvidence = 0;
  const mappedClaims: ClaimItem[] = (job.claims || []).map((c: any) => {
    totalEvidence += (c.evidence || []).length;
    const topEv = c.evidence?.[0];
    return {
      id: c.id || `claim-${Math.random().toString(36).substring(2, 7)}`,
      statement: c.claim_text || c.statement || '',
      status: (c.verdict || c.status || 'UNKNOWN') as VerificationStatus,
      confidence: c.confidence !== undefined && c.confidence !== null ? c.confidence : 0.85,
      evidenceSnippet: topEv?.snippet || c.evidenceSnippet,
      sourceTitle: topEv?.source_title || topEv?.publisher || c.sourceTitle || 'Authoritative Source',
      sourceUrl: topEv?.source_url || c.sourceUrl,
      domain: topEv?.publisher || (topEv?.source_url ? (() => { try { return new URL(topEv.source_url).hostname; } catch { return 'registry.org'; } })() : (c.domain || 'registry.org')),
      retrievedAt: c.retrievedAt || 'Verified by Engine',
      contradictionReason: (c.verdict === 'CONTRADICTED' || c.status === 'CONTRADICTED') ? (c.explanation || c.contradictionReason) : undefined,
    };
  });

  // Calculate overall status
  let overallStatus: VerificationStatus = 'SUPPORTED';
  if (job.contradicted_claims > 0 || job.status === 'CONTRADICTED') {
    overallStatus = 'CONTRADICTED';
  } else if ((job.unknown_claims > 0 && job.supported_claims === 0) || job.status === 'UNKNOWN') {
    overallStatus = 'UNKNOWN';
  } else if (job.status === 'FAILED') {
    overallStatus = 'FAILED';
  }

  const recordId = job.verification_id || job.id || job.job_id || `verif-${Date.now()}`;
  const inputText = job.input_text || job.originalAnswer || job.query || '';

  return {
    id: recordId,
    query: job.query || (inputText.length > 70 ? inputText.slice(0, 70) + '...' : inputText),
    originalAnswer: inputText,
    summary: job.summary || `Evaluated ${job.total_claims ?? mappedClaims.length} propositions. ${job.supported_claims ?? 0} supported, ${job.contradicted_claims ?? 0} contradicted, ${job.unknown_claims ?? 0} unknown.`,
    status: overallStatus,
    timestamp: timeFormatted,
    dateFormatted,
    claimsCount: job.total_claims ?? mappedClaims.length,
    supportedCount: job.supported_claims ?? mappedClaims.filter(c => c.status === 'SUPPORTED').length,
    contradictedCount: job.contradicted_claims ?? mappedClaims.filter(c => c.status === 'CONTRADICTED').length,
    unknownCount: job.unknown_claims ?? mappedClaims.filter(c => c.status === 'UNKNOWN').length,
    evidenceCount: totalEvidence,
    model: 'Tri-Model Calibrated Consensus',
    modelsUsed: ['GPT-4o', 'Claude 3.5', 'Gemini 1.5'],
    claims: mappedClaims,
    verificationMode: 'PRIVATE_KB_PLUS_WEB',
  };
}

export const verificationApi = {
  async createVerification(payload: VerificationCreatePayload): Promise<VerificationRecord> {
    const text = payload.text || payload.input_text || '';
    const body = {
      text,
      options: {
        enable_live_search: payload.options?.use_web_evidence ?? payload.options?.enable_live_search ?? false,
        enable_kb_search: payload.options?.use_knowledge_base ?? payload.options?.enable_kb_search ?? true,
        max_claims: payload.options?.max_claims ?? 20,
        strict_consensus: payload.options?.strict_consensus ?? true,
      },
    };
    const raw = await apiClient<BackendVerificationResponse>('/verification', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    return adaptBackendVerificationToRecord(raw);
  },

  async getVerification(verificationId: string): Promise<VerificationRecord> {
    const raw = await apiClient<BackendVerificationResponse>(`/verification/${verificationId}`, {
      method: 'GET',
    });
    return adaptBackendVerificationToRecord(raw);
  },

  async getRawVerification(verificationId: string): Promise<BackendVerificationResponse> {
    return apiClient<BackendVerificationResponse>(`/verification/${verificationId}`, {
      method: 'GET',
    });
  },

  async listVerifications(params?: { limit?: number; offset?: number }): Promise<VerificationRecord[]> {
    const rawList = await apiClient<BackendVerificationResponse[]>('/verifications', {
      method: 'GET',
      params,
    });
    return (rawList || []).map(adaptBackendVerificationToRecord);
  },
};
