import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SecurityBrandHero } from "./security-brand-hero";

describe("SecurityBrandHero component", () => {
  it("renders title, description and footer correctly", () => {
    render(
      <SecurityBrandHero
        icon="🔐"
        title="Bảo mật Tài khoản Host"
        description="Mã bảo mật 6 số sẽ được gửi trực tiếp đến hòm thư đã đăng ký của bạn."
        footerText="Liên hệ support@wstranslation.ai"
      />
    );

    expect(screen.getByText("Bảo mật Tài khoản Host")).toBeInTheDocument();
    expect(
      screen.getByText(/Mã bảo mật 6 số sẽ được gửi trực tiếp/i)
    ).toBeInTheDocument();
    expect(screen.getByText("🔐")).toBeInTheDocument();
    expect(screen.getByText(/Liên hệ support@wstranslation.ai/i)).toBeInTheDocument();
  });
});
