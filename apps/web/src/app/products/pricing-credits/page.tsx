"use client";

import React, { useState } from "react";
import { Check, ChevronDown, Coins, HelpCircle, Minus, Sparkles } from "lucide-react";
import { ProductPageShell } from "@/components/products/product-page-shell";
import { cn } from "@/lib/utils";

const PLANS = [
  {
    code: "FREE",
    name: "Free",
    price: "$0",
    credits: "200 Cr dùng thử (1 lần)",
    bonus: "+0% Top-up",
    features: [
      "Chế độ 1-on-1 (1 ngôn ngữ, 2 người)",
      "Phụ đề realtime (Text-only)",
      "Lưu biên bản online 7 ngày",
      "Giới hạn 15 phút/phòng",
    ],
  },
  {
    code: "PRO",
    name: "Pro",
    price: "$19/tháng",
    credits: "1.800 Cr / tháng",
    bonus: "+5% Top-up",
    highlight: true,
    features: [
      "1-on-1 & Broadcast (3 ngôn ngữ, 100 người)",
      "Giọng đọc Neural TTS + lọc từ nhạy cảm",
      "Passcode + lên lịch phòng trước",
      "Export .txt/.md (30 ngày) + AI Summary gốc",
    ],
  },
  {
    code: "BUSINESS",
    name: "Business",
    price: "$59/tháng",
    credits: "6.000 Cr / tháng",
    bonus: "+10% Top-up",
    features: [
      "Broadcast 6 ngôn ngữ, 300 người, 3 phòng song song",
      "Chọn giọng Nam/Nữ + 3 Co-Host + Custom Logo",
      "Export full .txt/.srt/.vtt/.csv (90 ngày)",
      "AI Summary đa ngôn ngữ + Auto Top-up + VAT",
    ],
  },
  {
    code: "ENTERPRISE",
    name: "Enterprise",
    price: "$199/tháng",
    credits: "21.000 Cr / tháng",
    bonus: "+15% Top-up",
    features: [
      "Broadcast 10 ngôn ngữ, 1.000 người, 10 phòng song song",
      "Full White-label + 10 Co-Host Speakers",
      "Từ điển không giới hạn + Import CSV",
      "Lưu biên bản 365 ngày + Analytics PDF",
    ],
  },
];

const TOPUP_PACKS = [
  { code: "PACK_S", name: "Starter Pack", price: "$10", credits: "1.000 Cr" },
  { code: "PACK_M", name: "Growth Pack", price: "$30", credits: "3.000 Cr" },
  { code: "PACK_L", name: "Scale Pack", price: "$100", credits: "10.000 Cr" },
];

type CellValue = boolean | string;

const COMPARISON_GROUPS: {
  group: string;
  rows: { label: string; values: [CellValue, CellValue, CellValue, CellValue] }[];
}[] = [
  {
    group: "Phòng & điều khiển",
    rows: [
      { label: "Chế độ phòng", values: ["1-on-1", "1-on-1 & Broadcast", "1-on-1 & Broadcast", "1-on-1 & Broadcast"] },
      { label: "Ngôn ngữ đích đồng thời", values: ["1", "3", "6", "10"] },
      { label: "Sĩ số người nghe tối đa", values: ["2", "100", "300", "1.000"] },
      { label: "Số phòng chạy song song", values: ["1 (tối đa 15p)", "1", "3", "10"] },
      { label: "Mật khẩu phòng & lên lịch trước", values: [false, true, true, true] },
      { label: "Nhiều diễn giả luân phiên (Co-Host)", values: ["1", "1", "3", "10"] },
      { label: "Tùy biến thương hiệu phòng nghe", values: [false, false, "Custom Logo/Màu", "Full White-label"] },
    ],
  },
  {
    group: "AI & giọng đọc",
    rows: [
      { label: "Giọng đọc Neural TTS (Polly + Azure vi-VN)", values: [false, true, true, true] },
      { label: "Chọn giọng đọc Nam / Nữ theo ngôn ngữ", values: [false, false, true, true] },
      { label: "Lọc từ nhạy cảm (Profanity Masking)", values: [false, true, true, true] },
      { label: "Bộ từ điển chuyên ngành", values: ["0", "2 bộ (50 từ)", "10 bộ (256 từ)", "Không giới hạn + CSV"] },
    ],
  },
  {
    group: "Biên bản & hậu kỳ",
    rows: [
      { label: "Thời gian lưu trữ biên bản trên S3", values: ["7 ngày", "30 ngày", "90 ngày", "365 ngày"] },
      { label: "Định dạng xuất file biên bản", values: ["Chỉ xem online", ".txt, .md", ".txt, .md, .srt, .vtt, .csv", "Full định dạng"] },
      { label: "Cho phép người nghe tải biên bản", values: [false, false, true, true] },
      { label: "AI tóm tắt cuộc họp (Bedrock)", values: [false, "Ngôn ngữ gốc (15 Cr)", "Đa ngôn ngữ (25 Cr)", "Đa ngôn ngữ (25 Cr)"] },
      { label: "Thống kê phân tích phiên (Analytics)", values: ["Cơ bản", "Cơ bản", "Chi tiết + CSV", "Chi tiết + PDF"] },
    ],
  },
  {
    group: "Thanh toán & hỗ trợ",
    rows: [
      { label: "Hạ cấp mềm tắt TTS khi còn < 1 phút", values: [false, true, true, true] },
      { label: "Tự động nạp gói Credit (Auto Top-up)", values: [false, false, true, true] },
      { label: "Xuất hóa đơn VAT doanh nghiệp (PDF)", values: [false, false, true, true] },
    ],
  },
];

