"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { DashboardSessionProvider } from "@/components/dashboard/dashboard-session-context";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import {
  getRefreshLeadDelayMs,
  silentRefreshSession,
  subscribeAuthSession,
} from "@/lib/auth-refresh";
import { type AuthSession, getAuthSession } from "@/lib/auth-storage";

const REFRESH_LEAD_TIME_MS = 60_000;

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const routerRef = useRef(router);
  routerRef.current = router;

  const [session, setSession] = useState<AuthSession | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const unsubscribe = subscribeAuthSession((nextSession) => {
      if (cancelled) {
        return;
      }
      if (!nextSession) {
        setSession(null);
        setIsReady(false);
        routerRef.current.replace("/login");
        return;
      }
      setSession(nextSession);
      setIsReady(true);
    });

    const initializeSession = async () => {
      // Attempt HttpOnly cookie recovery when accessToken is absent or expired.
      let currentSession = getAuthSession();
      if (!currentSession) {
        currentSession = await silentRefreshSession();
      }
      if (cancelled) {
        return;
      }
      if (!currentSession) {
        routerRef.current.replace("/login");
        return;
      }
      setSession(currentSession);
      setIsReady(true);
    };

    void initializeSession();

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    const expiresAt = session?.expiresAt;
    if (!expiresAt) {
      return;
    }

    let cancelled = false;
    let retryTimerId: number | null = null;

    const triggerProactiveRefresh = async () => {
      // Drop any pending retry so repeated visibilitychange events cannot stack timers.
      if (retryTimerId !== null) {
        window.clearTimeout(retryTimerId);
        retryTimerId = null;
      }
      const refreshed = await silentRefreshSession();
      if (cancelled) {
        return;
      }
      if (!refreshed) {
        if (Date.now() >= expiresAt) {
          routerRef.current.replace("/login");
        } else {
          // Retry after a transient network/5xx error while the access token still has time left.
          const retryDelayMs = Math.min(15_000, Math.max(1_000, expiresAt - Date.now()));
          retryTimerId = window.setTimeout(() => {
            void triggerProactiveRefresh();
          }, retryDelayMs);
        }
      }
    };

    const delayMs = getRefreshLeadDelayMs(expiresAt, REFRESH_LEAD_TIME_MS);
    const timerId = window.setTimeout(() => {
      void triggerProactiveRefresh();
    }, delayMs);

    const handleVisibilityChange = () => {
      if (
        document.visibilityState === "visible" &&
        Date.now() >= expiresAt - REFRESH_LEAD_TIME_MS
      ) {
        void triggerProactiveRefresh();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      cancelled = true;
      window.clearTimeout(timerId);
      if (retryTimerId !== null) {
        window.clearTimeout(retryTimerId);
      }
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [session?.expiresAt]);

  if (!isReady) {
    return <DashboardSkeleton includeHeader={true} />;
  }

  return (
    <DashboardSessionProvider session={session}>
      <div className="flex-1 bg-slate-50/70">
        <DashboardHeader
          userName={session?.user.fullName}
          userEmail={session?.user.email}
          avatarUrl={session?.user.avatarUrl}
        />
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
          {children}
        </main>
      </div>
    </DashboardSessionProvider>
  );
}
