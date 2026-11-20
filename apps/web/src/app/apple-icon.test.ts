import { describe, expect, it } from "vitest";
import AppleIcon, { contentType, size } from "./apple-icon";

describe("AppleIcon (apple-icon.tsx)", () => {
  it("exports standard 180x180 PNG metadata and returns an ImageResponse", () => {
    expect(size).toEqual({ width: 180, height: 180 });
    expect(contentType).toBe("image/png");

    const response = AppleIcon();
    expect(response).toBeInstanceOf(Response);
  });
});
