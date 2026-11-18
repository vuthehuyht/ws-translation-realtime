"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardHeader } from "@/components/dashboard/dashboard-header";
import { DashboardSessionProvider } from "@/components/dashboard/dashboard-session-context";
import { type AuthSession, getAuthSession } from "@/lib/auth-storage";

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
    // Check storage once on mount; avoid depending on router identity so unstable mocks
    // or Next.js router updates cannot trigger repeated setSession re-render loops.
    const currentSession = getAuthSession();
    if (!currentSession) {
      routerRef.current.replace("/login");
      return;
    }
    setSession(currentSession);
    setIsReady(true);
  }, []);

  if (!isReady) {
    return (
      <div className="flex flex-1 items-center justify-center bg-slate-50 text-sm text-muted-foreground">
        Đang tải không gian làm việc...
      </div>
    );
  }

  return (
    <DashboardSessionProvider session={session}>
      <div className="flex-1 bg-slate-50/70">
        <DashboardHeader
          userName={session?.user.fullName}
          userEmail={session?.user.email}
        />
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
          {children}
        </main>
      </div>
    </DashboardSessionProvider>
  );
}
