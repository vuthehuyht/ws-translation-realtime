import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SiteFooter } from "./site-footer";

describe("SiteFooter", () => {
  it("renders brand info, product links, support contact, legal links, and copyright", () => {
    render(<SiteFooter />);

    expect(screen.getByText("VoiceBridge AI")).toBeInTheDocument();
    expect(screen.getByText("Sản phẩm")).toBeInTheDocument();
    expect(screen.getByText("Hỗ trợ")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Phiên dịch trực tiếp" })
    ).toHaveAttribute("href", "/products/realtime-translation");
    expect(
      screen.getByRole("link", { name: "Bảng giá & gói cước" })
    ).toHaveAttribute("href", "/pricing");
    expect(
      screen.getByRole("link", { name: "Biên bản & tóm tắt AI" })
    ).toHaveAttribute("href", "/products/transcripts-ai-summary");
    expect(
      screen.getByRole("link", { name: "Từ điển thuật ngữ" })
    ).toHaveAttribute("href", "/products/custom-vocabularies");
    expect(screen.queryByText("Nền tảng")).toBeNull();
    expect(screen.queryByRole("link", { name: "Host Dashboard" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Khôi phục mật khẩu" })).toBeNull();
    expect(
      screen.getByRole("link", { name: /support@voicebridge\.ai/i })
    ).toHaveAttribute("href", "mailto:support@voicebridge.ai");
    expect(
      screen.getByRole("link", { name: "Điều khoản sử dụng" })
    ).toHaveAttribute("href", "/terms");
    expect(
      screen.getByRole("link", { name: "Chính sách bảo mật" })
    ).toHaveAttribute("href", "/privacy");
    expect(
      screen.getByText(/© 2026 VoiceBridge AI\. All rights reserved\./i)
    ).toBeInTheDocument();
  });
});
