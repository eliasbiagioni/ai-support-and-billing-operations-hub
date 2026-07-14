const STORAGE_KEY = 'sl_access_token';

let token: string | null =
  typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;

export function getToken(): string | null {
  return token;
}

export function setToken(next: string | null): void {
  token = next;
  if (typeof localStorage === 'undefined') return;
  if (next) {
    localStorage.setItem(STORAGE_KEY, next);
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}
