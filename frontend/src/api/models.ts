/**
 * VerifAI Model Ecosystem and Leaderboard API Client
 * Connects to /api/v1/models and /api/v1/models/leaderboard
 */

import { apiClient } from './client';
import type { ModelLeaderboardEntry, ProviderCatalog, ModelMetadata } from '../types';

export interface BackendModelItem {
  id: string;
  name: string;
  family: string;
  model_type: 'proprietary' | 'open-weight' | 'local';
  capabilities: string[];
  context_window: number;
  max_output_tokens?: number;
  recommended: boolean;
  description?: string;
}

export interface BackendProviderCatalog {
  provider: string;
  name: string;
  category: 'cloud' | 'local' | 'router';
  status: 'connected' | 'not_configured' | 'available';
  docs_url: string;
  models: BackendModelItem[];
}

export interface BackendModelCatalogResponse {
  total_providers: number;
  total_models: number;
  recommended_defaults: string[];
  providers: BackendProviderCatalog[];
}

export interface BackendLeaderboardResponse {
  total_models: number;
  updated_at: string;
  models: ModelLeaderboardEntry[];
}

export function adaptBackendProviderCatalog(p: BackendProviderCatalog): ProviderCatalog {
  return {
    provider: p.provider,
    name: p.name,
    category: p.category,
    status: p.status,
    docsUrl: p.docs_url,
    models: (p.models || []).map((m): ModelMetadata => ({
      id: m.id,
      name: m.name,
      family: m.family,
      provider: p.name,
      modelType: m.model_type,
      capabilities: m.capabilities,
      contextWindow: m.context_window,
      maxOutputTokens: m.max_output_tokens,
      recommended: m.recommended,
      description: m.description,
      isConnected: p.status === 'connected',
    })),
  };
}

export const modelsApi = {
  async getModelCatalog(): Promise<{ providers: ProviderCatalog[]; recommended: string[] }> {
    const resp = await apiClient<BackendModelCatalogResponse>('/models', {
      method: 'GET',
    });
    return {
      providers: (resp.providers || []).map(adaptBackendProviderCatalog),
      recommended: resp.recommended_defaults || [],
    };
  },

  async getModelLeaderboard(): Promise<ModelLeaderboardEntry[]> {
    const resp = await apiClient<any>('/models/leaderboard', {
      method: 'GET',
    });
    if (Array.isArray(resp)) {
      return resp;
    }
    return resp?.models || [];
  },
};
