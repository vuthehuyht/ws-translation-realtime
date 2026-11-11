import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { AudioTechHero } from "./audio-tech-hero";

describe("AudioTechHero component", () => {
  it("renders default title and latency trust metrics", () => {
    render(<AudioTechHero />);
    expect(
      screen.getByText(/Xóa bỏ rào cản ngôn ngữ/i)
    ).toBeInTheDocument();
    expect(screen.getByText("< 500ms")).toBeInTheDocument();
    expect(screen.getByText("1,000+")).toBeInTheDocument();
    expect(screen.getByText("$0 Idle")).toBeInTheDocument();
  });

  it("renders audio stream simulation with VAD badge and speech chips", () => {
    render(<AudioTechHero />);
    expect(screen.getByText("VAD: SPEAKING")).toBeInTheDocument();
    expect(screen.getByText("[vi-VN]")).toBeInTheDocument();
    expect(screen.getByText("[ja-JP]")).toBeInTheDocument();
  });

  it("renders free trial offer card when showTrialCard is true", () => {
    render(
      <AudioTechHero
        showTrialCard={true}
        title="Bắt đầu tổ chức phiên dịch trong 30 giây"
      />
    );
    expect(
      screen.getByText("Bắt đầu tổ chức phiên dịch trong 30 giây")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Tặng 10 phút dịch thử nghiệm miễn phí/i)
    ).toBeInTheDocument();
  });
});
