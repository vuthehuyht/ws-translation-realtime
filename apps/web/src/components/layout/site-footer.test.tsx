import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SiteFooter } from "./site-footer";

describe("SiteFooter", () => {
  it("renders global brand info, navigation links, and copyright", () => {
    render(<SiteFooter />);

    expect(screen.getByText("VoiceBridge AI")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Host Dashboard" })
    ).toHaveAttribute("href", "/dashboard");
    expect(screen.getByRole("link", { name: "Đăng nhập" })).toHaveAttribute(
      "href",
      "/login"
    );
    expect(
      screen.getByText(/điều khoản sử dụng \(sắp ra mắt\)/i)
    ).toHaveAttribute("aria-disabled", "true");
    expect(
      screen.getByText(/chính sách bảo mật \(sắp ra mắt\)/i)
    ).toHaveAttribute("aria-disabled", "true");
    expect(
      screen.getByRole("link", { name: "Khôi phục mật khẩu" })
    ).toHaveAttribute("href", "/forgot-password");
    expect(
      screen.getByText(/© 2026 VoiceBridge AI\. All rights reserved\./i)
    ).toBeInTheDocument();
  });
});
