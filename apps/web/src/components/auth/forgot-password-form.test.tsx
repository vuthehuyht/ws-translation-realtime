import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { ApiError } from "@/lib/api-client";
import * as authApi from "@/lib/auth-api";
import { ForgotPasswordForm } from "./forgot-password-form";

describe("ForgotPasswordForm component", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders back link, input field and submit button", () => {
    render(<ForgotPasswordForm />);
    expect(screen.getByRole("link", { name: /Quay lại Đăng nhập/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Địa chỉ Email đã đăng ký/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Gửi mã xác thực qua Email/i })
    ).toBeInTheDocument();
  });

  it("shows error message when submitting empty email without calling API", async () => {
    const spy = vi.spyOn(authApi, "forgotPassword");
    render(<ForgotPasswordForm />);
    const submitBtn = screen.getByRole("button", {
      name: /Gửi mã xác thực qua Email/i,
    });

    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Vui lòng nhập địa chỉ email đã đăng ký/i)
    ).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();
  });

  it("shows error message when entering invalid email format without calling API", async () => {
    const spy = vi.spyOn(authApi, "forgotPassword");
    render(<ForgotPasswordForm />);
    const emailInput = screen.getByLabelText(/Địa chỉ Email đã đăng ký/i);
    const submitBtn = screen.getByRole("button", {
      name: /Gửi mã xác thực qua Email/i,
    });

    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Địa chỉ email không hợp lệ/i)
    ).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();
  });

  it("normalizes email, shows loading state, calls forgotPassword API, and invokes onSubmitSuccess", async () => {
    let resolveRequest!: (value: authApi.ForgotPasswordResponse) => void;
    const pendingPromise = new Promise<authApi.ForgotPasswordResponse>((resolve) => {
      resolveRequest = resolve;
    });
    const apiSpy = vi.spyOn(authApi, "forgotPassword").mockReturnValueOnce(pendingPromise);
    const handleSuccess = vi.fn();

    render(<ForgotPasswordForm onSubmitSuccess={handleSuccess} />);

    const emailInput = screen.getByLabelText(/Địa chỉ Email đã đăng ký/i);
    const submitBtn = screen.getByRole("button", {
      name: /Gửi mã xác thực qua Email/i,
    });

    fireEvent.change(emailInput, { target: { value: "  Host@Example.COM  " } });
    fireEvent.click(submitBtn);

    expect(submitBtn).toBeDisabled();
    expect(apiSpy).toHaveBeenCalledWith({ email: "host@example.com" });

    resolveRequest({
      status: "OTP_SENT",
      email: "host@example.com",
      message: "If an active account exists for this email, a password reset code has been sent.",
    });

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith("host@example.com");
    });
    expect(submitBtn).not.toBeDisabled();
  });

  it("formats 429 rate-limit error with retryAfter in seconds", async () => {
    vi.spyOn(authApi, "forgotPassword").mockRejectedValueOnce(
      new ApiError(429, "RATE_LIMIT_EXCEEDED", "Too many requests", { retryAfter: 45 })
    );
    const handleSuccess = vi.fn();
    render(<ForgotPasswordForm onSubmitSuccess={handleSuccess} />);

    fireEvent.change(screen.getByLabelText(/Địa chỉ Email đã đăng ký/i), {
      target: { value: "host@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Gửi mã xác thực qua Email/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Vui lòng thử lại sau 45 giây/i
    );
    expect(handleSuccess).not.toHaveBeenCalled();
  });

  it("formats 429 rate-limit error with retryAfter in exact minutes and minutes+seconds", async () => {
    vi.spyOn(authApi, "forgotPassword")
      .mockRejectedValueOnce(
        new ApiError(429, "RATE_LIMIT_EXCEEDED", "Too many requests", { retryAfter: 900 })
      )
      .mockRejectedValueOnce(
        new ApiError(429, "RATE_LIMIT_EXCEEDED", "Too many requests", { retryAfter: 125 })
      )
      .mockRejectedValueOnce(new ApiError(429, "RATE_LIMIT_EXCEEDED", "Too many requests"));

    render(<ForgotPasswordForm />);
    const emailInput = screen.getByLabelText(/Địa chỉ Email đã đăng ký/i);
    const submitBtn = screen.getByRole("button", { name: /Gửi mã xác thực qua Email/i });
    fireEvent.change(emailInput, { target: { value: "host@example.com" } });

    fireEvent.click(submitBtn);
    expect(await screen.findByRole("alert")).toHaveTextContent(/sau 15 phút\./i);

    fireEvent.click(submitBtn);
    expect(await screen.findByRole("alert")).toHaveTextContent(/sau 2 phút 5 giây\./i);

    fireEvent.click(submitBtn);
    expect(await screen.findByRole("alert")).toHaveTextContent(/sau ít phút\./i);
  });

  it("handles 422, 503, generic ApiError, and network error, and clears error on input edit", async () => {
    vi.spyOn(authApi, "forgotPassword")
      .mockRejectedValueOnce(new ApiError(422, "VALIDATION_ERROR", "Invalid"))
      .mockRejectedValueOnce(new ApiError(503, "SERVICE_UNAVAILABLE", "Redis down"))
      .mockRejectedValueOnce(new ApiError(400, "BAD_REQUEST", "Custom API message"))
      .mockRejectedValueOnce(new TypeError("Failed to fetch"));

    render(<ForgotPasswordForm />);
    const emailInput = screen.getByLabelText(/Địa chỉ Email đã đăng ký/i);
    const submitBtn = screen.getByRole("button", { name: /Gửi mã xác thực qua Email/i });
    fireEvent.change(emailInput, { target: { value: "host@example.com" } });

    fireEvent.click(submitBtn);
    expect(await screen.findByRole("alert")).toHaveTextContent(/Địa chỉ email không hợp lệ/i);

    fireEvent.click(submitBtn);
    expect(await screen.findByRole("alert")).toHaveTextContent(/Hệ thống tạm thời bận/i);

    fireEvent.click(submitBtn);
    expect(await screen.findByRole("alert")).toHaveTextContent(/Custom API message/i);

    fireEvent.click(submitBtn);
    expect(await screen.findByRole("alert")).toHaveTextContent(/Không thể kết nối tới máy chủ/i);

    // Editing email clears the error alert
    fireEvent.change(emailInput, { target: { value: "other@example.com" } });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
