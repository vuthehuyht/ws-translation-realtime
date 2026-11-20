import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { DeleteAccountSection } from "./delete-account-section";
import { saveAuthSession } from "@/lib/auth-storage";

describe("DeleteAccountSection", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    saveAuthSession(
      {
        tokens: {
          accessToken: "valid-token",
          idToken: "id-token",
          expiresIn: 3600,
          tokenType: "Bearer",
        },
        user: {
          id: "user-1",
          email: "host@example.com",
          role: "HOST",
          status: "ACTIVE",
          fullName: "Host User",
          defaultSourceLang: "vi-VN",
          defaultTargetLangs: ["en-US"],
          timezone: "Asia/Ho_Chi_Minh",
        },
      },
      true
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requires typing DELETE before enabling permanent deletion and invokes callback on 204", async () => {
    const onDeleted = vi.fn();
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    render(
      <DeleteAccountSection
        email="host@example.com"
        walletBalance="$2.00 USD"
        onAccountDeleted={onDeleted}
      />
    );

    expect(screen.getByText(/7 ngày/i)).toBeInTheDocument();
    expect(
      screen.getByText(/không nhận các quyền lợi\/ưu đãi chào mừng/i)
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^Xóa tài khoản$/i }));

    const confirmButton = screen.getByRole("button", {
      name: /Xóa vĩnh viễn tài khoản/i,
    });
    expect(confirmButton).toBeDisabled();

    const input = screen.getByLabelText(/Nhập.*DELETE.*để xác nhận/i);
    fireEvent.change(input, { target: { value: "delete" } });
    expect(confirmButton).toBeDisabled();

    fireEvent.change(input, { target: { value: "DELETE" } });
    expect(confirmButton).toBeEnabled();

    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(onDeleted).toHaveBeenCalledTimes(1);
    });
    expect(fetchSpy).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/users/me",
      expect.objectContaining({
        method: "DELETE",
        body: JSON.stringify({ confirmation: "DELETE" }),
      })
    );
  });

  it("displays conflict message when backend returns 409 for active rooms", async () => {
    const onDeleted = vi.fn();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "RESOURCE_CONFLICT",
            message: "Cannot delete account while you have active rooms",
          },
        }),
        { status: 409, headers: { "Content-Type": "application/json" } }
      )
    );

    render(
      <DeleteAccountSection
        email="host@example.com"
        onAccountDeleted={onDeleted}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /^Xóa tài khoản$/i }));
    fireEvent.change(screen.getByLabelText(/Nhập.*DELETE.*để xác nhận/i), {
      target: { value: "DELETE" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Xóa vĩnh viễn tài khoản/i })
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /đang có phòng dịch hoạt động/i
    );
    expect(onDeleted).not.toHaveBeenCalled();
  });

  it("closes modal on Escape or Cancel and shows fallback alert on network failure", async () => {
    const onDeleted = vi.fn();
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Network down"));

    render(
      <DeleteAccountSection
        email="host@example.com"
        onAccountDeleted={onDeleted}
      />
    );

    const trigger = screen.getByRole("button", { name: /^Xóa tài khoản$/i });
    fireEvent.click(trigger);
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // Escape closes modal and restores focus to trigger
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(document.activeElement).toBe(trigger);

    // Reopen and cancel via Cancel button
    fireEvent.click(trigger);
    fireEvent.click(screen.getByRole("button", { name: "Hủy" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    // Reopen and trigger network error
    fireEvent.click(trigger);
    fireEvent.change(screen.getByLabelText(/Nhập.*DELETE.*để xác nhận/i), {
      target: { value: "DELETE" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Xóa vĩnh viễn tài khoản/i })
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Không thể xóa tài khoản lúc này/i
    );
    expect(onDeleted).not.toHaveBeenCalled();
  });
});
