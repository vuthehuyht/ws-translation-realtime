import React from "react";
import { cn } from "@/lib/utils";

interface SecurityBrandHeroProps {
  icon?: React.ReactNode;
  title: string;
  description: React.ReactNode;
  footerText?: React.ReactNode;
  className?: string;
}

export function SecurityBrandHero({
  icon,
  title,
  description,
  footerText,
  className,
}: SecurityBrandHeroProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col justify-between overflow-hidden bg-[radial-gradient(circle_at_20%_30%,_#1e1b4b_0%,_#0f172a_60%,_#020617_100%)] p-8 sm:p-10 lg:p-12 text-white",
        className
      )}
    >
      {/* Ambient background glows */}
      <div
        className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-indigo-500/25 blur-[80px]"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -bottom-20 -right-20 h-72 w-72 rounded-full bg-cyan-500/20 blur-[80px]"
        aria-hidden="true"
      />

      {/* Top Brand & Security Content */}
      <div className="relative z-10 space-y-4">
        {icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/12 bg-white/8 text-2xl backdrop-blur-md">
            {icon}
          </div>
        )}

        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl lg:text-[1.85rem] leading-[1.25]">
          {title}
        </h1>

        <div className="max-w-md text-sm text-[#94a3b8] leading-relaxed space-y-2">
          {description}
        </div>
      </div>

      {/* Bottom Footer or Security Note */}
      {footerText && (
        <div className="relative z-10 border-t border-white/8 pt-4 text-xs text-[#64748b]">
          {footerText}
        </div>
      )}
    </div>
  );
}
