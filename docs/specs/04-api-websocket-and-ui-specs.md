# Đặc tả Hợp đồng API, Giao thức WebSocket & Danh mục Màn hình Giao diện (API Contracts, WebSocket Schemas & UI/UX Specs)

- **Mã tài liệu**: `DOC-04-API-UI`
- **Phiên bản**: `2.1` (Bổ sung GDPR Delete, Multi-Speaker, Mic Check Lobby, Consent Banner & đồng bộ JSON `summary.json` theo PostgreSQL + Credits)
- **Ngày cập nhật**: 2026-11-19
- **Stack Kỹ thuật**:
  - **Frontend**: `Next.js 15 (App Router, TypeScript, TailwindCSS)`
  - **Backend**: `Python 3.12+ (FastAPI + asyncio/uvloop + Pydantic v2 + SQLAlchemy 2.0 Async)`
- **Tài liệu liên quan**:
  - [01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md)
  - [02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md)
  - [03-system-architecture-and-techstack.md](file:///D:/code/ws-translation-realtime/docs/specs/03-system-architecture-and-techstack.md)
  - [epics-and-sub-epics.md](file:///D:/code/ws-translation-realtime/docs/tasks/epics-and-sub-epics.md)

---

## 1. Cấu trúc Tổ chức Dự án (Monorepo Structure: Next.js + FastAPI Docker trên ECS)

Dự án được tổ chức theo mô hình Monorepo với 2 Docker Image độc lập (`apps/web/Dockerfile` và `apps/backend/Dockerfile`), tự động build/test/push lên **Amazon ECR** và triển khai lên **Amazon ECS Fargate** qua **GitHub Actions**:

```text
ws-translation-realtime/
├── .github/
│   └── workflows/                    # GitHub Actions CI: backend-ci, frontend-ci, infra-ci, pr-check
├── apps/
│   ├── web/                          # Next.js 15 (App Router, TypeScript, TailwindCSS, output: "standalone")
│   │   ├── Dockerfile                # Multi-stage node:20-alpine image (~120MB) cho ECS Service "web"
│   │   ├── src/app/                  # Route groups: (auth) [DONE], (dashboard) [Preview], live rooms [Planned]
│   │   ├── src/components/           # auth/*, dashboard/*, layout/* kèm Vitest tests co-located
│   │   ├── src/lib/                  # api-client, api-base, auth-api, auth-refresh, auth-logout, auth-storage
│   │   └── src/worklets/             # [Planned] AudioWorklet PCM 16kHz + Silero VAD + Local Ring Buffer
│   │
│   └── backend/                      # Python 3.12 (FastAPI + asyncio/uvloop + Pydantic v2)
│       ├── Dockerfile                # Multi-stage python:3.12-slim + uv cho ECS Service "backend"
│       ├── app/
│       │   ├── main.py               # FastAPI App Factory (/api/v1/*, CORS, RFC 7807, Lifespan)
│       │   ├── api/
│       │   │   ├── deps.py           # DI: DB session, Redis, JWKS AccessTokenContext, AuthService
│       │   │   └── v1/               # Routers: health.py [DONE], auth.py [DONE]; rooms/wallets/transcripts [Planned]
│       │   ├── core/                 # config.py, db.py (asyncpg), security.py, exceptions.py (RFC 7807)
│       │   ├── models/               # SQLAlchemy 2.0 ORM Models (10 PostgreSQL 16 Tables)
│       │   ├── repositories/         # base.py, user_repository.py, wallet_repository.py, room_repository.py
│       │   ├── schemas/              # requests/, responses/, ws_protocol.py (16-byte >IQBBH frame)
│       │   ├── services/             # auth_service.py, token_blocklist.py, wallet_service.py
│       │   ├── integrations/         # cognito.py, cognito_jwks.py, s3.py, appsync.py (+ offline mocks)
│       │   ├── ws/                   # [Planned] WebSocket Audio Ingest & Graceful Handover Handler
│       │   └── workers/              # [Planned] Per-Second Credit Billing Worker, Cron Sweep & S3 Transcript Compiler
│       ├── alembic/                  # Database Migrations (20261112_0001_initial_schema.py)
│       ├── tests/                    # Pytest-asyncio suite (api/ & unit/ mirroring app/)
│       └── pyproject.toml
│
├── infra/
│   └── terraform/                    # Terraform Multi-Env (environments/{local,dev,prod} + modules/*)
├── docs/                             # specs/, tasks/ (epics & roadmap)
└── Makefile                          # Unified commands: install, lint, format, test, build, tf-validate, deploy-*
```

---

## 2. Đặc tả REST API Endpoints (FastAPI `/api/v1`)

Toàn bộ các endpoint của Host yêu cầu Header `Authorization: Bearer <Cognito_AccessToken>`. Các endpoint của Listener dùng `Authorization: Bearer <Ephemeral_Room_JWT>`.

### 2.1. Phân hệ Hệ thống, Xác thực & Hồ sơ (`Health, Auth & Profile`)

| Method | Endpoint | Quyền | Trạng thái | Mô tả & Payload chính |
| :---: | :--- | :---: | :---: | :--- |
| `GET` | `/api/v1/health` | Public | `DONE` | Health & Liveness Check (`{"status": "ok", "service": ..., "env": ...}`). |
| `POST` | `/api/v1/auth/register` | Public | `DONE` | Đăng ký Host (`email`, `password`, `fullName`) qua Cognito `SignUp` -> `201 Created`. Trả phản hồi đồng nhất `CONFIRMATION_REQUIRED` chống user enumeration. |
| `POST` | `/api/v1/auth/confirm` | Public | `DONE` | Xác thực OTP 6 số (`email`, `otpCode`) -> `200 OK` (`{"status": "CONFIRMED"}`). Transaction ACID khởi tạo `users`, `user_profiles`, `wallets` (Welcome Bonus `$2.00`) và `payment_transactions`. |
| `POST` | `/api/v1/auth/resend-otp` | Public | `DONE` | Gửi lại OTP kích hoạt (`email`) với Redis cooldown 60s (`retryAfter: 60`). |
| `POST` | `/api/v1/auth/login` | Public | `DONE` | Đăng nhập (`email`, `password`, `rememberMe`). Trả `tokens` (`accessToken`, `idToken`, `expiresIn`, `tokenType`) + `user` trong JSON; `refreshToken` chỉ được set qua HttpOnly cookie `ws_refresh_token` (`Path=/api/v1/auth`, `SameSite=Lax`, `Cache-Control: no-store`). |
| `POST` | `/api/v1/auth/refresh` | Cookie | `DONE` | Làm mới `accessToken` & `idToken` ngầm **chỉ nhận cookie** `ws_refresh_token` (không chấp nhận body token để bảo vệ HttpOnly). Tự động xóa cookie nếu token hết hạn/bị thu hồi. |
| `POST` | `/api/v1/auth/logout` | Host | `DONE` | Đăng xuất (`204 No Content`), hỗ trợ `{"globalSignOut": true/false}` -> Cognito `RevokeToken`/`GlobalSignOut` + ghi Redis Token Blocklist + xóa auth cookies. |
| `POST` | `/api/v1/auth/forgot-password` | Public | `DONE` | Gửi OTP đặt lại mật khẩu (`email`) với Redis rate limit 3 lần/15 phút, phản hồi đồng nhất chống enumeration. |
| `POST` | `/api/v1/auth/reset-password` | Public | `DONE` | Xác nhận OTP + mật khẩu mới (`email`, `otpCode`, `newPassword`), giới hạn 5 lần sai OTP, tự động `GlobalSignOut` thu hồi toàn bộ phiên cũ và xóa cookies. |
| `GET` | `/api/v1/users/me` | Host | `TODO` | Lấy thông tin hồ sơ Host + Gói hiện tại (`entitlements`) + Số dư Credit 3 ngăn (`promo`, `plan`, `topup`, `total`). |
| `PATCH` | `/api/v1/users/me` | Host | `TODO` | Cập nhật `fullName`, `avatarUrl`, `defaultSourceLang`, `billingCompanyInfo`. |
| `DELETE` | `/api/v1/users/me` | Host | `TODO` | **Xóa tài khoản & dữ liệu cá nhân (`FR-107`, GDPR/PDPA)**: Xóa Cognito user, thu hồi mọi phiên và ẩn danh dữ liệu cá nhân. |

### 2.2. Phân hệ Quản lý Phòng & Tham gia (`Rooms & Sessions`)

| Method | Endpoint | Quyền | Mô tả & Payload chính |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/rooms` | Host | **Tạo phòng mới** (`FR-201`). Kiểm tra ví đủ $\ge 10$ phút.<br>- **Body**: `{"title": "Hội thảo AI", "mode": "BROADCAST", "sourceLang": "vi-VN", "targetLangs": ["en-US", "ja-JP", "ko-KR"], "allowListenerDownload": true, "autoDegradeTts": true, "passcode": null}`<br>- **Response (`201`)**: `{"roomId": "rm_01J...", "roomCode": "849-201", "joinUrl": "https://.../r/849-201", "estimatedBurnRatePerMin": 0.12}` |
| `GET` | `/api/v1/rooms` | Host | Danh sách các phòng đã tạo của Host (phân trang, lọc theo `status`). |
| `GET` | `/api/v1/rooms/{roomId}` | Host / Listener | Lấy chi tiết cấu hình phòng, trạng thái hiện tại, số người đang nghe và trạng thái file biên bản (`transcriptStatus`, `summaryStatus`). |
| `PATCH` | `/api/v1/rooms/{roomId}/settings` | Host | Cập nhật nóng danh sách `targetLangs` hoặc `allowListenerDownload` ngay khi phòng đang chạy (`FR-203`). |
| `POST` | `/api/v1/rooms/{roomId}/state` | Host | Điều khiển trạng thái phòng (`FR-205`):<br>- **Body**: `{"action": "START" | "PAUSE" | "RESUME" | "END_ROOM"}` *(chuyển từ `IDLE` Mic Check Lobby -> `ACTIVE` khi bấm `START`)*. |
| `POST` | `/api/v1/rooms/{roomId}/speakers` | Host | Cấp / thu hồi quyền Diễn giả phụ (`Co-Host / Multi-Speaker`, `FR-207`, `BUSINESS`: tối đa 3, `ENTERPRISE`: tối đa 10). |
| `POST` | `/api/v1/rooms/join` | Public (Guest) | **Người nghe vào phòng** (`FR-106`, `FR-202`).<br>- **Body**: `{"roomCode": "849-201", "passcode": null, "displayName": "Minh", "preferredLang": "ja-JP"}`<br>- **Response (`200`)**: `{"roomId": "rm_01J...", "ephemeralToken": "eyJ...", "appSyncEndpoint": "wss://...", "channelPrefix": "rooms/rm_01J.../lang/"}` |
| `POST` | `/api/v1/rooms/{roomId}/tts-toggle` | Listener | Bật/tắt nhận giọng đọc TTS cho ngôn ngữ đang chọn (`FR-404`).<br>- **Body**: `{"lang": "ja-JP", "enabled": true}` -> Backend gọi `HINCRBY room:{id}:tts_count ja-JP 1`. |

### 2.3. Phân hệ Lịch sử Bản dịch, Tải xuống & Tóm tắt AI (`Transcripts & AI Summary`)

| Method | Endpoint | Quyền | Mô tả & Payload chính |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/rooms/{roomId}/transcripts` | Host / Listener | **Đồng bộ lịch sử phụ đề** khi vào phòng muộn hoặc F5 trang (`FR-402`).<br>- **Query**: `?lang=ja-JP&afterSeq=0&limit=200`<br>- **Response (`200`)**: Danh sách các câu `Final` lấy từ Redis live buffer (khi phòng đang ACTIVE) hoặc từ `master.json` trên S3 (khi phòng đã kết thúc). |
| `GET` | `/api/v1/rooms/{roomId}/transcripts/export` | Host / Listener* | **Tải file biên bản dịch** (`FR-406`). *(Listener chỉ tải được nếu `allowListenerDownload == true`)*.<br>- **Query**: `?format=srt|vtt|txt|md|csv&lang=ja-JP`<br>- **Response (`200`)**: `{"downloadUrl": "https://s3.../presigned-url...", "expiresInSec": 3600}` |
| `POST` | `/api/v1/rooms/{roomId}/summary` | **Chỉ Host** | **Kích hoạt AI Tóm tắt Nội dung** qua Amazon Bedrock (`FR-407`).<br>- Nếu đã có (`summaryStatus == READY`): Trả về ngay bản tóm tắt, không trừ tiền.<br>- Nếu chưa có: Gọi Bedrock sinh tóm tắt đa ngôn ngữ, lưu S3 `summary.json`, trừ phí 1 lần vào ví Host.<br>- **Response (`200`)**: Xem cấu trúc JSON ở **Mục 3.4**. |
| `GET` | `/api/v1/rooms/{roomId}/summary` | Host / Listener* | **Xem bản Tóm tắt AI đã tạo** (`?lang=vi-VN`). Trả về `404` nếu Host chưa từng bấm tạo tóm tắt cho phòng này. |
| `DELETE` | `/api/v1/rooms/{roomId}/transcripts` | **Chỉ Host** | **Xóa biên bản dịch & AI Summary trên S3** (`FR-107`, GDPR/PDPA) theo yêu cầu quyền riêng tư của Host. |

### 2.4. Phân hệ Gói Dịch vụ, Ví Credit 3 Ngăn, Nạp tiền & Lịch sử (`Plans, Subscriptions, Wallets & Billing`)

| Method | Endpoint | Quyền | Mô tả & Payload chính |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/plans` | Public | Danh sách 4 gói Subscription cố định (`FREE`/`PRO`/`BUSINESS`/`ENTERPRISE`), `monthlyCredits`, `topupBonusPct` và `entitlements`. |
| `GET` | `/api/v1/credit-packs` | Host | Danh sách 3 gói Top-up lẻ cố định (`PACK_S`/`PACK_M`/`PACK_L`) kèm số Credit bonus tính sẵn theo gói của Host. |
| `GET` | `/api/v1/subscriptions/me` | Host | Thông tin gói hiện tại, ngày hết chu kỳ, `cancelAtPeriodEnd` và object `entitlements`. |
| `POST` | `/api/v1/subscriptions/checkout` | Host | Mua mới / Nâng cấp gói cố định (`{"planCode": "PRO", "provider": "STRIPE" | "VIETQR"}`). |
| `POST` | `/api/v1/subscriptions/cancel` | Host | Hủy gia hạn cuối chu kỳ (`cancel_at_period_end = true`). |
| `GET` | `/api/v1/wallets/me` | Host | Lấy số dư chi tiết 3 ngăn (`promoCredits`, `planCredits`, `topupCredits`, `totalCredits`, mốc hết hạn) & cài đặt Auto Top-up/Degrade. |
| `POST` | `/api/v1/wallets/topup` | Host | **Mua gói Top-up Credit cố định** (`FR-501`): `{"packCode": "PACK_M", "provider": "STRIPE" | "VIETQR"}` -> trả `transactionId`, `checkoutUrl` / `qrCodeDataUrl`. |
| `POST` | `/api/v1/webhooks/payment/{provider}` | Webhook | Nhận kết quả thanh toán từ Stripe / VietQR (`FR-502`). Verify HMAC + Idempotency -> kích hoạt Subscription hoặc cộng `topup_credits` + đồng bộ Redis `wallet:{hostId}:credits`. |
| `PUT` | `/api/v1/wallets/auto-topup` | Host | Cấu hình tự động nạp gói Credit (`FR-503`, `BUSINESS+`): `{"enabled": true, "thresholdCredits": 500, "packCode": "PACK_M", "paymentMethodId": "pm_..."}`. |
| `GET` | `/api/v1/wallets/me/topup-history` | Host | **Lịch sử Nạp tiền & Mua gói** (`FR-508`, phân trang + lọc theo loại/cổng/ngày + tải biên lai PDF VAT). |
| `GET` | `/api/v1/wallets/me/usage-history` | Host | **Lịch sử Sử dụng Credit** từ `credit_ledger` (`FR-508`, theo phiên phòng, AI Summary, Credit hết hạn + phân bổ 3 ngăn). |
| `GET` | `/api/v1/wallets/me/sessions/{roomId}/breakdown` | Host | Chi tiết đối soát từng giây thực tế (`audioSeconds`, `listenerSeconds`, `mtChars`, `ttsChars`, `creditsDeducted`, biểu đồ + xuất CSV). |
| `GET` | `/api/v1/rooms/{roomId}/analytics` | Host | Thống kê phân bố ngôn ngữ & đỉnh người nghe theo thời gian (`FR-408`, `BUSINESS+`). |

---

## 3. Đặc tả Giao thức WebSocket & JSON Payload Schemas

### 3.1. Luồng 1: Speaker Ingest WebSocket (`FastAPI` trên ECS Fargate)
- **Endpoint**: `wss://stream.domain.com/ws/v1/rooms/{roomId}/ingest?token={speakerJwt}&lastCommittedSeq={seq}`
- **Chiều Client -> Server**:
  - **Binary Frame**: Khung âm thanh 16-byte Header + PCM/Opus Payload (như đã định nghĩa tại mục 3.1 của `DOC-03-SAD`).
  - **Text Control Frame**: `{"type": "END_OF_SPEECH"}` hoặc `{"type": "PING"}`.
- **Chiều Server -> Client (Text JSON Frame)**:

```json
// 1. Xác nhận ACK mỗi 500ms để phục vụ Failover (< 300ms timeout)
{
  "event": "STREAM_ACK",
  "lastReceivedSeq": 1420,
  "lastCommittedSeq": 1395
}

// 2. Yêu cầu chuyển giao kết nối không gián đoạn khi Scale-in / Rolling Update (FR-602)
{
  "event": "PREPARE_HANDOVER",
  "resumeFromSeq": 1450,
  "reason": "TASK_DRAINING"
}

// 3. Cập nhật số dư Credit 3 ngăn & cảnh báo trực tiếp cho Host mỗi giây (FR-504, FR-507)
{
  "event": "BILLING_TICK",
  "totalCredits": 420.50,
  "buckets": { "promo": 0.00, "plan": 120.50, "topup": 300.00 },
  "sessionCreditsUsed": 185.20,
  "burnRatePerMinCredits": 15.00,
  "estimatedRemainingMinutes": 28.0,
  "warningLevel": "NONE" // "NONE" | "LOW_BALANCE_WARNING" | "GRACEFUL_DEGRADATION" | "QUOTA_EXHAUSTED"
}
```

### 3.2. Luồng 2: Listener Fan-out qua AWS AppSync Events
- **Topic Kênh Ngôn ngữ**: `rooms/{roomId}/lang/{langCode}` (ví dụ: `rooms/rm_123/lang/vi-VN`)
- **Payload Bản tin Phụ đề & Âm thanh (`SUBTITLE_EVENT`)**:

```json
{
  "event": "SUBTITLE_SEGMENT",
  "roomId": "rm_01J9X...",
  "segmentId": "seg_00042",
  "speakerId": "usr_host_01",
  "speakerName": "Dr. Alex",
  "seqStart": 1400,
  "seqEnd": 1435,
  "startTimeMs": 140000,
  "endTimeMs": 143500,
  "isFinal": true,
  "sourceLang": "en-US",
  "sourceText": "We decided to migrate our database to a serverless NoSQL architecture.",
  "targetLang": "vi-VN",
  "translatedText": "Chúng tôi đã quyết định chuyển đổi cơ sở dữ liệu sang kiến trúc NoSQL không máy chủ.",
  "ttsAudioUrl": "https://cdn.domain.com/tts/rm_01J9X/seg_00042_vi-VN.mp3"
}
```
> **Lưu ý**: Khi `isFinal == false` (câu đang nói dở), `ttsAudioUrl` luôn là `null`. Khi `isFinal == true` và ngôn ngữ đó có người bật loa (`tts_count > 0`), `ttsAudioUrl` sẽ chứa đường dẫn CloudFront CDN để Client đưa vào hàng đợi phát âm thanh thích ứng (`FR-405`).

### 3.3. Cấu trúc JSON Lưu trữ Bản dịch Chuẩn trên S3 (`master.json`)
Được tạo bởi `export_worker.py` ngay khi phòng kết thúc (`END_ROOM`):

```json
{
  "roomId": "rm_01J9X...",
  "title": "Hội thảo Kiến trúc Đám mây 2026",
  "sourceLang": "en-US",
  "targetLangs": ["vi-VN", "ja-JP"],
  "startedAt": "2026-11-09T14:00:00Z",
  "endedAt": "2026-11-09T15:30:00Z",
  "totalSegments": 342,
  "segments": [
    {
      "segmentId": "seg_00001",
      "seqStart": 1,
      "seqEnd": 28,
      "startTimeMs": 0,
      "endTimeMs": 2800,
      "speakerName": "Dr. Alex",
      "sourceText": "Welcome everyone to our cloud architecture session.",
      "translations": {
        "vi-VN": "Chào mừng mọi người đến với buổi chia sẻ về kiến trúc đám mây của chúng tôi.",
        "ja-JP": "クラウドアーキテクチャセッションへようこそ。"
      }
    }
  ]
}
```

### 3.4. Cấu trúc JSON Bản Tóm tắt AI trên S3 (`summary.json` — `FR-407`)
Được tạo bởi `ai_summary.py` (gọi **Amazon Bedrock**) khi Host bấm nút *"Tóm tắt nội dung bằng AI"*:

```json
{
  "roomId": "rm_01J9X...",
  "generatedAt": "2026-11-19T15:32:10Z",
  "modelId": "anthropic.claude-3-5-haiku-20241022-v1:0",
  "creditsCharged": 25.00,
  "summariesByLang": {
    "vi-VN": {
      "overview": "Buổi hội thảo tập trung vào thiết kế kiến trúc dịch thuật realtime trên AWS Single-AZ kết hợp PostgreSQL 16 (ACID) và ElastiCache Redis để tối ưu độ trễ < 500ms và kiểm soát trừ Credit theo từng giây.",
      "keyTakeaways": [
        {
          "timestamp": "02:15",
          "topic": "Tính toàn vẹn ACID với PostgreSQL 16 & Ví Credit 3 ngăn",
          "summary": "Áp dụng transaction nguyên tử theo thứ tự Promo -> Plan -> Top-up cùng sổ cái usage_ledger và credit_ledger."
        },
        {
          "timestamp": "18:40",
          "topic": "Kiến trúc Single-AZ kết hợp Redis Ring Buffer",
          "summary": "Giữ toàn bộ ECS Worker và Redis trong 1 Availability Zone để đạt độ trễ < 1ms và không tốn phí băng thông chéo AZ."
        }
      ],
      "actionItems": [
        "Hoàn thiện bộ tài liệu đặc tả API và giao thức WebSocket.",
        "Triển khai hạ tầng Terraform và kiểm thử chịu tải với 1.000 kết nối người nghe."
      ]
    },
    "en-US": {
      "overview": "The session focused on realtime translation architecture on AWS Single-AZ combining PostgreSQL 16 (ACID) and Redis...",
      "keyTakeaways": [],
      "actionItems": []
    }
  }
}
```

---

## 4. Danh mục Màn hình Giao diện (`Next.js App Router UI/UX Screens`)

Hệ thống Web App (`apps/web`) bao gồm **6 màn hình chính** được thiết kế tối ưu cho cả Desktop và Mobile:

| Mã MH | Đường dẫn (`Route`) | Đối tượng | Trạng thái | Các thành phần giao diện cốt lõi (UI Components) |
| :--- | :--- | :---: | :---: | :--- |
| **SCR-01** | `/login`, `/register`, `/verify-otp`, `/forgot-password`, `/reset-password` | Host | `DONE` *(Email/OTP)* | - Form đăng nhập / đăng ký (`PasswordMeter`), xác thực OTP 6 số (`OtpInput6`), quên & đặt lại mật khẩu kết nối đầy đủ Backend Cognito API + Silent Refresh.<br>- Nút Google/Apple SSO (`SocialSsoButtons`) đã có UI, chờ nối OAuth2 (`EP02-S4`). |
| **SCR-02** | `/dashboard` | Host | `IN_PROGRESS` *(UI Preview)* | - Đã triển khai giao diện preview (`WalletCard`, `CreateRoomCard`, `RecentRoomsList`, `DashboardHeader`, `DashboardSessionContext`) với dữ liệu mẫu.<br>- Chờ nối Wallet API (`EP03-S1`) & Room API (`EP04-S2`). |
| **SCR-03** | `/rooms/[roomId]/host` | Host / Speaker | `TODO` | **Màn hình Điều khiển & Phát biểu Trực tiếp**:<br>- **Chế độ Lobby / Mic Check (`IDLE`, `0 Cr`)**: Kiểm tra thiết bị micro, sóng âm và đèn VAD trước khi bấm nút `Bắt đầu phiên (START)`.<br>- **Thanh Trạng thái Phiên & Đồng hồ Credit từng giây (Live Billing Meter)**: Hiển thị số người nghe, tốc độ tiêu thụ (`Cr/phút`, cảnh báo x2 luồng ở chế độ `1-on-1`), số phút còn lại ước tính và nút **Nạp nhanh `PACK_S/M/L` tại chỗ**.<br>- **Khu vực Thu âm & Co-Host**: Nút Bật/Tắt Mic, biểu đồ sóng âm kèm đèn VAD, quản lý Speakers phụ (`BUSINESS+`), nút `Tạm dừng` / `Kết thúc phòng`.<br>- **Khung Phụ đề Trực tiếp & Modal QR Chiếu Hội trường** (kèm Custom Branding nếu `BUSINESS+`). |
| **SCR-04** | `/r/[roomCode]` | Listener (Mobile / Web) | `TODO` | **Màn hình Người nghe (Không cần đăng nhập)**:<br>- **Banner Minh bạch Quyền riêng tư (`FR-107`)**: Thông báo *"Phiên này đang được dịch thuật & lưu biên bản AI"* + Custom Branding (`BUSINESS+`) / White-label (`ENTERPRISE`).<br>- **Thanh Công cụ Nổi (Floating Action Bar)**: Dropdown đổi ngôn ngữ tức thì (`< 200ms`, gắn nhãn nếu ngôn ngữ đang ở chế độ `Text-only`), nút **Bật/Tắt Loa (Audio TTS)** kèm trạng thái hàng đợi, nút Đơn ngữ / Song ngữ, nút **Tải biên bản** (nếu Host cho phép).<br>- **Khung Phụ đề Cuộn Thông minh (Auto-scroll Transcript View)**: Tải đầy đủ câu đã nói từ đầu buổi khi vào muộn/F5; chữ `Partial` mượt và chốt `Final` kèm mốc thời gian. |
| **SCR-05** | `/dashboard/rooms/[roomId]/history` | Host & Listener* | `TODO` | **Màn hình Chi tiết Lịch sử Dịch, Tải xuống, AI Summary & Analytics**:<br>- **Tab 1 — Nội dung Bản dịch (Full Transcript)**: Xem lại theo từng câu, tìm kiếm, đổi ngôn ngữ, nút tải theo `exportFormats` của gói, và nút **Xóa biên bản** (`FR-107`, chỉ Host).<br>- **Tab 2 — Tóm tắt Nội dung AI (AI Meeting Summary)**: Nút **"✨ Tóm tắt AI"** (`15 Cr` Pro / `25 Cr` Business+, xem lại `0 Cr`); hiển thị Overview, Key Takeaways `[mm:ss]` nhảy tới câu tương ứng, Action Items.<br>- **Tab 3 — Phân tích & Chi phí Phiên (Chỉ Host)**: Biểu đồ phân bố ngôn ngữ, đỉnh người nghe (`Session Analytics` + xuất CSV/PDF theo gói) và bóc tách Credit tiêu thụ theo từng giây. |
| **SCR-06** | `/dashboard/billing` | Host | `TODO` | Gồm **4 Tab**: (1) **Gói dịch vụ** (so sánh 4 gói `FREE`/`PRO`/`BUSINESS`/`ENTERPRISE`, Nâng cấp/Hủy gia hạn), (2) **Mua thêm Credit** (`PACK_S`/`M`/`L` kèm `+Bonus%`, Promo Code, Auto Top-up), (3) **Lịch sử Nạp tiền** (`payment_transactions` + tải PDF VAT), (4) **Lịch sử Sử dụng Credit** (`credit_ledger` + Drawer bóc tách từng giây & xuất CSV). |
