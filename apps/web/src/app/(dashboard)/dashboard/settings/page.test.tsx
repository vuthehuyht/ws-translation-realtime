import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import SettingsPage from "./page";
import { getAuthSession, saveAuthSession } from "@/lib/auth-storage";
import type { UserMe } from "@/lib/user-api";

const sampleUserMe: UserMe = {
  id: "user-1",
  email: "host@example.com",
  role: "HOST",
  status: "ACTIVE",
  fullName: "Nguyen Van A",
  phoneNumber: null,
  bio: null,
  avatarUrl: null,
  timezone: "Asia/Ho_Chi_Minh",
  defaultSourceLang: "vi-VN",
  defaultTargetLangs: ["en-US"],
  companyName: null,
  taxCode: null,
  companyAddress: null,
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

describe("Settings Page (/dashboard/settings)", () => {
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

  it("loads and saves default translation preferences", async () => {
    const updatedUser: UserMe = {
      ...sampleUserMe,
      defaultSourceLang: "en-US",
      defaultTargetLangs: ["en-US", "ja-JP"],
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

    render(<SettingsPage />);

    const sourceSelect = await screen.findByLabelText("Ngôn ngữ nguồn mặc định");
    fireEvent.change(sourceSelect, { target: { value: "en-US" } });
    fireEvent.click(screen.getByRole("button", { name: /日本語 \(ja-JP\)/i }));
    fireEvent.click(screen.getByRole("button", { name: /Lưu cài đặt dịch/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Đã lưu cấu hình dịch thuật mặc định.")
      ).toBeInTheDocument();
    });
    expect(getAuthSession()?.user.defaultSourceLang).toBe("en-US");
    expect(getAuthSession()?.user.defaultTargetLangs).toEqual(["en-US", "ja-JP"]);
  });
});
