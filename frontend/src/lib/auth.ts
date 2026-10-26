export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  created_at?: string;
}

const TOKEN_KEY = "nexushunt_auth_token";
const USER_KEY = "nexushunt_auth_user";

export const DEFAULT_USER: AuthUser = {
  id: "default",
  email: "sujahathmhmd@gmail.com",
  full_name: "M.S. Mohamed Sujahath",
};

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser {
  if (typeof window === "undefined") return DEFAULT_USER;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return DEFAULT_USER;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return DEFAULT_USER;
  }
}

export function setSession(user: AuthUser, token?: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.setItem(USER_KEY, JSON.stringify(DEFAULT_USER));
}

export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = getStoredToken();
  const user = getStoredUser();

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (user && user.id) {
    headers["X-User-Id"] = user.id;
  }
  return headers;
}
