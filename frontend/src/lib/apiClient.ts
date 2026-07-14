import { getToken, setToken } from '@/lib/authToken';
import { ApiError, isApiErrorBody } from '@/lib/errors';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
);

type QueryValue = string | number | boolean | null | undefined;

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  body?: unknown;
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = new URL(`${BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, signal } = options;

  const headers: Record<string, string> = {};
  if (body) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch {
    throw new ApiError(0, 'network_error', 'Unable to reach the server.');
  }

  // Session expired or revoked: clear the stored token and bounce to login.
  if (response.status === 401 && token) {
    setToken(null);
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const raw: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    if (isApiErrorBody(raw)) {
      throw new ApiError(
        response.status,
        raw.error.code,
        raw.error.message,
        raw.error.details,
      );
    }
    throw new ApiError(response.status, 'http_error', `Request failed (${response.status}).`);
  }

  return raw as T;
}
