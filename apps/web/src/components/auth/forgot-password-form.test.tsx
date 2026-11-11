import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ForgotPasswordForm } from "./forgot-password-form";

describe("ForgotPasswordForm component", () => {
  it("renders back link, input field and submit button", () => {
    render(<ForgotPasswordForm />);
    expect(screen.getByRole("link", { name: /Quay lại Đăng nhập/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Địa chỉ Email đã đăng ký/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Gửi mã xác thực qua Email/i })
    ).toBeInTheDocument();
  });

  it("shows error message when submitting empty email", async () => {
    render(<ForgotPasswordForm />);
    const submitBtn = screen.getByRole("button", {
      name: /Gửi mã xác thực qua Email/i,
    });

    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Vui lòng nhập địa chỉ email đã đăng ký/i)
    ).toBeInTheDocument();
  });

  it("shows error message when entering invalid email format", async () => {
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
  });

  it("calls onSubmitSuccess callback with valid email", async () => {
    const handleSuccess = vi.fn();
    render(<ForgotPasswordForm onSubmitSuccess={handleSuccess} />);

    const emailInput = screen.getByLabelText(/Địa chỉ Email đã đăng ký/i);
    const submitBtn = screen.getByRole("button", {
      name: /Gửi mã xác thực qua Email/i,
    });

    fireEvent.change(emailInput, { target: { value: "host@example.com" } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith("host@example.com");
    });
  });
});
