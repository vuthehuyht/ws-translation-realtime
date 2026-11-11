import { describe, it, expect } from "vitest";
import { cn, formatCurrency, formatDuration } from "./utils";

describe("utils module", () => {
  describe("cn", () => {
    it("merges class names correctly without conflicts", () => {
      expect(cn("px-2 py-1", "bg-white")).toBe("px-2 py-1 bg-white");
      expect(cn("p-2", "p-4")).toBe("p-4");
      expect(cn("text-red-500", undefined, null, false && "text-blue-500")).toBe("text-red-500");
    });
  });

  describe("formatCurrency", () => {
    it("formats USD currency correctly", () => {
      expect(formatCurrency(48.5, "USD")).toBe("$48.50");
      expect(formatCurrency(0, "USD")).toBe("$0.00");
    });

    it("formats VND currency correctly", () => {
      const v = formatCurrency(1235000, "VND");
      expect(v).toContain("1.235.000");
    });
  });

  describe("formatDuration", () => {
    it("formats seconds into mm:ss format", () => {
      expect(formatDuration(0)).toBe("00:00");
      expect(formatDuration(45)).toBe("00:45");
      expect(formatDuration(75)).toBe("01:15");
    });

    it("formats seconds into hh:mm:ss format when over 1 hour", () => {
      expect(formatDuration(3665)).toBe("01:01:05");
    });
  });
});
