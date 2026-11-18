import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { signOutSession, LogoutUnavailableError } from "./auth-logout";
import { cancelPendingRefreshes, silentRefreshSessionDetailed } from "./auth-refresh";
import {
  AUTH_SESSION_STORAGE_KEY,
  peekAuthSession,
  saveAuthSession,
} from "./auth-storage";

const user = {
  id: "user-1",
  email: "host@example.com",
  role: "HOST",
  status: "ACTIVE",
  fullName: "Host",
  defaultSourceLang: "vi-VN",
  defaultTargetLangs: ["en-US"],
  timezone: "Asia/Ho_Chi_Minh",
};

function seed(expiresAt?: number) {
  saveAuthSession(
    {
      tokens: {
        accessToken: "acc-stored",
        idToken: "id",
        expiresIn: 3600,
        tokenType: "Bearer",
      },
      user,
      expiresAt,
    },
    true
  );
}

const noContent = () => new Response(null, { status: 204 });
const errorResponse = (status: number) =>
  new Response(JSON.stringify({ error: { code: `HTTP_${status}`, message: "x" } }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const refreshOk = (accessToken: string) =>
  new Response(
    JSON.stringify({
      tokens: { accessToken, idToken: "id", expiresIn: 3600, tokenType: "Bearer" },
      user,
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );

function authHeaderOf(call: unknown[]): string | null {
  return new Headers((call[1] as RequestInit).headers).get("Authorization");
}

describe("signOutSession (TASK-AUTH-08)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends the stored token even when it is already expired", async () => {
    seed(Date.now() - 60_000);
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(noContent());

    await signOutSession();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/api/v1/auth/logout");
    expect(authHeaderOf(fetchMock.mock.calls[0])).toBe("Bearer acc-stored");
    // Expired tokens must not be silently cleared before the server revoked the cookie.
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).not.toBeNull();
  });

  it("rethrows non-401 failures so the caller keeps the session", async () => {
    seed();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(errorResponse(502));

    await expect(signOutSession()).rejects.toMatchObject({ status: 502 });
  });

  it("treats 401 followed by a definitive refresh rejection as signed out", async () => {
    seed();
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(errorResponse(401))
      .mockResolvedValueOnce(errorResponse(401));

    await expect(signOutSession()).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[1][0])).toContain("/api/v1/auth/refresh");
  });

  it("does not claim success when 401 is followed by a transient refresh failure", async () => {
    seed();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(errorResponse(401))
      .mockResolvedValueOnce(errorResponse(503));

    await expect(signOutSession()).rejects.toBeInstanceOf(LogoutUnavailableError);
  });

  it("does not claim success when 401 is followed by a network error", async () => {
    seed();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(errorResponse(401))
      .mockRejectedValueOnce(new TypeError("network down"));

    await expect(signOutSession({ global: true })).rejects.toBeInstanceOf(LogoutUnavailableError);
  });

  it("refreshes and retries once with the new token after a 401", async () => {
    seed();
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(errorResponse(401))
      .mockResolvedValueOnce(refreshOk("acc-fresh"))
      .mockResolvedValueOnce(noContent());

    await signOutSession({ global: true });

    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(authHeaderOf(fetchMock.mock.calls[2])).toBe("Bearer acc-fresh");
    expect((fetchMock.mock.calls[2][1] as RequestInit).body).toBe(
      JSON.stringify({ global: true })
    );
  });

  it("without a stored token, resolves when refresh is definitively rejected", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(errorResponse(401));

    await expect(signOutSession()).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("without a stored token, fails when the cookie state is unknown", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(errorResponse(500));

    await expect(signOutSession()).rejects.toBeInstanceOf(LogoutUnavailableError);
  });

  it("drops a refresh that was already in flight so it cannot resurrect the session", async () => {
    seed();
    let resolveRefresh!: (response: Response) => void;
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveRefresh = resolve;
          })
      )
      .mockResolvedValueOnce(noContent());

    const pendingRefresh = silentRefreshSessionDetailed();
    await signOutSession();
    resolveRefresh(refreshOk("acc-late"));

    await expect(pendingRefresh).resolves.toEqual({ status: "unavailable" });
    // The late token must not overwrite what was stored before sign-out
    expect(peekAuthSession()?.tokens.accessToken).toBe("acc-stored");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("lets later refreshes work normally after a cancelled one", async () => {
    seed();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(refreshOk("acc-new"));

    cancelPendingRefreshes();
    const outcome = await silentRefreshSessionDetailed();

    expect(outcome.status).toBe("refreshed");
    expect(peekAuthSession()?.tokens.accessToken).toBe("acc-new");
  });
});
