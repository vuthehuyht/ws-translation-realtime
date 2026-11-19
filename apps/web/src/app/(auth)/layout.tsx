import React from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-1 items-center justify-center bg-muted/30 px-4 pt-16 pb-10 sm:px-6 sm:pt-24 sm:pb-12 lg:px-8 lg:pt-28 lg:pb-14">
      <div className="w-full max-w-5xl overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
        {children}
      </div>
    </div>
  );
}
