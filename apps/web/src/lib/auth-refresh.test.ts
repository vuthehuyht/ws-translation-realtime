import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getRefreshLeadDelayMs,
  silentRefreshSession,
  subscribeAuthSession,
} from "./auth-refresh";
import {
  AUTH_SESSION_STORAGE_KEY,
  getAuthSession,
  saveAuthSession,
  type AuthSession,
} from "./auth-storage";

const INITIAL_SESSION: AuthSession = {
  tokens: {
    accessToken: "old-acc",
    idToken: "old-id",
    expiresIn: 3600,
    tokenType: "Bearer",
  },
  user: {
    id: "user-1",
    email: "host@example.com",
    role: "HOST",
    status: "ACTIVE",
    fullName: "Host User",
    defaultSourceLang: "vi-VN",
    defaultTargetLangs: ["en-US"],
    timezone: "Asia/Ho_Chi_Minh",
  },
};

function makeRefreshJsonResponse(accessToken = "new-acc", status = 200): Response {
  return new Response(
    JSON.stringify({
      tokens: {
        accessToken,
        idToken: "new-id",
        refreshToken: null,
        expiresIn: 3600,
        tokenType: "Bearer",
      },
      user: INITIAL_SESSION.user,
    }),
    { status, headers: { "Content-Type": "application/json" } }
  );
}

describe("auth-refresh", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-11-18T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("deduplicates concurrent silentRefreshSession calls into a single fetch and notifies subscribers", async () => {
    saveAuthSession(INITIAL_SESSION, true);

    let resolveFetch!: (res: Response) => void;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        })
    );

    const listener = vi.fn();
    const unsubscribe = subscribeAuthSession(listener);

    const p1 = silentRefreshSession();
    const p2 = silentRefreshSession();
    const p3 = silentRefreshSession();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    resolveFetch(makeRefreshJsonResponse("deduped-acc"));

    const [r1, r2, r3] = await Promise.all([p1, p2, p3]);
    expect(r1?.tokens.accessToken).toBe("deduped-acc");
    expect(r2?.tokens.accessToken).toBe("deduped-acc");
    expect(r3?.tokens.accessToken).toBe("deduped-acc");

    expect(listener).toHaveBeenCalledTimes(1);
    expect(getAuthSession()?.tokens.accessToken).toBe("deduped-acc");
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).not.toBeNull();
    unsubscribe();
  });

  it("clears auth session and notifies null when /refresh returns 401 or 403", async () => {
    saveAuthSession(INITIAL_SESSION, true);
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { code: "UNAUTHORIZED", message: "Expired" } }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      })
    );

    const listener = vi.fn();
    const unsubscribe = subscribeAuthSession(listener);

    const result = await silentRefreshSession();
    expect(result).toBeNull();
    expect(getAuthSession()).toBeNull();
    expect(listener).toHaveBeenCalledWith(null);
    unsubscribe();
  });

  it("preserves existing valid session on transient network failure", async () => {
    saveAuthSession(INITIAL_SESSION, false);
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network down"));

    const result = await silentRefreshSession();
    expect(result).toBeNull();
    expect(getAuthSession()?.tokens.accessToken).toBe("old-acc");
  });

  it("computes refresh lead delay clamped at zero", () => {
    const now = Date.now();
    expect(getRefreshLeadDelayMs(now + 3600 * 1000)).toBe(3540 * 1000);
    expect(getRefreshLeadDelayMs(now + 30 * 1000)).toBe(0);
  });

  it("restores expired rememberMe session back into localStorage after silent refresh", async () => {
    saveAuthSession(INITIAL_SESSION, true);
    vi.advanceTimersByTime(3600 * 1000 + 1);
    expect(getAuthSession()).toBeNull();

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      makeRefreshJsonResponse("restored-remembered-acc")
    );

    const restored = await silentRefreshSession();
    expect(restored?.tokens.accessToken).toBe("restored-remembered-acc");
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).not.toBeNull();
    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
  });
});
