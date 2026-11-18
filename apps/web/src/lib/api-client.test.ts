import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest, getApiBaseUrl } from "./api-client";
import { getAuthSession, saveAuthSession, type AuthSession } from "./auth-storage";

const SAMPLE_SESSION: AuthSession = {
  tokens: {
    accessToken: "initial-acc",
    idToken: "initial-id",
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

describe("api-client", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("attaches Bearer token when auth=true and sends credentials include", async () => {
    saveAuthSession(SAMPLE_SESSION, true);
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const res = await apiRequest<{ ok: boolean }>("/api/v1/rooms", {
      method: "GET",
      auth: true,
    });

    expect(res.ok).toBe(true);
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.credentials).toBe("include");
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer initial-acc");
  });

  it("retries once after silent refresh when a protected request returns 401", async () => {
    saveAuthSession(SAMPLE_SESSION, true);

    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ error: { code: "UNAUTHORIZED", message: "Expired" } }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            tokens: {
              accessToken: "refreshed-acc",
              idToken: "refreshed-id",
              refreshToken: null,
              expiresIn: 3600,
              tokenType: "Bearer",
            },
            user: SAMPLE_SESSION.user,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ balance: "10.00" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    const data = await apiRequest<{ balance: string }>("/api/v1/users/me", {
      method: "GET",
      auth: true,
    });

    expect(data.balance).toBe("10.00");
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toBe("http://localhost:8000/api/v1/auth/refresh");
    const retryHeaders = new Headers(fetchMock.mock.calls[2][1]?.headers);
    expect(retryHeaders.get("Authorization")).toBe("Bearer refreshed-acc");
    expect(getAuthSession()?.tokens.accessToken).toBe("refreshed-acc");
  });

  it("does not attempt silent refresh on /api/v1/auth/login 401 responses", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { code: "UNAUTHORIZED", message: "Bad creds" } }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      })
    );

    await expect(
      apiRequest("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: "a@b.com", password: "bad" }),
      })
    ).rejects.toBeInstanceOf(ApiError);

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("fails fast with 401 after a single refresh attempt when auth=true and refresh fails", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { code: "UNAUTHORIZED", message: "Expired" } }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      })
    );

    await expect(
      apiRequest("/api/v1/users/me", {
        method: "GET",
        auth: true,
      })
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      code: "UNAUTHORIZED",
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/api/v1/auth/refresh");
  });

  it("uses same-origin relative URLs in production when NEXT_PUBLIC_API_URL is unset", () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    expect(getApiBaseUrl()).toBe("");
    vi.unstubAllEnvs();
  });
});
