import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { PasswordMeter, calculatePasswordStrength } from "./password-meter";

describe("calculatePasswordStrength helper", () => {
  it("returns score 0 for empty password", () => {
    const result = calculatePasswordStrength("");
    expect(result.score).toBe(0);
    expect(result.label).toBe("Chưa nhập mật khẩu");
  });

  it("returns score 1 for short simple password", () => {
    const result = calculatePasswordStrength("abc");
    expect(result.score).toBe(1);
    expect(result.label).toContain("Mật khẩu yếu");
  });

  it("returns score 2 for password with length >= 8 but only letters", () => {
    const result = calculatePasswordStrength("passwordABC");
    expect(result.score).toBe(2);
    expect(result.label).toContain("Mật khẩu trung bình");
  });

  it("returns score 3 for password with letters and numbers", () => {
    const result = calculatePasswordStrength("Password123");
    expect(result.score).toBe(3);
    expect(result.label).toContain("Mật khẩu khá");
  });

  it("returns score 4 for strong password with length >= 8, uppercase, numbers, and special chars", () => {
    const result = calculatePasswordStrength("P@ssw0rd!2026");
    expect(result.score).toBe(4);
    expect(result.label).toBe("Mật khẩu mạnh (gồm chữ hoa, số và ký tự đặc biệt)");
  });
});

describe("PasswordMeter component", () => {
  it("renders 4 indicator bars", () => {
    render(<PasswordMeter password="test" />);
    const bars = screen.getAllByTestId("password-strength-bar");
    expect(bars).toHaveLength(4);
  });

  it("displays correct feedback text for strong password", () => {
    render(<PasswordMeter password="P@ssw0rd!2026" />);
    expect(screen.getByText(/Mật khẩu mạnh/i)).toBeInTheDocument();
  });
});
