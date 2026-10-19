/**
 * VerifAI Central API Client
 * Normalizes HTTP requests, handles Bearer authentication, and standardizes error responses.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api/v1'
    : '/api/v1');

export interface ApiErrorDetails {
  code?: string;
  message: string;
  status: number;
  details?: any;
  requestId?: string;
}

export class ApiError extends Error {
  public status: number;
  public code?: string;
  public details?: any;
  public requestId?: string;

  constructor(error: ApiErrorDetails) {
    super(error.message);
    this.name = 'ApiError';
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
    this.requestId = error.requestId;
  }
}

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem('verifai_token');
  } catch {
    return null;
  }
}

export function setAuthToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem('verifai_token', token);
      localStorage.setItem('verifai_authenticated', 'true');
    } else {
      localStorage.removeItem('verifai_token');
      localStorage.removeItem('verifai_authenticated');
    }
  } catch {}
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
  timeoutMs?: number;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers: customHeaders, timeoutMs = 25000, ...fetchOptions } = options;

  let url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, val] of Object.entries(params)) {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val));
      }
    }
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const token = getAuthToken();
  const headers = new Headers(customHeaders);

  if (!headers.has('Content-Type') && !(fetchOptions.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
  if (!headers.has('X-Request-ID')) {
    headers.set('X-Request-ID', requestId);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort(new Error(`Request timed out after ${timeoutMs}ms`));
  }, timeoutMs);

  if (fetchOptions.signal) {
    fetchOptions.signal.addEventListener('abort', () => controller.abort());
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
  } catch (err: any) {
    if (controller.signal.aborted || err?.name === 'AbortError') {
      throw new ApiError({
        message: `Request timed out after ${Math.round(timeoutMs / 1000)}s. Please try again or check backend service.`,
        status: 408,
        code: 'REQUEST_TIMEOUT',
        requestId,
      });
    }
    throw new ApiError({
      message: err?.message || 'Network connection failed. Verify backend service is reachable.',
      status: 0,
      code: 'NETWORK_ERROR',
      requestId,
    });
  } finally {
    clearTimeout(timeoutId);
  }

  const respRequestId = response.headers.get('X-Request-ID') || requestId;

  if (!response.ok) {
    let errorData: any = null;
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText };
    }

    const message = errorData?.error?.message || errorData?.detail || errorData?.message || `Request failed with status ${response.status}`;
    const code = errorData?.error?.code || errorData?.code || `HTTP_${response.status}`;

    throw new ApiError({
      message,
      status: response.status,
      code,
      details: errorData?.error?.details || errorData?.details,
      requestId: respRequestId,
    });
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
