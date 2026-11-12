# Đặc tả Hợp đồng API, Giao thức WebSocket & Danh mục Màn hình Giao diện (API Contracts, WebSocket Schemas & UI/UX Specs)

- **Mã tài liệu**: `DOC-04-API-UI`
- **Phiên bản**: `1.0`
- **Ngày cập nhật**: 2026-11-09
- **Stack Kỹ thuật**:
  - **Frontend**: `Next.js 14/15 (App Router, TypeScript)`
  - **Backend**: `Python 3.12+ (FastAPI + asyncio/uvloop + Pydantic v2)`
- **Tài liệu liên quan**:
  - [01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md)
  - [02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md)
  - [03-system-architecture-and-techstack.md](file:///D:/code/ws-translation-realtime/docs/specs/03-system-architecture-and-techstack.md)

---

## 1. Cấu trúc Tổ chức Dự án (Monorepo Structure: Next.js + FastAPI Docker trên ECS)

Dự án được tổ chức theo mô hình Monorepo với 2 Docker Image độc lập (`apps/web/Dockerfile` và `apps/backend/Dockerfile`), tự động build/test/push lên **Amazon ECR** và triển khai lên **Amazon ECS Fargate** qua **GitHub Actions**:

```text
ws-translation-realtime/
├── .github/
│   └── workflows/
│       └── ci-cd.yml                 # GitHub Actions: Lint/Test -> Build Docker -> Push ECR -> Deploy ECS
├── apps/
│   ├── web/                          # Next.js 15 (App Router, TypeScript, TailwindCSS, output: "standalone")
│   │   ├── Dockerfile                # Multi-stage node:20-alpine image (~120MB) cho ECS Service "web"
│   │   ├── src/app/                  # Các màn hình: Dashboard, Live Room, Listener View, History
│   │   ├── src/worklets/             # AudioWorklet cắt PCM 16kHz + Silero VAD
│   │   └── src/lib/                  # AppSync WebSocket Client & Adaptive Audio Queue
│   │
│   └── backend/                      # Python 3.12 (FastAPI + asyncio/uvloop + Pydantic v2)
│       ├── Dockerfile                # Multi-stage python:3.12-slim + uv + libopus0 cho ECS Service "backend"
│       ├── app/
│       │   ├── main.py               # Unified FastAPI Entrypoint (/api/v1/* + /ws/v1/* + Async Workers)
│       │   ├── api/v1/               # FastAPI Routers (auth, rooms, transcripts, wallets, webhooks)
│       │   ├── ws/                   # WebSocket Audio Ingest & Graceful Handover Handler
│       │   ├── workers/              # Asyncio Background Tasks (Billing worker & S3 Export task)
│       │   │   ├── billing_loop.py   # Chu kỳ chốt cước vi mô mỗi 10s (Redis + PostgreSQL UsageLedger)
│       │   │   └── export_task.py    # Đóng gói .txt/.srt/.vtt/.csv lên S3 ngay khi END_ROOM
│       │   ├── services/             # Business Logic (auth, rooms, billing, transcripts)
│       │   ├── integrations/         # AWS Clients (Cognito, S3, Transcribe, Translate, Polly, Bedrock, AppSync)
│       │   ├── models/               # SQLAlchemy 2.0 ORM Models (9 PostgreSQL Tables)
│       │   ├── schemas/              # Pydantic v2 Models (Request/Response & WebSocket Events)
│       │   └── core/                 # config.py, db.py (asyncpg engine), security.py, exceptions.py
│       ├── alembic/                  # Database Migrations (Alembic + asyncpg)
│       ├── tests/                    # Pytest-asyncio suite (chạy trong bước CI)
│       └── pyproject.toml
│
├── infra/                            # Terraform Multi-Environment Stacks (dev, staging, prod)
└── docker-compose.yml                # Chạy local toàn bộ stack: web + backend + redis + postgres
```

---

## 2. Đặc tả REST API Endpoints (FastAPI `/api/v1`)

Toàn bộ các endpoint của Host yêu cầu Header `Authorization: Bearer <Cognito_AccessToken>`. Các endpoint của Listener dùng `Authorization: Bearer <Ephemeral_Room_JWT>`.

### 2.1. Phân hệ Xác thực & Hồ sơ (`Auth & Profile`)

| Method | Endpoint | Quyền | Mô tả & Payload chính |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/users/me` | Host | Lấy thông tin hồ sơ Host + Số dư ví hiện tại (`balance`, `currency`, `autoTopupEnabled`). |
| `PATCH` | `/api/v1/users/me` | Host | Cập nhật `fullName`, `avatarUrl`, `defaultSourceLang`, `billingCompanyInfo`. |

### 2.2. Phân hệ Quản lý Phòng & Tham gia (`Rooms & Sessions`)

| Method | Endpoint | Quyền | Mô tả & Payload chính |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/rooms` | Host | **Tạo phòng mới** (`FR-201`). Kiểm tra ví đủ $\ge 10$ phút.<br>- **Body**: `{"title": "Hội thảo AI", "mode": "BROADCAST", "sourceLang": "vi-VN", "targetLangs": ["en-US", "ja-JP", "ko-KR"], "allowListenerDownload": true, "autoDegradeTts": true, "passcode": null}`<br>- **Response (`201`)**: `{"roomId": "rm_01J...", "roomCode": "849-201", "joinUrl": "https://.../r/849-201", "estimatedBurnRatePerMin": 0.12}` |
| `GET` | `/api/v1/rooms` | Host | Danh sách các phòng đã tạo của Host (phân trang, lọc theo `status`). |
| `GET` | `/api/v1/rooms/{roomId}` | Host / Listener | Lấy chi tiết cấu hình phòng, trạng thái hiện tại, số người đang nghe và trạng thái file biên bản (`transcriptStatus`, `summaryStatus`). |
| `PATCH` | `/api/v1/rooms/{roomId}/settings` | Host | Cập nhật nóng danh sách `targetLangs` hoặc `allowListenerDownload` ngay khi phòng đang chạy (`FR-203`). |
| `POST` | `/api/v1/rooms/{roomId}/state` | Host | Điều khiển trạng thái phòng (`FR-205`):<br>- **Body**: `{"action": "PAUSE" | "RESUME" | "END_ROOM"}` |
| `POST` | `/api/v1/rooms/join` | Public (Guest) | **Người nghe vào phòng** (`FR-106`, `FR-202`).<br>- **Body**: `{"roomCode": "849-201", "passcode": null, "displayName": "Minh", "preferredLang": "ja-JP"}`<br>- **Response (`200`)**: `{"roomId": "rm_01J...", "ephemeralToken": "eyJ...", "appSyncEndpoint": "wss://...", "channelPrefix": "rooms/rm_01J.../lang/"}` |
| `POST` | `/api/v1/rooms/{roomId}/tts-toggle` | Listener | Bật/tắt nhận giọng đọc TTS cho ngôn ngữ đang chọn (`FR-404`).<br>- **Body**: `{"lang": "ja-JP", "enabled": true}` -> Backend gọi `HINCRBY room:{id}:tts_count ja-JP 1`. |

### 2.3. Phân hệ Lịch sử Bản dịch, Tải xuống & Tóm tắt AI (`Transcripts & AI Summary`)

| Method | Endpoint | Quyền | Mô tả & Payload chính |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/rooms/{roomId}/transcripts` | Host / Listener | **Đồng bộ lịch sử phụ đề** khi vào phòng muộn hoặc F5 trang (`FR-402`).<br>- **Query**: `?lang=ja-JP&afterSeq=0&limit=200`<br>- **Response (`200`)**: Danh sách các câu `Final` lấy từ Redis live buffer (khi phòng đang ACTIVE) hoặc từ `master.json` trên S3 (khi phòng đã kết thúc). |
| `GET` | `/api/v1/rooms/{roomId}/transcripts/export` | Host / Listener* | **Tải file biên bản dịch** (`FR-406`). *(Listener chỉ tải được nếu `allowListenerDownload == true`)*.<br>- **Query**: `?format=srt|vtt|txt|md|csv&lang=ja-JP`<br>- **Response (`200`)**: `{"downloadUrl": "https://s3.../presigned-url...", "expiresInSec": 3600}` |
| `POST` | `/api/v1/rooms/{roomId}/summary` | **Chỉ Host** | **Kích hoạt AI Tóm tắt Nội dung** qua Amazon Bedrock (`FR-407`).<br>- Nếu đã có (`summaryStatus == READY`): Trả về ngay bản tóm tắt, không trừ tiền.<br>- Nếu chưa có: Gọi Bedrock sinh tóm tắt đa ngôn ngữ, lưu S3 `summary.json`, trừ phí 1 lần vào ví Host.<br>- **Response (`200`)**: Xem cấu trúc JSON ở **Mục 3.4**. |
| `GET` | `/api/v1/rooms/{roomId}/summary` | Host / Listener* | **Xem bản Tóm tắt AI đã tạo** (`?lang=vi-VN`). Trả về `404` nếu Host chưa từng bấm tạo tóm tắt cho phòng này. |

### 2.4. Phân hệ Ví điện tử, Nạp tiền & Hóa đơn (`Wallets & Billing`)

| Method | Endpoint | Quyền | Mô tả & Payload chính |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/wallets/topup` | Host | **Tạo lệnh nạp tiền** (`FR-501`).<br>- **Body**: `{"amountUsd": 50.0, "provider": "STRIPE" | "VIETQR"}`<br>- **Response (`201`)**: `{"transactionId": "tx_01J...", "checkoutUrl": "https://...", "qrCodeDataUrl": "data:image/png;base64,..."}` |
| `POST` | `/api/v1/webhooks/payment/{provider}` | Webhook | Nhận kết quả thanh toán từ Stripe / VietQR / SePay (`FR-502`). Kiểm tra HMAC Signature + Idempotency -> Cộng tiền vào PostgreSQL `wallets` và Redis `wallet:{hostId}:balance`. |
| `PUT` | `/api/v1/wallets/auto-topup` | Host | Cấu hình tự động nạp tiền (`FR-503`): `{"enabled": true, "thresholdUsd": 5.0, "amountUsd": 20.0, "paymentMethodId": "pm_..."}` |
| `GET` | `/api/v1/wallets/transactions` | Host | Lịch sử nạp tiền, trừ tiền theo phiên và tải hóa đơn PDF/CSV (`FR-508`). |

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

// 3. Cập nhật số dư ví & cảnh báo trực tiếp cho Host mỗi 10s (FR-504, FR-507)
{
  "event": "BILLING_TICK",
  "balanceUsd": 4.20,
  "sessionCostUsd": 1.85,
  "burnRatePerMinUsd": 0.15,
  "estimatedRemainingMinutes": 28.0,
  "warningLevel": "LOW_BALANCE_WARNING" // "NONE" | "LOW_BALANCE_WARNING" | "GRACEFUL_DEGRADATION" | "QUOTA_EXHAUSTED"
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
  "generatedAt": "2026-11-09T15:32:10Z",
  "modelId": "anthropic.claude-3-5-haiku-20241022-v1:0",
  "costUsd": 0.012,
  "summariesByLang": {
    "vi-VN": {
      "overview": "Buổi hội thảo tập trung vào lý do chuyển đổi từ cơ sở dữ liệu SQL truyền thống sang kiến trúc Serverless NoSQL (DynamoDB + Redis) nhằm tối ưu chi phí thời gian rảnh về $0 và chịu tải ghi cao cho hệ thống tính cước thời gian thực.",
      "keyTakeaways": [
        {
          "timestamp": "02:15",
          "topic": "Tối ưu chi phí với DynamoDB On-Demand",
          "summary": "Loại bỏ hoàn toàn chi phí duy trì instance 24/7 của RDS khi không có hội thảo diễn ra."
        },
        {
          "timestamp": "18:40",
          "topic": "Kiến trúc Single-AZ kết hợp Redis Ring Buffer",
          "summary": "Giữ toàn bộ ECS Worker và Redis trong 1 Availability Zone để đạt độ trễ < 1ms và không tốn phí băng thông chéo AZ."
        }
      ],
      "actionItems": [
        "Hoàn thiện bộ tài liệu đặc tả API và giao thức WebSocket.",
        "Triển khai hạ tầng AWS CDK và kiểm thử chịu tải với 1.000 kết nối người nghe."
      ]
    },
    "en-US": {
      "overview": "The session focused on migrating from traditional SQL to a Serverless NoSQL architecture...",
      "keyTakeaways": [],
      "actionItems": []
    }
  }
}
```

---

## 4. Danh mục Màn hình Giao diện (`Next.js App Router UI/UX Screens`)

Hệ thống Web App (`apps/web`) bao gồm **6 màn hình chính** được thiết kế tối ưu cho cả Desktop và Mobile:

| Mã MH | Đường dẫn (`Route`) | Đối tượng | Các thành phần giao diện cốt lõi (UI Components) |
| :--- | :--- | :---: | :--- |
| **SCR-01** | `/login`, `/register`, `/forgot-password` | Host | - Form đăng nhập / đăng ký tích hợp Amazon Cognito + Nút Google/Apple SSO.<br>- Màn hình nhập mã OTP 6 số xác thực tài khoản. |
| **SCR-02** | `/dashboard` | Host | - **Thẻ Số dư Ví (Wallet Card)**: Hiển thị số dư khả dụng (`$`), nút **Nạp tiền nhanh** (Mở Modal chọn Stripe hoặc quét mã VietQR tự động cập nhật số dư), và cấu hình bật/tắt **Auto Top-up**.<br>- **Nút Tạo Phòng Dịch Mới**: Chọn chế độ (`1-on-1` hoặc `Broadcast`), chọn ngôn ngữ nguồn, tick chọn tối đa 10 ngôn ngữ đích, checkbox *"Cho phép người nghe tải biên bản dịch"*.<br>- **Danh sách Phòng gần đây**: Trạng thái phòng, thời lượng, tổng chi phí và nút truy cập nhanh vào **Lịch sử & Tóm tắt AI**. |
| **SCR-03** | `/rooms/[roomId]/host` | Host / Speaker | **Màn hình Điều khiển & Phát biểu Trực tiếp**:<br>- **Thanh Trạng thái Phiên & Đồng hồ Cước (Live Billing Meter)**: Hiển thị số người đang nghe, tốc độ đốt tiền hiện tại (`$0.15/phút`), số phút còn lại ước tính và nút **Nạp nhanh tại chỗ (In-room Top-up)**.<br>- **Khu vực Thu âm (Audio Control)**: Nút Bật/Tắt Mic, biểu đồ sóng âm kèm đèn báo VAD (đang nói / khoảng lặng), nút `Tạm dừng` / `Kết thúc phòng`.<br>- **Khung Phụ đề Trực tiếp**: Hiển thị câu gốc đang nhận diện (`Partial`/`Final`) và bản dịch sang ngôn ngữ tự chọn.<br>- **Modal Chia sẻ Phòng**: Mã QR Code lớn để chiếu lên màn hình hội trường + Link tham gia (`join_url`). |
| **SCR-04** | `/r/[roomCode]` | Listener (Mobile / Web) | **Màn hình Người nghe (Không cần đăng nhập)**:<br>- **Thanh Công cụ Nổi (Floating Action Bar)**: Dropdown đổi ngôn ngữ nhận bản dịch tức thì (`< 200ms`), nút **Bật/Tắt Loa (Audio TTS)** kèm thanh trạng thái hàng đợi âm thanh, nút đổi chế độ hiển thị (Chỉ bản dịch / Song ngữ), và nút **Tải biên bản** (nếu Host cho phép).<br>- **Khung Phụ đề Cuộn Thông minh (Auto-scroll Transcript View)**: Tự động tải toàn bộ các câu đã nói từ đầu buổi ngay khi vừa quét QR vào phòng; chữ `Partial` chạy mượt và chốt thành đoạn văn kèm mốc thời gian khi `Final`. |
| **SCR-05** | `/dashboard/rooms/[roomId]/history` | Host & Listener* | **Màn hình Chi tiết Lịch sử Dịch, Tải xuống & Tóm tắt AI**:<br>- **Tab 1 — Nội dung Bản dịch (Full Transcript)**: Xem lại toàn bộ nội dung cuộc họp theo từng câu kèm thời gian, hỗ trợ tìm kiếm từ khóa và chuyển đổi đối chiếu giữa các ngôn ngữ. Có cụm nút **Tải xuống**: `.TXT`, `.SRT`, `.VTT`, `.CSV`.<br>- **Tab 2 — Tóm tắt Nội dung AI (AI Meeting Summary)**:<br>  + Nếu chưa tạo: Hiển thị nút **"✨ Tóm tắt nội dung buổi dịch bằng AI"** (kèm chi phí ước tính, ví dụ `~$0.01`).<br>  + Nếu đã tạo: Hiển thị đẹp mắt 3 phần (**Chủ đề cốt lõi**, **Các ý chính kèm mốc thời gian bấm vào để nhảy tới câu tương ứng**, **Action Items**), cho phép đổi ngôn ngữ xem tóm tắt và tải về dạng `.MD` / `.TXT`.<br>- **Tab 3 — Chi tiết Chi phí Phiên (Chỉ Host thấy)**: Biểu đồ tiêu thụ mỗi 10s bóc tách theo phí STT, phí Dịch chữ, phí Giọng đọc TTS và phí Người nghe. |
| **SCR-06** | `/dashboard/billing` | Host | - Lịch sử giao dịch nạp tiền (`PaymentTransactions`) và lịch sử trừ tiền theo từng phiên.<br>- Cài đặt thông tin xuất hóa đơn doanh nghiệp và tải biên lai PDF/CSV. |
