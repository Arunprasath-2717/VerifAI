/**
 * VerifAI History & User Data Lifecycle API Client
 * Connects to /api/v1/history endpoints.
 */

import { apiClient } from './client';
import { adaptBackendVerificationToRecord } from './verification';
import type { VerificationRecord, Conversation } from '../types';

export interface BackendAuditHistoryItem {
  id: string;
  verification_id: string;
  stage: string;
  event_type: string;
  status: string;
  message: string;
  details?: any;
  timestamp: string;
}

export interface BackendAuditHistoryResponse {
  total: number;
  limit: number;
  offset: number;
  items: BackendAuditHistoryItem[];
}

export interface BackendPurgeResponse {
  success: boolean;
  deleted_conversations: number;
  deleted_verifications: number;
  deleted_documents: number;
  message: string;
}

export const historyApi = {
  async listVerifications(params?: {
    verdict?: string;
    job_status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ total: number; items: VerificationRecord[] }> {
    const resp = await apiClient<any>('/history/verifications', {
      method: 'GET',
      params,
    });
    return {
      total: resp.total || 0,
      items: (resp.items || []).map(adaptBackendVerificationToRecord),
    };
  },

  async getVerification(verificationId: string): Promise<VerificationRecord> {
    const resp = await apiClient<any>(`/history/verifications/${verificationId}`, {
      method: 'GET',
    });
    return adaptBackendVerificationToRecord(resp);
  },

  async deleteVerification(verificationId: string): Promise<void> {
    await apiClient(`/history/verifications/${verificationId}`, {
      method: 'DELETE',
    });
  },

  async listConversations(params?: {
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ total: number; items: any[] }> {
    const resp = await apiClient<any>('/history/conversations', {
      method: 'GET',
      params,
    });
    return {
      total: resp.total || 0,
      items: resp.items || [],
    };
  },

  async listAudit(params?: { limit?: number; offset?: number }): Promise<BackendAuditHistoryResponse> {
    return apiClient<BackendAuditHistoryResponse>('/history/audit', {
      method: 'GET',
      params,
    });
  },

  async purgeUserData(): Promise<BackendPurgeResponse> {
    return apiClient<BackendPurgeResponse>('/history/purge', {
      method: 'DELETE',
    });
  },
};
