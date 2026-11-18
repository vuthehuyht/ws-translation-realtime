import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  AUTH_REMEMBER_ME_KEY,
  AUTH_SESSION_STORAGE_KEY,
  clearAuthSession,
  getAuthSession,
  getRememberMePreference,
  saveAuthSession,
  type AuthSession,
} from "./auth-storage";

const SAMPLE_SESSION: AuthSession = {
  tokens: {
    accessToken: "acc-123",
    idToken: "id-123",
    refreshToken: "ref-123",
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

describe("auth-storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-11-18T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("saves session with computed expiresAt and returns it while valid", () => {
    saveAuthSession(SAMPLE_SESSION, true);

    const stored = getAuthSession();
    expect(stored).not.toBeNull();
    expect(stored?.user.email).toBe("host@example.com");
    expect(stored?.expiresAt).toBe(Date.now() + 3600 * 1000);
    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
  });

  it("returns null and clears storage once the access token expires while preserving rememberMe", () => {
    saveAuthSession(SAMPLE_SESSION, true);

    vi.advanceTimersByTime(3600 * 1000 + 1);

    expect(getAuthSession()).toBeNull();
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
    expect(getRememberMePreference()).toBe(true);
  });

  it("clears both localStorage and sessionStorage on clearAuthSession", () => {
    saveAuthSession(SAMPLE_SESSION, false);
    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).not.toBeNull();

    clearAuthSession();
    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
  });

  it("treats stored sessions without expiresAt as invalid and clears storage", () => {
    window.localStorage.setItem(
      AUTH_SESSION_STORAGE_KEY,
      JSON.stringify(SAMPLE_SESSION)
    );

    expect(getAuthSession()).toBeNull();
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
  });

  it("clears corrupt JSON in sessionStorage so it cannot block future sessions", () => {
    saveAuthSession(SAMPLE_SESSION, true);
    window.sessionStorage.setItem(AUTH_SESSION_STORAGE_KEY, "{not-valid-json");

    expect(getAuthSession()).toBeNull();
    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
  });

  it("strips refreshToken from Web Storage and preserves rememberMe preference", () => {
    saveAuthSession(SAMPLE_SESSION, true);

    const raw = window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY);
    expect(raw).not.toBeNull();
    expect(JSON.parse(raw as string).tokens.refreshToken).toBeUndefined();
    expect(window.localStorage.getItem(AUTH_REMEMBER_ME_KEY)).toBe("1");
    expect(getRememberMePreference()).toBe(true);

    clearAuthSession();
    expect(getRememberMePreference()).toBe(false);
    expect(window.localStorage.getItem(AUTH_REMEMBER_ME_KEY)).toBeNull();
  });
});
