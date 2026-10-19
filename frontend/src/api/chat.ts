/**
 * VerifAI Chat & Multi-LLM API Client
 * Connects to /api/v1/chat endpoints with full multi-model support and SSE streaming.
 */

import { apiClient, getAuthToken } from './client';
import { adaptBackendVerificationToRecord } from './verification';
import type {
  Conversation,
  ChatMessage,
  ModelResponse,
  ChatEvaluation,
  ClaimComparisonItem,
  VerificationStatus,
} from '../types';

export interface BackendLLMModelSelection {
  provider: string;
  model_name: string;
}

export interface BackendLLMRunResponse {
  id: string;
  conversation_id: string;
  message_id?: string;
  owner_id: string;
  provider: string;
  model_name: string;
  prompt: string;
  response?: string | null;
  status: string;
  started_at: string;
  completed_at?: string | null;
  latency_ms?: number | null;
  error_code?: string | null;
  error_message?: string | null;
  verification?: any | null;
}

export interface BackendMessageResponse {
  id: string;
  conversation_id: string;
  owner_id: string;
  role: string;
  content: string;
  sequence_number: number;
  created_at: string;
  llm_runs: BackendLLMRunResponse[];
}

export interface BackendConversationResponse {
  id: string;
  owner_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface BackendConversationDetailResponse {
  id: string;
  owner_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: BackendMessageResponse[];
}

export interface BackendConversationListResponse {
  total: number;
  limit: number;
  offset: number;
  items: BackendConversationResponse[];
}

export interface BackendChatPromptRequest {
  prompt: string;
  models: BackendLLMModelSelection[];
  verify?: boolean;
  options?: {
    use_web_evidence?: boolean;
    use_knowledge_base?: boolean;
    strictness?: string;
  };
}

export interface BackendChatPromptResponse {
  conversation_id: string;
  user_message_id: string;
  prompt: string;
  runs: BackendLLMRunResponse[];
  cross_model_disagreement: boolean;
  disagreement_summary?: string | null;
}

/** Map backend status string to frontend ModelResponse status */
function mapRunStatus(status: string): 'Waiting' | 'Running' | 'Completed' | 'Failed' | 'Unavailable' {
  switch (status?.toUpperCase()) {
    case 'COMPLETED':
      return 'Completed';
    case 'FAILED':
      return 'Failed';
    case 'STREAMING':
    case 'PENDING':
      return 'Running';
    case 'UNAVAILABLE':
      return 'Unavailable';
    default:
      return 'Completed';
  }
}

/** Convert a backend run with verification into a ChatEvaluation */
function buildChatEvaluationFromRuns(runs: BackendLLMRunResponse[], disagreementSummary?: string | null): ChatEvaluation | undefined {
  // Find first run with verification payload
  const runWithVerif = runs.find((r) => r.verification);
  if (!runWithVerif || !runWithVerif.verification) {
    return undefined;
  }

  const verif = runWithVerif.verification;
  const verifRecord = adaptBackendVerificationToRecord(verif);

  const claims: ClaimComparisonItem[] = (verifRecord.claims || []).map((c) => ({
    id: c.id,
    statement: c.statement,
    modelAgreement: {
      agreeCount: runs.filter((r) => r.status === 'COMPLETED').length,
      totalModels: runs.length,
      consensusNote: disagreementSummary || 'Model consensus evaluated against verified evidence.',
    },
    evidenceSourcesCount: c.evidenceSnippet ? 1 : 0,
    verificationVerdict: c.status,
    confidence: c.confidence,
    evidenceList: c.evidenceSnippet
      ? [
          {
            source: c.sourceTitle || 'Retrieved Evidence',
            title: c.sourceTitle || 'Verified Document Source',
            domain: c.domain || 'knowledge-base',
            url: c.sourceUrl || '#',
            retrievedTime: c.retrievedAt || new Date().toISOString(),
            excerpt: c.evidenceSnippet,
            type: 'Internal KB',
          },
        ]
      : [],
    modelJudgments: runs.map((r) => ({
      model: r.model_name,
      verdict: c.status,
      reasoning: r.error_message || 'Assessed against factual audit evidence.',
    })),
  }));

  const modelJudgmentsSummary = runs.map((r) => ({
    model: r.model_name,
    verdict: verifRecord.status,
    notes: r.status === 'COMPLETED' ? `Completed in ${r.latency_ms?.toFixed(0) || '0'}ms` : (r.error_message || 'Run failed'),
  }));

  return {
    id: verif.verification_id || verif.id || `eval-${Date.now()}`,
    overallDecision: verifRecord.status,
    claimsAnalyzed: verifRecord.claimsCount,
    evidenceSourcesCount: verifRecord.evidenceCount,
    modelsEvaluatedCount: runs.length,
    decisionRationale: verifRecord.summary || disagreementSummary || 'Multi-model claims verified via authoritative backend verification pipeline.',
    claims,
    modelJudgmentsSummary,
    finalVerifaiDecision: verifRecord.status,
  };
}

/** Adapt a backend conversation detail to the frontend Conversation interface */
export function adaptBackendConversation(detail: BackendConversationDetailResponse): Conversation {
  const messages: ChatMessage[] = [];
  const modelSet = new Set<string>();

  for (const m of detail.messages || []) {
    if (m.role === 'user') {
      messages.push({
        id: m.id,
        sender: 'user',
        content: m.content,
        timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });
    } else {
      const modelResponses: ModelResponse[] = (m.llm_runs || []).map((r) => {
        modelSet.add(r.model_name);
        return {
          model: r.model_name,
          provider: r.provider,
          text: r.response || (r.status === 'FAILED' ? `[Model Error]: ${r.error_message || 'Provider execution failed'}` : ''),
          status: mapRunStatus(r.status),
          latencyMs: r.latency_ms ? Math.round(r.latency_ms) : undefined,
          errorReason: r.error_message || undefined,
        };
      });

      const evaluation = buildChatEvaluationFromRuns(m.llm_runs || []);

      messages.push({
        id: m.id,
        sender: 'assistant',
        content: m.content,
        timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        modelResponses,
        evaluation,
        verifiedRecordId: evaluation?.id,
      });
    }
  }

  return {
    id: detail.id,
    title: detail.title,
    updatedAt: detail.updated_at,
    messageCount: messages.length,
    models: Array.from(modelSet),
    messages,
  };
}

export const chatApi = {
  async listConversations(params?: { search?: string; limit?: number; offset?: number }): Promise<BackendConversationListResponse> {
    return apiClient<BackendConversationListResponse>('/chat/conversations', {
      method: 'GET',
      params,
    });
  },

  async createConversation(title: string = 'New Conversation'): Promise<BackendConversationResponse> {
    return apiClient<BackendConversationResponse>('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },

  async getConversation(conversationId: string): Promise<BackendConversationDetailResponse> {
    return apiClient<BackendConversationDetailResponse>(`/chat/conversations/${conversationId}`, {
      method: 'GET',
    });
  },

  async deleteConversation(conversationId: string): Promise<{ deleted: boolean; conversation_id: string }> {
    return apiClient<{ deleted: boolean; conversation_id: string }>(`/chat/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  },

  async sendMessage(conversationId: string, request: BackendChatPromptRequest): Promise<BackendChatPromptResponse> {
    return apiClient<BackendChatPromptResponse>(`/chat/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * SSE Stream prompt execution lifecycle events
   */
  async streamMessage(
    conversationId: string,
    request: BackendChatPromptRequest,
    onEvent: (eventType: string, data: any) => void,
    onError: (err: Error) => void,
    onComplete: (finalData?: BackendChatPromptResponse) => void
  ): Promise<() => void> {
    const controller = new AbortController();
    const token = getAuthToken();
    const url = `/api/v1/chat/conversations/${conversationId}/messages/stream`;

    (async () => {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            'X-Request-ID': `req-sse-${Date.now()}`,
          },
          body: JSON.stringify(request),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`SSE streaming failed with status ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Streaming response body unavailable.');
        }

        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';

          for (const block of parts) {
            if (!block.trim()) continue;
            let eventType = 'message';
            let dataStr = '';

            const lines = block.split('\n');
            for (const line of lines) {
              if (line.startsWith('event: ')) {
                eventType = line.slice(7).trim();
              } else if (line.startsWith('data: ')) {
                dataStr = line.slice(6).trim();
              }
            }

            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);
                onEvent(eventType, parsed);
                if (eventType === 'COMPLETE') {
                  onComplete(parsed);
                }
              } catch {
                onEvent(eventType, dataStr);
              }
            }
          }
        }

        onComplete();
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          onError(err);
        }
      }
    })();

    return () => controller.abort();
  },
};
