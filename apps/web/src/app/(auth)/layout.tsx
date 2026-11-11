import React from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-5xl overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
        {children}
      </div>
    </div>
  );
}
