# Hệ thống Dịch Thuật Giọng Nói Thời Gian Thực Đa Ngôn Ngữ (Realtime Speech-to-Speech & Speech-to-Text Translation)

Nền tảng dịch thuật giọng nói trực tiếp độ trễ thấp trên **AWS**, hỗ trợ song song chế độ **Đàm thoại 2 chiều (1-on-1 Bi-directional)** và **Hội thảo đa ngôn ngữ (1-to-Many Broadcast lên tới 1.000 người nghe/phòng, 10 ngôn ngữ đồng thời)** theo mô hình **4 Gói Subscription cố định + Ví Credit 3 ngăn (`1 USD = 100 Credits`) + Tính cước chính xác theo từng giây (Per-Second Billing)**.

---

## 1. Kiến trúc & Công nghệ Cốt lõi (Tech Stack)

- **Frontend (`apps/web`)**: Next.js 15 (App Router, TypeScript, `output: "standalone"`), TailwindCSS, Vitest, WebAudio API (`AudioWorklet` + Silero VAD), AWS AppSync Events WebSocket Client.
- **Backend (`apps/backend`)**: Python 3.12+, **FastAPI**, **Uvicorn (`uvloop` + `httptools`)**, **Pydantic v2**, Clean Architecture (`api` / `services` / `repositories` / `models` / `integrations`), quản lý gói bằng **`uv`**.
- **Database & In-Memory State**:
  - **PostgreSQL 16 (Primary ACID Database — SQLAlchemy 2.0 Async + `asyncpg` + Alembic)**: 10 bảng quan hệ (`users`, `user_profiles`, `wallets`, `payment_transactions`, `promo_codes`, `promo_redemptions`, `custom_vocabularies`, `rooms`, `room_transcripts`, `usage_ledger`).
  - **Amazon ElastiCache for Redis (Single-AZ)**: Lưu đệm 10 giây âm thanh (`Audio Ring Buffer`) phục vụ Hot-Failover, đếm số người nghe bật loa (`tts_count`), Rate-limiting & Token Blocklist, và đồng bộ số dư ví thời gian thực.
  - **Amazon S3 + CloudFront CDN**: Lưu trữ biên bản dịch đa định dạng & AI Summary (90 ngày) và file âm thanh TTS (24 giờ).
- **AWS AI & Fan-out Pipeline**:
  - **STT**: Amazon Transcribe Streaming (HTTP/2 bi-directional stream).
  - **MT**: Amazon Translate (dịch song song $N$ ngôn ngữ đích `< 150ms`).
  - **TTS**: Multi-Provider Neural TTS (**Amazon Polly Neural** primary + **Azure AI Speech Neural `southeastasia`** qua `httpx.AsyncClient` cho Tiếng Việt `vi-VN`, `th-TH`, `id-ID` — Demand-driven chỉ tổng hợp cho ngôn ngữ có người bật loa).
  - **AI Meeting Summary**: Amazon Bedrock (`Claude 3.5 Haiku` / `Amazon Nova Lite` — tóm tắt nội dung lịch sử phiên dịch On-Demand).
  - **Realtime Fan-out & Auth**: AWS AppSync Events + Amazon Cognito (JWKS RS256 + HttpOnly Refresh Cookie).
- **IaC & CI/CD**: **Terraform** đa môi trường (`infra/terraform/environments/{local,dev,prod}`) + **GitHub Actions CI** (`backend-ci`, `frontend-ci`, `infra-ci`, `pr-check`) -> Build 2 Docker Images riêng (`web` & `backend`) -> Push lên **Amazon ECR** -> Rolling Deploy không gián đoạn lên **Amazon ECS Fargate** (Single-AZ `ap-southeast-1a`).

---

## 2. Bộ Tài liệu Đặc tả & Lộ trình (`docs/`)

Toàn bộ thiết kế nghiệp vụ, chức năng, kiến trúc hạ tầng, hợp đồng API và phân rã Epic/Task được lưu trong `docs/`:

