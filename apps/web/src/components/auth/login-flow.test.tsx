import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import LoginPage from "@/app/(auth)/login/page";
import { AUTH_SESSION_STORAGE_KEY } from "@/lib/auth-storage";

const pushMock = vi.fn();
let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  useSearchParams: () => mockSearchParams,
}));

describe("LoginPage integration flow", () => {
  beforeEach(() => {
    pushMock.mockReset();
    mockSearchParams = new URLSearchParams();
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows verified banner and prefills email from query params", () => {
    mockSearchParams = new URLSearchParams(
      "verified=1&email=verified@example.com"
    );

    render(<LoginPage />);

    expect(
      screen.getByText(/tài khoản của bạn đã được xác thực thành công/i)
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Địa chỉ email")).toHaveValue("verified@example.com");
  });

  it("shows deleted account confirmation banner when deleted=1 query param is present", () => {
    mockSearchParams = new URLSearchParams("deleted=1");

    render(<LoginPage />);

    expect(
      screen.getByText(/tài khoản của bạn đã được xóa và ẩn danh dữ liệu cá nhân/i)
    ).toBeInTheDocument();
  });

  it("logs in via backend API, saves session to localStorage when rememberMe is checked, and redirects to /dashboard", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          tokens: {
            accessToken: "acc-123",
            idToken: "id-123",
            refreshToken: "ref-123",
            expiresIn: 3600,
            tokenType: "Bearer",
          },
          user: {
            id: "u-1",
            email: "host@example.com",
            role: "HOST",
            status: "ACTIVE",
            fullName: "Host User",
            defaultSourceLang: "vi-VN",
            defaultTargetLangs: ["en-US"],
            timezone: "Asia/Ho_Chi_Minh",
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Địa chỉ email"), {
      target: { value: "Host@Example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), {
      target: { value: "Password123!" },
    });
    fireEvent.click(screen.getByLabelText("Ghi nhớ đăng nhập"));
    fireEvent.click(
      screen.getByRole("button", { name: "Đăng nhập vào hệ thống" })
    );

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/dashboard");
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/auth/login",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          email: "host@example.com",
          password: "Password123!",
          rememberMe: true,
        }),
      })
    );

    const saved = window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY);
    expect(saved).not.toBeNull();
    expect(JSON.parse(saved as string).tokens.refreshToken).toBeUndefined();
    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
  });

  it("displays invalid credentials message on 401 response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "UNAUTHORIZED",
            message: "Invalid email or password",
          },
        }),
        { status: 401, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Địa chỉ email"), {
      target: { value: "host@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), {
      target: { value: "WrongPass123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Đăng nhập vào hệ thống" })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/email hoặc mật khẩu không chính xác/i)
      ).toBeInTheDocument();
    });
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("displays suspended account message on 403 response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "FORBIDDEN",
            message: "Account is suspended",
          },
        }),
        { status: 403, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Địa chỉ email"), {
      target: { value: "suspended@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), {
      target: { value: "Password123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Đăng nhập vào hệ thống" })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/tài khoản của bạn đã bị tạm khóa/i)
      ).toBeInTheDocument();
    });
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("saves session to sessionStorage when rememberMe is unchecked", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          tokens: {
            accessToken: "acc-session",
            idToken: "id-session",
            refreshToken: "ref-session",
            expiresIn: 3600,
            tokenType: "Bearer",
          },
          user: {
            id: "u-2",
            email: "session@example.com",
            role: "HOST",
            status: "ACTIVE",
            fullName: "Session Host",
            defaultSourceLang: "vi-VN",
            defaultTargetLangs: ["en-US"],
            timezone: "Asia/Ho_Chi_Minh",
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Địa chỉ email"), {
      target: { value: "session@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), {
      target: { value: "Password123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Đăng nhập vào hệ thống" })
    );

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/dashboard");
    });

    expect(window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)).not.toBeNull();
    expect(window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY)).toBeNull();
  });

  it("shows OTP verification prompt and link when 401 indicates unconfirmed user", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "UNAUTHORIZED",
            message: "User is not confirmed. Please enter OTP",
          },
        }),
        { status: 401, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Địa chỉ email"), {
      target: { value: "new.host@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), {
      target: { value: "Password123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Đăng nhập vào hệ thống" })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/tài khoản chưa được xác thực otp/i)
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("link", { name: /xác thực otp ngay/i })
    ).toHaveAttribute("href", "/verify-otp?email=new.host%40example.com");
  });

  it("displays validation error message on 422 response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "VALIDATION_ERROR",
            message: "Unprocessable entity",
          },
        }),
        { status: 422, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Địa chỉ email"), {
      target: { value: "host@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), {
      target: { value: "Password123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Đăng nhập vào hệ thống" })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/thông tin đăng nhập chưa hợp lệ/i)
      ).toBeInTheDocument();
    });
  });

  it("displays network error message when fetch rejects", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network down"));

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Địa chỉ email"), {
      target: { value: "host@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), {
      target: { value: "Password123!" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Đăng nhập vào hệ thống" })
    );

    await waitFor(() => {
      expect(
        screen.getByText(/không thể kết nối đến máy chủ/i)
      ).toBeInTheDocument();
    });
  });
});
