"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import type { CreateRoomFormPayload } from "@/components/dashboard/create-room-card";
import { useDashboardSession } from "@/components/dashboard/dashboard-session-context";
import {
  CreateRoomCardSkeleton,
  RecentRoomsListSkeleton,
  WalletCardSkeleton,
} from "@/components/dashboard/dashboard-skeleton";
import type { RecentRoomItem } from "@/components/dashboard/recent-rooms-list";

const WalletCard = dynamic(
  () => import("@/components/dashboard/wallet-card").then((mod) => mod.WalletCard),
  { loading: () => <WalletCardSkeleton /> }
);

const CreateRoomCard = dynamic(
  () =>
    import("@/components/dashboard/create-room-card").then((mod) => mod.CreateRoomCard),
  { loading: () => <CreateRoomCardSkeleton /> }
);

const RecentRoomsList = dynamic(
  () =>
    import("@/components/dashboard/recent-rooms-list").then(
      (mod) => mod.RecentRoomsList
    ),
  { loading: () => <RecentRoomsListSkeleton /> }
);

const INITIAL_PREVIEW_ROOMS: RecentRoomItem[] = [
  {
    id: "rm-9104",
    code: "RM-9104",
    title: "Client Sync APAC",
    mode: "1-on-1",
    langs: "EN -> VI",
    status: "LIVE",
    duration: "12m 00s",
    cost: "$0.90",
  },
  {
    id: "rm-8492",
    code: "RM-8492",
    title: "Tech Summit 2026 Keynote",
    mode: "Broadcast",
    langs: "VI -> EN, JA, KO (+2)",
    status: "ENDED",
    duration: "45m 10s",
    cost: "$6.78",
  },
];

export default function DashboardPage() {
  const session = useDashboardSession();
  const displayName =
    session?.user.fullName?.trim() || session?.user.email || "Host";

  const [balance, setBalance] = useState<number>(2.0);
  const [autoTopUp, setAutoTopUp] = useState<boolean>(true);
  const [rooms, setRooms] = useState<RecentRoomItem[]>(INITIAL_PREVIEW_ROOMS);
  const [notice, setNotice] = useState<string | null>(null);

  const handleTopUpConfirm = (
    amountUsd: number,
    method: "stripe" | "vietqr"
  ) => {
    setBalance((prev) => prev + amountUsd);
    const providerLabel = method === "stripe" ? "Stripe" : "VietQR";
    setNotice(
      `Đã ghi nhận yêu cầu nạp +$${amountUsd.toFixed(2)} qua ${providerLabel} (UI preview, sẽ kết nối Wallet API ở task tiếp theo).`
    );
  };

  const handleToggleAutoTopUp = (nextValue: boolean) => {
    setAutoTopUp(nextValue);
    setNotice(
      `Auto Top-up đã chuyển sang trạng thái ${nextValue ? "BẬT" : "TẮT"}.`
    );
  };

  const handleCreateRoom = (payload: CreateRoomFormPayload) => {
    const randomCode = Math.floor(1000 + Math.random() * 8999);
    const sourceShort = payload.sourceLang.split("-")[0].toUpperCase();
    const targetPreview = payload.targetLangs
      .slice(0, 2)
      .map((code) => code.split("-")[0].toUpperCase())
      .join(", ");
    const extraCount =
      payload.targetLangs.length > 2
        ? ` (+${payload.targetLangs.length - 2})`
        : "";

    const newRoom: RecentRoomItem = {
      id: `rm-${randomCode}`,
      code: `RM-${randomCode}`,
      title: payload.title || `Phiên dịch mới #${randomCode}`,
      mode: payload.mode === "BROADCAST" ? "Broadcast" : "1-on-1",
      langs: `${sourceShort} -> ${targetPreview}${extraCount}`,
      status: "LIVE",
      duration: "00m 00s",
      cost: "$0.00",
    };

    setRooms((prev) => [newRoom, ...prev]);
    setNotice(
      `Đã khởi tạo phòng #${newRoom.code} (UI preview, sẽ điều hướng sang Live Room khi Room API sẵn sàng).`
    );
  };

  const handleRoomAction = (room: RecentRoomItem) => {
    setNotice(
      room.status === "LIVE"
        ? `Màn hình Live Host Studio cho phòng #${room.code} đang được phát triển.`
        : `Màn hình Lịch sử & Tóm tắt AI cho phòng #${room.code} đang được phát triển.`
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Xin chào, {displayName}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Quản lý số dư ví, khởi tạo phòng dịch trực tiếp và xem lại lịch sử
            biên bản AI.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-700">
            <span>UI Preview (Dữ liệu mẫu)</span>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-semibold text-emerald-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            <span>AWS Realtime Pipeline · &lt; 500ms</span>
          </div>
        </div>
      </div>

      {notice && (
        <div
          role="status"
          className="flex items-center justify-between gap-4 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-xs font-medium text-indigo-800"
        >
          <span>{notice}</span>
          <button
            type="button"
            onClick={() => setNotice(null)}
            className="shrink-0 font-semibold text-indigo-700 hover:underline"
          >
            Đóng
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <WalletCard
            balance={balance}
            autoTopUp={autoTopUp}
            onToggleAutoTopUp={handleToggleAutoTopUp}
            onTopUpConfirm={handleTopUpConfirm}
            onViewBilling={() =>
              setNotice("Màn hình Lịch sử giao dịch & Hóa đơn đang được phát triển.")
            }
          />
        </div>

        <div className="lg:col-span-8">
          <CreateRoomCard
            initialSourceLang={session?.user.defaultSourceLang}
            initialTargetLangs={session?.user.defaultTargetLangs}
            onCreateRoom={handleCreateRoom}
          />
        </div>
      </div>

      <RecentRoomsList rooms={rooms} onRoomAction={handleRoomAction} />
    </div>
  );
}
