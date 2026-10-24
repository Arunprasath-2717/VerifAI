/**
 * VerifAI Knowledge Base API Client
 * Connects to /api/v1/knowledge endpoints for document management, uploads, and search.
 */

import { apiClient, getAuthToken } from './client';
import type { KnowledgeDocument } from '../types';

export interface BackendChunkResponse {
  id: string;
  document_id: string;
  owner_id: string;
  chunk_index: number;
  text: string;
  start_offset: number;
  end_offset: number;
  metadata_json?: any;
  created_at: string;
}

export interface BackendDocumentResponse {
  id: string;
  owner_id: string;
  filename: string;
  title: string;
  description?: string | null;
  content_type: string;
  size_bytes: number;
  content_hash: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface BackendDocumentDetailResponse extends BackendDocumentResponse {
  chunks: BackendChunkResponse[];
}

export interface BackendDocumentListResponse {
  owner_id: string;
  total_documents: number;
  documents: BackendDocumentResponse[];
}

export interface BackendKnowledgeSearchItem {
  document_id: string;
  chunk_id: string;
  owner_id: string;
  document_title: string;
  filename: string;
  chunk_index: number;
  snippet: string;
  relevance_score: number;
  overlap_tokens: number;
  evidence_source: string;
  metadata_json?: any;
}

export interface BackendKnowledgeSearchResponse {
  query: string;
  owner_id: string;
  sufficiency: string;
  threshold_used: number;
  min_overlap_tokens_used: number;
  total_chunks_matched: number;
  results: BackendKnowledgeSearchItem[];
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function detectDocType(filename: string, contentType: string): 'PDF' | 'DOCX' | 'CSV' | 'TXT' | 'MD' {
  const ext = filename.split('.').pop()?.toUpperCase() || '';
  if (ext === 'PDF' || contentType.includes('pdf')) return 'PDF';
  if (ext === 'DOCX' || ext === 'DOC' || contentType.includes('word')) return 'DOCX';
  if (ext === 'CSV' || contentType.includes('csv')) return 'CSV';
  if (ext === 'MD' || ext === 'MARKDOWN') return 'MD';
  return 'TXT';
}

export function adaptBackendDocumentToFrontend(doc: BackendDocumentResponse): KnowledgeDocument {
  return {
    id: doc.id,
    name: doc.title || doc.filename,
    type: detectDocType(doc.filename, doc.content_type),
    size: formatBytes(doc.size_bytes),
    status: 'Indexed',
    uploadedDate: new Date(doc.created_at).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }),
    chunksCount: doc.chunk_count,
    category: doc.content_type.split('/')[1]?.toUpperCase() || 'DOCUMENT',
    // No document reliability score is provided by the indexing API.
    description: doc.description || undefined,
  };
}

export const knowledgeApi = {
  async listDocuments(): Promise<KnowledgeDocument[]> {
    const resp = await apiClient<BackendDocumentListResponse>('/knowledge/documents', {
      method: 'GET',
    });
    return (resp.documents || []).map(adaptBackendDocumentToFrontend);
  },

  async getDocument(documentId: string): Promise<BackendDocumentDetailResponse> {
    return apiClient<BackendDocumentDetailResponse>(`/knowledge/documents/${documentId}`, {
      method: 'GET',
    });
  },

  async createDocument(data: { title: string; text: string; filename?: string; description?: string }): Promise<KnowledgeDocument> {
    const resp = await apiClient<BackendDocumentResponse>('/knowledge/documents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return adaptBackendDocumentToFrontend(resp);
  },

  async uploadFile(file: File, title?: string, description?: string): Promise<KnowledgeDocument> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);

    const doc = await apiClient<BackendDocumentResponse>('/knowledge/upload', {
      method: 'POST',
      body: formData,
    });
    return adaptBackendDocumentToFrontend(doc);
  },

  async deleteDocument(documentId: string): Promise<void> {
    await apiClient(`/knowledge/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  async search(query: string, maxPassages: number = 5): Promise<BackendKnowledgeSearchResponse> {
    return apiClient<BackendKnowledgeSearchResponse>('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query, max_passages: maxPassages }),
    });
  },
};
