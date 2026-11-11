import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { RegisterForm } from "./register-form";

describe("RegisterForm component", () => {
  it("renders all required form inputs and buttons matching mockup", () => {
    render(<RegisterForm />);
    expect(screen.getByLabelText(/Họ và tên/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Địa chỉ Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Mật khẩu/i)).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: /Điều khoản Dịch vụ/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Tạo tài khoản" })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Google/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Apple/i })).toBeInTheDocument();
  });

  it("shows validation error messages when submitting empty form", async () => {
    render(<RegisterForm />);
    const submitBtn = screen.getByRole("button", {
      name: "Tạo tài khoản",
    });

    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Vui lòng nhập họ và tên/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Vui lòng nhập địa chỉ email/i)).toBeInTheDocument();
    expect(screen.getByText(/Vui lòng nhập mật khẩu/i)).toBeInTheDocument();
  });

  it("shows validation error when password is shorter than 8 characters", async () => {
    render(<RegisterForm />);
    const passwordInput = screen.getByLabelText(/^Mật khẩu/i);
    const submitBtn = screen.getByRole("button", {
      name: "Tạo tài khoản",
    });

    fireEvent.change(passwordInput, { target: { value: "12345" } });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Mật khẩu phải có ít nhất 8 ký tự/i)
    ).toBeInTheDocument();
  });

  it("shows validation error for invalid email format", async () => {
    render(<RegisterForm />);
    const emailInput = screen.getByLabelText(/Địa chỉ Email/i);
    const submitBtn = screen.getByRole("button", {
      name: "Tạo tài khoản",
    });

    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Địa chỉ email không hợp lệ/i)
    ).toBeInTheDocument();
  });

  it("shows validation error when terms are unchecked", async () => {
    render(<RegisterForm />);
    const nameInput = screen.getByLabelText(/Họ và tên/i);
    const emailInput = screen.getByLabelText(/Địa chỉ Email/i);
    const passwordInput = screen.getByLabelText(/^Mật khẩu/i);
    const termsCheckbox = screen.getByRole("checkbox", {
      name: /Điều khoản Dịch vụ/i,
    });
    const submitBtn = screen.getByRole("button", {
      name: "Tạo tài khoản",
    });

    fireEvent.change(nameInput, { target: { value: "Nguyen Van A" } });
    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "Password123!" } });
    fireEvent.click(termsCheckbox); // uncheck terms
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Bạn cần đồng ý với Điều khoản Dịch vụ/i)
    ).toBeInTheDocument();
  });

  it("calls onSubmitSuccess callback with form data when form is valid", async () => {
    const handleSuccess = vi.fn();
    render(<RegisterForm onSubmitSuccess={handleSuccess} />);

    fireEvent.change(screen.getByLabelText(/Họ và tên/i), {
      target: { value: "Nguyen Van A" },
    });
    fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
      target: { value: "host@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
      target: { value: "P@ssword2026!" },
    });

    const submitBtn = screen.getByRole("button", {
      name: "Tạo tài khoản",
    });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalledWith({
        fullName: "Nguyen Van A",
        email: "host@example.com",
        password: "P@ssword2026!",
      });
    });
  });
});