1. **[01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md) — Nghiệp vụ, 4 Gói cố định & Cơ chế Tính Credit (BRD & Billing)**
   - Mục tiêu nghiệp vụ, Technical SLA, Business KPIs (`Gross Margin >= 55%`) & Non-Goals v1.
   - Phân quyền `Host`, `Speaker`, `Listener`, `System Admin`, Anti-abuse gói `FREE` & Quyền riêng tư (Consent/GDPR).
   - 4 gói Subscription cố định (`FREE`/`PRO`/`BUSINESS`/`ENTERPRISE`), Ví Credit 3 ngăn (`1 USD = 100 Cr`, trừ `Promo -> Plan -> Top-up`), tính cước chính xác **theo từng giây**, 2 sổ Lịch sử Nạp & Sử dụng, Multi-provider TTS (`vi-VN`) và Notification Matrix.

2. **[02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md) — Danh sách 47 Chức năng Hệ thống (FSD)**
   - Ma trận **47 chức năng chi tiết** (`FR-101` .. `FR-609`) chia làm 6 phân hệ (`MOD-01` đến `MOD-06`).
   - Bao gồm đầy đủ luồng Auth Cognito + GDPR (`FR-107`), Mic Check Lobby, 5 tính năng mở rộng theo gói (`FR-207`, `FR-208`), Multi-provider TTS (`vi-VN`), Xuất biên bản đa định dạng, **AI Tóm tắt Bedrock (`FR-407`)**, **Session Analytics (`FR-408`)** và **6 phân hệ System Admin Portal (`FR-604` .. `FR-609`)**.

3. **[03-system-architecture-and-techstack.md](file:///D:/code/ws-translation-realtime/docs/specs/03-system-architecture-and-techstack.md) — Kiến trúc Hệ thống, HA/Zero-Downtime & CI/CD (SAD)**
   - Kiến trúc triển khai **AWS Single-AZ** (tiết kiệm 100% phí Cross-AZ, độ trễ nội bộ `< 1ms`).
   - Cơ chế **Zero-Downtime Failover** (Redis Audio Ring Buffer + Make-Before-Break Handover) đảm bảo không mất chữ và không ngắt kết nối của 1.000 người nghe khi container gặp sự cố hoặc khi Rolling Update.
   - Thiết kế 16-byte Binary Audio Frame, Redis Keys, **10 bảng PostgreSQL 16**, Terraform IaC và GitHub Actions CI/CD.

4. **[04-api-websocket-and-ui-specs.md](file:///D:/code/ws-translation-realtime/docs/specs/04-api-websocket-and-ui-specs.md) — Hợp đồng API, WebSocket Schemas & Giao diện (API & UI Specs)**
   - Cấu trúc thư mục Monorepo (`apps/web`, `apps/backend`, `infra/terraform`).
   - Đặc tả toàn bộ REST API Endpoints (`/api/v1/*`, cập nhật đầy đủ 8 Auth endpoints đã triển khai) và WebSocket JSON Payloads.
   - Cấu trúc file lưu trữ S3 (`master.json` và `summary.json`).
   - Danh mục 6 màn hình giao diện Next.js (`SCR-01` .. `SCR-06`).

5. **[epics-and-sub-epics.md](file:///D:/code/ws-translation-realtime/docs/tasks/epics-and-sub-epics.md) — Phân rã 9 Epic & 39 Sub-Epic Theo Tính năng**
   - Chia toàn bộ dự án thành **9 Epic lớn** (`EPIC-01` .. `EPIC-09`) và **39 Sub-Epic** kèm trạng thái triển khai thực tế (`DONE` / `IN_PROGRESS` / `TODO`), phân tầng `P0`/`P1`/`P2` và sơ đồ phụ thuộc.

6. **[implementation-tasks-roadmap.md](file:///D:/code/ws-translation-realtime/docs/tasks/implementation-tasks-roadmap.md) — Bảng Phân rã 120 Task Nguyên tử (Granular Tasks)**
   - Đặc tả chi tiết input/output, luồng xử lý và tiêu chí nghiệm thu cho từng task kỹ thuật (đã đồng bộ Credit 3 ngăn, Per-Second Billing, Admin Portal & tiến độ `[DONE]`).

---

## 3. Hướng dẫn cho AI Coding Agents

Xem file **[AGENTS.md](file:///D:/code/ws-translation-realtime/AGENTS.md)** tại thư mục gốc để nắm rõ các quy tắc kỹ thuật bắt buộc (Guardrails), quy ước code/commit và lệnh kiểm tra (Verification Commands).
