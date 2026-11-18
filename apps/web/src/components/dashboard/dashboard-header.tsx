"use client";

import React, { useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  AudioWaveform,
  CreditCard,
  LayoutDashboard,
  LogOut,
} from "lucide-react";
import { signOutSession } from "@/lib/auth-logout";
import { clearAuthSession } from "@/lib/auth-storage";
import { cn } from "@/lib/utils";

interface DashboardHeaderProps {
  userName?: string | null;
  userEmail?: string;
}

const NAV_ITEMS = [
  {
    href: "/dashboard",
    label: "Tổng quan",
    icon: LayoutDashboard,
    disabled: false,
  },
  {
    href: "/dashboard/billing",
    label: "Thanh toán",
    icon: CreditCard,
    // Keep billing disabled until the /dashboard/billing route is implemented to avoid 404 navigation.
    disabled: true,
  },
];

export function DashboardHeader({
  userName,
  userEmail,
}: DashboardHeaderProps) {
  const pathname = usePathname();
  const router = useRouter();

  const displayName = userName?.trim() || userEmail || "Host";
  const avatarInitial = displayName.charAt(0).toUpperCase();

  const [isSigningOut, setIsSigningOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);
  // A ref closes the double-submit window that state alone leaves open within one tick.
  const signingOutRef = useRef(false);

  const handleLogout = async (global: boolean) => {
    if (signingOutRef.current) {
      return;
    }
    if (
      global &&
      !window.confirm("Đăng xuất khỏi tất cả thiết bị? Mọi phiên đang mở sẽ bị đóng.")
    ) {
      return;
    }
    signingOutRef.current = true;
    setIsSigningOut(true);
    setLogoutError(null);
    try {
      await signOutSession({ global });
    } catch (error) {
      // Keep the session: clearing locally while the HttpOnly cookie is alive would let silent
      // refresh sign the user straight back in.
      console.error("Logout failed", error);
      setLogoutError("Không thể đăng xuất lúc này. Vui lòng thử lại.");
      signingOutRef.current = false;
      setIsSigningOut(false);
      return;
    }
    clearAuthSession();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-sm shadow-indigo-600/25">
              <AudioWaveform className="h-5 w-5" />
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-bold tracking-tight text-foreground">
                VoiceBridge AI
              </p>
              <p className="text-[11px] font-medium text-muted-foreground">
                Host Studio
              </p>
            </div>
          </Link>

          <nav
            aria-label="Dashboard navigation"
            className="flex items-center gap-1"
          >
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              if (item.disabled) {
                return (
                  <span
                    key={item.href}
                    aria-disabled="true"
                    title="Trang Thanh toán đang được phát triển"
                    className="inline-flex cursor-not-allowed items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold text-muted-foreground/60"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                      Sắp ra mắt
                    </span>
                  </span>
                );
              }

              const isActive =
                item.href === "/dashboard"
                  ? pathname === "/dashboard"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2.5 rounded-full border border-border bg-background px-3 py-1.5 md:flex">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600/15 text-xs font-bold text-indigo-600">
              {avatarInitial}
            </span>
            <div className="text-left leading-tight">
              <p className="text-xs font-semibold text-foreground">
                {displayName}
              </p>
              {userEmail && userName && (
                <p className="text-[11px] text-muted-foreground">{userEmail}</p>
              )}
            </div>
          </div>

          {logoutError && (
            <p role="alert" className="text-xs font-medium text-destructive">
              {logoutError}
            </p>
          )}

          <button
            type="button"
            onClick={() => void handleLogout(true)}
            disabled={isSigningOut}
            title="Đăng xuất khỏi tất cả thiết bị"
            className="inline-flex items-center rounded-lg px-2 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-60"
          >
            Mọi thiết bị
          </button>

          <button
            type="button"
            onClick={() => void handleLogout(false)}
            disabled={isSigningOut}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-60"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </div>
    </header>
  );
}
