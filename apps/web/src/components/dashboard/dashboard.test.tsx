import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import DashboardLayout from "@/app/(dashboard)/layout";
import DashboardPage from "@/app/(dashboard)/dashboard/page";
import { saveAuthSession } from "@/lib/auth-storage";

const pushMock = vi.fn();
const replaceMock = vi.fn();
const routerMock = { push: pushMock, replace: replaceMock };

vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
  usePathname: () => "/dashboard",
}));

describe("Host Dashboard (SCR-02)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    replaceMock.mockReset();
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  it("redirects to /login when there is no active auth session", async () => {
    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/login");
    });
  });

  it("renders dashboard sections, supports top-up modal and room creation for authenticated host", async () => {
    saveAuthSession(
      {
        tokens: {
          accessToken: "acc-1",
          idToken: "id-1",
          refreshToken: "ref-1",
          expiresIn: 3600,
          tokenType: "Bearer",
        },
        user: {
          id: "user-1",
          email: "host@example.com",
          role: "HOST",
          status: "ACTIVE",
          fullName: "Nguyen Van A",
          defaultSourceLang: "vi-VN",
          defaultTargetLangs: ["en-US", "ja-JP"],
          timezone: "Asia/Ho_Chi_Minh",
        },
      },
      true
    );

    render(
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /xin chào, nguyen van a/i })
      ).toBeInTheDocument();
    });

    expect(screen.getByTestId("wallet-balance")).toHaveTextContent("$2.00");
    expect(screen.getByText(/đã chọn 2\/10 ngôn ngữ đích/i)).toBeInTheDocument();

    // Open Top-Up modal and confirm $25 package
    fireEvent.click(
      screen.getByRole("button", { name: /nạp tiền nhanh/i })
    );
    fireEvent.click(screen.getByRole("button", { name: "$25" }));
    fireEvent.click(
      screen.getByRole("button", { name: /xác nhận nạp \$25\.00/i })
    );
    expect(screen.getByTestId("wallet-balance")).toHaveTextContent("$27.00");

    // Create a new room
    fireEvent.change(screen.getByLabelText(/tên phòng họp/i), {
      target: { value: "Hội nghị Đối tác Q4" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /tạo & mở phòng dịch ngay/i })
    );

    expect(screen.getAllByText("Hội nghị Đối tác Q4").length).toBeGreaterThan(0);

    // Logout clears session and redirects to /login
    fireEvent.click(screen.getByRole("button", { name: /đăng xuất/i }));
    expect(pushMock).toHaveBeenCalledWith("/login");
    expect(window.localStorage.length).toBe(0);
  });
});
