# Thiết kế Kiến trúc Hệ thống, HA/Zero-Downtime & Tech Stack (System Architecture & Technical Design)

- **Mã tài liệu**: `DOC-03-SAD`
- **Phiên bản**: `2.1` (Bổ sung Multi-Provider TTS `vi-VN`, Per-Second Metering + 15s ACID Flush, Entitlements Cache & SES Notification Worker)
- **Ngày cập nhật**: 2026-11-19
- **Tài liệu liên quan**:
  - [01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md)
  - [02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md)
  - [epics-and-sub-epics.md](file:///D:/code/ws-translation-realtime/docs/tasks/epics-and-sub-epics.md)

---

## 1. Kiến trúc Tổng thể trên AWS (Single-AZ Optimized Architecture)

### 1.1. Nguyên lý Thiết kế Cốt lõi
1. **Tách biệt hoàn toàn tầng Ingest (Nhận âm thanh) và tầng Fan-out (Phát kết quả)**:
   - **Tầng Ingest & AI Orchestration**: Sử dụng cụm container **Amazon ECS Fargate** (State-recoverable qua Redis) để duy trì kết nối gRPC/HTTP2 streaming liên tục với các dịch vụ AI của AWS.
   - **Tầng Fan-out (1.000 người nghe/phòng)**: Sử dụng hoàn toàn dịch vụ Serverless **AWS AppSync Events** (cho phụ đề JSON realtime) kết hợp **Amazon CloudFront + S3** (cho các đoạn âm thanh TTS). Nhờ đó, kết nối của 1.000 người nghe không bao giờ bị ảnh hưởng khi tầng Compute phía sau co giãn hoặc gặp sự cố.
2. **Triển khai Single-AZ (1 Availability Zone) tối ưu chi phí và độ trễ**:
   - Toàn bộ các thành phần Compute & In-memory State trong VPC (**ECS Fargate Tasks** và **ElastiCache Redis**) được đặt chung trong **1 Availability Zone duy nhất** (ví dụ: `ap-southeast-1a`).
   - Triệt tiêu **100% chi phí băng thông chéo AZ (Cross-AZ Data Transfer = $0)** khi Worker liên tục ghi/đọc Audio Ring Buffer trên Redis, đồng thời đạt độ trễ mạng nội bộ `< 1ms`.
   - Tính sẵn sàng cao (HA) trong 1 AZ được đảm bảo bằng cách luôn duy trì tối thiểu **2 ECS Fargate Tasks** chạy độc lập cùng chia sẻ trạng thái qua Redis.

### 1.2. Sơ đồ Kiến trúc Hệ thống Chi tiết

```mermaid
flowchart TB
    subgraph Clients["Tầng Client (Web / Mobile SDK)"]
        Speaker["🎤 Speaker Client\n(Opus/PCM 16kHz + SeqID)\nLocal Ring Buffer (5s)"]
        Listeners["🎧 1..1.000 Listener Clients\n(AppSync WebSocket Subscriber)\nAdaptive Audio Queue"]
    end

    subgraph Edge_Serverless["Tầng AWS Edge & Serverless Fan-out"]
        ALB["AWS Application Load Balancer (AZ-a)\n- /* -> ECS Web (Next.js)\n- /api/* & /ws/* -> ECS Backend (FastAPI)"]
        AppSync["AWS AppSync Events\n(Serverless WebSocket Pub/Sub)\nTopic: rooms/{id}/lang/{code}"]
        CDN["Amazon CloudFront + S3\n(TTS Audio 24h & Transcript Exports 90d)"]
    end

    subgraph VPC_SingleAZ["AWS VPC — Single Availability Zone (ap-southeast-1a)"]
        subgraph ECS_Cluster["Amazon ECS Fargate Cluster (Single-AZ)"]
            WebService["ECS Service: web (Next.js 15 Docker)\nAuto-Scaling: 2..6 Tasks"]
            subgraph BackendService["ECS Service: backend (Python 3.12 FastAPI + uvloop Docker)\nAuto-Scaling: 2..20 Tasks (REST API + WS Ingest + Async Workers)"]
                Task1["FastAPI Task #1"]
                Task2["FastAPI Task #2"]
            end
        end
        Redis[("Amazon ElastiCache for Redis\n(Single-AZ Node)\n- Audio Ring Buffer (10s)\n- Active TTS Listeners Counter\n- Host Wallet Balance")]
    end

    subgraph AWS_AI["Tầng AWS Native AI Pipeline"]
        Transcribe["Amazon Transcribe Streaming\n(HTTP/2 Bi-directional Stream)"]
        Translate["Amazon Translate\n(Parallel N-Language MT)"]
        Polly["Multi-Provider Neural TTS\nAmazon Polly (Primary)\n+ Azure AI Speech southeastasia (vi-VN, th-TH, id-ID)"]
        Bedrock["Amazon Bedrock\n(Claude 3.5 Haiku / Nova Lite)\nOn-Demand AI Meeting Summary"]
    end

    subgraph Data_Storage["Tầng Persistent Data & Auth"]
        Cognito["Amazon Cognito\n(Host User Pool + JWKS RS256)"]
        Postgres[("Amazon RDS PostgreSQL 16\n(10 bảng ACID: users, user_profiles,\nwallets, payment_transactions, promo_codes,\npromo_redemptions, custom_vocabularies,\nrooms, room_transcripts, usage_ledger)")]
    end

    %% Luồng Ingest & Web
    Speaker == "1. HTTPS / WSS (/api, /ws)" ==> ALB
    Listeners -. "HTTPS (UI & REST /api)" .-> ALB
    ALB --> WebService
    ALB ==> Task1
    ALB -. "Hot Failover / Load Share" .-> Task2
    Task1 <-->|"XADD / XRANGE (<1ms)"| Redis
    Task2 <-->|"XADD / XRANGE (<1ms)"| Redis

    %% Luồng AI
    Task1 == "2. PCM Stream" ==> Transcribe
    Transcribe == "3. Partial/Final Text" ==> Task1
    Task1 == "4. Translate N Langs" ==> Translate
    Task1 == "5. Synthesize Speech" ==> Polly
    Task1 -- "6a. PutObject (.mp3 / Exports)" --> CDN
    Task1 -. "6c. Asyncpg ACID Ledger / Billing" .-> Postgres
    Task1 -. "7. Generate AI Summary" .-> Bedrock

    %% Luồng Fan-out
    Task1 == "6b. Publish JSON Event" ==> AppSync
    AppSync == "8a. Push Subtitle (<50ms)" ==> Listeners
    CDN == "8b. Fetch Audio / Transcript" ==> Listeners
```

---

## 2. Thiết kế Cơ chế HA, Auto-Scaling & Zero-Downtime

### 2.1. Kịch bản 1: Container xử lý âm thanh bị sập đột ngột (Crash / OOM Failover)
Khi `ECS Task #1` đang xử lý câu nói dở dang của Speaker mà bị crash:
1. **Phát hiện nhanh (`< 300ms`)**: Giao thức WebSocket giữa Speaker Client và ECS Task sử dụng cơ chế xác nhận `ACK` mỗi 500ms. Khi socket đóng hoặc quá `300ms` không nhận được `ACK`, Speaker Client lập tức mở kết nối mới qua ALB kèm theo tham số `room_id` và `last_sent_seq`.
2. **Tiếp quản & Khôi phục từ Redis Ring Buffer**:
   - ALB định tuyến kết nối mới vào `ECS Task #2` (đang chạy sẵn trong cùng `AZ-a`).
   - `ECS Task #2` truy vấn Redis key `room:{id}:state` để lấy `last_committed_seq` (số thứ tự frame cuối cùng của câu `Final` trước đó).
   - `ECS Task #2` đọc toàn bộ các frame âm thanh từ `last_committed_seq + 1` đến hiện tại từ Redis Stream `room:{id}:audio_buffer` và bơm tốc độ cao (Fast-replay) vào phiên **Amazon Transcribe Streaming** mới mở, sau đó ghép nối liền mạch với các frame mới từ Speaker Client gửi lên.
   - **Kết quả**: Câu đang nói dở vẫn được nhận diện và dịch trọn vẹn, không mất chữ nào; 1.000 người nghe trên AppSync Events không hề bị ngắt kết nối.

### 2.2. Kịch bản 2: Thu hẹp hệ thống (Scale-In) hoặc Cập nhật phần mềm (Rolling Deploy)
Để đảm bảo **0ms gián đoạn** khi tắt một container chủ động:
1. **ECS Task Scale-in Protection**: Các Task đang có `active_speaker_streams > 0` tự động gọi API `UpdateTaskProtection(protectionEnabled=true)` để hệ thống Auto Scaling chỉ tắt các Task đang rảnh rỗi.
2. **Giao thức Chuyển giao Chủ động (Make-Before-Break Handover)**:
   - Khi một Task bắt buộc phải dừng (nhận tín hiệu `SIGTERM` khi deploy phiên bản mới, với thời gian chờ `stopTimeout = 120s`), Task đánh dấu trạng thái `DRAINING`.
   - Ngay khi người nói vừa kết thúc câu hiện tại (`Transcribe IsPartial == false`), Task gửi gói tin điều khiển `{"event": "PREPARE_HANDOVER"}` về cho Speaker Client.
   - Speaker Client giữ nguyên kết nối cũ (`Conn A`), đồng thời mở kết nối mới (`Conn B`) tới một Task khỏe mạnh khác trên ALB.
   - Khi `Conn B` trả về tín hiệu `{"event": "HANDOVER_READY"}`, Speaker Client bắt đầu gửi frame âm thanh tiếp theo (`seq_id + 1`) qua `Conn B` và đóng `Conn A`.

### 2.3. Cấu hình Auto-Scaling cho ECS Fargate
- **Kích thước mỗi Task**: `1 vCPU`, `2 GB Memory` (hỗ trợ tối đa `30` luồng Speaker đồng thời/Task).
- **Min Capacity**: `2 Tasks` (luôn chạy trong `AZ-a` để sẵn sàng Failover).
- **Max Capacity**: `20 Tasks` (hỗ trợ tới `600` phòng hội thảo đồng thời).
- **Quy tắc Scale Out**: Thêm `+2 Tasks` ngay khi `Average ActiveStreamsPerTask >= 20` hoặc `CPU Utilization >= 60%` trong 60 giây.
- **Quy tắc Scale In**: Giảm `-1 Task` khi `Average ActiveStreamsPerTask <= 5` liên tục trong 10 phút.

---

## 3. Thiết kế Giao thức & Cấu trúc Dữ liệu (Data Structures & Schemas)

### 3.1. Giao thức Khung Âm thanh Nhị phân (WebSocket Binary Audio Frame)
Speaker Client gửi các frame âm thanh mỗi `100ms` (PCM 16kHz, 16-bit, Mono = `3.200 bytes` hoặc Opus `~400 bytes`) theo cấu trúc:

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        seq_id (UInt32)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                     timestamp_ms (UInt64)                     +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  codec (UInt8)|  flags (UInt8)|        reserved (UInt16)      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Audio Payload (Variable)                   |
|                         (PCM / Opus)                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
- `codec`: `1` = PCM 16kHz 16-bit Mono, `2` = Opus 16kHz.
- `flags`: Bit `0` = `is_speech` (kết quả từ VAD tại client), Bit `1` = `end_of_turn`.

### 3.2. Thiết kế Cấu trúc Dữ liệu trên Amazon ElastiCache (Redis)

| Redis Key Pattern | Kiểu dữ liệu | TTL | Mục đích sử dụng |
| :--- | :--- | :---: | :--- |
| `room:{roomId}:meta` | `HASH` | 12h | Lưu thông tin nhanh của phòng: `hostId`, `mode`, `sourceLang`, `targetLangs` (JSON), `status`, `activeWorkerId`. |
| `room:{roomId}:audio_buffer` | `STREAM` | 60s | Lưu cuốn chiếu tối đa `100` entries gần nhất (`MAXLEN ~ 100`, tương ứng 10 giây âm thanh) gồm `seq_id`, `timestamp`, `pcm_bytes` để phục vụ Hot-Failover. |
| `room:{roomId}:checkpoint` | `HASH` | 12h | Lưu `last_received_seq` và `last_committed_seq` (mốc frame của câu `Final` gần nhất đã dịch xong). |
| `room:{roomId}:tts_count` | `HASH` | 12h | Lưu số người nghe đang bật loa theo từng ngôn ngữ (ví dụ: `{"en-US": 42, "ja-JP": 15, "ko-KR": 0}`). Worker đọc key này trước khi gọi Polly. |
| `host:{hostId}:entitlements` | `STRING` (JSON) | 15m | Cache `planCode` và object `entitlements` của gói Subscription hiện tại phục vụ `EntitlementGuard` (`< 1ms`), tự invalidate khi nâng/hạ gói. |
| `wallet:{hostId}:credits` | `HASH` | 24h | Số dư Credit 3 ngăn thời gian thực (`promo`, `plan`, `topup`, `total`), trừ realtime mỗi 1 giây theo Per-Second Metering và flush ACID xuống PostgreSQL. |

### 3.3. Thiết kế Cơ sở Dữ liệu Quan hệ trên PostgreSQL 16 (10 Bảng ACID & S3 Offload)

Cơ sở dữ liệu chính của hệ thống là **PostgreSQL 16**, kết nối bất đồng bộ qua **SQLAlchemy 2.0 Async (`asyncpg`)** và quản lý di trú lược đồ qua **Alembic** (`apps/backend/alembic/versions/20261112_0001_initial_schema.py`). Hiện tại ORM (`apps/backend/app/models/`) đã định nghĩa đầy đủ **10 bảng quan hệ**:

1. **Bảng `users`** (`app/models/user.py`):
   - `id`: `VARCHAR(64)` Primary Key (khớp `sub` của Amazon Cognito User Pool)
   - `email`: `VARCHAR(255)` UNIQUE NOT NULL (Indexed)
   - `role`: `VARCHAR(32)` NOT NULL DEFAULT `'HOST'` (`HOST` | `ADMIN`)
   - `status`: `VARCHAR(32)` NOT NULL DEFAULT `'ACTIVE'` (`ACTIVE` | `SUSPENDED`)
   - `created_at` / `updated_at`: `TIMESTAMPTZ`

2. **Bảng `user_profiles`** (`app/models/user.py`):
   - `id`: `UUID` Primary Key
   - `user_id`: `VARCHAR(64)` UNIQUE NOT NULL (FK $\rightarrow$ `users.id` ON DELETE CASCADE)
   - `full_name`: `VARCHAR(255)` NOT NULL
   - `avatar_url`: `VARCHAR(1024)` NULL
   - `timezone`: `VARCHAR(64)` NOT NULL DEFAULT `'Asia/Ho_Chi_Minh'`
   - `default_source_lang`: `VARCHAR(16)` NOT NULL DEFAULT `'vi-VN'`
   - `default_target_langs`: `JSON` NOT NULL DEFAULT `'["en-US"]'`
   - `company_name`: `VARCHAR(255)` NULL
   - `tax_code`: `VARCHAR(64)` NULL
   - `company_address`: `VARCHAR(512)` NULL
   - `stripe_customer_id`: `VARCHAR(128)` NULL (Indexed)
   - `preferences`: `JSON` NOT NULL DEFAULT `'{}'`
   - `created_at` / `updated_at`: `TIMESTAMPTZ`
   - *(Ghi chú mở rộng cho `EP02-S5`: sẽ bổ sung migration cột `phone_number`, `bio` khi triển khai Profile API).*

3. **Bảng `wallets`** (`app/models/wallet.py`):
   - `id`: `UUID` Primary Key
   - `host_id`: `VARCHAR(64)` UNIQUE NOT NULL (FK $\rightarrow$ `users.id` ON DELETE CASCADE)
   - `balance`: `NUMERIC(12, 4)` NOT NULL DEFAULT `0.0000`
   - `currency`: `VARCHAR(8)` NOT NULL DEFAULT `'USD'`
   - `auto_degrade_tts`: `BOOLEAN` NOT NULL DEFAULT `TRUE`
   - `auto_topup_enabled`: `BOOLEAN` NOT NULL DEFAULT `FALSE`
   - `auto_topup_threshold`: `NUMERIC(12, 4)` NULL
   - `auto_topup_amount`: `NUMERIC(12, 4)` NULL
   - `default_payment_method_id`: `VARCHAR(128)` NULL
   - `created_at` / `updated_at`: `TIMESTAMPTZ`

4. **Bảng `payment_transactions`** (`app/models/wallet.py`):
   - `id`: `UUID` Primary Key
   - `host_id`: `VARCHAR(64)` NOT NULL (FK $\rightarrow$ `users.id` ON DELETE CASCADE, Indexed)
   - `transaction_id`: `VARCHAR(128)` UNIQUE NOT NULL (Indexed — bảo đảm Idempotency cho Stripe/VietQR/Welcome Bonus)
   - `type`: `VARCHAR(32)` NOT NULL (Indexed — `TOP_UP` | `AUTO_TOP_UP` | `PROMO_CREDIT` | `USAGE_DEDUCTION` | `REFUND` | `ADMIN_ADJUSTMENT`)
   - `provider`: `VARCHAR(32)` NOT NULL (`STRIPE` | `VIETQR` | `VNPAY` | `SYSTEM` | `INTERNAL`)
   - `amount`: `NUMERIC(12, 4)` NOT NULL
   - `currency`: `VARCHAR(8)` NOT NULL DEFAULT `'USD'`
   - `status`: `VARCHAR(32)` NOT NULL DEFAULT `'PENDING'` (Indexed — `PENDING` | `SUCCEEDED` | `FAILED`)
   - `metadata_json`: `JSON` NOT NULL DEFAULT `'{}'`
   - `created_at` / `completed_at`: `TIMESTAMPTZ`

5. **Bảng `promo_codes`** (`app/models/wallet.py` — `FR-509`):
   - `id`: `UUID` Primary Key, `code` (`VARCHAR(32)` UNIQUE Indexed), `credit_amount` (`NUMERIC(12, 4)`), `max_redemptions` (`INT`), `redemptions_count` (`INT` default `0`), `expires_at` (`TIMESTAMPTZ` NULL), `is_active` (`BOOL` default `TRUE`), `created_at` (`TIMESTAMPTZ`).

6. **Bảng `promo_redemptions`** (`app/models/wallet.py` — `FR-509`):
   - `id`: `UUID` Primary Key, `promo_code_id` (`UUID` FK $\rightarrow$ `promo_codes.id`), `user_id` (`VARCHAR(64)` FK $\rightarrow$ `users.id`), `credit_amount` (`NUMERIC(12, 4)`), `redeemed_at` (`TIMESTAMPTZ`).
   - Ràng buộc `UNIQUE(promo_code_id, user_id)` (`uq_promo_code_user`) chống nhận trùng mã khuyến mãi.

7. **Bảng `custom_vocabularies`** (`app/models/vocabulary.py` — `FR-206`):
   - `id`: `UUID` Primary Key, `host_id` (`VARCHAR(64)` FK $\rightarrow$ `users.id`), `name` (`VARCHAR(128)`), `language_code` (`VARCHAR(16)` default `'vi-VN'`), `terms` (`JSON`), `aws_vocab_name` (`VARCHAR(128)` NULL), `sync_status` (`VARCHAR(32)` default `'PENDING'`), `created_at` / `updated_at`.

8. **Bảng `rooms`** (`app/models/room.py`):
   - `id`: `VARCHAR(64)` Primary Key
   - `host_id`: `VARCHAR(64)` NOT NULL (FK $\rightarrow$ `users.id` ON DELETE CASCADE, Indexed)
   - `title`: `VARCHAR(255)` NOT NULL
   - `source_language`: `VARCHAR(16)` NOT NULL DEFAULT `'vi-VN'`
   - `target_languages`: `JSON` NOT NULL DEFAULT `'[]'`
   - `status`: `VARCHAR(32)` NOT NULL DEFAULT `'IDLE'` (Indexed — `IDLE` | `ACTIVE` | `PAUSED` | `ENDED`)
   - `host_token_hash`: `VARCHAR(128)` NOT NULL
   - `listener_passcode`: `VARCHAR(64)` NULL
   - `started_at` / `ended_at` / `created_at` / `updated_at`: `TIMESTAMPTZ`
   - *(Ghi chú mở rộng cho `EP04-S2`: sẽ bổ sung migration các cột `room_code`, `mode`, `max_listeners`, `vocabulary_id`, `allow_listener_download`, `total_cost`, `total_duration_sec`).*

9. **Bảng `room_transcripts`** (`app/models/room.py`):
   - `id`: `UUID` Primary Key
   - `room_id`: `VARCHAR(64)` NOT NULL (FK $\rightarrow$ `rooms.id` ON DELETE CASCADE, Indexed)
   - `s3_key_master` / `s3_key_txt` / `s3_key_srt` / `s3_key_vtt` / `s3_key_csv`: `VARCHAR(512)` NULL
   - `summary_status`: `VARCHAR(32)` NOT NULL DEFAULT `'PENDING'` (`PENDING` | `GENERATING` | `READY` | `FAILED`)
   - `summary_s3_key`: `VARCHAR(512)` NULL
   - `summary_cost_usd`: `NUMERIC(8, 4)` NOT NULL DEFAULT `0.0000`
   - `created_at` / `updated_at`: `TIMESTAMPTZ`

10. **Bảng `usage_ledger`** (`app/models/room.py` — Sổ cái kiểm toán chi phí theo từng giây thực tế):
    - `id`: `UUID` Primary Key
    - `room_id`: `VARCHAR(64)` NOT NULL (FK $\rightarrow$ `rooms.id` ON DELETE CASCADE, Indexed)
    - `interval_index`: `INTEGER` NOT NULL
    - `start_time` / `end_time`: `TIMESTAMPTZ` NOT NULL
    - `audio_seconds`: `NUMERIC(8, 2)` NOT NULL
    - `stt_cost`: `NUMERIC(10, 6)` NOT NULL DEFAULT `0`
    - `mt_character_count`: `INTEGER` NOT NULL DEFAULT `0`, `mt_cost`: `NUMERIC(10, 6)` NOT NULL DEFAULT `0`
    - `tts_character_count`: `INTEGER` NOT NULL DEFAULT `0`, `tts_cost`: `NUMERIC(10, 6)` NOT NULL DEFAULT `0`
    - `fanout_event_count`: `INTEGER` NOT NULL DEFAULT `0`, `fanout_cost`: `NUMERIC(10, 6)` NOT NULL DEFAULT `0`
    - `total_cost`: `NUMERIC(10, 6)` NOT NULL
    - `created_at`: `TIMESTAMPTZ` NOT NULL

> **Lộ trình Migration tiếp theo (`0002_credit_plans_and_ledger` — xem [2026-11-19-credit-plans-and-billing-design.md](file:///D:/code/ws-translation-realtime/docs/superpowers/specs/2026-11-19-credit-plans-and-billing-design.md))**:
> - Thêm **4 bảng mới**: `plans` (4 gói cố định + JSONB `entitlements`), `subscriptions` (gói đang hoạt động & chu kỳ của Host), `credit_packs` (3 gói Top-up cố định `PACK_S/M/L`), và `credit_ledger` (Sổ cái lịch sử sử dụng & biến động Credit theo sự kiện).
> - Nâng cấp `wallets` thành 3 ngăn (`promo_credits`, `plan_credits`, `topup_credits` + hạn dùng & `auto_topup_pack_id`), `payment_transactions` thêm `credits_granted`/`bonus_credits`/`bucket`, `usage_ledger` thêm `duration_seconds`/`listener_seconds`/`credits_deducted`/`deducted_breakdown`, `room_transcripts` thêm `expires_at` (chốt retention theo gói tại thời điểm kết thúc phòng + 14 ngày ân hạn khi hạ gói), và `rooms` thêm `scheduled_start_at`/`branding_config`/`tts_voice_config`/`profanity_filter_enabled`/`speaker_ids`.

---

## 4. Danh mục Công nghệ & Dịch vụ AWS (Full Tech Stack)

### 4.1. Phần mềm & Ngôn ngữ Lập trình (Application Stack)
- **Frontend Service (`ecs-service-web` — Docker Image riêng trên ECS Fargate)**:
  - Framework & Ngôn ngữ: **Next.js 15 (App Router, TypeScript, `output: "standalone"`)** + **TailwindCSS / Shadcn UI**.
  - Đóng gói Docker multi-stage (`node:20-alpine`), chạy trên ECS Fargate đằng sau ALB (`/*`).
  - Xử lý âm thanh: **WebAudio API (`AudioWorklet`)** + bộ lọc VAD (`@ricky0123/vad-web` - Silero VAD WebAssembly) để cắt khoảng lặng ngay tại trình duyệt.
  - Nhận bản dịch: **AWS Amplify / AppSync Events WebSocket Client**.
- **Backend Service (`ecs-service-backend` — Docker Image riêng trên ECS Fargate)**:
  - Framework & Ngôn ngữ: **Python 3.12+ (`FastAPI` + `asyncio` + `Uvicorn` với `uvloop`)** + **Pydantic v2**.
  - Đóng gói Docker multi-stage (`python:3.12-slim`), chạy trên ECS Fargate đằng sau ALB (`/api/*` và `/ws/*`), đảm nhiệm đồng thời:
    1. **REST API (`/api/v1/*`)**: Quản lý phòng, cấp Ephemeral JWT cho người nghe, xử lý Webhook thanh toán, xuất file biên bản dịch và gọi AI Summary.
    2. **Realtime Audio Ingest WebSocket (`/ws/v1/*`)**: Nhận luồng âm thanh nhị phân, ghi Redis Ring Buffer, điều phối STT -> MT -> TTS và bắn sự kiện qua AppSync Events.
    3. **Async Background Tasks (`asyncio.create_task`)**: Vòng lặp đo lường từng giây (1s Redis + 15s/Event ACID flush PostgreSQL `usage_ledger`/`credit_ledger`), đóng gói file `.txt`/`.srt`/`.vtt`/`.csv` lên S3 khi kết thúc phòng, Cron sweep hết hạn Credit/Subscription (kèm Grace Period 3 ngày) và gửi thông báo Amazon SES.
  - Thư viện bất đồng bộ (Non-blocking I/O):
    - **`sqlalchemy.ext.asyncio` + `asyncpg`**: Kết nối bất đồng bộ tới PostgreSQL 16 (Alembic migrations).
    - **`amazon-transcribe`**: SDK chính thức của AWS hỗ trợ native `asyncio` HTTP/2 bi-directional streaming.
    - **`aioboto3` / `aiobotocore`**: Gọi song song (`asyncio.gather`) tới Amazon Cognito, Amazon Translate, Amazon Polly, Amazon Bedrock và S3 mà không chặn Event Loop.
    - **`redis.asyncio`**: Đọc/ghi Redis Stream Ring Buffer (`XADD`/`XRANGE`), Rate-limit & Token Blocklist với độ trễ `< 1ms`.
- **Infrastructure as Code (IaC) & CI/CD**:
  - **Terraform (`infra/terraform/`)** đa môi trường (`local`, `dev`, `prod`) với các module tái sử dụng (`vpc`, `alb`, `ecr`, `ecs`, `rds`, `elasticache`, `cognito`, `appsync`, `s3_cloudfront`, `iam`, `security`, `waf`, `dev_box_ec2`).
  - **GitHub Actions CI/CD** (`.github/workflows/backend-ci.yml`, `frontend-ci.yml`, `infra-ci.yml`, `pr-check.yml`): Tự động chạy Lint/Typecheck/Test/Terraform Validate trên mỗi PR; giai đoạn CD (AWS OIDC -> Push ECR -> ECS Rolling Deployment) thuộc `EP01-S4`.

### 4.2. Dịch vụ Đám mây AWS (AWS Services Mapping)

| Nhóm chức năng | Dịch vụ AWS sử dụng | Chế độ triển khai & Tính phí |
| :--- | :--- | :--- |
| **Container Registry** | **Amazon ECR** | 2 Repositories riêng biệt: `ws-translation/web` (Next.js) và `ws-translation/backend` (FastAPI), bật Lifecycle Policy giữ 10 images gần nhất. |
| **Compute (FE & BE)** | **Amazon ECS on AWS Fargate** | Single-AZ (`ap-southeast-1a`) gồm 2 Services:<br>- `ecs-web`: Auto-scaling `2..6 Tasks` (`0.5 vCPU, 1GB RAM`).<br>- `ecs-backend`: Auto-scaling `2..20 Tasks` (`1 vCPU, 2GB RAM`), kết hợp Fargate On-Demand + Fargate Spot. |
| **Load Balancing** | **AWS Application Load Balancer (ALB)** | 1 ALB duy nhất định tuyến theo Path:<br>- `/api/*`, `/ws/*` -> Target Group `ecs-backend` (bật WebSocket & Deregistration Delay 120s).<br>- `/*` -> Target Group `ecs-web`. |
| **Realtime Fan-out** | **AWS AppSync Events** | Serverless Pub/Sub WebSocket, tính phí thuần túy theo số triệu bản tin và số phút kết nối. |
| **Media CDN & Storage** | **Amazon S3** + **Amazon CloudFront** | - **TTS Audio Chunks (`.mp3`)**: S3 Lifecycle tự động xóa sau **24 giờ**, phân phối qua CloudFront Edge Cache.<br>- **Compiled Transcripts (`.txt`, `.srt`, `.vtt`, `.csv`, `.json`)**: Đóng gói lên S3 khi kết thúc phòng, S3 Lifecycle tự động xóa sau **90 ngày**, tải xuống qua S3 Pre-signed URL. |
| **In-Memory State** | **Amazon ElastiCache for Redis** | Node đơn trong `AZ-a` (ví dụ: `cache.t4g.micro` hoặc `cache.t4g.small` cho giai đoạn đầu, nâng cấp không gián đoạn khi tăng tải). |
| **Speech-to-Text (STT)** | **Amazon Transcribe Streaming** | HTTP/2 Streaming API, tính phí theo giây âm thanh thực tế. |
| **Machine Translation (MT)** | **Amazon Translate** | Real-time Text Translation API, tính phí theo số ký tự dịch. |
| **Text-to-Speech (TTS)** | **Amazon Polly Neural** *(Primary)* + **Azure AI Speech Neural (`southeastasia`)** *(cho `vi-VN`, `th-TH`, `id-ID`)* | Bọc qua `TTSProviderAdapter` (`app/integrations/tts.py`); gọi Azure REST `cognitiveservices/v1` qua `httpx.AsyncClient` (không cài C++ SDK, đồng vùng Singapore `< 5ms`). Dùng gói **`F0` Free** (500k ký tự/tháng) cho `local`/`dev`, và gói **`S0` Standard** (`$16/1M ký tự`, commercial-use, high concurrency) cho `prod`. Voice `vi-VN`: `vi-VN-HoaiMyNeural` (Nữ) / `vi-VN-NamMinhNeural` (Nam). Key lưu trên AWS Secrets Manager (`AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`); tự fallback `Text-only` (`0 Cr`) khi timeout/`5xx` hoặc chưa cấu hình key. |
| **Email Notifications** | **Amazon SES** | Gửi OTP Cognito và 8 loại thông báo nghiệp vụ (Hóa đơn PDF, Nhắc gia hạn VietQR T-7/T-3/T-1, `PAST_DUE`, Promo sắp hết hạn, Biên bản/AI Summary sẵn sàng). |
| **AI Meeting Summary (LLM)** | **Amazon Bedrock** (`Claude 3.5 Haiku` / `Amazon Nova Lite`) | Gọi On-Demand khi Host bấm nút *"Tóm tắt nội dung AI"*, tính phí theo Input/Output Tokens và lưu cache kết quả trên S3 trong 90 ngày. |
| **Primary Relational DB** | **Amazon RDS for PostgreSQL 16** (Local: PostgreSQL 16 Docker / DevBox) | Cơ sở dữ liệu quan hệ ACID chính (10 bảng), kết nối qua `asyncpg` & SQLAlchemy 2.0, migration qua Alembic. |
| **Authentication** | **Amazon Cognito** | Quản lý tài khoản Host; Backend FastAPI trực tiếp xác thực Cognito JWT và cấp Ephemeral JWT cho người nghe. |
| **Monitoring & Tracing** | **Amazon CloudWatch** + **AWS X-Ray** | Thu thập Container Logs, Custom Metrics (Latency STT/MT/TTS), cảnh báo lỗi và theo dõi cước phí. |

---

## 5. Thiết kế Quy trình CI/CD, Đóng gói Docker & Triển khai ECS (CI/CD & Deployment Architecture)

### 5.1. Kiến trúc Luồng CI/CD với GitHub Actions, Amazon ECR & ECS Fargate

```mermaid
flowchart LR
    subgraph GitHub["GitHub Repository (Monorepo)"]
        Push["Git Push / Merge PR\n(main / staging)"]
        GHA["GitHub Actions Runner\n(Path Filter: apps/web vs apps/backend)"]
    end

    subgraph CI_Pipeline["Giai đoạn CI (Test & Build Docker)"]
        TestFE["Job 1a: Frontend CI\n- pnpm lint & typecheck\n- vitest unit tests\n- Docker build (Next.js Standalone)"]
        TestBE["Job 1b: Backend CI\n- ruff lint & mypy\n- pytest-asyncio\n- Docker build (Python 3.12 + uvloop)"]
    end

    subgraph AWS_Cloud["AWS Cloud (OIDC Auth - Không dùng Static Keys)"]
        ECR_Web[("Amazon ECR\nrepo: ws-translation/web\ntag: git-sha & latest")]
        ECR_BE[("Amazon ECR\nrepo: ws-translation/backend\ntag: git-sha & latest")]
        ECS_Web["ECS Fargate Service: web\nRolling Update (Min Healthy 100%)"]
        ECS_BE["ECS Fargate Service: backend\nZero-Downtime Rolling Deploy\n+ SIGTERM Handover (120s)"]
    end

    Push --> GHA
    GHA -->|"Thay đổi trong apps/web/**"| TestFE
    GHA -->|"Thay đổi trong apps/backend/**"| TestBE
    TestFE -->|"Push Image"| ECR_Web
    TestBE -->|"Push Image"| ECR_BE
    ECR_Web -->|"Update Task Definition"| ECS_Web
    ECR_BE -->|"Update Task Definition"| ECS_BE
```

### 5.2. Thiết kế Đóng gói Docker Riêng biệt cho FE (`web`) và BE (`backend`)

1. **Frontend Dockerfile (`apps/web/Dockerfile` — Next.js 15 Standalone)**:
   - **Stage 1 (`deps`)**: Dùng `node:20-alpine`, cài đặt dependencies qua `pnpm install --frozen-lockfile`.
   - **Stage 2 (`builder`)**: Chạy `pnpm build` với cấu hình `output: "standalone"` trong `next.config.ts` để tách riêng thư mục `.next/standalone` siêu nhẹ (loại bỏ toàn bộ `devDependencies`).
   - **Stage 3 (`runner`)**: Dùng `node:20-alpine` chạy dưới quyền user `nextjs` (non-root), copy `.next/standalone` và `.next/static`, mở cổng `3000`, khởi chạy bằng `node server.js` (Kích thước image chỉ `~120MB`, thời gian khởi động container `< 2 giây`).
   - **Healthcheck**: `GET /api/health` trả về `200 OK`.

2. **Backend Dockerfile (`apps/backend/Dockerfile` — Python 3.12 FastAPI + `uvloop`)**:
   - **Stage 1 (`builder`)**: Dùng `python:3.12-slim` kết hợp trình quản lý gói tốc độ cao **`uv`** (`ghcr.io/astral-sh/uv`), biên dịch toàn bộ thư viện (`fastapi`, `uvicorn[standard]`, `uvloop`, `amazon-transcribe`, `aioboto3`, `redis`) vào môi trường ảo `/opt/venv`.
   - **Stage 2 (`runner`)**: Dùng `python:3.12-slim`, cài đặt `libopus0` / `ffmpeg` (phục vụ xử lý frame âm thanh Opus/PCM), chạy dưới quyền user `appuser` (non-root), mở cổng `8000`.
   - **Entrypoint**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop uvloop --http httptools --ws websockets --timeout-graceful-shutdown 120`.
   - **Healthcheck**: `GET /api/v1/health` (kiểm tra kết nối Redis ping `< 5ms`) trả về `200 OK`.

### 5.3. Quy trình Chi tiết trên GitHub Actions (`.github/workflows/`)

Pipeline được tách thành các workflow chuyên biệt theo **Path Filtering** (chỉ chạy job cho phần có thay đổi code):

1. **Giai đoạn 1 — Kiểm tra Chất lượng Code & Unit Test (Đã triển khai trên mọi Pull Request và Push)**:
   - **`frontend-ci.yml`** (`apps/web/**`): `pnpm lint` (ESLint) + `pnpm typecheck` (`tsc --noEmit`) + `pnpm test:run` (Vitest) + `pnpm build`.
   - **`backend-ci.yml`** (`apps/backend/**`): `uv run ruff check .` (Lint) + `uv run mypy app` (Typecheck) + `uv run pytest -v` (Unit & Async Integration Tests với `fakeredis` + SQLite/PostgreSQL async + mock AWS clients).
   - **`infra-ci.yml`** (`infra/terraform/**`): `terraform fmt -check -recursive` + `terraform validate` cho cả 3 môi trường (`local`, `dev`, `prod`).
   - **`pr-check.yml`**: Kiểm tra tiêu chuẩn PR/Commit.

2. **Giai đoạn 2 — Build Docker Image & Push lên Amazon ECR (Planned trong `EP01-S4` — Khi merge vào `staging` hoặc `main`)**:
   - Xác thực với AWS thông qua `aws-actions/configure-aws-credentials` (pin SHA 40 ký tự) sử dụng **IAM OIDC Identity Provider** (không dùng static AWS key).
   - Sử dụng **Docker Buildx** kết hợp **GitHub Actions Cache (`type=gha`)** để tái sử dụng các Docker layers không đổi (giảm thời gian build từ 4 phút xuống `< 45 giây`).
   - Gắn 2 thẻ (tags) cho mỗi lần build: `:<git-commit-sha>` (bất biến để rollback tức thì) và `:latest`.
   - Đẩy tương ứng lên 2 kho ECR:
     - `123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/ws-translation/web:<sha>`
     - `123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/ws-translation/backend:<sha>`

3. **Giai đoạn 3 — Triển khai Không Gián Đoạn lên Amazon ECS Fargate (Zero-Downtime Rolling Deploy)**:
   - Render bản mới của ECS Task Definition với image tag `:<git-commit-sha>`.
   - Gọi `aws-actions/amazon-ecs-deploy-task-definition@v2` cập nhật service tương ứng (`ecs-web` hoặc `ecs-backend`) với cấu hình:
     - `deploymentConfiguration`: `minimumHealthyPercent = 100%`, `maximumPercent = 200%` (ECS khởi tạo các container phiên bản mới lên trước, đợi vượt qua ALB Healthcheck thành công 100% rồi mới gửi tín hiệu `SIGTERM` cho container cũ).
     - Đối với `ecs-backend`: Khi container cũ nhận `SIGTERM`, cơ chế **Make-Before-Break Handover (`FR-602`)** tự động kích hoạt trong thời gian `stopTimeout = 120s`, chuyển toàn bộ các phòng đang nói sang container mới với **0ms gián đoạn**.
   - **Tự động Rollback (ECS Deployment Circuit Breaker)**: Bật `enableFaultInjection / deploymentCircuitBreaker (enable=true, rollback=true)`. Nếu container mới bị lỗi healthcheck liên tiếp, ECS tự động hủy đợt deploy và quay về bản `:<previous-sha>` đang chạy ổn định.
