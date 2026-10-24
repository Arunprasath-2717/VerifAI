import { apiClient, setAuthToken } from './client';

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  role?: string;
  user_id?: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  terms_accepted: boolean;
}

export interface UsernameAvailability {
  username: string;
  available: boolean;
}

export interface LoginPayload {
  email_or_username: string;
  password: string;
}

export const authApi = {
  async checkUsername(username: string): Promise<UsernameAvailability> {
    return apiClient<UsernameAvailability>('/auth/username-availability', {
      method: 'GET',
      params: { username: username.trim().toLowerCase() },
      timeoutMs: 10000,
    });
  },

  async register(data: RegisterPayload): Promise<UserResponse> {
    // Never silently replace a requested username with a random suffix.
    // Availability previews are advisory; the backend unique index is final.
    return apiClient<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username: data.username.trim().toLowerCase(),
        email: data.email.trim().toLowerCase(),
        password: data.password,
        terms_accepted: data.terms_accepted,
      }),
    });
  },

  async login(data: LoginPayload): Promise<TokenResponse> {
    const result = await apiClient<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email_or_username: data.email_or_username.trim(),
        password: data.password,
      }),
    });
    if (result.access_token) setAuthToken(result.access_token);
    return result;
  },

  async firebaseAuth(
    idToken: string, 
    displayName?: string,
    options?: { is_signup?: boolean; terms_accepted?: boolean }
  ): Promise<TokenResponse> {
    const payload: { 
      id_token: string; 
      display_name?: string;
      is_signup?: boolean;
      terms_accepted?: boolean;
    } = { id_token: idToken };
    if (displayName) {
      payload.display_name = displayName;
    }
    if (options?.is_signup !== undefined) {
      payload.is_signup = options.is_signup;
    }
    if (options?.terms_accepted !== undefined) {
      payload.terms_accepted = options.terms_accepted;
    }
    const res = await apiClient<TokenResponse>('/auth/firebase', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (res.access_token) {
      setAuthToken(res.access_token);
    }
    return res;
  },

  async getMe(): Promise<UserResponse> {
    return apiClient<UserResponse>('/auth/me', {
      method: 'GET',
    });
  },

  logout(): void {
    setAuthToken(null);
  },
};
