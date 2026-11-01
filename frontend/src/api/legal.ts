import { apiClient } from './client';

export interface LegalVersionsResponse {
  terms_version: string;
  privacy_version: string;
  terms_effective_date: string;
  privacy_effective_date: string;
  legal_contact_email: string;
  governing_law: string;
  minimum_age_requirement: string;
}

export interface UserConsentStatusResponse {
  terms_accepted: boolean;
  terms_version?: string;
  privacy_version?: string;
  consented_at?: string;
  requires_reacceptance: boolean;
}

export interface ConsentRecordResponse {
  status: string;
  consent_id: string;
  consented_at: string;
  terms_version: string;
  privacy_version: string;
}

export const legalApi = {
  /**
   * Fetch active legal versions, effective dates, and legal metadata.
   */
  async getVersions(): Promise<LegalVersionsResponse> {
    return apiClient<LegalVersionsResponse>('/legal/versions', {
      method: 'GET',
    });
  },

  /**
   * Check consent status for the currently authenticated user.
   */
  async getConsentStatus(): Promise<UserConsentStatusResponse> {
    return apiClient<UserConsentStatusResponse>('/legal/consent', {
      method: 'GET',
    });
  },

  /**
   * Explicitly record consent for an authenticated user (e.g. during re-acceptance).
   */
  async recordConsent(data: {
    terms_version: string;
    privacy_version: string;
    action_source?: string;
  }): Promise<ConsentRecordResponse> {
    return apiClient<ConsentRecordResponse>('/legal/consent', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
