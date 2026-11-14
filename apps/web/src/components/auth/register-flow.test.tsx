import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import RegisterPage from "@/app/(auth)/register/page";
import VerifyOtpPage from "@/app/(auth)/verify-otp/page";

const pushMock = vi.fn();
let currentEmailParam = "";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
  useSearchParams: () => new URLSearchParams(currentEmailParam ? { email: currentEmailParam } : {}),
}));

describe("Full Registration Flow (RegisterPage -> VerifyOtpPage)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    currentEmailParam = "";
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("completes register -> resend-otp -> confirm-otp -> redirect to login", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "CONFIRMATION_REQUIRED",
            email: "flow.host@example.com",
            userSub: "sub-flow-1",
          }),
          { status: 201, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "OTP_SENT",
            email: "flow.host@example.com",
            retryAfter: 60,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "CONFIRMED",
            userSub: "sub-flow-1",
            walletBalance: "2.0000",
            currency: "USD",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

    // Step 1: Render /register and submit form
    const { unmount } = render(<RegisterPage />);

    fireEvent.change(screen.getByLabelText(/Họ và tên/i), {
      target: { value: "Flow Host" },
    });
    fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
      target: { value: "Flow.Host@Example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
      target: { value: "StrongPass123!" },
    });
    fireEvent.click(
      screen.getByRole("checkbox", { name: /Điều khoản Dịch vụ/i })
    );
    fireEvent.click(screen.getByRole("button", { name: "Tạo tài khoản" }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith(
        "/verify-otp?email=flow.host%40example.com"
      );
    });
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "http://localhost:8000/api/v1/auth/register",
      expect.objectContaining({ method: "POST" })
    );

    unmount();

    // Step 2: Render /verify-otp with email query param
    vi.useFakeTimers();
    currentEmailParam = "flow.host@example.com";
    render(<VerifyOtpPage />);

    expect(screen.getByText("flow.host@example.com")).toBeInTheDocument();

    // Advance 60s cooldown and resend OTP
    await act(async () => {
      vi.advanceTimersByTime(60000);
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Gửi lại mã OTP/i }));
    });
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://localhost:8000/api/v1/auth/resend-otp",
      expect.objectContaining({ method: "POST" })
    );

    // Step 3: Paste 6-digit OTP -> auto confirm -> $2.00 Welcome Bonus -> redirect to /login
    await act(async () => {
      fireEvent.paste(screen.getByLabelText("Mã OTP số 1"), {
        clipboardData: { getData: () => "123456" },
      });
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "http://localhost:8000/api/v1/auth/confirm",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "flow.host@example.com",
          otpCode: "123456",
        }),
      })
    );
    expect(
      screen.getByText(/Kích hoạt tài khoản thành công!/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/\$2\.00 USD/i)).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(1200);
    });
    expect(pushMock).toHaveBeenCalledWith(
      "/login?verified=1&email=flow.host%40example.com"
    );
  });

  it("shows 409 conflict banner on RegisterPage when email already exists", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "RESOURCE_CONFLICT",
            message: "User already exists",
          },
        }),
        { status: 409, headers: { "Content-Type": "application/json" } }
      )
    );

    render(<RegisterPage />);

    fireEvent.change(screen.getByLabelText(/Họ và tên/i), {
      target: { value: "Existing Host" },
    });
    fireEvent.change(screen.getByLabelText(/Địa chỉ Email/i), {
      target: { value: "existing@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^Mật khẩu/i), {
      target: { value: "StrongPass123!" },
    });
    fireEvent.click(
      screen.getByRole("checkbox", { name: /Điều khoản Dịch vụ/i })
    );
    fireEvent.click(screen.getByRole("button", { name: "Tạo tài khoản" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Email này đã được đăng ký/i
    );
    expect(pushMock).not.toHaveBeenCalled();
  });
});
