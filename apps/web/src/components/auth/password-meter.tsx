import React from "react";
import { cn } from "@/lib/utils";

export interface PasswordStrengthResult {
  score: number; // 0 to 4
  label: string;
  colorClass: string;
}

/**
 * Calculates password strength score (0-4) based on length, complexity and character variety.
 */
export function calculatePasswordStrength(password: string): PasswordStrengthResult {
  if (!password) {
    return {
      score: 0,
      label: "Chưa nhập mật khẩu",
      colorClass: "bg-muted",
    };
  }

  let points = 0;

  // Length checks
  if (password.length >= 6) points += 1;
  if (password.length >= 8) points += 1;

  // Complexity checks
  const hasLetters = /[a-zA-Z]/.test(password);
  const hasNumbers = /[0-9]/.test(password);
  const hasSpecial = /[^a-zA-Z0-9]/.test(password);

  if (hasLetters && hasNumbers) points += 1;
  if (hasSpecial && password.length >= 8) points += 1;

  // Clamp points to 1..4 when password is not empty
  const score = Math.min(Math.max(points, 1), 4);

  switch (score) {
    case 1:
      return {
        score: 1,
        label: "Mật khẩu yếu (tối thiểu 8 ký tự)",
        colorClass: "bg-red-500",
      };
    case 2:
      return {
        score: 2,
        label: "Mật khẩu trung bình (thêm số hoặc chữ hoa)",
        colorClass: "bg-amber-500",
      };
    case 3:
      return {
        score: 3,
        label: "Mật khẩu khá (thêm ký tự đặc biệt)",
        colorClass: "bg-blue-500",
      };
    case 4:
    default:
      return {
        score: 4,
        label: "Mật khẩu mạnh (gồm chữ hoa, số và ký tự đặc biệt)",
        colorClass: "bg-emerald-500",
      };
  }
}

interface PasswordMeterProps {
  password: string;
  className?: string;
}

export function PasswordMeter({ password, className }: PasswordMeterProps) {
  const { score, label, colorClass } = calculatePasswordStrength(password);

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex gap-1.5" aria-hidden="true">
        {[1, 2, 3, 4].map((step) => {
          const isActive = score >= step;
          return (
            <div
              key={step}
              data-testid="password-strength-bar"
              className={cn(
                "h-1.5 flex-1 rounded-full transition-colors duration-200",
                isActive ? colorClass : "bg-muted"
              )}
            />
          );
        })}
      </div>
      <p
        className={cn(
          "text-xs font-medium transition-colors duration-200",
          score === 0 && "text-muted-foreground",
          score === 1 && "text-red-500",
          score === 2 && "text-amber-500",
          score === 3 && "text-blue-500",
          score === 4 && "text-emerald-500"
        )}
      >
        {label}
      </p>
    </div>
  );
}
