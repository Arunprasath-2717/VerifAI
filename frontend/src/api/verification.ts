import { apiClient } from './client';
import type { VerificationRecord, ClaimItem, VerificationStatus, VerificationEvidence, VerificationJudge, VerificationAuditEntry } from '../types';

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
  document_title?: string | null;
  relevance_score?: number | null;
  authority_score?: number | null;
}

export interface BackendJudgeEvaluation {
  id: string;
  judge_name: string;
  judgment: string;
  confidence?: number | null;
  rationale?: string | null;
  evidence_references?: string[] | null;
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
  const mappedClaims: ClaimItem[] = (job.claims || []).map((c: BackendClaim, index: number) => {
    // Preserve every evidence and judge record, rather than only the first
    // evidence snippet. Tabs must reflect the actual verification response.
    const evidence: VerificationEvidence[] = (c.evidence || []).map((entry, evidenceIndex) => ({
      id: entry.id || `claim-${index}-evidence-${evidenceIndex}`,
      snippet: entry.snippet || '',
      sourceUrl: entry.source_url || undefined,
      sourceTitle: entry.source_title || undefined,
      publisher: entry.publisher || undefined,
      publicationDate: entry.publication_date || undefined,
      retrieverName: entry.retriever_name || undefined,
      evidenceSource: entry.evidence_source || undefined,
      documentTitle: entry.document_title || undefined,
      relevanceScore: typeof entry.relevance_score === 'number' ? entry.relevance_score : undefined,
      authorityScore: typeof entry.authority_score === 'number' ? entry.authority_score : undefined,
    }));
    const judges: VerificationJudge[] = (c.judges || []).map((judge, judgeIndex) => ({
      id: judge.id || `claim-${index}-judge-${judgeIndex}`,
      judgeName: judge.judge_name,
      judgment: judge.judgment,
      confidence: typeof judge.confidence === 'number' ? judge.confidence : undefined,
      rationale: judge.rationale || undefined,
      evidenceReferences: judge.evidence_references || undefined,
    }));
    totalEvidence += evidence.length;
    const topEv = evidence[0];
    return {
      id: c.id || `claim-${index}`,
      statement: c.claim_text || (c as any).statement || '',
      status: (c.verdict || (c as any).status || 'UNKNOWN') as VerificationStatus,
      confidence: typeof c.confidence === 'number' ? c.confidence : undefined,
      evidence,
      judges,
      evidenceSnippet: topEv?.snippet || (c as any).evidenceSnippet,
      sourceTitle: topEv?.sourceTitle || topEv?.publisher || (c as any).sourceTitle,
      sourceUrl: topEv?.sourceUrl || (c as any).sourceUrl,
      domain: topEv?.sourceUrl ? (() => {
        try { return new URL(topEv.sourceUrl).hostname; } catch { return undefined; }
      })() : (c as any).domain,
      retrievedAt: (c as any).retrievedAt,
      explanation: c.explanation || undefined,
      unknownReason: c.unknown_reason || undefined,
      contradictionReason: (c.verdict === 'CONTRADICTED' || (c as any).status === 'CONTRADICTED')
        ? c.explanation || (c as any).contradictionReason : undefined,
    };
  });
  const auditTrail: VerificationAuditEntry[] = (job.audit_trail || []).map(
    (event: BackendAuditRecord, index: number) => ({
      id: event.id || `audit-${index}`,
      stage: event.stage,
      eventType: event.event_type,
      status: event.status,
      message: event.message,
      timestamp: event.timestamp,
    })
  );

  // Distinguish pipeline status from actual claim judgments. Missing, partial,
  // or failed evaluations must never be interpreted as fully SUPPORTED.
  let overallStatus: VerificationStatus = 'UNKNOWN';
  if (job.status === 'FAILED' || job.status === 'UNAVAILABLE') {
    overallStatus = job.status;
  } else if (job.contradicted_claims > 0 || job.status === 'CONTRADICTED') {
    overallStatus = 'CONTRADICTED';
  } else if (job.unknown_claims > 0 || job.status === 'UNKNOWN') {
    overallStatus = 'UNKNOWN';
  } else if (job.supported_claims > 0 && job.supported_claims === job.total_claims) {
    overallStatus = 'SUPPORTED';
  }

  const recordId = job.verification_id || job.id || job.job_id;
  if (!recordId) {
    throw new Error('Verification response does not contain a valid record ID.');
  }
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
    model: 'Backend verification',
    claims: mappedClaims,
    auditTrail,
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
      // Verification may perform multiple sequential retrieval/judge operations.
      timeoutMs: 120000,
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
