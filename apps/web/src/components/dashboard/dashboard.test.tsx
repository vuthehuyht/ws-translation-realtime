import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import DashboardLayout from "@/app/(dashboard)/layout";
import DashboardPage from "@/app/(dashboard)/dashboard/page";
import { getAuthSession, saveAuthSession } from "@/lib/auth-storage";

const pushMock = vi.fn();
const replaceMock = vi.fn();
const routerMock = { push: pushMock, replace: replaceMock };

vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
  usePathname: () => "/dashboard",
}));

describe("Host Dashboard (SCR-02)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    replaceMock.mockReset();
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("redirects to /login when there is no active auth session and silent refresh fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ error: { code: "UNAUTHORIZED", message: "Missing" } }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      })
    );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/login");
    });
  });

  it("recovers expired session via silent refresh on dashboard mount", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          tokens: {
            accessToken: "recovered-acc",
            idToken: "recovered-id",
            refreshToken: null,
            expiresIn: 3600,
            tokenType: "Bearer",
          },
          user: {
            id: "user-1",
            email: "host@example.com",
            role: "HOST",
            status: "ACTIVE",
            fullName: "Recovered Host",
            defaultSourceLang: "vi-VN",
            defaultTargetLangs: ["en-US"],
            timezone: "Asia/Ho_Chi_Minh",
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /xin chào, recovered host/i })
      ).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/auth/refresh",
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
    expect(replaceMock).not.toHaveBeenCalled();
  });

  it("proactively refreshes access token 60s before expiry", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-11-18T12:00:00Z"));

    saveAuthSession(
      {
        tokens: {
          accessToken: "acc-initial",
          idToken: "id-initial",
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

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          tokens: {
            accessToken: "acc-proactive",
            idToken: "id-proactive",
            refreshToken: null,
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
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    expect(
      screen.getByRole("heading", { name: /xin chào, nguyen van a/i })
    ).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3540 * 1000);
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/auth/refresh",
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
    expect(getAuthSession()?.tokens.accessToken).toBe("acc-proactive");
  });

  it("retries proactive refresh after transient network failure while token is still valid", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-11-18T12:00:00Z"));

    saveAuthSession(
      {
        tokens: {
          accessToken: "acc-initial",
          idToken: "id-initial",
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

    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("Transient blip"))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            tokens: {
              accessToken: "acc-recovered-retry",
              idToken: "id-recovered-retry",
              refreshToken: null,
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
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    // Trigger initial proactive attempt (fails transiently), then advance 15s for retry
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3540 * 1000);
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(15 * 1000);
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(getAuthSession()?.tokens.accessToken).toBe("acc-recovered-retry");
  });

  it("refreshes on visibilitychange when tab returns near token expiry", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-11-18T12:00:00Z"));

    saveAuthSession(
      {
        tokens: {
          accessToken: "acc-initial",
          idToken: "id-initial",
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

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          tokens: {
            accessToken: "acc-visibility",
            idToken: "id-visibility",
            refreshToken: null,
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
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    // Jump system clock within the 60s lead window without firing setTimeout, then wake tab
    vi.setSystemTime(new Date("2026-11-18T12:59:30Z"));
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => "visible",
    });

    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(getAuthSession()?.tokens.accessToken).toBe("acc-visibility");
  });

  it("renders dashboard sections, supports top-up modal and room creation for authenticated host", async () => {
    saveAuthSession(
      {
        tokens: {
          accessToken: "acc-1",
          idToken: "id-1",
          refreshToken: "ref-1",
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
          defaultTargetLangs: ["en-US", "ja-JP"],
          timezone: "Asia/Ho_Chi_Minh",
        },
      },
      true
    );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /xin chào, nguyen van a/i })
      ).toBeInTheDocument();
    });

    expect(screen.getByTestId("wallet-balance")).toHaveTextContent("$2.00");
    expect(screen.getByText(/đã chọn 2\/10 ngôn ngữ đích/i)).toBeInTheDocument();

    // Open Top-Up modal and confirm $25 package
    fireEvent.click(
      screen.getByRole("button", { name: /nạp tiền nhanh/i })
    );
    fireEvent.click(screen.getByRole("button", { name: "$25" }));
    fireEvent.click(
      screen.getByRole("button", { name: /xác nhận nạp \$25\.00/i })
    );
    expect(screen.getByTestId("wallet-balance")).toHaveTextContent("$27.00");

    // Create a new room
    fireEvent.change(screen.getByLabelText(/tên phòng họp/i), {
      target: { value: "Hội nghị Đối tác Q4" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /tạo & mở phòng dịch ngay/i })
    );

    expect(screen.getAllByText("Hội nghị Đối tác Q4").length).toBeGreaterThan(0);

    // Logout clears session and redirects to /login
    fireEvent.click(screen.getByRole("button", { name: /đăng xuất/i }));
    expect(pushMock).toHaveBeenCalledWith("/login");
    expect(window.localStorage.length).toBe(0);
  });
});