const FAQS = [
  {
    q: "Thứ tự trừ 3 ngăn Credit và hạn sử dụng hoạt động thế nào?",
    a: "Hệ thống luôn ưu tiên trừ ngăn sắp hết hạn trước theo đúng thứ tự: Promo Credits (hạn dùng 30 ngày) -> Plan Credits (tặng hàng tháng, reset cuối chu kỳ) -> Top-up Credits (mua lẻ, không bao giờ hết hạn).",
  },
  {
    q: "Nếu hủy gia hạn hoặc hạ về gói FREE, tôi có bị mất Top-up Credits hay biên bản cũ không?",
    a: "Không. Toàn bộ Top-up Credits được bảo toàn 100% để bạn tiếp tục sử dụng. Biên bản các phòng đã kết thúc vẫn giữ nguyên hạn lưu trữ tại thời điểm tạo phòng và có thêm 14 ngày ân hạn để tải về.",
  },
  {
    q: "Chế độ 1-on-1 song công 2 chiều tính Credit như thế nào?",
    a: "Do cả hai người tham gia đều có thể nói đồng thời (2 luồng nhận diện giọng nói & dịch máy chạy song song), tổng thời lượng tiếng nói của cả 2 đầu micro được tính chính xác theo từng giây vào ví của Host.",
  },
  {
    q: "Nếu dịch vụ AI gặp sự cố (lỗi 5xx), tôi có bị trừ Credit không?",
    a: "Tuyệt đối không. Mọi khung âm thanh hoặc ký tự dịch/giọng đọc bị lỗi 5xx từ phía nhà cung cấp AI đều được loại trừ hoàn toàn khỏi bộ đếm trừ Credit (0 Cr).",
  },
];

function renderMatrixCell(val: CellValue) {
  if (typeof val === "boolean") {
    return val ? (
      <Check className="mx-auto h-4 w-4 text-emerald-600" aria-label="Có hỗ trợ" />
    ) : (
      <Minus className="mx-auto h-4 w-4 text-slate-300" aria-label="Không hỗ trợ" />
    );
  }
  return <span className="text-xs font-medium text-foreground">{val}</span>;
}

