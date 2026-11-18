"use client";

import React, { createContext, useContext } from "react";
import type { AuthSession } from "@/lib/auth-storage";

const DashboardSessionContext = createContext<AuthSession | null>(null);

export function DashboardSessionProvider({
  session,
  children,
}: {
  session: AuthSession | null;
  children: React.ReactNode;
}) {
  return (
    <DashboardSessionContext.Provider value={session}>
      {children}
    </DashboardSessionContext.Provider>
  );
}

export function useDashboardSession(): AuthSession | null {
  return useContext(DashboardSessionContext);
}
