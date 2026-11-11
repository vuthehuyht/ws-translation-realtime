import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ResetPasswordForm } from "./reset-password-form";

describe("ResetPasswordForm component", () => {
  it("renders OTP input, password fields and submit button", () => {
    render(<ResetPasswordForm />);
    expect(screen.getByText(/Mã xác thực OTP \(6 số\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Mật khẩu mới/i)).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Xác nhận lại mật khẩu mới/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Lưu Mật khẩu & Đăng nhập ngay/i })
    ).toBeInTheDocument();
  });

  it("shows error messages when submitting empty form", async () => {
    render(<ResetPasswordForm />);
    const submitBtn = screen.getByRole("button", {
      name: /Lưu Mật khẩu & Đăng nhập ngay/i,
    });

    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Vui lòng nhập đầy đủ mã OTP 6 số/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Vui lòng nhập mật khẩu mới/i)).toBeInTheDocument();
  });

  it("shows error when password is less than 8 characters", async () => {
    render(<ResetPasswordForm />);
    // Type 6 digits in OTP
    const firstOtpInput = screen.getByLabelText("Mã OTP số 1");
    fireEvent.paste(firstOtpInput, {
      clipboardData: { getData: () => "123456" },
    });

    const passwordInput = screen.getByLabelText(/^Mật khẩu mới/i);
    fireEvent.change(passwordInput, { target: { value: "12345" } });

    const submitBtn = screen.getByRole("button", {
      name: /Lưu Mật khẩu & Đăng nhập ngay/i,
    });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Mật khẩu phải có ít nhất 8 ký tự/i)
    ).toBeInTheDocument();
  });

  it("shows error when confirmation password does not match", async () => {
    render(<ResetPasswordForm />);
    const firstOtpInput = screen.getByLabelText("Mã OTP số 1");
    fireEvent.paste(firstOtpInput, {
      clipboardData: { getData: () => "123456" },
    });

    fireEvent.change(screen.getByLabelText(/^Mật khẩu mới/i), {
      target: { value: "StrongPass123!" },
    });
    fireEvent.change(screen.getByLabelText(/Xác nhận lại mật khẩu mới/i), {
      target: { value: "DifferentPass123!" },
    });

    const submitBtn = screen.getByRole("button", {
      name: /Lưu Mật khẩu & Đăng nhập ngay/i,
    });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Mật khẩu xác nhận không khớp/i)
    ).toBeInTheDocument();
  });

  it("calls onSubmitSuccess callback with otp and new password", async () => {
    const handleSuccess = vi.fn();
    render(<ResetPasswordForm onSubmitSuccess={handleSuccess} />);

    const firstOtpInput = screen.getByLabelText("Mã OTP số 1");
    fireEvent.paste(firstOtpInput, {
      clipboardData: { getData: () => "849201" },
    });

    fireEvent.change(screen.getByLabelText(/^Mật khẩu mới/i), {
      target: { value: "NewStrongPass@2026" },
    });
    fireEvent.change(screen.getByLabelText(/Xác nhận lại mật khẩu mới/i), {
      target: { value: "NewStrongPass@2026" },
    });

    const submitBtn = screen.getByRole("button", {
      name: /Lưu Mật khẩu & Đăng nhập ngay/i,
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith({
        otp: "849201",
        password: "NewStrongPass@2026",
      });
    });
  });
});
