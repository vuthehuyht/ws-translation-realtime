import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ProfilePage from "./page";
import { getAuthSession, saveAuthSession } from "@/lib/auth-storage";
import type { UserMe } from "@/lib/user-api";

const sampleUserMe: UserMe = {
  id: "user-1",
  email: "host@example.com",
  role: "HOST",
  status: "ACTIVE",
  fullName: "Nguyen Van A",
  phoneNumber: "+84901234567",
  bio: "Event host",
  avatarUrl: null,
  timezone: "Asia/Ho_Chi_Minh",
  defaultSourceLang: "vi-VN",
  defaultTargetLangs: ["en-US"],
  companyName: "VoiceBridge JSC",
  taxCode: "0101234567",
  companyAddress: "District 1, HCMC",
  preferences: {
    vadSensitivity: "medium",
    subtitleMode: "bilingual",
  },
  wallet: {
    balance: "2.0000",
    currency: "USD",
    autoDegradeTts: true,
    autoTopupEnabled: false,
  },
};

describe("Profile Page (/dashboard/profile)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    saveAuthSession(
      {
        tokens: {
          accessToken: "valid-token",
          idToken: "id-token",
          expiresIn: 3600,
          tokenType: "Bearer",
        },
        user: {
          id: "user-1",
          email: "host@example.com",
          role: "HOST",
          status: "ACTIVE",
          fullName: "Nguyen Van A",
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

  it("renders profile data, updates basic info, and syncs auth session", async () => {
    const updatedUser: UserMe = {
      ...sampleUserMe,
      fullName: "Nguyen Van B",
    };

    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(sampleUserMe), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(updatedUser), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<ProfilePage />);

    const nameInput = await screen.findByLabelText("Họ và tên");
    expect(nameInput).toHaveValue("Nguyen Van A");
    expect(screen.getByText("$2.00")).toBeInTheDocument();

    fireEvent.change(nameInput, { target: { value: "Nguyen Van B" } });
    fireEvent.click(screen.getByRole("button", { name: /Lưu thông tin$/i }));

    await waitFor(() => {
      expect(screen.getByText("Đã lưu thông tin cá nhân.")).toBeInTheDocument();
    });
    expect(getAuthSession()?.user.fullName).toBe("Nguyen Van B");
  });

  it("uploads avatar via presigned URL -> PUT -> confirm and updates session", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(sampleUserMe), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            uploadUrl: "/api/v1/users/me/avatar/mock-upload/avatars/user-1/pic.png",
            s3Key: "avatars/user-1/pic.png",
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
            avatarUrl: "https://cdn.example.com/avatars/user-1/pic.png",
            s3Key: "avatars/user-1/pic.png",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

    render(<ProfilePage />);

    const fileInput = await screen.findByTestId("avatar-file-input");
    const file = new File([new Uint8Array([1, 2, 3, 4])], "pic.png", {
      type: "image/png",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(
        screen.getByText("Đã cập nhật ảnh đại diện thành công.")
      ).toBeInTheDocument();
    });
    expect(getAuthSession()?.user.avatarUrl).toBe(
      "https://cdn.example.com/avatars/user-1/pic.png"
    );
  });

  it("validates VAT tax code and submits password change", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(sampleUserMe), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "PASSWORD_CHANGED",
            message: "Password has been changed successfully.",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

    render(<ProfilePage />);

    const taxInput = await screen.findByLabelText("Mã số thuế");
    fireEvent.change(taxInput, { target: { value: "123" } });
    fireEvent.click(screen.getByRole("button", { name: /Lưu thông tin VAT/i }));

    expect(
      await screen.findByText(/Mã số thuế phải gồm 10 hoặc 13 chữ số/i)
    ).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Mật khẩu hiện tại"), {
      target: { value: "OldPassword1!" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu mới"), {
      target: { value: "NewPassword2@" },
    });
    fireEvent.change(screen.getByLabelText("Xác nhận mật khẩu mới"), {
      target: { value: "NewPassword2@" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^Đổi mật khẩu$/i }));

    await waitFor(() => {
      expect(screen.getByText("Đã đổi mật khẩu thành công.")).toBeInTheDocument();
    });
  });
});
