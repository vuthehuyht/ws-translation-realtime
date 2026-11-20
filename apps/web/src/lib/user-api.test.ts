import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { saveAuthSession } from "./auth-storage";
import {
  changePassword,
  confirmAvatarUpload,
  deleteAccount,
  getMe,
  requestAvatarUploadUrl,
  updateBillingInfo,
  updatePreferences,
  updateProfile,
  uploadAvatarBinary,
} from "./user-api";

describe("user-api", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    saveAuthSession(
      {
        tokens: {
          accessToken: "test-access-token",
          idToken: "test-id-token",
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
      },
      true
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls GET /api/v1/users/me with Bearer token", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ id: "user-1", fullName: "Host User" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const me = await getMe();
    expect(me.id).toBe("user-1");

    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/api/v1/users/me");
    expect((init?.headers as Headers).get("Authorization")).toBe(
      "Bearer test-access-token"
    );
  });

  it("calls PATCH profile, PATCH preferences, PUT billing-info, and POST change-password", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() =>
        Promise.resolve(
          new Response(JSON.stringify({ status: "OK" }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          })
        )
      );

    await updateProfile({ fullName: "Updated Name", timezone: "Asia/Tokyo" });
    await updatePreferences({
      defaultSourceLang: "en-US",
      defaultTargetLangs: ["vi-VN"],
    });
    await updateBillingInfo({
      companyName: "ACME",
      taxCode: "0101234567",
      companyAddress: "HCM",
    });
    await changePassword({
      oldPassword: "OldPassword1!",
      newPassword: "NewPassword2@",
    });

    expect(fetchSpy).toHaveBeenCalledTimes(4);
    expect(String(fetchSpy.mock.calls[0][0])).toContain(
      "/api/v1/users/me/profile"
    );
    expect(fetchSpy.mock.calls[0][1]?.method).toBe("PATCH");
    expect(String(fetchSpy.mock.calls[1][0])).toContain(
      "/api/v1/users/me/preferences"
    );
    expect(String(fetchSpy.mock.calls[2][0])).toContain(
      "/api/v1/users/me/billing-info"
    );
    expect(fetchSpy.mock.calls[2][1]?.method).toBe("PUT");
    expect(String(fetchSpy.mock.calls[3][0])).toContain(
      "/api/v1/users/me/change-password"
    );
  });

  it("handles avatar presigned URL, binary PUT, and confirm endpoints", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            uploadUrl: "/api/v1/users/me/avatar/mock-upload/avatars/user-1/a.png",
            s3Key: "avatars/user-1/a.png",
            fields: {},
            expiresIn: 900,
            maxSizeBytes: 2097152,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            avatarUrl: "https://cdn.example.com/avatars/user-1/a.png",
            s3Key: "avatars/user-1/a.png",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

    const file = new File([new Uint8Array([1, 2, 3])], "avatar.png", {
      type: "image/png",
    });
    const presigned = await requestAvatarUploadUrl({
      fileName: file.name,
      fileType: "image/png",
      fileSizeBytes: file.size,
    });
    await uploadAvatarBinary(presigned.uploadUrl, file);
    const confirmed = await confirmAvatarUpload(presigned.s3Key);

    expect(confirmed.avatarUrl).toBe(
      "https://cdn.example.com/avatars/user-1/a.png"
    );
    expect(fetchSpy).toHaveBeenCalledTimes(3);
  });

  it("calls DELETE /api/v1/users/me with confirmation payload", async () => {
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    await deleteAccount({ confirmation: "DELETE" });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toContain("/api/v1/users/me");
    expect(init?.method).toBe("DELETE");
    expect(init?.credentials).toBe("include");
    expect(init?.body).toBe(JSON.stringify({ confirmation: "DELETE" }));
  });
});
