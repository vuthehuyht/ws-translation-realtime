import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "./api-client";
import { confirmRegistration, registerHost, resendOtp } from "./auth-api";

describe("auth-api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls POST /api/v1/auth/register with HOST role default", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: "CONFIRMATION_REQUIRED",
          email: "host@example.com",
          userSub: "sub-123",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } }
      )
    );

    const res = await registerHost({
      fullName: "Host User",
      email: "host@example.com",
      password: "Password123!",
    });

    expect(res.userSub).toBe("sub-123");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/auth/register",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          fullName: "Host User",
          email: "host@example.com",
          password: "Password123!",
          role: "HOST",
        }),
      })
    );
  });

  it("calls POST /api/v1/auth/confirm and returns walletBalance", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          status: "CONFIRMED",
          userSub: "sub-123",
          walletBalance: "2.0000",
          currency: "USD",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    const res = await confirmRegistration({
      email: "host@example.com",
      otpCode: "123456",
    });

    expect(res.status).toBe("CONFIRMED");
    expect(res.walletBalance).toBe("2.0000");
  });

  it("throws ApiError with RFC 7807 fields on 429 resend-otp", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "RATE_LIMIT_EXCEEDED",
            message: "Please wait 45 seconds",
            details: { retryAfter: 45 },
          },
        }),
        { status: 429, headers: { "Content-Type": "application/json" } }
      )
    );

    await expect(resendOtp({ email: "host@example.com" })).rejects.toMatchObject({
      name: "ApiError",
      status: 429,
      code: "RATE_LIMIT_EXCEEDED",
      message: "Please wait 45 seconds",
      details: { retryAfter: 45 },
    });
  });

  it("creates ApiError instance", () => {
    const err = new ApiError(409, "RESOURCE_CONFLICT", "Exists");
    expect(err).toBeInstanceOf(Error);
    expect(err.status).toBe(409);
  });
});
