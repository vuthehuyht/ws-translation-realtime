# Hệ thống Dịch Thuật Giọng Nói Thời Gian Thực Đa Ngôn Ngữ (Realtime Speech-to-Speech & Speech-to-Text Translation)

Nền tảng dịch thuật giọng nói trực tiếp độ trễ thấp trên **AWS**, hỗ trợ song song chế độ **Đàm thoại 2 chiều (1-on-1 Bi-directional)** và **Hội thảo đa ngôn ngữ (1-to-Many Broadcast lên tới 1.000 người nghe/phòng, 10 ngôn ngữ đồng thời)** theo mô hình tính phí **Pay-as-you-go (Micro-billing mỗi 10 giây)**.

---

## 1. Kiến trúc & Công nghệ Cốt lõi (Tech Stack)

- **Frontend (`apps/web`)**: Next.js 15 (App Router, TypeScript, `output: "standalone"`), TailwindCSS, Shadcn UI, WebAudio API (`AudioWorklet` + Silero VAD), AWS AppSync Events WebSocket Client.
- **Backend (`apps/backend`)**: Python 3.12+, **FastAPI**, **Uvicorn (`uvloop` + `httptools`)**, **Pydantic v2**, quản lý gói bằng **`uv`**.
- **Database & In-Memory State (100% Serverless NoSQL)**:
  - **Amazon ElastiCache for Redis (Single-AZ)**: Lưu đệm 10 giây âm thanh (`Audio Ring Buffer`) phục vụ Hot-Failover, đếm số người nghe bật loa (`tts_count`) và trừ tiền nguyên tử (`INCRBYFLOAT`).
  - **Amazon DynamoDB (On-Demand)**: 6 bảng (`Users`, `Wallets`, `PaymentTransactions`, `Rooms`, `RoomTranscripts` [TTL 24h], `UsageLedger`).
- **AWS AI & Fan-out Pipeline**:
  - **STT**: Amazon Transcribe Streaming (HTTP/2 bi-directional stream).
  - **MT**: Amazon Translate (dịch song song $N$ ngôn ngữ đích `< 150ms`).
  - **TTS**: Amazon Polly Neural (Demand-driven — chỉ tổng hợp giọng nói cho ngôn ngữ có người bật loa).
  - **AI Meeting Summary**: Amazon Bedrock (`Claude 3.5 Haiku` / `Amazon Nova Lite` — tóm tắt nội dung lịch sử phiên dịch On-Demand).
  - **Realtime Fan-out & Storage**: AWS AppSync Events + Amazon S3 & CloudFront CDN.
- **CI/CD & Triển khai**: GitHub Actions (AWS OIDC) -> Build 2 Docker Images riêng (`web` & `backend`) -> Push lên **Amazon ECR** -> Rolling Deploy không gián đoạn lên **Amazon ECS Fargate** (Single-AZ `ap-southeast-1a`).

---

## 2. Bộ Tài liệu Đặc tả Hệ thống (`docs/specs/`)

Toàn bộ thiết kế nghiệp vụ, chức năng, kiến trúc hạ tầng và hợp đồng API được quy định chi tiết trong 4 tài liệu:

1. **[01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md) — Nghiệp vụ & Cơ chế Tính phí (BRD & Billing)**
   - Mục tiêu nghiệp vụ, KPI & SLA (`Partial < 500ms`, `Final < 800ms`, `TTS < 1.2s`).
   - Phân quyền `Host`, `Speaker`, `Listener`, `System Admin`.
   - Quy tắc tối ưu chi phí thông minh (VAD lọc khoảng lặng, Demand-driven TTS, Partial Debounce 300ms).
   - Công thức tính cước vi mô mỗi 10 giây, nạp tiền Stripe/VietQR, Auto Top-up và chính sách lưu trữ (24h DynamoDB / 90 ngày S3).

2. **[02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md) — Danh sách 38 Chức năng Hệ thống (FSD)**
   - Ma trận **38 chức năng chi tiết** (`FR-101` .. `FR-604`) chia làm 6 phân hệ (`MOD-01` đến `MOD-06`).
   - Bao gồm đầy đủ luồng Auth qua Amazon Cognito, Ví & Cổng thanh toán, Đồng bộ/Xuất biên bản dịch đa định dạng (`.txt`, `.srt`, `.vtt`, `.csv`), và tính năng **AI Tóm tắt Nội dung Lịch sử Dịch (`FR-407`)**.

3. **[03-system-architecture-and-techstack.md](file:///D:/code/ws-translation-realtime/docs/specs/03-system-architecture-and-techstack.md) — Kiến trúc Hệ thống, HA/Zero-Downtime & CI/CD (SAD)**
   - Kiến trúc triển khai **AWS Single-AZ** (tiết kiệm 100% phí Cross-AZ, độ trễ nội bộ `< 1ms`).
   - Cơ chế **Zero-Downtime Failover** (Redis Audio Ring Buffer + Make-Before-Break Handover) đảm bảo không mất chữ và không ngắt kết nối của 1.000 người nghe khi container gặp sự cố hoặc khi Rolling Update.
   - Thiết kế 16-byte Binary Audio Frame, Redis Keys, 6 bảng DynamoDB và quy trình GitHub Actions CI/CD -> ECR -> ECS Fargate.

4. **[04-api-websocket-and-ui-specs.md](file:///D:/code/ws-translation-realtime/docs/specs/04-api-websocket-and-ui-specs.md) — Hợp đồng API, WebSocket Schemas & Giao diện (API & UI Specs)**
   - Cấu trúc thư mục Monorepo (`apps/web`, `apps/backend`, `infra`).
   - Đặc tả toàn bộ REST API Endpoints (`/api/v1/*`) và WebSocket JSON Payloads.
   - Cấu trúc file lưu trữ S3 (`master.json` và `summary.json`).
   - Danh mục 6 màn hình giao diện Next.js (`SCR-01` .. `SCR-06`).

---

## 3. Hướng dẫn cho AI Coding Agents

Xem file **[AGENTS.md](file:///D:/code/ws-translation-realtime/AGENTS.md)** tại thư mục gốc để nắm rõ các quy tắc kỹ thuật bắt buộc (Guardrails), quy ước code/commit và lệnh kiểm tra (Verification Commands).
