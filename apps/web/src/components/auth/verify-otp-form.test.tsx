import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api-client";
import * as authApi from "@/lib/auth-api";
import { VerifyOtpForm } from "./verify-otp-form";

describe("VerifyOtpForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("auto-submits 6-digit OTP and displays $2.00 Welcome Bonus on success", async () => {
    const confirmSpy = vi
      .spyOn(authApi, "confirmRegistration")
      .mockResolvedValueOnce({
        status: "CONFIRMED",
        userSub: "sub-123",
        walletBalance: "2.0000",
        currency: "USD",
      });
    const onVerified = vi.fn();

    render(<VerifyOtpForm email="host@example.com" onVerified={onVerified} />);

    const firstInput = screen.getByLabelText("Mã OTP số 1");
    fireEvent.paste(firstInput, {
      clipboardData: {
        getData: () => "123456",
      },
    });

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith({
        email: "host@example.com",
        otpCode: "123456",
      });
    });

    expect(
      await screen.findByText(/Kích hoạt tài khoản thành công!/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/\$2\.00 USD/i)).toBeInTheDocument();
    expect(onVerified).toHaveBeenCalledTimes(1);
  });

  it("shows error message once without infinite auto-submit loop when OTP returns 422", async () => {
    vi.useFakeTimers();
    const confirmSpy = vi
      .spyOn(authApi, "confirmRegistration")
      .mockRejectedValue(new ApiError(422, "VALIDATION_ERROR", "Invalid code"));

    render(<VerifyOtpForm email="host@example.com" />);

    const firstInput = screen.getByLabelText("Mã OTP số 1");
    await act(async () => {
      fireEvent.paste(firstInput, {
        clipboardData: {
          getData: () => "000000",
        },
      });
    });

    expect(
      screen.getByText(/Mã OTP không chính xác hoặc đã hết hạn/i)
    ).toBeInTheDocument();

    // Advance countdown ticks to ensure re-renders do not re-trigger auto-submit
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });
    expect(confirmSpy).toHaveBeenCalledTimes(1);
  });

  it("shows missing email alert when email prop is empty", () => {
    render(<VerifyOtpForm email="" />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      /Thiếu địa chỉ email xác thực/i
    );
  });

  it("enables resend button after 60s countdown and calls resendOtp", async () => {
    vi.useFakeTimers();
    const resendSpy = vi.spyOn(authApi, "resendOtp").mockResolvedValueOnce({
      status: "OTP_SENT",
      email: "host@example.com",
      retryAfter: 60,
    });

    render(<VerifyOtpForm email="host@example.com" />);

    const resendBtn = screen.getByRole("button", { name: /Gửi lại mã sau 60s/i });
    expect(resendBtn).toBeDisabled();

    await act(async () => {
      vi.advanceTimersByTime(60000);
    });

    const activeBtn = screen.getByRole("button", { name: /Gửi lại mã OTP/i });
    expect(activeBtn).toBeEnabled();

    await act(async () => {
      fireEvent.click(activeBtn);
    });

    expect(resendSpy).toHaveBeenCalledWith({ email: "host@example.com" });
    expect(
      screen.getByText(/Đã gửi lại mã OTP mới/i)
    ).toBeInTheDocument();
  });
});
