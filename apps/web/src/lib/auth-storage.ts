import type { LoginTokens, UserProfile } from "./auth-api";

export const AUTH_SESSION_STORAGE_KEY = "ws_translation_auth_session";
export const AUTH_REMEMBER_ME_KEY = "ws_translation_remember_me";

export interface AuthSession {
  tokens: LoginTokens;
  user: UserProfile;
  expiresAt?: number;
}

function omitRefreshToken(tokens: LoginTokens): LoginTokens {
  const copy: LoginTokens = { ...tokens };
  delete copy.refreshToken;
  return copy;
}

/**
 * Persist authenticated access/ID tokens and user profile in localStorage (Remember Me)
 * or sessionStorage (current browser tab session only).
 *
 * The 30-day refreshToken is stored exclusively in an HttpOnly cookie by the backend
 * and is explicitly stripped before serializing into Web Storage.
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
  // Strip refreshToken from Web Storage because the browser holds it in an HttpOnly cookie.
  const safeTokens = omitRefreshToken(session.tokens);

  const sessionWithExpiry: AuthSession = {
    ...session,
    tokens: safeTokens,
    expiresAt: session.expiresAt ?? Date.now() + expiresInSeconds * 1000,
  };

  const serialized = JSON.stringify(sessionWithExpiry);
  window.localStorage.setItem(AUTH_REMEMBER_ME_KEY, rememberMe ? "1" : "0");
  if (rememberMe) {
    window.localStorage.setItem(AUTH_SESSION_STORAGE_KEY, serialized);
    window.sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  } else {
    window.sessionStorage.setItem(AUTH_SESSION_STORAGE_KEY, serialized);
    window.localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  }
}

export function getRememberMePreference(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  return window.localStorage.getItem(AUTH_REMEMBER_ME_KEY) === "1";
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
      // Preserve rememberMe preference so silent refresh writes back to the original storage.
      clearAuthSession({ preserveRememberMe: true });
      return null;
    }
    return parsed as AuthSession;
  } catch {
    clearAuthSession({ preserveRememberMe: true });
    return null;
  }
}

/**
 * Read the stored session without validating or clearing it on expiry.
 *
 * Logout needs the stale access token of an expired session: the backend accepts it (signature
 * only) so it can still revoke the refresh cookie.
 */
export function peekAuthSession(): AuthSession | null {
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
    return parsed.tokens?.accessToken ? (parsed as AuthSession) : null;
  } catch {
    return null;
  }
}

export function clearAuthSession(options?: {
  preserveRememberMe?: boolean;
}): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  window.sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  if (!options?.preserveRememberMe) {
    window.localStorage.removeItem(AUTH_REMEMBER_ME_KEY);
  }
}
