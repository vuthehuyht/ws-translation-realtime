import { getApiBaseUrl } from "./api-base";
import type { RefreshSessionResponse } from "./auth-api";
import {
  clearAuthSession,
  getRememberMePreference,
  saveAuthSession,
  type AuthSession,
} from "./auth-storage";

type SessionListener = (session: AuthSession | null) => void;

const listeners = new Set<SessionListener>();
let inFlightRefresh: Promise<AuthSession | null> | null = null;

function getRefreshEndpointUrl(): string {
  return `${getApiBaseUrl()}/api/v1/auth/refresh`;
}

function notifyListeners(session: AuthSession | null): void {
  for (const listener of listeners) {
    listener(session);
  }
}

/**
 * Subscribe to silent refresh updates (new session or forced logout on 401/403).
 */
export function subscribeAuthSession(listener: SessionListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * Compute milliseconds to wait before triggering proactive token refresh.
 */
export function getRefreshLeadDelayMs(
  expiresAt: number,
  leadTimeMs = 60_000
): number {
  return Math.max(0, expiresAt - Date.now() - leadTimeMs);
}

/**
 * Refresh the Host access/ID token using the browser's HttpOnly refresh cookie.
 * Concurrent callers share a single in-flight request to prevent duplicate Cognito calls.
 */
export function silentRefreshSession(): Promise<AuthSession | null> {
  if (typeof window === "undefined") {
    return Promise.resolve(null);
  }

  if (inFlightRefresh) {
    return inFlightRefresh;
  }

  inFlightRefresh = (async (): Promise<AuthSession | null> => {
    try {
      const response = await fetch(getRefreshEndpointUrl(), {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        // Clear local auth state only on definitive authentication/account rejections.
        if (response.status === 401 || response.status === 403) {
          clearAuthSession();
          notifyListeners(null);
        }
        return null;
      }

      const payload = (await response.json()) as RefreshSessionResponse;
      if (!payload.tokens?.accessToken || !payload.user?.id) {
        // Distinguish a malformed 200 response from a network failure when debugging.
        console.error("Silent refresh returned a malformed payload");
        return null;
      }

      const expiresInSeconds =
        payload.tokens.expiresIn > 0 ? payload.tokens.expiresIn : 3600;
      const nextSession: AuthSession = {
        tokens: payload.tokens,
        user: payload.user,
        expiresAt: Date.now() + expiresInSeconds * 1000,
      };

      saveAuthSession(nextSession, getRememberMePreference());
      notifyListeners(nextSession);
      return nextSession;
    } catch {
      // Preserve any still-valid session on transient network errors.
      return null;
    } finally {
      inFlightRefresh = null;
    }
  })();

  return inFlightRefresh;
}
