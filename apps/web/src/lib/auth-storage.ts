import type { LoginTokens, UserProfile } from "./auth-api";

export const AUTH_SESSION_STORAGE_KEY = "ws_translation_auth_session";

export interface AuthSession {
  tokens: LoginTokens;
  user: UserProfile;
  expiresAt?: number;
}

/**
 * Persist authenticated tokens and user profile in localStorage (Remember Me)
 * or sessionStorage (current browser tab session only).
 *
 * TODO(TASK-AUTH-07/TASK-AUTH-08): Move the 30-day refreshToken out of Web Storage
 * into an HttpOnly; Secure; SameSite=Lax cookie before production deployment.
 */
export function saveAuthSession(
  session: AuthSession,
  rememberMe: boolean
): void {
  if (typeof window === "undefined") {
    return;
  }

  const expiresInSeconds =
    session.tokens.expiresIn > 0 ? session.tokens.expiresIn : 3600;
  const sessionWithExpiry: AuthSession = {
    ...session,
    expiresAt: session.expiresAt ?? Date.now() + expiresInSeconds * 1000,
  };

  const serialized = JSON.stringify(sessionWithExpiry);
  if (rememberMe) {
    window.localStorage.setItem(AUTH_SESSION_STORAGE_KEY, serialized);
    window.sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  } else {
    window.sessionStorage.setItem(AUTH_SESSION_STORAGE_KEY, serialized);
    window.localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  }
}

export function getAuthSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw =
    window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY) ??
    window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY);

  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<AuthSession>;
    const hasValidExpiry =
      typeof parsed.expiresAt === "number" && Number.isFinite(parsed.expiresAt);
    if (
      !parsed.tokens?.accessToken ||
      !parsed.user?.id ||
      !hasValidExpiry ||
      Date.now() >= (parsed.expiresAt as number)
    ) {
      // Drop malformed, un-expirable, or expired sessions to prevent stale auth state.
      clearAuthSession();
      return null;
    }
    return parsed as AuthSession;
  } catch {
    clearAuthSession();
    return null;
  }
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  window.sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
}
