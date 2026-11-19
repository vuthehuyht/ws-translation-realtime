"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AudioWaveform,
  ChevronDown,
  CreditCard,
  LogOut,
  Settings,
  ShieldAlert,
  User,
} from "lucide-react";
import { signOutSession } from "@/lib/auth-logout";
import { clearAuthSession } from "@/lib/auth-storage";
import { cn } from "@/lib/utils";

interface DashboardHeaderProps {
  userName?: string | null;
  userEmail?: string;
}

export function DashboardHeader({
  userName,
  userEmail,
}: DashboardHeaderProps) {
  const router = useRouter();

  const displayName = userName?.trim() || userEmail || "Host";
  const avatarInitial = displayName.charAt(0).toUpperCase();

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);
  // A ref closes the double-submit window that state alone leaves open within one tick.
  const signingOutRef = useRef(false);
  const menuContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isMenuOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      if (
        menuContainerRef.current &&
        !menuContainerRef.current.contains(event.target as Node)
      ) {
        setIsMenuOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMenuOpen]);

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

        <div ref={menuContainerRef} className="relative flex items-center gap-3">
          <button
            type="button"
            aria-label="Mở menu tài khoản"
            aria-haspopup="menu"
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen((prev) => !prev)}
            className={cn(
              "flex items-center gap-2.5 rounded-full border border-border bg-background px-2.5 py-1.5 text-left transition-colors hover:bg-muted/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 sm:px-3",
              isMenuOpen && "border-primary/40 bg-muted/60"
            )}
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-600/15 text-xs font-bold text-indigo-600">
              {avatarInitial}
            </span>
            <div className="hidden leading-tight md:block">
              <p className="max-w-[160px] truncate text-xs font-semibold text-foreground">
                {displayName}
              </p>
              {userEmail && userName && (
                <p className="max-w-[160px] truncate text-[11px] text-muted-foreground">
                  {userEmail}
                </p>
              )}
            </div>
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 text-muted-foreground transition-transform duration-150",
                isMenuOpen && "rotate-180 text-foreground"
              )}
            />
          </button>

          {isMenuOpen && (
            <div
              role="menu"
              aria-label="Menu tài khoản"
              className="absolute right-0 top-full z-40 mt-2 w-64 origin-top-right rounded-xl border border-border bg-card p-1.5 shadow-lg shadow-slate-900/10"
            >
              <div className="border-b border-border/80 px-3 py-2.5">
                <p className="truncate text-xs font-semibold text-foreground">
                  {displayName}
                </p>
                {userEmail && (
                  <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                    {userEmail}
                  </p>
                )}
              </div>

              <div className="py-1">
                <button
                  type="button"
                  role="menuitem"
                  disabled
                  title="Trang Hồ sơ cá nhân đang được phát triển"
                  className="flex w-full cursor-not-allowed items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-muted-foreground/70"
                >
                  <span className="inline-flex items-center gap-2">
                    <User className="h-3.5 w-3.5" />
                    <span>Hồ sơ cá nhân</span>
                  </span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                    Sắp ra mắt
                  </span>
                </button>

                <button
                  type="button"
                  role="menuitem"
                  disabled
                  title="Trang Cài đặt đang được phát triển"
                  className="flex w-full cursor-not-allowed items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-muted-foreground/70"
                >
                  <span className="inline-flex items-center gap-2">
                    <Settings className="h-3.5 w-3.5" />
                    <span>Cài đặt</span>
                  </span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                    Sắp ra mắt
                  </span>
                </button>

                <button
                  type="button"
                  role="menuitem"
                  disabled
                  title="Trang Thanh toán & Gói Credit đang được phát triển"
                  className="flex w-full cursor-not-allowed items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-muted-foreground/70"
                >
                  <span className="inline-flex items-center gap-2">
                    <CreditCard className="h-3.5 w-3.5" />
                    <span>Thanh toán &amp; Gói Credit</span>
                  </span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                    Sắp ra mắt
                  </span>
                </button>
              </div>

              <div className="border-t border-border/80 pt-1">
                {logoutError && (
                  <p
                    role="alert"
                    className="mx-2 mb-1 rounded-md bg-destructive/10 px-2.5 py-1.5 text-[11px] font-medium text-destructive"
                  >
                    {logoutError}
                  </p>
                )}

                <button
                  type="button"
                  role="menuitem"
                  onClick={() => void handleLogout(false)}
                  disabled={isSigningOut}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-60"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Đăng xuất</span>
                </button>

                <button
                  type="button"
                  role="menuitem"
                  onClick={() => void handleLogout(true)}
                  disabled={isSigningOut}
                  title="Đăng xuất khỏi tất cả thiết bị"
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10 disabled:opacity-60"
                >
                  <ShieldAlert className="h-3.5 w-3.5" />
                  <span>Đăng xuất mọi thiết bị</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
