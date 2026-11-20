import { getApiBaseUrl } from "./api-base";
import type { RefreshSessionResponse, UserProfile } from "./auth-api";
import {
  clearAuthSession,
  getAuthSession,
  getRememberMePreference,
  saveAuthSession,
  type AuthSession,
} from "./auth-storage";

type SessionListener = (session: AuthSession | null) => void;

const listeners = new Set<SessionListener>();
let inFlightRefresh: Promise<RefreshOutcome> | null = null;
// Bumped on sign-out so refreshes started earlier cannot write a session back afterwards.
let sessionEpoch = 0;

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
 * Result of a silent refresh attempt.
 * - `rejected`: the backend answered 401/403, so no usable refresh cookie exists.
 * - `unavailable`: network error, 5xx or malformed payload; the cookie's state is unknown.
 */
export type RefreshOutcome =
  | { status: "refreshed"; session: AuthSession }
  | { status: "rejected" }
  | { status: "unavailable" };

/**
 * Refresh the Host access/ID token using the browser's HttpOnly refresh cookie.
 * Concurrent callers share a single in-flight request to prevent duplicate Cognito calls.
 */
export async function silentRefreshSession(): Promise<AuthSession | null> {
  const outcome = await silentRefreshSessionDetailed();
  return outcome.status === "refreshed" ? outcome.session : null;
}

/**
 * Same as silentRefreshSession but tells a definitive rejection apart from a transient failure,
 * which callers like logout need to decide whether the server-side session may still be alive.
 */
export function silentRefreshSessionDetailed(): Promise<RefreshOutcome> {
  if (typeof window === "undefined") {
    return Promise.resolve({ status: "unavailable" });
  }

  if (inFlightRefresh) {
    return inFlightRefresh;
  }

  const epoch = sessionEpoch;
  const request = (async (): Promise<RefreshOutcome> => {
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
          return { status: "rejected" };
        }
        return { status: "unavailable" };
      }

      const payload = (await response.json()) as RefreshSessionResponse;
      if (!payload.tokens?.accessToken || !payload.user?.id) {
        // Distinguish a malformed 200 response from a network failure when debugging.
        console.error("Silent refresh returned a malformed payload");
        return { status: "unavailable" };
      }

      if (epoch !== sessionEpoch) {
        // A sign-out started while this request was in flight; saving the fresh token now
        // would resurrect the session the user just asked to end.
        return { status: "unavailable" };
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
      return { status: "refreshed", session: nextSession };
    } catch {
      // Preserve any still-valid session on transient network errors.
      return { status: "unavailable" };
    }
  })();

  inFlightRefresh = request;
  // Cleared via .finally (not try/finally) so a cancelled request cannot null out a newer one.
  void request.finally(() => {
    if (inFlightRefresh === request) {
      inFlightRefresh = null;
    }
  });
  return request;
}

/**
 * Discard refreshes that are already in flight: their result will not be saved or broadcast,
 * and new callers start a fresh request. Call this before revoking a session on the server.
 */
export function cancelPendingRefreshes(): void {
  sessionEpoch += 1;
  inFlightRefresh = null;
}

/**
 * Merge updated user profile fields into the active session and broadcast to subscribers
 * (e.g. DashboardHeader) without requiring a token refresh round-trip.
 */
export function patchAuthSessionUser(
  partialUser: Partial<UserProfile>
): AuthSession | null {
  const current = getAuthSession();
  if (!current) {
    return null;
  }
  const nextSession: AuthSession = {
    ...current,
    user: {
      ...current.user,
      ...partialUser,
    },
  };
  saveAuthSession(nextSession, getRememberMePreference());
  notifyListeners(nextSession);
  return nextSession;
}
