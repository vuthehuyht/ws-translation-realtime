"use client";

import React from "react";

export function WalletCardSkeleton() {
  return (
    <div
      data-testid="wallet-card-skeleton"
      className="h-full rounded-2xl border border-border bg-card p-6 shadow-sm animate-pulse"
    >
      <div className="flex items-center justify-between">
        <div className="h-4 w-28 rounded bg-slate-200" />
        <div className="h-6 w-20 rounded-full bg-slate-200" />
      </div>
      <div className="mt-5 h-9 w-36 rounded-lg bg-slate-200" />
      <div className="mt-2 h-3.5 w-44 rounded bg-slate-100" />
      <div className="mt-6 space-y-3">
        <div className="h-10 w-full rounded-xl bg-slate-200" />
        <div className="h-9 w-full rounded-xl bg-slate-100" />
      </div>
    </div>
  );
}

export function CreateRoomCardSkeleton() {
  return (
    <div
      data-testid="create-room-card-skeleton"
      className="h-full rounded-2xl border border-border bg-card p-6 shadow-sm animate-pulse"
    >
      <div className="h-5 w-48 rounded bg-slate-200" />
      <div className="mt-2 h-3.5 w-72 rounded bg-slate-100" />
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="h-10 rounded-xl bg-slate-100" />
        <div className="h-10 rounded-xl bg-slate-100" />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <div className="h-9 rounded-lg bg-slate-100" />
        <div className="h-9 rounded-lg bg-slate-100" />
        <div className="h-9 rounded-lg bg-slate-100" />
        <div className="h-9 rounded-lg bg-slate-100" />
      </div>
      <div className="mt-6 h-11 w-full rounded-xl bg-slate-200" />
    </div>
  );
}

export function RecentRoomsListSkeleton() {
  return (
    <div
      data-testid="recent-rooms-skeleton"
      className="rounded-2xl border border-border bg-card p-6 shadow-sm animate-pulse"
    >
      <div className="h-5 w-40 rounded bg-slate-200" />
      <div className="mt-4 space-y-3">
        <div className="h-14 w-full rounded-xl bg-slate-100" />
        <div className="h-14 w-full rounded-xl bg-slate-100" />
      </div>
    </div>
  );
}

export function DashboardSkeleton({ includeHeader = false }: { includeHeader?: boolean }) {
  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="dashboard-skeleton"
      className="flex-1 bg-slate-50/70"
    >
      <span className="sr-only">Đang tải không gian làm việc...</span>

      {includeHeader && (
        <div className="border-b border-border bg-card/80 px-4 py-3.5 sm:px-6 lg:px-8 animate-pulse">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <div className="h-6 w-40 rounded bg-slate-200" />
            <div className="flex items-center gap-3">
              <div className="h-8 w-28 rounded-lg bg-slate-100" />
              <div className="h-8 w-24 rounded-lg bg-slate-200" />
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between animate-pulse">
          <div className="space-y-2">
            <div className="h-7 w-56 rounded-lg bg-slate-200" />
            <div className="h-4 w-80 max-w-full rounded bg-slate-100" />
          </div>
          <div className="flex gap-2">
            <div className="h-7 w-36 rounded-full bg-slate-200" />
            <div className="h-7 w-44 rounded-full bg-slate-100" />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <WalletCardSkeleton />
          </div>
          <div className="lg:col-span-8">
            <CreateRoomCardSkeleton />
          </div>
        </div>

        <RecentRoomsListSkeleton />
      </div>
    </div>
  );
}
