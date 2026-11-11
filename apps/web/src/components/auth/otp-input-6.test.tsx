import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { OtpInput6 } from "./otp-input-6";

describe("OtpInput6 component", () => {
  it("renders exactly 6 input fields", () => {
    render(<OtpInput6 value="" onChange={vi.fn()} />);
    const inputs = screen.getAllByRole("textbox");
    expect(inputs).toHaveLength(6);
  });

  it("calls onChange when typing digits", () => {
    const handleChange = vi.fn();
    render(<OtpInput6 value="" onChange={handleChange} />);
    const firstInput = screen.getByLabelText("Mã OTP số 1");

    fireEvent.change(firstInput, { target: { value: "8" } });
    expect(handleChange).toHaveBeenCalledWith("8");
  });

  it("handles paste event and populates 6 digits", () => {
    const handleChange = vi.fn();
    const handleComplete = vi.fn();
    const { rerender } = render(
      <OtpInput6 value="" onChange={handleChange} onComplete={handleComplete} />
    );

    const firstInput = screen.getByLabelText("Mã OTP số 1");
    fireEvent.paste(firstInput, {
      clipboardData: {
        getData: () => "849201",
      },
    });

    expect(handleChange).toHaveBeenCalledWith("849201");

    // Rerender with value
    rerender(
      <OtpInput6
        value="849201"
        onChange={handleChange}
        onComplete={handleComplete}
      />
    );
    expect(handleComplete).toHaveBeenCalledWith("849201");
  });

  it("handles backspace to delete previous digit", () => {
    const handleChange = vi.fn();
    render(<OtpInput6 value="8" onChange={handleChange} />);
    const secondInput = screen.getByLabelText("Mã OTP số 2");

    fireEvent.keyDown(secondInput, { key: "Backspace" });
    expect(handleChange).toHaveBeenCalledWith("");
  });
});
