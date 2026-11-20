"use client";

import React, { useMemo, useState } from "react";
import { Mic } from "lucide-react";

export interface RecentRoomItem {
  id: string;
  code: string;
  title: string;
  mode: "Broadcast" | "1-on-1";
  langs: string;
  status: "LIVE" | "ENDED";
  duration: string;
  cost: string;
}

interface RecentRoomsListProps {
  rooms: RecentRoomItem[];
  onRoomAction?: (room: RecentRoomItem) => void;
}

export function RecentRoomsList({
  rooms,
  onRoomAction,
}: RecentRoomsListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "LIVE" | "ENDED">(
    "ALL"
  );

  const filteredRooms = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return rooms.filter((room) => {
      const matchesText =
        !q ||
        room.title.toLowerCase().includes(q) ||
        room.code.toLowerCase().includes(q);
      const matchesStatus =
        statusFilter === "ALL" || room.status === statusFilter;
      return matchesText && matchesStatus;
    });
  }, [rooms, searchQuery, statusFilter]);

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <div className="flex flex-col gap-3 border-b border-border p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-bold text-foreground">
            Phòng dịch gần đây
          </h2>
          <p className="text-xs text-muted-foreground">
            Theo dõi phiên đang chạy, thời lượng, chi phí và xem lại tóm tắt AI.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm tên hoặc mã phòng..."
            aria-label="Tìm kiếm phòng dịch"
            className="h-9 rounded-lg border border-border bg-background px-3 text-xs text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:outline-none"
          />
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as "ALL" | "LIVE" | "ENDED")
            }
            aria-label="Lọc trạng thái phòng"
            className="h-9 rounded-lg border border-border bg-background px-2.5 text-xs font-medium text-foreground focus-visible:border-primary focus-visible:outline-none"
          >
            <option value="ALL">Tất cả trạng thái</option>
            <option value="LIVE">Đang LIVE</option>
            <option value="ENDED">Đã kết thúc</option>
          </select>
        </div>
      </div>

      {filteredRooms.length === 0 ? (
        <div className="px-4 py-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
            <Mic className="h-6 w-6" />
          </div>
          <h3 className="mt-3 text-sm font-bold text-foreground">
            Chưa có phòng dịch nào
          </h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Hãy chọn ngôn ngữ đích và bấm &quot;Tạo &amp; mở phòng dịch ngay&quot; ở
            phía trên.
          </p>
        </div>
      ) : (
        <>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/50 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Phòng / Mã</th>
                  <th className="px-5 py-3">Chế độ</th>
                  <th className="px-5 py-3">Ngôn ngữ</th>
                  <th className="px-5 py-3">Trạng thái</th>
                  <th className="px-5 py-3">Thời lượng</th>
                  <th className="px-5 py-3">Chi phí</th>
                  <th className="px-5 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredRooms.map((room) => (
                  <tr
                    key={room.id}
                    className="transition-colors hover:bg-muted/30"
                  >
                    <td className="px-5 py-3.5">
                      <p className="font-semibold text-foreground">
                        {room.title}
                      </p>
                      <p className="font-mono text-[11px] text-muted-foreground">
                        #{room.code}
                      </p>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-foreground">
                      {room.mode}
                    </td>
                    <td className="px-5 py-3.5 text-muted-foreground">
                      {room.langs}
                    </td>
                    <td className="px-5 py-3.5">
                      <RoomStatusBadge status={room.status} />
                    </td>
                    <td className="px-5 py-3.5 tabular-nums text-foreground">
                      {room.duration}
                    </td>
                    <td className="px-5 py-3.5 font-semibold tabular-nums text-foreground">
                      {room.cost}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <RoomActionButton
                        room={room}
                        onAction={onRoomAction}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="divide-y divide-border/60 md:hidden">
            {filteredRooms.map((room) => (
              <div key={room.id} className="space-y-2.5 p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-foreground">
                      {room.title}
                    </p>
                    <p className="font-mono text-[11px] text-muted-foreground">
                      #{room.code} · {room.mode}
                    </p>
                  </div>
                  <RoomStatusBadge status={room.status} />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{room.langs}</span>
                  <span className="font-semibold tabular-nums text-foreground">
                    {room.duration} · {room.cost}
                  </span>
                </div>
                <RoomActionButton room={room} onAction={onRoomAction} />
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function RoomActionButton({
  room,
  onAction,
}: {
  room: RecentRoomItem;
  onAction?: (room: RecentRoomItem) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onAction?.(room)}
      className={
        room.status === "LIVE"
          ? "rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700"
          : "rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted"
      }
    >
      {room.status === "LIVE" ? "Vào lại phòng" : "Lịch sử & AI"}
    </button>
  );
}

function RoomStatusBadge({ status }: { status: "LIVE" | "ENDED" }) {
  if (status === "LIVE") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
        LIVE
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
      ENDED
    </span>
  );
}
