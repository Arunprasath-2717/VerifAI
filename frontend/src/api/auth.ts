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
  password: string;
  username?: string;
  full_name?: string;
  terms_accepted?: boolean;
}

export interface LoginPayload {
  email?: string;
  username?: string;
  email_or_username?: string;
  username_or_email?: string;
  password: string;
}

export const authApi = {
  async register(data: RegisterPayload): Promise<UserResponse> {
    const base = (data.username || data.full_name || data.email.split('@')[0] || 'user')
      .replace(/[^a-zA-Z0-9_-]/g, '_')
      .toLowerCase();
    
    let cleanUsername = base.length < 3 ? `${base}_usr` : base.slice(0, 64);

    try {
      const user = await apiClient<UserResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          email: data.email.trim().toLowerCase(),
          username: cleanUsername,
          password: data.password,
          terms_accepted: data.terms_accepted ?? true,
        }),
      });

      // Automatically authenticate session upon successful registration
      try {
        await authApi.login({
          email_or_username: data.email.trim().toLowerCase(),
          password: data.password,
        });
      } catch {}

      return user;
    } catch (err: any) {
      // If username was already taken, retry with random suffix if user didn't specify custom username
      if (err?.message?.toLowerCase().includes('username') && !data.username) {
        const uniqueUsername = `${cleanUsername.slice(0, 56)}_${Math.floor(1000 + Math.random() * 9000)}`;
        const user = await apiClient<UserResponse>('/auth/register', {
          method: 'POST',
          body: JSON.stringify({
            email: data.email.trim().toLowerCase(),
            username: uniqueUsername,
            password: data.password,
          }),
        });

        try {
          await authApi.login({
            email_or_username: data.email.trim().toLowerCase(),
            password: data.password,
          });
        } catch {}

        return user;
      }
      throw err;
    }
  },

  async login(data: LoginPayload): Promise<TokenResponse> {
    const identifier = (data.email_or_username || data.username_or_email || data.email || data.username || '').trim();
    
    const res = await apiClient<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email_or_username: identifier,
        password: data.password,
      }),
    });

    if (res.access_token) {
      setAuthToken(res.access_token);
    }
    return res;
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
