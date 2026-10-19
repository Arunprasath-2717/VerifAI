/**
 * VerifAI Provider Management API Client
 * Connects to /api/v1/providers endpoints for secure API key configuration and connectivity testing.
 */

import { apiClient } from './client';
import type { AIProvider } from '../types';

export interface BackendProviderResponse {
  id: string;
  name: string;
  category: 'cloud' | 'local' | 'router';
  status: 'Connected' | 'Not Connected' | 'Unavailable' | 'Error';
  models: string[];
  configured_at?: string | null;
  key_masked?: string | null;
  base_url?: string | null;
  organization_id?: string | null;
  key_label?: string | null;
  docs_url?: string | null;
}

export interface BackendProviderListResponse {
  providers: BackendProviderResponse[];
}

export interface BackendProviderKeyUpdateRequest {
  api_key?: string;
  apiKey?: string;
  base_url?: string;
  baseUrl?: string;
  organization_id?: string;
  organizationId?: string;
  key_label?: string;
  keyLabel?: string;
  name?: string;
  models?: string[];
  category?: 'cloud' | 'local' | 'router';
}

export interface BackendProviderKeyUpdateResponse {
  success?: boolean;
  message?: string;
  provider?: BackendProviderResponse;
}

export interface BackendProviderTestResponse {
  id?: string;
  success: boolean;
  status?: string;
  message: string;
  latency_ms?: number;
}

export function adaptBackendProvider(p: BackendProviderResponse | any): AIProvider {
  return {
    id: p.id,
    name: p.name,
    category: p.category,
    status: p.status,
    models: p.models || [],
    configuredAt: p.configuredAt || p.configured_at || undefined,
    keyMasked: p.keyMasked || p.key_masked || undefined,
    baseUrl: p.baseUrl || p.base_url || undefined,
    organizationId: p.organizationId || p.organization_id || undefined,
    keyLabel: p.keyLabel || p.key_label || undefined,
    docsUrl: p.docsUrl || p.docs_url || undefined,
  };
}

export const providersApi = {
  async listProviders(): Promise<AIProvider[]> {
    const resp = await apiClient<any>('/providers', {
      method: 'GET',
    });
    const items = Array.isArray(resp) ? resp : (resp?.providers || []);
    return items.map(adaptBackendProvider);
  },

  async saveKey(
    providerId: string,
    data: BackendProviderKeyUpdateRequest
  ): Promise<AIProvider> {
    const payload = {
      apiKey: data.apiKey || data.api_key || '',
      baseUrl: data.baseUrl || data.base_url || null,
      organizationId: data.organizationId || data.organization_id || null,
      keyLabel: data.keyLabel || data.key_label || null,
      name: data.name || null,
      models: data.models || [],
      category: data.category || 'cloud',
    };
    const resp = await apiClient<any>(`/providers/${providerId}/key`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return adaptBackendProvider(resp?.provider || resp);
  },

  async unlinkKey(providerId: string): Promise<any> {
    const resp = await apiClient<any>(`/providers/${providerId}/key`, {
      method: 'DELETE',
    });
    return resp?.provider ? adaptBackendProvider(resp.provider) : resp;
  },

  async testConnection(providerId: string): Promise<BackendProviderTestResponse> {
    return apiClient<BackendProviderTestResponse>(`/providers/${providerId}/test`, {
      method: 'POST',
    });
  },
};
