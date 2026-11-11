import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { LoginForm } from "./login-form";

describe("LoginForm component", () => {
  it("renders all required form controls, buttons, and links matching mockup", () => {
    render(<LoginForm />);
    expect(screen.getByLabelText(/Địa chỉ Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Mật khẩu/i)).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /Ghi nhớ đăng nhập/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Đăng nhập vào Hệ thống/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Google/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Apple/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Quên mật khẩu\?/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Đăng ký miễn phí/i })).toBeInTheDocument();
  });

  it("shows validation error messages when submitting empty form", async () => {
    render(<LoginForm />);
    const submitBtn = screen.getByRole("button", {
      name: /Đăng nhập vào Hệ thống/i,
    });

    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Vui lòng nhập địa chỉ email/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Vui lòng nhập mật khẩu/i)).toBeInTheDocument();
  });

  it("shows validation error for invalid email format", async () => {
    render(<LoginForm />);
    const emailInput = screen.getByLabelText(/Địa chỉ Email/i);
    const submitBtn = screen.getByRole("button", {
      name: /Đăng nhập vào Hệ thống/i,
    });

    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Địa chỉ email không hợp lệ/i)
    ).toBeInTheDocument();
  });

  it("toggles password visibility when clicking eye button", () => {
    render(<LoginForm />);
    const passwordInput = screen.getByLabelText(/^Mật khẩu/i) as HTMLInputElement;
    const toggleBtn = screen.getByRole("button", { name: /Hiện mật khẩu/i });

    expect(passwordInput.type).toBe("password");
    fireEvent.click(toggleBtn);
    expect(passwordInput.type).toBe("text");

    const hideBtn = screen.getByRole("button", { name: /Ẩn mật khẩu/i });
    fireEvent.click(hideBtn);
    expect(passwordInput.type).toBe("password");
  });

  it("calls onSubmitSuccess callback with form data when form is valid", async () => {
    const handleSuccess = vi.fn();
    render(<LoginForm onSubmitSuccess={handleSuccess} />);

    fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
      target: { value: "host@company.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
      target: { value: "SecurePass123!" },
    });

    const rememberCheckbox = screen.getByRole("checkbox", {
      name: /Ghi nhớ đăng nhập/i,
    });
    fireEvent.click(rememberCheckbox);

    const submitBtn = screen.getByRole("button", {
      name: /Đăng nhập vào Hệ thống/i,
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith({
        email: "host@company.com",
        password: "SecurePass123!",
        rememberMe: true,
      });
    });
  });
});
