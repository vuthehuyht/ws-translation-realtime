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

  it("shows dashboard skeleton while session recovery is in flight", async () => {
    let resolveRefresh!: (response: Response) => void;
    vi.spyOn(globalThis, "fetch").mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          resolveRefresh = resolve;
        })
    );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    expect(screen.getByTestId("dashboard-skeleton")).toBeInTheDocument();

    resolveRefresh(
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
            fullName: "Skeleton Host",
            defaultSourceLang: "vi-VN",
            defaultTargetLangs: ["en-US"],
            timezone: "Asia/Ho_Chi_Minh",
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /xin chào, skeleton host/i })
      ).toBeInTheDocument();
    });
    expect(screen.queryByTestId("dashboard-skeleton")).toBeNull();
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
    expect(screen.getByText("VoiceBridge AI")).toBeInTheDocument();
    expect(screen.queryByText("Host Studio")).not.toBeInTheDocument();

    expect(await screen.findByTestId("wallet-balance")).toHaveTextContent("200 Cr");
    expect(await screen.findByText(/đã chọn 2\/10 ngôn ngữ đích/i)).toBeInTheDocument();

    // Open Top-Up modal and confirm the 3.000 Cr pack (PACK_M)
    fireEvent.click(
      screen.getByRole("button", { name: /nạp tiền nhanh/i })
    );
    fireEvent.click(screen.getByRole("button", { name: /3\.000 Cr/ }));
    fireEvent.click(
      screen.getByRole("button", { name: /xác nhận nạp 3\.000 Cr/i })
    );
    expect(screen.getByTestId("wallet-balance")).toHaveTextContent("3.200 Cr");

    // Create a new room
    fireEvent.change(screen.getByLabelText(/tên phòng họp/i), {
      target: { value: "Hội nghị Đối tác Q4" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /tạo & mở phòng dịch ngay/i })
    );

    expect(screen.getAllByText("Hội nghị Đối tác Q4").length).toBeGreaterThan(0);

    // Open account dropdown menu by clicking the user name & email pill
    fireEvent.click(screen.getByRole("button", { name: /mở menu tài khoản/i }));
    expect(screen.getByRole("menuitem", { name: /hồ sơ cá nhân/i })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /cài đặt/i })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /thanh toán & gói credit/i })).toBeInTheDocument();

    // Logout revokes the session on the backend, clears local state and redirects to /login
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    fireEvent.click(screen.getByRole("menuitem", { name: /^đăng xuất$/i }));
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/login");
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/api/v1/auth/logout");
    expect(init?.body).toBe(JSON.stringify({ global: false }));
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer acc-1");
    expect(window.localStorage.length).toBe(0);
  });

  describe("logout (TASK-AUTH-08)", () => {
    const seedSession = () =>
      saveAuthSession(
        {
          tokens: {
            accessToken: "acc-logout",
            idToken: "id-logout",
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

    const openAccountMenu = async () => {
      const trigger = await screen.findByRole("button", { name: /mở menu tài khoản/i });
      fireEvent.click(trigger);
    };

    it("closes the account menu on Escape key", async () => {
      seedSession();
      render(
        <DashboardLayout>
          <DashboardPage />
        </DashboardLayout>
      );
      await openAccountMenu();
      expect(screen.getByRole("menu", { name: /menu tài khoản/i })).toBeInTheDocument();

      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("menu", { name: /menu tài khoản/i })).toBeNull();
    });

    it("keeps the session and shows an error when the backend cannot revoke the token", async () => {
      seedSession();
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify({ error: { code: "BAD_GATEWAY", message: "down" } }), {
          status: 502,
          headers: { "Content-Type": "application/json" },
        })
      );

      render(
        <DashboardLayout>
          <DashboardPage />
        </DashboardLayout>
      );
      await openAccountMenu();

      fireEvent.click(screen.getByRole("menuitem", { name: /^đăng xuất$/i }));

      expect(await screen.findByRole("alert")).toHaveTextContent(/không thể đăng xuất/i);
      expect(pushMock).not.toHaveBeenCalledWith("/login");
      expect(getAuthSession()?.tokens.accessToken).toBe("acc-logout");
    });

    it("sends global=true when signing out of every device", async () => {
      seedSession();
      const confirmMock = vi.spyOn(window, "confirm").mockReturnValue(true);
      const fetchMock = vi
        .spyOn(globalThis, "fetch")
        .mockResolvedValueOnce(new Response(null, { status: 204 }));

      render(
        <DashboardLayout>
          <DashboardPage />
        </DashboardLayout>
      );
      await openAccountMenu();

      fireEvent.click(screen.getByRole("menuitem", { name: /đăng xuất mọi thiết bị/i }));

      await waitFor(() => {
        expect(pushMock).toHaveBeenCalledWith("/login");
      });
      expect(confirmMock).toHaveBeenCalledTimes(1);
      expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ global: true }));
      expect(getAuthSession()).toBeNull();
    });

    it("does nothing when the user cancels the sign-out-everywhere confirmation", async () => {
      seedSession();
      vi.spyOn(window, "confirm").mockReturnValue(false);
      const fetchMock = vi.spyOn(globalThis, "fetch");

      render(
        <DashboardLayout>
          <DashboardPage />
        </DashboardLayout>
      );
      await openAccountMenu();

      fireEvent.click(screen.getByRole("menuitem", { name: /đăng xuất mọi thiết bị/i }));

      expect(fetchMock).not.toHaveBeenCalled();
      expect(pushMock).not.toHaveBeenCalledWith("/login");
      expect(getAuthSession()?.tokens.accessToken).toBe("acc-logout");
    });

    it("disables both buttons and sends a single request while signing out", async () => {
      seedSession();
      let resolveLogout!: (response: Response) => void;
      const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveLogout = resolve;
          })
      );

      render(
        <DashboardLayout>
          <DashboardPage />
        </DashboardLayout>
      );
      await openAccountMenu();
      const logoutButton = screen.getByRole("menuitem", { name: /^đăng xuất$/i });

      fireEvent.click(logoutButton);
      fireEvent.click(logoutButton);

      await waitFor(() => {
        expect(logoutButton).toBeDisabled();
      });
      expect(screen.getByRole("menuitem", { name: /đăng xuất mọi thiết bị/i })).toBeDisabled();
      expect(fetchMock).toHaveBeenCalledTimes(1);

      resolveLogout(new Response(null, { status: 204 }));
      await waitFor(() => {
        expect(pushMock).toHaveBeenCalledWith("/login");
      });
    });

    it("re-enables the buttons after a failed sign-out so the user can retry", async () => {
      seedSession();
      vi.spyOn(globalThis, "fetch")
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ error: { code: "BAD_GATEWAY", message: "down" } }), {
            status: 502,
            headers: { "Content-Type": "application/json" },
          })
        )
        .mockResolvedValueOnce(new Response(null, { status: 204 }));

      render(
        <DashboardLayout>
          <DashboardPage />
        </DashboardLayout>
      );
      await openAccountMenu();
      const logoutButton = screen.getByRole("menuitem", { name: /^đăng xuất$/i });

      fireEvent.click(logoutButton);
      await screen.findByRole("alert");
      expect(logoutButton).toBeEnabled();

      fireEvent.click(logoutButton);
      await waitFor(() => {
        expect(pushMock).toHaveBeenCalledWith("/login");
      });
      expect(screen.queryByRole("alert")).toBeNull();
    });
  });
});