export default function PricingCreditsProductPage() {
  const [targetLangs, setTargetLangs] = useState(3);
  const [listeners, setListeners] = useState(50);
  const [withTts, setWithTts] = useState(true);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(0);

  // Per-minute estimate based on retail rates (STT 5.5 + MT ~2.8/lang + TTS ~3.2/lang + Listeners 0.5/100)
  const sttPerMin = 5.5;
  const mtPerMin = targetLangs * 2.8;
  const ttsPerMin = withTts ? targetLangs * 3.2 : 0;
  const listenerPerMin = (listeners / 100) * 0.5;
  const burnRatePerMin = sttPerMin + mtPerMin + ttsPerMin + listenerPerMin;
  const proMinutes = Math.floor(1800 / burnRatePerMin);

  return (
    <ProductPageShell
      badge="Bảng giá & gói cước"
      title="Bảng giá minh bạch, tính cước chính xác theo từng giây"
      subtitle="Quy đổi đơn giản 1 USD = 100 Credits. Luôn ưu tiên trừ Credit sắp hết hạn trước (Khuyến mãi -> Gói tháng -> Nạp thêm không hết hạn) và chỉ tính đúng thời lượng sử dụng thực tế."
    >
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {PLANS.map((plan) => (
          <div
            key={plan.code}
            className={cn(
              "flex flex-col justify-between rounded-2xl border bg-card p-5 shadow-sm",
              plan.highlight
                ? "border-indigo-600 ring-1 ring-indigo-600/20"
                : "border-border"
            )}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-foreground">{plan.name}</span>
                {plan.highlight && (
                  <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
                    Phổ biến
                  </span>
                )}
              </div>
              <p className="mt-2 text-2xl font-bold text-foreground">{plan.price}</p>
              <p className="mt-1 text-xs font-semibold text-indigo-600">{plan.credits}</p>
              <p className="text-[11px] text-muted-foreground">Bonus nạp lẻ: {plan.bonus}</p>
              <ul className="mt-4 space-y-2 text-xs text-muted-foreground">
                {plan.features.map((feat) => (
                  <li key={feat} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm lg:col-span-7">
          <div className="flex items-center gap-2">
            <Coins className="h-4 w-4 text-indigo-600" />
            <h2 className="text-base font-bold text-foreground">
              Bộ mô phỏng tốc độ tiêu thụ Credit (Burn Rate)
            </h2>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Điều chỉnh cấu hình phòng để ước tính số Credit tiêu thụ mỗi phút (tính
            chính xác theo từng giây thực tế).
          </p>

          <div className="mt-5 space-y-4">
            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Số ngôn ngữ đích đồng thời</span>
                <span className="font-bold text-indigo-600">{targetLangs} ngôn ngữ</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={targetLangs}
                onChange={(e) => setTargetLangs(Number(e.target.value))}
                className="mt-2 w-full accent-indigo-600"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Số người nghe trực tuyến</span>
                <span className="font-bold text-indigo-600">{listeners} người</span>
              </div>
              <input
                type="range"
                min={10}
                max={1000}
                step={10}
                value={listeners}
                onChange={(e) => setListeners(Number(e.target.value))}
                className="mt-2 w-full accent-indigo-600"
              />
            </div>

            <label className="flex cursor-pointer items-center gap-2.5 text-xs font-medium text-foreground">
              <input
                type="checkbox"
                checked={withTts}
                onChange={(e) => setWithTts(e.target.checked)}
                className="h-4 w-4 rounded border-border accent-indigo-600"
              />
              <span>Bật giọng đọc Neural TTS (Polly + Azure vi-VN)</span>
            </label>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-4">
            <div>
              <p className="text-[11px] text-muted-foreground">Ước tính Burn Rate</p>
              <p className="text-xl font-bold text-indigo-700">
                {burnRatePerMin.toFixed(1)} Cr / phút
              </p>
            </div>
            <div>
              <p className="text-[11px] text-muted-foreground">
                Thời lượng với gói PRO (1.800 Cr)
              </p>
              <p className="text-xl font-bold text-emerald-700">~{proMinutes} phút</p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm lg:col-span-5">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-600" />
            <h2 className="text-base font-bold text-foreground">
              3 gói Top-up lẻ cố định (không hết hạn)
            </h2>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Mua thêm bất cứ lúc nào qua Stripe hoặc VietQR, tự động cộng thêm % Bonus
            theo gói Subscription hiện tại.
          </p>
          <div className="mt-4 space-y-3">
            {TOPUP_PACKS.map((pack) => (
              <div
                key={pack.code}
                className="flex items-center justify-between rounded-xl border border-border bg-background px-4 py-3"
              >
                <div>
                  <p className="text-xs font-bold text-foreground">{pack.name}</p>
                  <p className="text-[11px] text-muted-foreground">{pack.credits} gốc</p>
                </div>
                <span className="rounded-lg bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
                  {pack.price}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Comparison Matrix */}
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-5">
          <h2 className="text-base font-bold text-foreground">
            So sánh chi tiết tính năng giữa 4 gói
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Toàn bộ giới hạn và tính năng được mở khóa tự động ngay khi nâng gói.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] border-collapse text-left">
            <thead>
              <tr className="border-b border-border bg-slate-50/80 text-xs font-bold text-foreground">
                <th className="px-6 py-3.5">Tính năng</th>
                <th className="px-4 py-3.5 text-center">Free ($0)</th>
                <th className="px-4 py-3.5 text-center text-indigo-700">Pro ($19)</th>
                <th className="px-4 py-3.5 text-center">Business ($59)</th>
                <th className="px-4 py-3.5 text-center">Enterprise ($199)</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_GROUPS.map((section) => (
                <React.Fragment key={section.group}>
                  <tr className="border-b border-border bg-muted/40">
                    <td
                      colSpan={5}
                      className="px-6 py-2.5 text-[11px] font-bold uppercase tracking-wider text-muted-foreground"
                    >
                      {section.group}
                    </td>
                  </tr>
                  {section.rows.map((row) => (
                    <tr
                      key={row.label}
                      className="border-b border-border/60 last:border-b-0"
                    >
                      <td className="px-6 py-3 text-xs font-medium text-foreground">
                        {row.label}
                      </td>
                      {row.values.map((val, idx) => (
                        <td
                          key={`${row.label}-${idx}`}
                          className={cn(
                            "px-4 py-3 text-center",
                            idx === 1 && "bg-indigo-50/30"
                          )}
                        >
                          {renderMatrixCell(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* FAQ Accordion */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <HelpCircle className="h-4 w-4 text-indigo-600" />
          <h2 className="text-base font-bold text-foreground">
            Câu hỏi thường gặp về gói &amp; ví Credit
          </h2>
        </div>

        <div className="mt-4 divide-y divide-border/70">
          {FAQS.map((item, index) => {
            const isOpen = openFaqIndex === index;
            return (
              <div key={item.q} className="py-3.5 first:pt-1 last:pb-0">
                <button
                  type="button"
                  aria-expanded={isOpen}
                  onClick={() => setOpenFaqIndex(isOpen ? null : index)}
                  className="flex w-full items-center justify-between gap-4 text-left text-xs font-semibold text-foreground hover:text-indigo-700 sm:text-sm"
                >
                  <span>{item.q}</span>
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-150",
                      isOpen && "rotate-180 text-indigo-600"
                    )}
                  />
                </button>
                {isOpen && (
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                    {item.a}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </ProductPageShell>
  );
}
