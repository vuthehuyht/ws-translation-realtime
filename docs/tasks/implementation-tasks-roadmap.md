# Danh mục Chức năng & Bảng Phân rã Task Chi tiết (Granular Task Breakdown & Technical Roadmap)

- **Mã tài liệu**: `DOC-05-TASKS`
- **Phiên bản**: `3.1` (Bổ sung đầy đủ 6 phân hệ System Admin Portal `TASK-OPS-09..13` & `TASK-UI-12..13` — 120 Tasks)
- **Ngày cập nhật**: 2026-11-19
- **Tài liệu tham chiếu**:
  - [epics-and-sub-epics.md](file:///D:/code/ws-translation-realtime/docs/tasks/epics-and-sub-epics.md) *(Bản phân rã 9 Epic & 36 Sub-Epic kèm phân tầng `P0/P1/P2`)*
  - [01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md)
  - [02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md)
  - [03-system-architecture-and-techstack.md](file:///D:/code/ws-translation-realtime/docs/specs/03-system-architecture-and-techstack.md)
  - [04-api-websocket-and-ui-specs.md](file:///D:/code/ws-translation-realtime/docs/specs/04-api-websocket-and-ui-specs.md)
  - [2026-11-12-backend-clean-architecture-postgres-redesign.md](file:///D:/code/ws-translation-realtime/docs/superpowers/specs/2026-11-12-backend-clean-architecture-postgres-redesign.md)

---

## Mục lục Phân hệ (12 Phân hệ - 120 Chức năng Nguyên tử)

1. [Phân hệ 1: Xác thực & Quản lý Tài khoản (Authentication & Accounts)](#phân-hệ-1-xác-thực--quản-lý-tài-khoản-authentication--accounts) (11 Tasks — 8 `DONE`)
2. [Phân hệ 2: Hồ sơ Cá nhân, Doanh nghiệp & Quyền riêng tư GDPR (User Profile & Privacy)](#phân-hệ-2-hồ-sơ-cá-nhân--cài-đặt-doanh-nghiệp-user-profile--settings) (6 Tasks)
3. [Phân hệ 3: Gói Dịch vụ, Entitlements, Ví Credit 3 Ngăn & Lịch sử (Plans, Credit Wallet & History)](#phân-hệ-3-quản-lý-ví-điện-tử-cá-nhân-crud-ví--quản-lý-tài-chính) (11 Tasks)
4. [Phân hệ 4: Thanh toán Gói cố định, Top-up Pack, Stripe, VietQR & Promo](#phân-hệ-4-cổng-thanh-toán--nạp-tiền-top-up-stripe-vietqr--promo) (7 Tasks)
5. [Phân hệ 5: Quản lý Bộ Từ điển Chuyên ngành (Custom Vocabularies CRUD & AWS Sync)](#phân-hệ-5-quản-lý-bộ-từ-điển-chuyên-ngành-custom-vocabularies-crud--aws-sync) (8 Tasks)
6. [Phân hệ 6: Quản lý Phòng, Mic Check & Tính năng Mở rộng Theo Gói (Room Lifecycle & Tier Features)](#phân-hệ-6-quản-lý-phòng--phiên-dịch-room--session-lifecycle) (15 Tasks)
7. [Phân hệ 7: Thu âm & Giao thức Nhị phân (Audio Ingest & Worklets)](#phân-hệ-7-thu-âm--giao-thức-nhị-phân-audio-ingest--worklets) (8 Tasks)
8. [Phân hệ 8: Nhận diện, Dịch thuật & Multi-Provider Neural TTS (Streaming AI Pipeline)](#phân-hệ-8-nhận-diện-dịch-thuật--tổng-hợp-giọng-nói-ai-streaming-ai-pipeline) (11 Tasks)
9. [Phân hệ 9: Đo đếm & Tính cước Theo Từng Giây (Per-Second Credit Billing Engine)](#phân-hệ-9-đo-đếm--tính-cước-theo-từng-giây-per-second-credit-billing-engine) (7 Tasks)
10. [Phân hệ 10: Biên bản S3, AI Tóm tắt Bedrock & Session Analytics](#phân-hệ-10-biên-bản-dịch-thuật--ai-tóm-tắt-qua-bedrock-transcripts--ai-summary) (10 Tasks)
11. [Phân hệ 11: Hạ tầng, Độ sẵn sàng cao & Cổng Quản trị Admin (`ADM-01..06`)](#phân-hệ-11-hạ-tầng-độ-sẵn-sàng-cao--quản-trị-hệ-thống-ha-failover--admin-portal) (13 Tasks)
12. [Phân hệ 12: Màn hình Giao diện Người dùng Web & Admin Portal (Next.js 15 UI Screens)](#phân-hệ-12-màn-hình-giao-diện-người-dùng-web-nextjs-15-ui-screens) (13 Tasks — 3 `DONE`)

---

## Phân hệ 1: Xác thực & Quản lý Tài khoản (Authentication & Accounts)

### `TASK-AUTH-01`: Đăng ký tài khoản Host bằng Email & Password `[DONE]` *(Anti-abuse blocklist bổ sung ở `TASK-PLAN-04`)*
- **Mã chức năng**: `FR-101.1` | **Scope**: `Backend API & Cognito`
- **Nghiệp vụ chi tiết**:
  - Nhận `email`, `password`, `fullName`.
  - Validate định dạng email hợp lệ (RFC 5322), mật khẩu tối thiểu 8 ký tự, có ít nhất 1 chữ hoa, 1 chữ thường, 1 số và 1 ký tự đặc biệt.
  - Gọi AWS Cognito `SignUp` API với `Username = email`, `Password = password`, `UserAttributes = [{Name: "email", Value: email}, {Name: "name", Value: fullName}]`.
  - Bắt lỗi Cognito: `UsernameExistsException` (báo email đã tồn tại), `InvalidPasswordException` (mật khẩu không đạt chuẩn).
- **Luồng xử lý (Flow)**:
  1. Client gửi `POST /api/v1/auth/register` kèm body JSON.
  2. Middleware / Pydantic validate schema.
  3. Service gọi AWS Cognito `SignUp`.
  4. Cognito sinh mã OTP 6 số và gửi mail qua Amazon SES.
  5. Trả về `201 Created` kèm `userSub` và hướng dẫn nhập mã xác thực OTP.
- **Input / Output**:
  - Input: `{"email": "host@domain.com", "password": "Password123@", "fullName": "Nguyễn Văn A"}`
  - Output: `{"status": "CONFIRMATION_REQUIRED", "email": "host@domain.com", "userSub": "uuid..."}`
- **Bảng DB tác động**: Chưa lưu vào PostgreSQL (đợi bước confirm OTP).
- **Tiêu chí nghiệm thu (AC)**: Đăng ký thành công trả về `201`, nhận được email OTP qua SES, email trùng bị trả về `409 Conflict`.

### `TASK-AUTH-02`: Xác thực mã OTP kích hoạt tài khoản & Khởi tạo Ví/Profile `[DONE]`
- **Mã chức năng**: `FR-101.2` | **Scope**: `Backend API & PostgreSQL`
- **Nghiệp vụ chi tiết**:
  - Nhận `email`, `otpCode` (6 chữ số).
  - Gọi AWS Cognito `ConfirmSignUp` với `Username = email`, `ConfirmationCode = otpCode`.
  - Mở một Transaction PostgreSQL duy nhất (`ACID`):
    1. Kiểm tra bảng `users`: Nếu chưa có, tạo bản ghi `users (id = cognito_sub, email = email, role = 'HOST', status = 'ACTIVE')`.
    2. Tạo bản ghi `user_profiles (user_id = users.id, full_name = fullName, timezone = 'Asia/Ho_Chi_Minh', default_source_lang = 'vi-VN', default_target_langs = '["en-US"]')`.
    3. Tạo bản ghi `wallets (host_id = users.id, balance = 2.0000, currency = 'USD', auto_degrade_tts = true, auto_topup_enabled = false)` (Tặng $2.00 Welcome Bonus dùng thử).
    4. Ghi một bản ghi vào `payment_transactions (host_id = users.id, transaction_id = 'welcome_' + sub, type = 'PROMO_CREDIT', provider = 'SYSTEM', amount = 2.00, status = 'SUCCEEDED')`.
  - Cam kết tính bất biến (Idempotent): Nếu user gửi mã OTP lần 2 hoặc trigger bị gọi lặp lại, không xảy ra duplicate key error.
- **Luồng xử lý (Flow)**:
  1. Client gửi `POST /api/v1/auth/confirm` với `email`, `otpCode`.
  2. Backend gọi Cognito `ConfirmSignUp`.
  3. Lấy thông tin `sub` từ Cognito `AdminGetUser`.
  4. Thực thi transaction PostgreSQL khởi tạo 3 bảng.
  5. Trả về `200 OK` (`{"status": "CONFIRMED"}`, không lộ thông tin nội bộ tài khoản).
- **Input / Output**:
  - Input: `{"email": "host@domain.com", "otpCode": "123456"}`
  - Output: `{"status": "CONFIRMED"}`
- **Bảng DB tác động**: `users`, `user_profiles`, `wallets`, `payment_transactions`.
- **Tiêu chí nghiệm thu (AC)**: 100% tài khoản xác thực OTP thành công đều có bản ghi `wallets` với số dư `$2.00`.

### `TASK-AUTH-03`: Gửi lại mã OTP kích hoạt (Resend OTP) `[DONE]`
- **Mã chức năng**: `FR-101.3` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Nhận `email`.
  - Kiểm tra Rate-limit trên Redis: Không cho phép gửi lại quá 1 lần trong vòng 60 giây (`SET email:{email}:resend_limit 1 EX 60 NX`).
  - Gọi AWS Cognito `ResendConfirmationCode`.
  - Xử lý lỗi nếu tài khoản đã được kích hoạt từ trước (`InvalidParameterException: User is already confirmed`).
- **Luồng xử lý (Flow)**:
  1. Client gửi `POST /api/v1/auth/resend-otp` với `{"email": "..."}`.
  2. Backend kiểm tra rate limit Redis -> Nếu dính chặn trả về `429 Too Many Requests`.
  3. Gọi Cognito resend OTP -> SES gửi email.
  4. Trả về `200 OK` kèm thời gian chờ 60 giây tiếp theo.
- **Tiêu chí nghiệm thu (AC)**: Không thể spam gửi OTP liên tục; email chưa đăng ký trả về `404 Not Found`.

### `TASK-AUTH-04`: Đăng nhập Host bằng Email & Mật khẩu (HttpOnly Refresh Cookie + JWKS RS256) `[DONE]`
- **Mã chức năng**: `FR-102.1` | **Scope**: `Backend API & Cognito`
- **Nghiệp vụ chi tiết**:
  - Nhận `email`, `password`.
  - Thực hiện xác thực Cognito qua luồng `USER_SRP_AUTH` (hoặc `USER_PASSWORD_AUTH` nếu dev local).
  - Trả về bộ 3 Token chuẩn JWT:
    - `id_token`: Chứa claims người dùng (sub, email, name).
    - `access_token`: Dùng xác thực API (hạn 60 phút).
    - `refresh_token`: Dùng làm mới phiên (hạn 30 ngày).
  - Kiểm tra trạng thái tài khoản trong PostgreSQL `users.status`: Nếu `SUSPENDED`, chặn đăng nhập với mã `403 Account Suspended`.
- **Luồng xử lý (Flow)**:
  1. Client gửi `POST /api/v1/auth/login`.
  2. Cognito `InitiateAuth` -> Xác thực credentials.
  3. Backend truy vấn DB kiểm tra `status` và quyền.
  4. Trả về Token trong response body (hoặc set HttpOnly Cookie).
- **Tiêu chí nghiệm thu (AC)**: Đăng nhập đúng trả về Token; sai mật khẩu trả về `401 Unauthorized`; tài khoản bị khóa bị từ chối `403`.

### `TASK-AUTH-05`: Đăng nhập nhanh bằng Google SSO (OAuth2 / OpenID Connect)
- **Mã chức năng**: `FR-102.2` | **Scope**: `Backend API & Cognito Hosted UI`
- **Nghiệp vụ chi tiết**:
  - Nhận `authCode` sau khi người dùng redirect từ Google OAuth2 qua Cognito Domain.
  - Backend đổi `authCode` lấy token từ Cognito OAuth2 token endpoint (`/oauth2/token`).
  - Lấy thông tin user (email, google_sub, name, picture).
  - Nếu là lần đầu đăng nhập qua Google: Tự động tạo bản ghi `users`, `user_profiles` (lưu `avatar_url` từ Google), và `wallets` (cộng $2.00 dùng thử).
  - Nếu đã tồn tại: Cập nhật trạng thái và trả về JWT.
- **Tiêu chí nghiệm thu (AC)**: Đăng nhập Google 1 chạm thành công; tự động tạo ví cho user Google mới.

### `TASK-AUTH-06`: Đăng nhập nhanh bằng Apple SSO
- **Mã chức năng**: `FR-102.3` | **Scope**: `Backend API & Cognito`
- **Nghiệp vụ chi tiết**:
  - Tương tự Google SSO, xử lý callback Apple ID Token qua Cognito Identity Provider.
  - Xử lý trường hợp Apple ẩn email (`privaterelay.appleid.com`).
  - Khởi tạo ví và hồ sơ cá nhân cho user Apple mới.
- **Tiêu chí nghiệm thu (AC)**: Đăng nhập Apple SSO trơn tru trên thiết bị iOS / Safari.

### `TASK-AUTH-07`: Làm mới Access Token ngầm bằng HttpOnly Cookie (Silent Token Refresh) `[DONE]`
- **Mã chức năng**: `FR-102.4` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/auth/refresh`.
  - Nhận `refreshToken`.
  - Gọi AWS Cognito `InitiateAuth` với `AuthFlow = REFRESH_TOKEN_AUTH`.
  - Nhận `AccessToken` mới và `IdToken` mới.
  - Đảm bảo phiên làm việc của Host không bị ngắt quãng khi đang chủ trì phòng họp kéo dài nhiều giờ.
- **Tiêu chí nghiệm thu (AC)**: Cấp lại AccessToken hợp lệ mà không bắt user nhập lại mật khẩu.

### `TASK-AUTH-08`: Đăng xuất tài khoản, Thu hồi Token & Redis Blocklist (Logout / Revoke Session) `[DONE]`
- **Mã chức năng**: `FR-105.1` | **Scope**: `Backend API & Security`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/auth/logout`.
  - Nhận `accessToken` và tham số tùy chọn `global = true/false`.
  - Nếu `global = false`: Gọi Cognito `RevokeToken` cho refresh token tương ứng.
  - Nếu `global = true`: Gọi Cognito `GlobalSignOut` để đăng xuất user khỏi tất cả các thiết bị.
  - Xóa cookie phiên tại Client.
- **Tiêu chí nghiệm thu (AC)**: Token sau khi đăng xuất không thể tiếp tục gọi API bảo mật.

### `TASK-AUTH-09`: Yêu cầu mã OTP Quên mật khẩu (Forgot Password) `[DONE]`
- **Mã chức năng**: `FR-103.1` | **Scope**: `Backend API & Cognito`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/auth/forgot-password`.
  - Nhận `email`.
  - Kiểm tra Rate-limit trên Redis (tối đa 3 lần/15 phút).
  - Gọi AWS Cognito `ForgotPassword`. SES gửi mã OTP 6 số về email người dùng.
- **Tiêu chí nghiệm thu (AC)**: Gửi mã OTP thành công; giới hạn chống spam hoạt động chuẩn xác.

### `TASK-AUTH-10`: Xác nhận đặt lại mật khẩu mới bằng OTP (Reset Password) `[DONE]`
- **Mã chức năng**: `FR-103.2` | **Scope**: `Backend API & Cognito`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/auth/reset-password`.
  - Nhận `email`, `otpCode`, `newPassword`.
  - Validate mật khẩu mới theo chính sách bảo mật.
  - Gọi AWS Cognito `ConfirmForgotPassword`.
  - Tự động gọi `GlobalSignOut` để hủy các phiên đăng nhập cũ trên mọi thiết bị.
- **Tiêu chí nghiệm thu (AC)**: Đặt lại mật khẩu thành công; mật khẩu cũ không còn tác dụng.

### `TASK-AUTH-11`: Đổi mật khẩu trong trang Cá nhân (Change Password)
- **Mã chức năng**: `FR-104.2` | **Scope**: `Backend API & Cognito`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/users/me/change-password` (yêu cầu AccessToken).
  - Nhận `oldPassword`, `newPassword`.
  - Gọi Cognito `ChangePassword(PreviousPassword, ProposedPassword, AccessToken)`.
  - Trả về mã lỗi `400` nếu mật khẩu cũ không đúng.
- **Tiêu chí nghiệm thu (AC)**: Đổi mật khẩu thành công ngay trong trang cài đặt tài khoản.

---

## Phân hệ 2: Hồ sơ Cá nhân & Cài đặt Doanh nghiệp (User Profile & Settings)

### `TASK-PROF-01`: Xem thông tin Hồ sơ Cá nhân & Số dư Ví
- **Mã chức năng**: `FR-104.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/users/me`.
  - Join dữ liệu từ 3 bảng: `users`, `user_profiles`, `wallets`.
  - Trả về: `id`, `email`, `fullName`, `phoneNumber`, `avatarUrl`, `timezone`, `defaultSourceLang`, `defaultTargetLangs`, `companyName`, `taxCode`, `companyAddress`, `wallet: { balance, currency, autoDegradeTts, autoTopupEnabled }`.
- **Tiêu chí nghiệm thu (AC)**: Trả về đầy đủ profile trong `< 50ms`.

### `TASK-PROF-02`: Cập nhật thông tin cơ bản người dùng
- **Mã chức năng**: `FR-104.3` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PATCH /api/v1/users/me/profile`.
  - Nhận các trường tùy chọn: `fullName`, `phoneNumber`, `timezone`, `bio`.
  - Validate: số điện thoại hợp lệ (chuẩn E.164), timezone thuộc danh sách hợp lệ (e.g. `pytz.all_timezones`).
  - Cập nhật vào bảng `user_profiles`, ghi nhận `updated_at = now()`.
- **Tiêu chí nghiệm thu (AC)**: Cập nhật thành công và hiển thị ngay trên UI.

### `TASK-PROF-03`: Cập nhật Cấu hình Ngôn ngữ & Dịch thuật Mặc định
- **Mã chức năng**: `FR-104.4` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PATCH /api/v1/users/me/preferences`.
  - Nhận `defaultSourceLang` (e.g. `vi-VN`), `defaultTargetLangs` (mảng tối đa 10 ngôn ngữ, e.g. `["en-US", "ja-JP", "ko-KR"]`), `preferences` (JSON settings: độ nhạy VAD, hiển thị phụ đề song ngữ hay đơn ngữ).
  - Validate mã ngôn ngữ nằm trong danh sách hỗ trợ của AWS Transcribe và Translate.
  - Lưu vào `user_profiles.default_source_lang`, `user_profiles.default_target_langs`, `user_profiles.preferences`.
- **Tiêu chí nghiệm thu (AC)**: Khi tạo phòng mới, tự động điền các giá trị mặc định này.

### `TASK-PROF-04`: Cập nhật Thông tin Doanh nghiệp & Xuất hóa đơn VAT
- **Mã chức năng**: `FR-104.5` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PUT /api/v1/users/me/billing-info`.
  - Nhận `companyName`, `taxCode` (Mã số thuế), `companyAddress`.
  - Validate định dạng mã số thuế (10 hoặc 13 chữ số).
  - Lưu vào bảng `user_profiles`. Thông tin này sẽ tự động gắn vào các biên lai thanh toán PDF tải về sau này.
- **Tiêu chí nghiệm thu (AC)**: Lưu thông tin thuế chuẩn xác, tự động render lên hóa đơn nạp tiền.

### `TASK-PROF-05`: Sinh Presigned URL tải lên Ảnh đại diện (Avatar Upload)
- **Mã chức năng**: `FR-104.6` | **Scope**: `Backend API & Amazon S3`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/users/me/avatar/upload-url`.
  - Nhận `fileName`, `fileType` (`image/jpeg`, `image/png`, `image/webp`), `fileSizeBytes` (tối đa 2MB = 2,097,152 bytes).
  - Sinh Amazon S3 Presigned URL PUT:
    - S3 Key: `avatars/{userId}/{uuid}.{ext}`
    - Hạn dùng: 15 phút.
    - Header ràng buộc: `Content-Type: fileType`, `Content-Length-Range: 1 to 2097152`.
  - Trả về `uploadUrl` và `s3Key`.
- **Tiêu chí nghiệm thu (AC)**: Client upload ảnh trực tiếp lên S3 thành công không qua trung gian backend.

### `TASK-PROF-06`: Xác nhận cập nhật Ảnh đại diện sau khi Upload S3
- **Mã chức năng**: `FR-104.7` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/users/me/avatar/confirm`.
  - Nhận `s3Key`.
  - Kiểm tra file tồn tại trên S3 qua `s3.head_object`.
  - Tạo CDN URL CloudFront: `https://cdn.domain.com/{s3Key}`.
  - Cập nhật `user_profiles.avatar_url = cdnUrl`.
- **Tiêu chí nghiệm thu (AC)**: Avatar hiển thị ngay trên thanh điều hướng sau khi xác nhận.

---

## Phân hệ 3: Quản lý Ví Điện tử Cá nhân (CRUD Ví & Quản lý Tài chính)

### `TASK-PLAN-01`: Migration 4 Gói cố định, Subscription, Credit Packs & Ví Credit 3 Ngăn
- **Mã chức năng**: `FR-501.0` | **Scope**: `Backend Models & Alembic`
- **Nghiệp vụ chi tiết**:
  - Alembic migration `0002_credit_plans_and_ledger`: tạo bảng `plans`, `subscriptions`, `credit_packs`, `credit_ledger`; nâng cấp `wallets` thêm `promo_credits`, `promo_expires_at`, `plan_credits`, `plan_credits_expires_at`, `topup_credits`, `auto_topup_pack_id`, `auto_topup_threshold_credits` (`CHECK >= 0`); nâng cấp `payment_transactions`, `usage_ledger`, `room_transcripts`, `rooms`.
  - Seed 4 gói cố định (`FREE $0`, `PRO $19 / 1.800 Cr`, `BUSINESS $59 / 6.000 Cr`, `ENTERPRISE $199 / 21.000 Cr`) và 3 gói Top-up lẻ (`PACK_S $10 / 1.000 Cr`, `PACK_M $30 / 3.000 Cr`, `PACK_L $100 / 10.000 Cr`).
- **Tiêu chí nghiệm thu (AC)**: Migration upgrade/downgrade sạch trên PostgreSQL 16; dữ liệu seed idempotent.

### `TASK-PLAN-02`: Bộ kiểm soát Quyền lợi Gói (`EntitlementGuard`) & Redis Cache
- **Mã chức năng**: `FR-509.2` | **Scope**: `Backend Core & Redis`
- **Nghiệp vụ chi tiết**:
  - Đọc `plans.entitlements` từ cache Redis `host:{hostId}:entitlements` (TTL 15 phút, fallback PostgreSQL).
  - Kiểm tra tập trung: `allowedRoomModes`, `maxTargetLangs`, `maxListeners`, `maxConcurrentRooms`, `allowTts`, `allowRoomPasscode`, `allowScheduledRooms`, `maxSpeakersPerRoom`, `brandingLevel`, `allowTtsVoiceSelection`, `allowProfanityFilter`, `exportFormats`, `aiSummaryLevel`, `analyticsLevel`, `allowAutoTopup`, `allowVatInvoice`.
  - Nếu vượt gói -> ném `403 UPGRADE_REQUIRED` kèm `requiredPlan`.
- **Tiêu chí nghiệm thu (AC)**: Độ trễ kiểm tra quyền `< 1ms`; tự invalidate cache ngay khi nâng/hạ gói.

### `TASK-PLAN-03`: API Danh mục Gói, Credit Packs & Quản lý Subscription
- **Mã chức năng**: `FR-501.0` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - `GET /api/v1/plans` (Public): trả 4 gói cố định và bảng `entitlements`.
  - `GET /api/v1/credit-packs` (Host): trả `PACK_S/M/L` kèm `% Bonus` tính sẵn theo gói của Host.
  - `GET /api/v1/subscriptions/me` & `POST /api/v1/subscriptions/cancel` (`cancel_at_period_end = true`).
- **Tiêu chí nghiệm thu (AC)**: Frontend render động bảng giá và khóa/mở tính năng không cần hard-code.

### `TASK-PLAN-04`: Cron Sweep Hết hạn Credit, Grace Period 3 ngày, SES Notification Worker & Anti-Abuse `FREE`
- **Mã chức năng**: `FR-509.3`, `FR-101.4` | **Scope**: `Backend Worker & Amazon SES`
- **Nghiệp vụ chi tiết**:
  - Chạy hàng giờ: sweep `promo_credits` quá hạn & `plan_credits` hết chu kỳ về `0` + ghi `credit_ledger (CREDIT_EXPIRED)`, bảo toàn `topup_credits`; giữ Grace Period 3 ngày cho Stripe `PAST_DUE`; gửi Email/In-app nhắc gia hạn VietQR T-7/T-3/T-1 và 8 sự kiện Notification Matrix qua Amazon SES.
  - Chặn disposable email domain + IP rate-limit khi đăng ký tài khoản `FREE` mới.
- **Tiêu chí nghiệm thu (AC)**: Không bao giờ xóa nhầm `topup_credits`; 100% sự kiện hết hạn có bản ghi `credit_ledger`.

### `TASK-WAL-01`: Lấy thông tin Chi tiết Ví Credit 3 Ngăn (Read Wallet)
- **Mã chức năng**: `FR-504.1` | **Scope**: `Backend API & Redis`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/wallets/me`.
  - Trả số dư chi tiết (`1 USD = 100 Credits`, `NUMERIC(12, 2)`): `promoCredits` (+ `promoExpiresAt`), `planCredits` (+ `planCreditsExpiresAt`), `topupCredits`, `totalCredits`, `autoDegradeTts`, `autoTopupEnabled`, `autoTopupThresholdCredits`, `autoTopupPackCode`.
  - Nếu Host đang có phòng hoạt động, đồng bộ với Redis Hash `wallet:{hostId}:credits`.
- **Tiêu chí nghiệm thu (AC)**: Trả chính xác số dư cả 3 ngăn trong `< 20ms`.

### `TASK-WAL-02`: Cập nhật Cài đặt Tiết kiệm & Tự động Hạ cấp TTS
- **Mã chức năng**: `FR-507.2` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PATCH /api/v1/wallets/me/settings` (kiểm tra `entitlements.allowAutoDegradeTts`, mở từ `PRO+`).
  - Cập nhật `wallets.auto_degrade_tts`.
- **Tiêu chí nghiệm thu (AC)**: Cập nhật cờ thành công và có hiệu lực ngay ở giây tiếp theo.

### `TASK-WAL-03`: Bật / Tắt và Cấu hình Tự động Nạp Gói Credit (Auto Top-up Settings)
- **Mã chức năng**: `FR-503.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PUT /api/v1/wallets/auto-topup` (kiểm tra `entitlements.allowAutoTopup` — chỉ `BUSINESS+`).
  - Nhận `enabled: boolean`, `thresholdCredits` (VD `500 Cr`), `packCode` (`PACK_S` | `PACK_M` | `PACK_L`).
  - Bắt buộc có `default_payment_method_id` mới cho phép bật `enabled = true`.
- **Tiêu chí nghiệm thu (AC)**: Gói `FREE`/`PRO` trả về `403 UPGRADE_REQUIRED`; thiếu thẻ trả về `400 Bad Request`.

### `TASK-WAL-04`: Quản lý Phương thức Thanh toán Thẻ đã lưu (Stripe SetupIntent)
- **Mã chức năng**: `FR-503.2` | **Scope**: `Backend API & Stripe`
- **Nghiệp vụ chi tiết**:
  - Endpoints `POST /wallets/me/payment-methods/{setup-intent,confirm}`, `GET /wallets/me/payment-methods`, `DELETE /wallets/me/payment-methods/{id}` (PCI-DSS compliant, không lưu PAN/CVV).
- **Tiêu chí nghiệm thu (AC)**: Lưu và xóa thẻ an toàn; xóa thẻ tự tắt `auto_topup_enabled`.

### `TASK-WAL-05`: Lịch sử Nạp tiền (`topup-history`) & Lịch sử Sử dụng Credit (`usage-history`)
- **Mã chức năng**: `FR-508.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - **Lịch sử Nạp tiền & Mua gói**: `GET /api/v1/wallets/me/topup-history` (từ `payment_transactions`, lọc theo `type`, `provider`, `status`, `startDate`, `endDate`, trả `creditsGranted`, `bonusCredits`, `bucket`, `invoicePdfUrl`).
  - **Lịch sử Sử dụng Credit**: `GET /api/v1/wallets/me/usage-history` (từ `credit_ledger`, lọc theo `eventType`: `ROOM_USAGE` | `AI_SUMMARY` | `CREDIT_EXPIRED`, trả `description`, `creditsDelta`, `bucketBreakdown`, `balanceAfter`).
- **Tiêu chí nghiệm thu (AC)**: Phân trang & lọc chuẩn xác, số dư `balanceAfter` khớp 100% sổ cái.

### `TASK-WAL-06`: Bảng Kê Đối soát Từng Giây của 1 Phiên dịch (Session Usage Breakdown)
- **Mã chức năng**: `FR-508.2` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/wallets/me/sessions/{roomId}/breakdown`.
  - Truy vấn `usage_ledger` của `roomId`: `totalAudioSeconds`, `totalListenerSeconds`, `totalTranslatedChars`, `totalTtsChars`, bóc tách 4 khoản phí ra **Credits** (`STT`, `MT`, `TTS`, `Listeners`), phân bổ trừ 3 ngăn `Promo / Plan / Top-up`, chuỗi thời gian và nút xuất **CSV**.
- **Tiêu chí nghiệm thu (AC)**: Tổng Credit các dòng `usage_ledger` khớp 100% với dòng `ROOM_USAGE` trong `credit_ledger`.

### `TASK-WAL-07`: Tải Biên lai / Hóa đơn Điện tử VAT (Receipt PDF Download)
- **Mã chức năng**: `FR-508.3` | **Scope**: `Backend API & PDF Generator`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/wallets/transactions/{transactionId}/receipt` (kiểm tra `entitlements.allowVatInvoice` cho hóa đơn VAT doanh nghiệp `BUSINESS+`).
  - Render PDF hiển thị mã giao dịch, gói/pack, số tiền, số Credit (+ bonus) và thông tin công ty/MST từ `user_profiles`.
- **Tiêu chí nghiệm thu (AC)**: File PDF sắc nét, đúng thông tin thuế.

---

## Phân hệ 4: Cổng Thanh toán & Nạp tiền (Top-up, Stripe, VietQR & Promo)

### `TASK-PAY-01`: Tạo Lệnh Thanh toán Quốc tế qua Stripe (Subscription & Top-up Pack cố định)
- **Mã chức năng**: `FR-501.1` | **Scope**: `Backend API & Stripe`
- **Nghiệp vụ chi tiết**:
  - `POST /api/v1/subscriptions/checkout` (`planCode: PRO|BUSINESS|ENTERPRISE`, `provider: STRIPE`): tạo Stripe Checkout Session (`mode=subscription`, giá cố định `$19/$59/$199`).
  - `POST /api/v1/wallets/topup` (`packCode: PACK_S|PACK_M|PACK_L`, `provider: STRIPE`): tạo Checkout Session (`mode=payment`, giá cố định `$10/$30/$100`), tính sẵn `bonusCredits` theo gói.
  - Lưu `payment_transactions (status = 'PENDING')`.
- **Tiêu chí nghiệm thu (AC)**: Tạo session Stripe thành công cho cả Subscription và Top-up Pack.

### `TASK-PAY-02`: Xử lý Webhook Stripe & Cộng Credit Nguyên tử (Stripe Webhook IPN)
- **Mã chức năng**: `FR-502.1` | **Scope**: `Backend Webhook & PostgreSQL`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/webhooks/payment/stripe`.
  - Verify `stripe-signature`, khóa dòng `FOR UPDATE` theo `transaction_id` chống trùng lặp:
    - Nếu là Subscription (`checkout.session.completed` / `invoice.paid`): cập nhật `subscriptions`, cấp `plan_credits` chu kỳ 30 ngày, xóa cache `host:{id}:entitlements`, ghi `credit_ledger`.
    - Nếu là gia hạn lỗi (`invoice.payment_failed`): chuyển `status = 'PAST_DUE'` (Grace Period 3 ngày) + gửi email SES.
    - Nếu là Top-up Pack: cộng vào `wallets.topup_credits` + đồng bộ Redis `wallet:{hostId}:credits` + ghi `credit_ledger`.
- **Tiêu chí nghiệm thu (AC)**: Bắn trùng lặp 5 lần webhook chỉ cộng Credit đúng 1 lần.

### `TASK-PAY-03`: Tạo Mã VietQR Động Cố định cho Subscription 30 ngày & Top-up Pack
- **Mã chức năng**: `FR-501.2` | **Scope**: `Backend API & VietQR`
- **Nghiệp vụ chi tiết**:
  - Hỗ trợ `provider: VIETQR` trên `POST /api/v1/subscriptions/checkout` và `POST /api/v1/wallets/topup`.
  - Quy đổi giá gói cố định sang VND, sinh `txCode = "TR" + 6 digits` (hạn 15 phút), sinh chuỗi EMVCo QR + Base64 Data URL, lưu `payment_transactions (PENDING)`.
- **Tiêu chí nghiệm thu (AC)**: Quét QR bằng app ngân hàng VN tự điền đúng STK, số tiền và nội dung chuyển khoản.

### `TASK-PAY-04`: Xử lý Webhook Biến động Số dư Ngân hàng (SePay / Casso / VietQR IPN)
- **Mã chức năng**: `FR-502.2` | **Scope**: `Backend Webhook`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/webhooks/payment/vietqr`: verify HMAC/API key, parse `TR\d{6}`, khớp số tiền (sai số `< 1,000 VND`), khóa dòng `FOR UPDATE` -> kích hoạt Subscription 30 ngày (hoặc cộng `topup_credits`), cập nhật Redis, ghi `credit_ledger`, bắn WebSocket `PAYMENT_CONFIRMED` và gửi email biên lai.
- **Tiêu chí nghiệm thu (AC)**: Credit/Gói có hiệu lực `< 2 giây` sau khi chuyển khoản.

### `TASK-PAY-05`: Background Worker Tự động Nạp Gói Credit Ngầm (Stripe Off-session Auto Top-up)
- **Mã chức năng**: `FR-503.3` | **Scope**: `Backend Worker & Stripe`
- **Nghiệp vụ chi tiết**:
  - Kích hoạt khi `total_credits < auto_topup_threshold_credits` (chỉ gói `BUSINESS+` có `auto_topup_enabled = true`).
  - Dùng Redis lock `lock:auto_topup:{hostId}` (TTL 5 phút), tạo `PaymentIntent (off_session=True, confirm=True)` theo giá cố định của `auto_topup_pack_id`. Thành công -> cộng `topup_credits` (+ `% Bonus`); thất bại -> tắt tạm `auto_topup_enabled` + gửi email cảnh báo SES.
- **Tiêu chí nghiệm thu (AC)**: Cuộc họp tự nạp thêm Credit mượt mà không ngắt âm thanh.

### `TASK-PAY-06`: Kiểm tra & Kích hoạt Mã Khuyến mãi (`Promo Redeem` -> ngăn `promo_credits`)
- **Mã chức năng**: `FR-509.1` | **Scope**: `Backend API & PostgreSQL`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/wallets/promo-redeem` (nối vào `WalletService.redeem_promo`).
  - Cộng Credit vào `wallets.promo_credits` (gắn `promo_expires_at`), ghi `promo_redemptions`, `payment_transactions (PROMO_CREDIT)` và `credit_ledger (GRANT_PROMO)`.
- **Tiêu chí nghiệm thu (AC)**: Tuyệt đối không thể nhập 1 mã 2 lần; hết hạn hoặc hết lượt bị chặn 100%.

### `TASK-PAY-07`: Xử lý Hoàn tiền Giao dịch Lỗi (Refund Processing)
- **Mã chức năng**: `FR-604.3` | **Scope**: `Backend Admin & Stripe`
- **Nghiệp vụ chi tiết**:
  - Endpoint Admin `POST /api/v1/admin/transactions/{txId}/refund`: hoàn tiền Stripe (nếu giao dịch Stripe), trừ ngược số Credit tương ứng, ghi `payment_transactions (REFUND)` & `credit_ledger (REFUND)` kèm Audit Log.
- **Tiêu chí nghiệm thu (AC)**: Hoàn tiền và đối soát Credit chính xác 100%.

---

## Phân hệ 5: Quản lý Bộ Từ điển Chuyên ngành (Custom Vocabularies CRUD & AWS Sync)

### `TASK-VOC-01`: Tạo mới Bộ Từ điển Chuyên ngành (Create Vocabulary)
- **Mã chức năng**: `FR-206.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/vocabularies`.
  - Nhận `name` (tên bộ từ vựng, e.g. "Y khoa chuyên sâu"), `languageCode` (e.g. `vi-VN`), danh sách `terms` (mảng từ/cụm từ).
  - Validation:
    - Tên không trùng lặp trong các bộ từ điển của cùng 1 Host.
    - Mảng `terms` chứa từ 1 đến tối đa 256 từ khóa.
    - Mỗi từ dài từ 1 đến 50 ký tự, chỉ chứa chữ cái, chữ số, dấu cách và dấu gạch nối (không chứa ký tự lạ làm hỏng bộ phân tích Transcribe).
  - Lưu vào bảng `custom_vocabularies`.
- **Tiêu chí nghiệm thu (AC)**: Tạo thành công trả về `201 Created` kèm `id` của bộ từ vựng.

### `TASK-VOC-02`: Lấy Danh sách Bộ Từ điển của Host (List Vocabularies)
- **Mã chức năng**: `FR-206.2` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/vocabularies`.
  - Lọc theo `host_id` của user đang đăng nhập.
  - Trả về danh sách: `id`, `name`, `languageCode`, `termsCount` (số lượng từ), `createdAt`, `updatedAt`.
- **Tiêu chí nghiệm thu (AC)**: Host A không bao giờ nhìn thấy bộ từ điển của Host B.

### `TASK-VOC-03`: Xem Chi tiết và Danh sách Từ vựng trong Bộ Từ điển (Get Vocabulary Detail)
- **Mã chức năng**: `FR-206.3` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/vocabularies/{id}`.
  - Kiểm tra quyền sở hữu. Trả về toàn bộ danh sách `terms` JSONB.
- **Tiêu chí nghiệm thu (AC)**: Trả về chi tiết từ vựng trong `< 20ms`.

### `TASK-VOC-04`: Cập nhật Tên và Danh sách Từ vựng (Update Vocabulary)
- **Mã chức năng**: `FR-206.4` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PUT /api/v1/vocabularies/{id}`.
  - Nhận `name`, `terms`.
  - Validate danh sách từ mới. Cập nhật vào DB và đánh dấu cần đồng bộ lại AWS nếu đã từng đồng bộ.
- **Tiêu chí nghiệm thu (AC)**: Cập nhật thành công, lưu vết `updated_at`.

### `TASK-VOC-05`: Xóa Bộ Từ điển Chuyên ngành (Delete Vocabulary)
- **Mã chức năng**: `FR-206.5` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `DELETE /api/v1/vocabularies/{id}`.
  - Kiểm tra ràng buộc: Kiểm tra bảng `rooms WHERE vocabulary_id = :id AND status = 'ACTIVE'`.
  - Nếu đang có phòng hoạt động sử dụng từ điển này -> Chặn xóa với lỗi `409 Conflict: Vocabulary is currently in use by an active room`.
  - Nếu không có: Xóa bản ghi trong `custom_vocabularies`.
- **Tiêu chí nghiệm thu (AC)**: Chặn xóa an toàn khi đang có phòng chạy; xóa sạch khi không sử dụng.

### `TASK-VOC-06`: Import Danh sách Từ vựng từ file CSV / TXT
- **Mã chức năng**: `FR-206.6` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/vocabularies/{id}/import`.
  - Nhận file upload (`multipart/form-data`, file `.csv` hoặc `.txt`).
  - Đọc từng dòng, loại bỏ khoảng trắng thừa, loại bỏ trùng lặp.
  - Kiểm tra tổng số lượng từ sau khi gộp không vượt quá 256 từ.
  - Cập nhật vào mảng `terms` của từ điển.
- **Tiêu chí nghiệm thu (AC)**: Import 100 từ vựng từ file CSV trong $< 1\text{ giây}$.

### `TASK-VOC-07`: Đồng bộ Bộ từ vựng sang Amazon Transcribe Custom Vocabulary
- **Mã chức năng**: `FR-206.7` | **Scope**: `Backend Integrations & AWS Transcribe`
- **Nghiệp vụ chi tiết**:
  - Xây dựng background task đồng bộ:
    1. Định dạng danh sách từ vựng thành file text theo chuẩn AWS Transcribe Vocabulary.
    2. Upload file lên S3: `s3://.../vocabularies/{id}/transcribe.txt`.
    3. Gọi API `transcribe.create_vocabulary` (hoặc `update_vocabulary` nếu đã có).
    4. Tên vocabulary trên AWS: `vocab_{id}`.
    5. Polling định kỳ kiểm tra `transcribe.get_vocabulary`: Đợi trạng thái chuyển từ `PENDING` sang `READY`.
- **Tiêu chí nghiệm thu (AC)**: Vocabulary sẵn sàng trên AWS Transcribe để đưa vào phiên STT.

### `TASK-VOC-08`: Đồng bộ Thuật ngữ sang Amazon Translate Custom Terminology
- **Mã chức năng**: `FR-206.8` | **Scope**: `Backend Integrations & AWS Translate`
- **Nghiệp vụ chi tiết**:
  - Tương tự Transcribe, định dạng bảng thuật ngữ song ngữ CSV (cột ngôn ngữ nguồn và cột ngôn ngữ đích tương ứng).
  - Gọi AWS `translate.import_terminology` với định dạng CSV.
  - Giúp việc dịch tên thương hiệu, tên riêng không bị dịch sai nghĩa.
- **Tiêu chí nghiệm thu (AC)**: Terminology được áp dụng chính xác khi gọi Amazon Translate.

---

## Phân hệ 6: Quản lý Phòng & Phiên dịch (Room & Session Lifecycle)

### `TASK-ROOM-01`: Kiểm tra Entitlement & Số dư Credit Khởi tạo Phòng (Pre-flight Check)
- **Mã chức năng**: `FR-201.1` | **Scope**: `Backend Services`
- **Nghiệp vụ chi tiết**:
  - Kiểm tra `EntitlementGuard`: `mode` trong `allowedRoomModes`, `len(targetLangs) <= maxTargetLangs`, số phòng đang `ACTIVE` của Host `< maxConcurrentRooms` (`FREE`/`PRO`: 1, `BUSINESS`: 3, `ENTERPRISE`: 10). Vượt gói -> `403 UPGRADE_REQUIRED`.
  - Ước tính Burn Rate (`Cr/phút`) theo biểu giá Credit (`STT 5.5 Cr/phút`, `MT 3.5 Cr/1k`, `TTS 4.0 Cr/1k`, `Listeners 0.5 Cr/100/phút`); riêng chế độ `1_ON_1` nhân hệ số **2 luồng nói song công**.
  - Yêu cầu `total_credits >= estimatedBurnRatePerMin × 10 phút` -> Thiếu trả về `402 Payment Required` kèm gợi ý mua `PACK_S/M/L`.
- **Tiêu chí nghiệm thu (AC)**: Vượt gói trả `403 UPGRADE_REQUIRED`; thiếu Credit trả `402` kèm số Credit còn thiếu.

### `TASK-ROOM-02`: Tạo Phòng Dịch Mới & Chế độ Lobby Mic Check (Create Room)
- **Mã chức năng**: `FR-201.2` | **Scope**: `Backend API & PostgreSQL`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms`: chạy `TASK-ROOM-01`, sinh `roomCode` (`XXX-XXX`), băm `passcode` (chỉ `PRO+`), lưu `rooms` với trạng thái `IDLE` (cho phép Host kiểm tra micro & đèn VAD cục bộ `0 Cr` trước khi bấm `START`).
  - Giới hạn người nghe mặc định lấy từ `entitlements.maxListeners` (`FREE` 2 / `PRO` 100 / `BUSINESS` 300 / `ENTERPRISE` 1.000).
- **Tiêu chí nghiệm thu (AC)**: Tạo phòng `< 100ms`, không trừ Credit khi ở trạng thái `IDLE`.

### `TASK-ROOM-03`: Xem Danh sách Phòng do Host Tạo (List Rooms)
- **Mã chức năng**: `FR-201.3` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/rooms`.
  - Query params: `status` (`ALL`, `ACTIVE`, `ENDED`), `page`, `limit`.
  - Lọc theo `host_id` của user.
  - Trả về danh sách: `id`, `roomCode`, `title`, `mode`, `sourceLang`, `targetLangs`, `status`, `totalCost`, `totalDurationSec`, `createdAt`, `startedAt`, `endedAt`.
- **Tiêu chí nghiệm thu (AC)**: Phân trang mượt mà, lọc chính xác theo trạng thái phòng.

### `TASK-ROOM-04`: Xem Chi tiết Cấu hình & Trạng thái Phòng (Get Room Detail)
- **Mã chức năng**: `FR-201.4` | **Scope**: `Backend API & Redis`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/rooms/{roomId}`.
  - Đọc thông tin cấu hình từ PostgreSQL `rooms`.
  - Đọc số liệu thời gian thực từ Redis:
    - Số người đang nghe online: `SCARD room:{roomId}:listeners`.
    - Tốc độ đốt tiền hiện tại (`burnRatePerMin`).
    - Trạng thái biên bản (`room_transcripts.status`) và tóm tắt AI (`room_transcripts.summary_status`).
- **Tiêu chí nghiệm thu (AC)**: Trả về đầy đủ số liệu live của phòng trong $< 30ms$.

### `TASK-ROOM-05`: Kiểm tra Mã Phòng cho Người nghe (Check Room Code)
- **Mã chức năng**: `FR-202.1` | **Scope**: `Backend API (Public)`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/rooms/check/{roomCode}`.
  - Public endpoint, người nghe không cần đăng nhập.
  - Tìm phòng theo `roomCode`:
    - Nếu không tồn tại: Trả về `404 Room Not Found`.
    - Nếu `status == 'ENDED'`: Trả về `410 Room Has Ended`.
  - Trả về: `roomId`, `title`, `mode`, `sourceLang`, `availableTargetLangs`, `hasPassword` (boolean), `status`.
- **Tiêu chí nghiệm thu (AC)**: Người nghe quét QR biết ngay phòng có yêu cầu mật khẩu hay không mà không lộ mật khẩu.

### `TASK-ROOM-06`: Người nghe Xác thực & Nhận Ephemeral Token (Join Room)
- **Mã chức năng**: `FR-202.2` | **Scope**: `Backend API & Security`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/join`.
  - Nhận: `roomCode`, `passcode` (nếu phòng có mật khẩu), `displayName` (tùy chọn), `preferredLang`.
  - Kiểm tra mật khẩu: Dùng `bcrypt.checkpw(passcode, password_hash)`. Nếu sai -> `401 Invalid Room Passcode`.
  - **Kiểm tra Sĩ số tối đa**:
    - Đọc `currentListeners = SCARD room:{roomId}:listeners`.
    - Nếu `currentListeners >= rooms.max_listeners`: Từ chối với mã `429 Room Capacity Reached (Max 1000)`.
  - Cấp **Ephemeral JWT Token** (thời hạn 4 giờ) có chữ ký HMAC-SHA256:
    - Claim: `sub: guest_id`, `role: LISTENER`, `roomId`, `allowedChannels: ["rooms/{roomId}/lang/*"]`.
  - Thêm `guest_id` vào Redis Set `room:{roomId}:listeners`.
  - Trả về `ephemeralToken`, `appSyncEndpoint`, `channelPrefix`.
- **Tiêu chí nghiệm thu (AC)**: Người nghe vào phòng trong $< 200ms$, phân quyền nghiêm ngặt chỉ được Subscribe.

### `TASK-ROOM-07`: Cập nhật Nóng Danh sách Ngôn ngữ Đích khi Phòng Đang Chạy
- **Mã chức năng**: `FR-203.1` | **Scope**: `Backend API & Redis`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PATCH /api/v1/rooms/{roomId}/languages`.
  - Chỉ Host có quyền gọi. Nhận danh sách `targetLangs` mới (tối đa 10 ngôn ngữ).
  - Cập nhật PostgreSQL `rooms.target_langs`.
  - Cập nhật Redis Set `room:{roomId}:target_langs`.
  - Bắn sự kiện qua AppSync Events: `CONFIG_UPDATED` để thông báo cho toàn bộ listener trong phòng biết danh sách ngôn ngữ mới.
- **Tiêu chí nghiệm thu (AC)**: Ngôn ngữ mới có hiệu lực ngay ở câu nói tiếp theo mà không cần khởi động lại phòng.

### `TASK-ROOM-08`: Cập nhật Quyền Tải Biên bản Dịch của Người nghe
- **Mã chức năng**: `FR-201.5` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PATCH /api/v1/rooms/{roomId}/permissions`.
  - Nhận `allowListenerDownload: boolean`.
  - Cập nhật trường `rooms.allow_listener_download`.
  - Khi bật `true`, người nghe được phép tải file `.txt`, `.srt`, `.csv`. Khi `false`, mọi yêu cầu tải từ listener đều bị chặn `403`.
- **Tiêu chí nghiệm thu (AC)**: Cập nhật quyền có hiệu lực tức thời.

### `TASK-ROOM-09`: Tạm dừng Phòng Dịch (Pause Room)
- **Mã chức năng**: `FR-205.1` | **Scope**: `Backend API & WebSocket`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/{roomId}/pause`.
  - Kiểm tra trạng thái: Phải đang `ACTIVE`.
  - Chuyển `rooms.status = 'PAUSED'`, cập nhật Redis.
  - Tạm dừng luồng tiếp nhận âm thanh Ingest, ngừng gửi dữ liệu sang Transcribe/Translate/Polly.
  - Ngừng tính cước trong thời gian tạm dừng.
  - Báo trạng thái `PAUSED` tới toàn bộ Client trong phòng.
- **Tiêu chí nghiệm thu (AC)**: Khi tạm dừng, không phát sinh bất kỳ chi phí AI nào.

### `TASK-ROOM-10`: Tiếp tục Phòng Dịch sau Tạm dừng (Resume Room)
- **Mã chức năng**: `FR-205.2` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/{roomId}/resume`.
  - Kiểm tra trạng thái: Phải đang `PAUSED`.
  - Kiểm tra lại số dư ví: Phải đủ tối thiểu 5 phút hoạt động tiếp theo.
  - Chuyển `rooms.status = 'ACTIVE'`, cập nhật Redis.
  - Mở lại luồng tiếp nhận âm thanh Ingest và tiếp tục chu kỳ tính cước.
- **Tiêu chí nghiệm thu (AC)**: Phòng mở lại bình thường, tiếp tục phiên dịch mượt mà.

### `TASK-ROOM-11`: Kết thúc Phòng Dịch & Chốt Sổ Phiên (End Room)
- **Mã chức năng**: `FR-205.3` | **Scope**: `Backend API & Background Worker`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/{roomId}/end`.
  - Chuyển `rooms.status = 'ENDED'`, ghi nhận `ended_at = now()`, tính `total_duration_sec`.
  - Đóng kết nối WebSocket Ingest của Host.
  - Bắn sự kiện `ROOM_ENDED` qua AppSync tới toàn bộ người nghe.
  - Kích hoạt vòng chốt cước 10s cuối cùng (`Final Billing Flush`).
  - Tạo bản ghi `room_transcripts (room_id = roomId, status = 'PROCESSING')`.
  - Kích hoạt Background Task `TranscriptCompilerWorker` đóng gói bộ file S3.
  - Đặt cờ TTL giải phóng các key đệm âm thanh trên Redis sau 1 giờ.
- **Tiêu chí nghiệm thu (AC)**: Người nghe nhận thông báo kết thúc trong $< 500ms$; kích hoạt thành công tiến trình đóng gói S3.

### `TASK-ROOM-12`: Sinh Mã QR Code Chia sẻ Phòng Họp (Generate Share QR)
- **Mã chức năng**: `FR-201.6` | **Scope**: `Backend API & Frontend Utility`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/rooms/{roomId}/qr`.
  - Sinh URL tham gia: `https://domain.com/r/{roomCode}`.
  - Sinh ảnh QR Code chuẩn PNG / SVG Data URL độ phân giải cao (512x512) để Host trình chiếu lên máy chiếu hội trường.
- **Tiêu chí nghiệm thu (AC)**: Quét QR từ khoảng cách xa trên máy chiếu nhận diện tức thì.

### `TASK-ROOM-13`: Điểm danh & Theo dõi Hiện diện Người nghe (Listener Presence Heartbeat)
- **Mã chức năng**: `FR-202.3` | **Scope**: `Backend API & Redis`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/{roomId}/heartbeat`.
  - Định kỳ 30 giây, Client người nghe gửi request heartbeat kèm `guestId` và `lang`.
  - Cập nhật Redis: `SETEX room:{roomId}:presence:{guestId} 45 {lang}`.
  - Nếu quá 45 giây không có heartbeat (do đóng tab, mất mạng): Redis Key tự hết hạn, kích hoạt worker ngầm giảm biến đếm sĩ số và giảm `tts_count` của ngôn ngữ đó nếu đang bật loa.
- **Tiêu chí nghiệm thu (AC)**: Sĩ số phòng tự động cập nhật đúng thực tế khi người nghe rời phòng đột ngột.

### `TASK-ROOM-14`: Lên lịch Phòng trước (`Scheduled Rooms`) & Quản lý Nhiều Diễn giả (`Multi-Speaker / Co-Host`)
- **Mã chức năng**: `FR-207` | **Scope**: `Backend API & EntitlementGuard`
- **Nghiệp vụ chi tiết**:
  - Hỗ trợ `scheduledStartAt` khi tạo phòng (`PRO+`) -> sinh sẵn `roomCode`/`joinUrl`/QR Code để gửi trước sự kiện.
  - Endpoint `POST /api/v1/rooms/{roomId}/speakers` cấp/thu hồi quyền phát biểu cho Co-Host (`BUSINESS`: tối đa 3, `ENTERPRISE`: tối đa 10).
- **Tiêu chí nghiệm thu (AC)**: Người nghe quét QR trước giờ thấy màn hình chờ lịch sự; vượt số lượng Speaker trả `403 UPGRADE_REQUIRED`.

### `TASK-ROOM-15`: Tùy biến Thương hiệu (`Custom Branding`), Chọn Giọng TTS & Lọc từ Nhạy cảm
- **Mã chức năng**: `FR-208` | **Scope**: `Backend API, AI Pipeline & Frontend`
- **Nghiệp vụ chi tiết**:
  - Lưu `branding_config` (Logo/Màu cho `BUSINESS`, ẩn watermark White-label cho `ENTERPRISE`), `tts_voice_config` (chọn giọng Nam/Nữ `BUSINESS+`), `profanity_filter_enabled` (`PRO+` -> gắn `VocabularyFilterMethod=mask` sang Amazon Transcribe).
- **Tiêu chí nghiệm thu (AC)**: Cấu hình áp dụng tức thời trên màn hình Listener và pipeline STT/TTS.

---

## Phân hệ 7: Thu âm & Giao thức Nhị phân (Audio Ingest & Worklets)

### `TASK-AUD-01`: AudioWorklet Thu âm Chuẩn PCM 16kHz tại Trình duyệt
- **Mã chức năng**: `FR-301.1` | **Scope**: `Frontend WebAudio Worklet`
- **Nghiệp vụ chi tiết**:
  - Viết module `AudioWorkletProcessor` chạy độc lập trên audio rendering thread.
  - Nhận luồng micro từ `navigator.mediaDevices.getUserMedia`.
  - Tự động hạ mẫu (Downsampling) từ 44.1kHz / 48kHz về chuẩn 16,000 Hz, 16-bit Mono PCM.
  - Chia nhỏ thành từng khung âm thanh chuẩn `100ms` (1.600 samples = 3.200 bytes).
- **Tiêu chí nghiệm thu (AC)**: Thu âm ổn định 100ms/frame không drop mẫu, không giật lag giao diện chính.

### `TASK-AUD-02`: Phát hiện Tiếng nói VAD tại Client (Voice Activity Detection)
- **Mã chức năng**: `FR-301.2` | **Scope**: `Frontend AudioWorklet`
- **Nghiệp vụ chi tiết**:
  - Tích hợp bộ phát hiện tiếng nói (Silero VAD WASM hoặc thuật toán Energy RMS Threshold).
  - Đánh giá từng frame 100ms:
    - Nếu năng lượng âm thanh vượt ngưỡng nói -> Đánh dấu cờ `vad_flag = 1`.
    - Nếu là khoảng lặng -> Đánh dấu cờ `vad_flag = 0`.
  - Hiển thị trực quan đèn báo VAD (Xanh khi nói, Xám khi im lặng) trên màn hình Host.
- **Tiêu chí nghiệm thu (AC)**: Nhận diện chính xác khoảng lặng để hệ thống Backend không gửi dữ liệu rỗng sang AI.

### `TASK-AUD-03`: Đóng gói Gói tin Nhị phân 16-byte Big-Endian
- **Mã chức năng**: `FR-301.3` | **Scope**: `Frontend & Backend Protocol`
- **Nghiệp vụ chi tiết**:
  - Xây dựng cấu trúc đóng gói nhị phân 16 bytes Big-Endian (`>IQBBH`):
    - `seq_id` (Uint32, 4 bytes): Số thứ tự tăng dần từ 1.
    - `timestamp_ms` (BigUint64, 8 bytes): Mốc thời gian Unix timestamp.
    - `codec` (Uint8, 1 byte): `0x01` = PCM 16kHz, `0x02` = Opus.
    - `flags` (Uint8, 1 byte): Bit 0 = VAD (1: nói, 0: im), Bit 1 = End of utterance.
    - `reserved` (Uint16, 2 bytes): Dự phòng.
    - `payload` (16 bytes trở đi): Dữ liệu âm thanh raw.
  - Phía TypeScript dùng `DataView`; phía Python dùng `struct.unpack(">IQBBH", frame[:16])`.
- **Tiêu chí nghiệm thu (AC)**: Đóng gói và giải mã khớp 100% từng byte giữa Client TypeScript và Backend Python.

### `TASK-AUD-04`: Bộ đệm Vòng tròn Cục bộ 5 Giây tại Trình duyệt (Client Ring Buffer)
- **Mã chức năng**: `FR-301.4` | **Scope**: `Frontend Audio Worklet`
- **Nghiệp vụ chi tiết**:
  - Duy trì mảng cuốn chiếu chứa tối đa 50 frames (tương đương 5 giây âm thanh gần nhất).
  - Khi gửi frame qua WebSocket: Giữ frame trong bộ đệm.
  - Khi nhận bản tin `STREAM_ACK (lastCommittedSeq)` từ server: Xóa bỏ các frame có `seq_id <= lastCommittedSeq`.
  - Nếu mất kết nối mạng đột ngột: Giữ nguyên các frame chưa được ACK để sẵn sàng bơm lại khi kết nối lại.
- **Tiêu chí nghiệm thu (AC)**: Không tiêu tốn quá 2MB RAM tại trình duyệt, giữ an toàn 5 giây âm thanh khi rớt mạng.

### `TASK-AUD-05`: WebSocket Audio Ingest Endpoint tiếp nhận Luồng Âm thanh
- **Mã chức năng**: `FR-302.1` | **Scope**: `Backend WebSocket`
- **Nghiệp vụ chi tiết**:
  - Endpoint `WebSocket /ws/v1/rooms/{roomId}/ingest?token={token}`.
  - Xác thực token: Chỉ Host hoặc Speaker được cấp quyền mới được kết nối.
  - Kiểm tra trạng thái phòng: Nếu `rooms.status != 'ACTIVE'`, từ chối và đóng socket.
  - Tiếp nhận cả 2 dạng message:
    - Binary frame: Âm thanh 16-byte header + PCM payload.
    - Text frame: Lệnh điều khiển `{"type": "END_OF_SPEECH"}` hoặc `{"type": "PING"}`.
- **Tiêu chí nghiệm thu (AC)**: Tiếp nhận ổn định 10 frames/giây từ Speaker với độ trễ network $< 20ms$.

### `TASK-AUD-06`: Lưu đệm Luồng Âm thanh vào Redis Stream 10 Giây
- **Mã chức năng**: `FR-302.2` | **Scope**: `Backend WebSocket & Redis`
- **Nghiệp vụ chi tiết**:
  - Khi nhận từng frame âm thanh từ WebSocket:
    - Ghi vào Redis Stream:
      ```text
      XADD room:{roomId}:audio_buffer MAXLEN ~ 100 * seq {seq_id} ts {ts} vad {vad} data {raw_bytes}
      ```
    - Cập nhật biến đếm `last_received_seq = seq_id`.
    - Thời gian ghi đệm Redis Single-AZ bắt buộc $< 2ms$.
- **Tiêu chí nghiệm thu (AC)**: Luôn duy trì đúng 10 giây âm thanh gần nhất trong Redis Stream để phục vụ khôi phục sự cố.

### `TASK-AUD-07`: Vòng lặp Phản hồi ACK Mỗi 500ms (Stream ACK Loop)
- **Mã chức năng**: `FR-302.3` | **Scope**: `Backend WebSocket`
- **Nghiệp vụ chi tiết**:
  - Chạy một coroutine asyncio định kỳ mỗi 500ms gửi về Client:
    ```json
    {
      "event": "STREAM_ACK",
      "lastReceivedSeq": 1420,
      "lastCommittedSeq": 1395
    }
    ```
  - Giúp Client Speaker biết vị trí server đã nhận an toàn và vị trí AI đã chốt câu để cắt tỉa bộ đệm local.
- **Tiêu chí nghiệm thu (AC)**: Client nhận đều đặn bản tin ACK 2 lần/giây khi đang nói.

### `TASK-AUD-08`: Tự động Tạm dừng khi Speaker Im lặng Quá Lâu (Silence Auto-Pause)
- **Mã chức năng**: `FR-302.4` | **Scope**: `Backend WebSocket`
- **Nghiệp vụ chi tiết**:
  - Nếu tất cả các frame nhận được trong vòng 15 phút liên tục đều có cờ `vad_flag = 0` (hoặc không có frame nào gửi lên do Host quên tắt mic):
  - Hệ thống tự động chuyển trạng thái phòng sang `PAUSED`.
  - Gửi thông báo WebSocket: *"Phòng họp đã tự động tạm dừng do không phát hiện tiếng nói trong 15 phút để bảo vệ số dư ví"*.
- **Tiêu chí nghiệm thu (AC)**: Chống cháy túi cho Host khi quên tắt mic hoặc bỏ quên phòng họp mở qua đêm.

---

## Phân hệ 8: Nhận diện, Dịch thuật & Tổng hợp Giọng nói AI (Streaming AI Pipeline)

### `TASK-AI-01`: Đẩy luồng PCM vào Amazon Transcribe Streaming qua HTTP/2
- **Mã chức năng**: `FR-303.1` | **Scope**: `Backend Integrations & AWS Transcribe`
- **Nghiệp vụ chi tiết**:
  - Khởi tạo client `amazon-transcribe` bất đồng bộ:
    - `LanguageCode`: Theo `source_lang` của phòng (e.g. `vi-VN`, `en-US`).
    - `MediaSampleRateHertz`: 16000, `MediaEncoding`: `pcm`.
    - Nếu có từ điển chuyên ngành: Gán `VocabularyName`.
  - Bơm các frame âm thanh có `vad_flag == 1` vào luồng HTTP/2 request stream.
- **Tiêu chí nghiệm thu (AC)**: Dữ liệu âm thanh truyền liên tục không bị gián đoạn stream.

### `TASK-AI-02`: Xử lý Phân tách Kết quả Transcribe (Partial vs Final Segments)
- **Mã chức năng**: `FR-303.2` | **Scope**: `Backend AI Pipeline`
- **Nghiệp vụ chi tiết**:
  - Lắng nghe event stream từ Amazon Transcribe:
    - Khi nhận transcript:
      - `IsPartial = true`: Diễn giả đang nói giữa câu. Gán nhãn tạm thời và đẩy sang bộ đệm Debounce dịch nhanh.
      - `IsPartial = false`: Diễn giả dứt câu hoặc ngắt nghỉ. Đánh dấu mốc `Final`, chốt `seq_start`, `seq_end`, `startTimeMs`, `endTimeMs`, `sourceText`.
- **Tiêu chí nghiệm thu (AC)**: Nhận kết quả Partial trong $< 350ms$ từ lúc dứt âm; chốt câu Final chính xác.

### `TASK-AI-03`: Bộ đệm Debounce 300ms cho Bản dịch Câu dở dang (Partial MT Debounce)
- **Mã chức năng**: `FR-304.1` | **Scope**: `Backend Services`
- **Nghiệp vụ chi tiết**:
  - Với các câu `Partial`:
    - Chỉ kích hoạt dịch nếu: Đã cách lần dịch partial trước $\ge 300ms$ HOẶC câu nói có thêm $\ge 3$ từ mới.
    - Chỉ dịch sang các ngôn ngữ đích hiện đang có ít nhất 1 người nghe online xem phụ đề (`active_languages`).
    - Giúp giảm tới $60\%$ số lượng request gọi Amazon Translate không cần thiết.
- **Tiêu chí nghiệm thu (AC)**: Giảm chi phí dịch Partial rõ rệt, phụ đề chạy mượt không bị giật cục.

### `TASK-AI-04`: Gọi Dịch Đa Ngôn ngữ Song song qua Amazon Translate
- **Mã chức năng**: `FR-304.2` | **Scope**: `Backend Integrations & AWS Translate`
- **Nghiệp vụ chi tiết**:
  - Với câu đã chốt `Final`:
    - Dùng `asyncio.gather(*tasks)` gọi Amazon Translate song song sang toàn bộ các ngôn ngữ trong `target_langs`.
    - Nếu có thuật ngữ chuyên ngành: Truyền `TerminologyNames`.
    - Thu về Map bản dịch: `{"en-US": "Hello", "ja-JP": "こんにちは", "ko-KR": "안녕하세요"}`.
- **Tiêu chí nghiệm thu (AC)**: Dịch song song sang 10 ngôn ngữ hoàn tất trong $< 150ms$.

### `TASK-AI-05`: Kiểm tra Quyền TTS & Biến đếm Người nghe Bật loa (Demand-driven TTS Guard)
- **Mã chức năng**: `FR-305.1` | **Scope**: `Backend Services & Redis`
- **Nghiệp vụ chi tiết**:
  - Kiểm tra `entitlements.allowTts == true` (`PRO+`) và đọc `count = HGET room:{roomId}:tts_count {lang}`:
    - Nếu `allowTts == false` hoặc `count <= 0` -> **Tuyệt đối không gọi TTS** (`0 Cr`).
    - Nếu `count > 0` -> đưa vào danh sách sinh giọng đọc.
- **Tiêu chí nghiệm thu (AC)**: Tiết kiệm `100%` chi phí TTS cho gói Free và mọi ngôn ngữ không có người bật loa.

### `TASK-AI-06`: Tổng hợp Giọng đọc Multi-Provider Neural TTS (`Polly` + `Azure Speech vi-VN`) & S3 CDN
- **Mã chức năng**: `FR-305.2` | **Scope**: `Backend Integrations (app/integrations/tts.py)`
- **Nghiệp vụ chi tiết**:
  - Triển khai `TTSProviderAdapter`:
    - **Primary**: Amazon Polly Neural (`en-US`, `ja-JP`, `ko-KR`, `zh-CN`, `fr-FR`, `de-DE`, `es-ES`...) chọn `VoiceId` theo `rooms.tts_voice_config`.
    - **Azure AI Speech Neural (`southeastasia` Singapore)**: Gọi REST endpoint `POST https://{region}.tts.speech.microsoft.com/cognitiveservices/v1` bằng **`httpx.AsyncClient`** (SSML + `audio-24khz-48kbitrate-mono-mp3`, không dùng C++ SDK) cho **Tiếng Việt (`vi-VN-HoaiMyNeural` / `vi-VN-NamMinhNeural`)**, `th-TH`, `id-ID`; key lưu trên AWS Secrets Manager (`AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`); tự động hạ `Text-only` (`0 Cr`) khi lỗi `5xx`/timeout hoặc chưa cấu hình.
  - Upload `.mp3` lên S3 (`s3://.../tts/{roomId}/{segmentId}_{lang}.mp3`, Lifecycle 24h) -> trả CloudFront CDN URL `< 400ms`.
- **Tiêu chí nghiệm thu (AC)**: Hỗ trợ phát giọng đọc Nam/Nữ chuẩn cho cả Tiếng Việt `vi-VN` lẫn các ngôn ngữ quốc tế trong `< 400ms`; offline mock hoạt động ở `ENV=local/test`.

### `TASK-AI-07`: Đánh dấu Chốt câu & Cắt tỉa Bộ đệm Âm thanh (Commit Segment)
- **Mã chức năng**: `FR-306.1` | **Scope**: `Backend AI Pipeline & Redis`
- **Nghiệp vụ chi tiết**:
  - Khi một câu `Final` hoàn tất dịch và tạo TTS (nếu có):
    1. Cập nhật `last_committed_seq = seq_end` lên Redis.
    2. Cắt tỉa các frame âm thanh cũ hơn `last_committed_seq` trong Redis Stream `room:{roomId}:audio_buffer` để giải phóng RAM.
    3. Đảm bảo khi container crash thì container mới không bao giờ dịch lặp lại câu này.
- **Tiêu chí nghiệm thu (AC)**: Cập nhật vị trí chốt nguyên tử trên Redis trong $< 2ms$.

### `TASK-AI-08`: Lưu Đệm Phụ đề Trực tiếp vào Redis List (Live Transcripts Buffer)
- **Mã chức năng**: `FR-306.2` | **Scope**: `Backend Services & Redis`
- **Nghiệp vụ chi tiết**:
  - Đẩy câu `Final` hoàn chỉnh vào Redis List:
    ```text
    RPUSH room:{roomId}:live_transcripts <JSON_PAYLOAD>
    ```
  - Payload chứa: `segmentId`, `seqStart`, `seqEnd`, `startTimeMs`, `endTimeMs`, `sourceText`, `translations`, `ttsAudioUrls`.
  - Phục vụ người nghe vào muộn hoặc F5 trang tải lại toàn bộ nội dung từ đầu buổi.
- **Tiêu chí nghiệm thu (AC)**: Lưu trữ non-blocking, không làm tăng độ trễ luồng phát sóng.

### `TASK-AI-09`: Phát tán Bản dịch Đa kênh qua AWS AppSync Events
- **Mã chức năng**: `FR-401.1` | **Scope**: `Backend Integrations & AWS AppSync`
- **Nghiệp vụ chi tiết**:
  - Phát bản tin JSON `SUBTITLE_SEGMENT` vào đúng kênh ngôn ngữ:
    - Kênh: `rooms/{roomId}/lang/{langCode}`.
    - Payload chứa câu dịch, trạng thái `isFinal`, và `ttsAudioUrl` (nếu có).
  - Phân tán đồng thời tới tối đa 1.000 người nghe đang kết nối với độ trễ fan-out $< 50ms$.
- **Tiêu chí nghiệm thu (AC)**: Toàn bộ người nghe kênh ngôn ngữ tương ứng nhận được phụ đề tức thì.

### `TASK-AI-10`: Người nghe Bật / Tắt Nghe Giọng đọc Dịch (TTS Toggle API)
- **Mã chức năng**: `FR-404.1` | **Scope**: `Backend API & Redis`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/{roomId}/tts-toggle`.
  - Nhận `lang`, `enabled: boolean`.
  - Nếu `enabled == true`: Gọi `HINCRBY room:{roomId}:tts_count {lang} 1`.
  - Nếu `enabled == false`: Gọi `HINCRBY room:{roomId}:tts_count {lang} -1` (đảm bảo không bao giờ âm dưới 0).
  - Giúp backend biết chính xác khi nào cần gọi Polly, khi nào cần ngắt để tiết kiệm chi phí.
- **Tiêu chí nghiệm thu (AC)**: Biến đếm trên Redis tăng/giảm chính xác ngay khi người nghe bấm nút loa.

### `TASK-AI-11`: Hàng đợi Phát Âm thanh Thích ứng tại Trình duyệt (Adaptive Audio Queue)
- **Mã chức năng**: `FR-405.1` | **Scope**: `Frontend WebAudio`
- **Nghiệp vụ chi tiết**:
  - Xây dựng class `AdaptiveAudioQueue` tại trình duyệt người nghe:
    - Nhận danh sách các `ttsAudioUrl` của các câu Final.
    - Tải trước (Pre-fetch) file audio vào hàng đợi phát tuần tự bằng WebAudio Context.
    - **Thuật toán tăng tốc thông minh**:
      - Nếu hàng đợi có 0 hoặc 1 câu: Phát với tốc độ chuẩn `1.0x`.
      - Nếu hàng đợi bị dồn $\ge 2$ câu (do diễn giả nói nhanh): Tự động tăng tốc độ phát lên `1.15x` – `1.25x` (giữ nguyên cao độ giọng nói bằng `preservesPitch = true`).
      - Khi hàng đợi hết dồn: Tự động đưa tốc độ phát về lại `1.0x`.
- **Tiêu chí nghiệm thu (AC)**: Giọng đọc phát mượt mà, không bao giờ phát đè 2 câu lên nhau, không bị tụt hậu xa so với diễn giả.

---

## Phân hệ 9: Đo đếm & Tính cước Theo Từng Giây (Per-Second Credit Billing Engine)

### `TASK-MET-01`: Đo đếm Lưu lượng Chính xác Theo Từng Giây (`1s Redis Metering`)
- **Mã chức năng**: `FR-505.1` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Vòng lặp mỗi **1 giây** thu thập chính xác mức sử dụng thực tế của từng phòng `ACTIVE` (không làm tròn block 10s):
    - `audio_seconds`: Số giây có tiếng nói thực tế (`vad_flag == 1`, bước `0.1s`, tính cả 2 luồng ở chế độ `1-on-1`).
    - `mt_chars` & `tts_chars`: Ký tự dịch máy & ký tự TTS phát sinh trong giây đó.
    - `listener_seconds`: Tổng người-giây kết nối (cộng số lượng listener đang online tại giây đó).
  - Loại trừ `100%` mọi giây/ký tự phát sinh khi AI provider trả lỗi `5xx` (`0 Cr`).
- **Tiêu chí nghiệm thu (AC)**: Nói `3.4s` hay nghe `23s` chỉ tính đúng số giây thực tế đó.

### `TASK-MET-02`: Quy đổi Credit Theo Công thức Cost-Plus (`1 USD = 100 Credits`)
- **Mã chức năng**: `FR-506.1` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Áp dụng biểu giá Credit (đảm bảo Gross Margin `>= 55% – 65%`, cấu hình động từ DB/Redis):
    - $\text{Credits} = (\frac{S_{\text{audio}}}{60} \times 5.5) + (\frac{C_{\text{mt}}}{1000} \times 3.5) + (\frac{C_{\text{tts}}}{1000} \times 4.0) + (\frac{S_{\text{listener}}}{6000} \times 0.5)$
  - Lưu chính xác 2 chữ số thập phân (`NUMERIC(12, 2)`), đồng thời tính song song AWS COGS USD nội bộ cho Admin.
- **Tiêu chí nghiệm thu (AC)**: Khớp 100% biểu giá hiện hành, sai số `< 0.01 Cr`.

### `TASK-MET-03`: Khấu trừ 3 Ngăn Nguyên tử (`Promo -> Plan -> Top-up`) & Batch ACID Flush
- **Mã chức năng**: `FR-506.2` | **Scope**: `Backend Database Transaction & Redis Lua`
- **Nghiệp vụ chi tiết**:
  - Trừ realtime mỗi **1 giây** trên Redis `wallet:{hostId}:credits` qua Lua script nguyên tử (an toàn khi Host mở nhiều phòng đồng thời theo `maxConcurrentRooms`).
  - Flush nguyên tử xuống PostgreSQL định kỳ mỗi **15 giây** VÀ **ngay lập tức** khi `PAUSE` / `END_ROOM` / `QUOTA_EXHAUSTED`:
    1. Khóa dòng `wallets` trừ theo thứ tự `promo_credits -> plan_credits -> topup_credits` (`CHECK >= 0`).
    2. Ghi `usage_ledger` kèm `duration_seconds`, `audio_seconds`, `listener_seconds`, `credits_deducted`, `deducted_breakdown`.
    3. Cập nhật `rooms.total_credits_used`. Khi `END_ROOM`, ghi 1 dòng tổng hợp `ROOM_USAGE` vào `credit_ledger`.
- **Tiêu chí nghiệm thu (AC)**: Không bao giờ âm cả 3 ngăn; tổng `usage_ledger` khớp 100% `credit_ledger`.

### `TASK-MET-04`: Phát Bản tin `BILLING_TICK` (3 Ngăn Credit & Burn Rate) Mỗi Giây
- **Mã chức năng**: `FR-504.2` | **Scope**: `Backend WebSocket & Redis`
- **Nghiệp vụ chi tiết**:
  - Gửi gói JSON `BILLING_TICK` (`totalCredits`, `buckets: {promo, plan, topup}`, `sessionCreditsUsed`, `burnRatePerMinCredits`, `estimatedRemainingMinutes`, `warningLevel`) về màn hình Host.
- **Tiêu chí nghiệm thu (AC)**: Đồng hồ Credit nhảy mượt, phản ánh đúng mức tiêu thụ thực tế.

### `TASK-MET-05`: Xử lý Cảnh báo Số dư Thấp dưới 5 Phút (`LOW_BALANCE_WARNING`)
- **Mã chức năng**: `FR-507.1` | **Scope**: `Backend Billing & Frontend Modal`
- **Nghiệp vụ chi tiết**:
  - Khi `estimatedRemainingMinutes < 5.0` phút -> gửi `LOW_BALANCE_WARNING` + mở Popup mua nhanh `PACK_S/M/L` ngay trong phòng không ngắt âm thanh.
- **Tiêu chí nghiệm thu (AC)**: Cảnh báo chính xác tới từng giây.

### `TASK-MET-06`: Tự động Hạ cấp Dịch vụ Tắt TTS khi Dưới 1 Phút (`GRACEFUL_DEGRADATION`)
- **Mã chức năng**: `FR-507.3` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Khi `estimatedRemainingMinutes < 1.0` phút VÀ gói có `allowAutoDegradeTts` VÀ `wallets.auto_degrade_tts == true` -> đặt `tts_count = 0`, ngắt TTS, chỉ giữ phụ đề text.
- **Tiêu chí nghiệm thu (AC)**: Kéo dài thời gian phiên họp mà không mất phụ đề.

### `TASK-MET-07`: Tự động Đóng Phòng An toàn khi Hết Credit (`QUOTA_EXHAUSTED`)
- **Mã chức năng**: `FR-507.4` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Khi `total_credits <= 0.00` (hoặc gói `FREE` đạt giới hạn 15 phút/phòng): đợi dứt câu `Final`, flush chính xác phần giây lẻ cuối cùng, ghi dòng `ROOM_USAGE` vào `credit_ledger`, đóng phòng và kích hoạt đóng gói S3.
- **Tiêu chí nghiệm thu (AC)**: Không mất câu cuối, không âm Credit.

---

## Phân hệ 10: Biên bản Dịch thuật & AI Tóm tắt qua Bedrock (Transcripts & AI Summary)

### `TASK-TRN-01`: Đồng bộ Lịch sử Phụ đề Trực tiếp (Live Transcripts Sync)
- **Mã chức năng**: `FR-402.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/rooms/{roomId}/transcripts`.
  - Query params: `lang` (mã ngôn ngữ), `afterSeq` (mặc định 0), `limit` (mặc định 200).
  - Nếu phòng đang `ACTIVE`: Đọc danh sách các câu từ Redis List `room:{roomId}:live_transcripts`.
  - Nếu phòng đã `ENDED`: Đọc nội dung từ file S3 `master.json`.
  - Trả về danh sách các câu đã chốt sắp xếp theo thứ tự thời gian.
- **Tiêu chí nghiệm thu (AC)**: Người nghe F5 trang đọc lại toàn bộ nội dung từ đầu buổi trong $< 50ms$.

### `TASK-TRN-02`: Worker Đóng gói File master.json trên S3 khi Kết thúc Phòng
- **Mã chức năng**: `FR-406.1` | **Scope**: `Backend Background Worker & S3`
- **Nghiệp vụ chi tiết**:
  - Khi phòng nhận trạng thái `ENDED`:
    1. Đọc toàn bộ các câu từ Redis List `room:{roomId}:live_transcripts`.
    2. Đóng gói file chuẩn `master.json` chứa: metadata phòng, thời gian bắt đầu/kết thúc, tổng số câu, danh sách chi tiết từng câu kèm `translations` của toàn bộ ngôn ngữ đích.
    3. Upload lên S3: `s3://.../transcripts/{roomId}/master.json` (S3 Lifecycle lưu trữ 90 ngày).
- **Tiêu chí nghiệm thu (AC)**: File `master.json` chuẩn cấu trúc JSON, lưu trữ đầy đủ nội dung phiên dịch.

### `TASK-TRN-03`: Worker Xuất Biên bản Họp Định dạng Văn bản (.txt / .md)
- **Mã chức năng**: `FR-406.2` | **Scope**: `Backend Background Worker`
- **Nghiệp vụ chi tiết**:
  - Từ dữ liệu `master.json`, sinh file `.txt` ghi chép cuộc họp:
    - Định dạng: `[HH:MM:SS] Diễn giả: Nội dung câu nói`.
    - Hỗ trợ xuất dạng đơn ngữ hoặc song ngữ đối chiếu (Câu gốc + Câu dịch bên dưới).
    - Upload lên S3: `s3://.../transcripts/{roomId}/transcript_{lang}.txt`.
- **Tiêu chí nghiệm thu (AC)**: File văn bản rõ ràng, dễ đọc, ngắt dòng chuẩn xác.

### `TASK-TRN-04`: Worker Xuất Phụ đề Video Chuẩn .srt và .vtt
- **Mã chức năng**: `FR-406.3` | **Scope**: `Backend Background Worker`
- **Nghiệp vụ chi tiết**:
  - Sinh file phụ đề SubRip (`.srt`) cho từng ngôn ngữ:
    ```text
    1
    00:01:20,000 --> 00:01:24,500
    Chúng tôi đã chuyển đổi cơ sở dữ liệu sang kiến trúc NoSQL.
    ```
  - Sinh file WebVTT (`.vtt`) tối ưu phát trực tiếp trên trình duyệt web.
  - Upload lên S3: `subtitles_{lang}.srt` và `subtitles_{lang}.vtt`.
- **Tiêu chí nghiệm thu (AC)**: Mốc thời gian chuẩn xác tới mili-giây, khớp hoàn toàn với video quay lại buổi họp.

### `TASK-TRN-05`: Worker Xuất Bảng Đối chiếu Đa Ngôn ngữ Định dạng .csv
- **Mã chức năng**: `FR-406.4` | **Scope**: `Backend Background Worker`
- **Nghiệp vụ chi tiết**:
  - Sinh file bảng tính `.csv` (mã hóa UTF-8 with BOM để mở Excel không lỗi font):
    - Cột 1: `Timestamp` (`HH:MM:SS`).
    - Cột 2: `Speaker` (Tên diễn giả).
    - Cột 3: `Source Text` (Ngôn ngữ gốc).
    - Cột 4 .. N: Các cột ngôn ngữ đích tương ứng (`English`, `Japanese`, `Vietnamese`...).
  - Upload lên S3: `transcript_comparison.csv`.
- **Tiêu chí nghiệm thu (AC)**: Mở bằng Microsoft Excel và Google Sheets hiển thị tiếng Việt và tiếng Nhật chuẩn font.

### `TASK-TRN-06`: API Tải & Xóa File Biên bản Dịch (Phân quyền Gói, Listener & GDPR)
- **Mã chức năng**: `FR-406.5`, `FR-107` | **Scope**: `Backend API & S3 Presigned URL`
- **Nghiệp vụ chi tiết**:
  - `GET /api/v1/rooms/{roomId}/transcripts/export`: kiểm tra `format` thuộc `entitlements.exportFormats` (kèm 14 ngày ân hạn khi hạ gói) và quyền Listener (`allow_listener_download`), trả S3 Presigned URL 60 phút.
  - `DELETE /api/v1/rooms/{roomId}/transcripts` (chỉ Host): xóa toàn bộ file S3 của phòng & cập nhật metadata (GDPR/PDPA).
- **Tiêu chí nghiệm thu (AC)**: Chặn tải sai quyền gói/Listener với `403`; xóa S3 hoàn tất `< 5s`.

### `TASK-TRN-07`: Host Kích hoạt Tóm tắt Cuộc họp AI qua Amazon Bedrock (`15 Cr` / `25 Cr`)
- **Mã chức năng**: `FR-407.1` | **Scope**: `Backend API & Amazon Bedrock`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/{roomId}/summary` (chỉ Host, kiểm tra `entitlements.aiSummaryLevel`: `PRO` ngôn ngữ gốc `15 Cr`, `BUSINESS+` đa ngôn ngữ `25 Cr`).
  - Đọc `master.json` từ S3, gọi Bedrock (`Claude 3.5 Haiku` / `Nova Lite`), trừ Credit 1 lần qua thứ tự 3 ngăn `Promo -> Plan -> Top-up` + ghi `credit_ledger (AI_SUMMARY)`, lưu `summary.json` lên S3 và gửi SES notification khi xong.
- **Tiêu chí nghiệm thu (AC)**: Sinh tóm tắt cuộc họp 1 giờ `< 8s`; các lần xem lại sau = `0 Cr`.

### `TASK-TRN-08`: Cơ chế Cache $0 cho Bản Tóm tắt AI đã Tạo
- **Mã chức năng**: `FR-407.2` | **Scope**: `Backend Services`
- **Nghiệp vụ chi tiết**:
  - Khi Host bấm lại nút "Tóm tắt AI" hoặc khi người dùng xem lại tóm tắt:
    - Kiểm tra `room_transcripts.summary_status == 'READY'`.
    - Trả về ngay nội dung từ file S3 `summary.json`.
    - **Chi phí bằng $0**: Tuyệt đối không gọi lại Bedrock, không trừ thêm bất kỳ đồng nào trong ví của Host.
- **Tiêu chí nghiệm thu (AC)**: Lần xem thứ 2 trở đi phản hồi trong $< 50ms$ với chi phí `$0.00`.

### `TASK-TRN-09`: Tự động Dịch Bản Tóm tắt sang Toàn bộ Ngôn ngữ Đích
- **Mã chức năng**: `FR-407.3` | **Scope**: `Backend AI Services`
- **Nghiệp vụ chi tiết**:
  - Sau khi Bedrock sinh xong bản tóm tắt bằng ngôn ngữ nguồn:
    - Gọi Amazon Translate dịch nội dung tóm tắt (overview, takeaways, action items) sang toàn bộ các ngôn ngữ trong `target_langs`.
    - Lưu cấu trúc đa ngôn ngữ vào `summary.json` (`summariesByLang: { "vi-VN": {...}, "en-US": {...} }`).
- **Tiêu chí nghiệm thu (AC)**: Người nghe nước nào đọc được bản tóm tắt chuẩn ngôn ngữ của nước đó.

### `TASK-TRN-10`: Xem và Tải Bản Tóm tắt AI theo Ngôn ngữ Tùy chọn
- **Mã chức năng**: `FR-407.4` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/rooms/{roomId}/summary`.
  - Query params: `lang` (mặc định ngôn ngữ nguồn).
  - Trả về JSON tóm tắt của ngôn ngữ được chọn.
  - Hỗ trợ tải về dưới dạng file Markdown `.md` hoặc văn bản `.txt`.
- **Tiêu chí nghiệm thu (AC)**: Hiển thị đẹp mắt trên giao diện, hỗ trợ tải file tóm tắt nhanh chóng.

---

## Phân hệ 11: Hạ tầng, Độ sẵn sàng cao & Quản trị Hệ thống (HA, Failover & Admin Portal)

### `TASK-OPS-01`: Xử lý Chuyển giao SIGTERM Không Mất Từ khi Deploy (0ms Handover)
- **Mã chức năng**: `FR-602.1` | **Scope**: `Backend Lifespan & ECS Fargate`
- **Nghiệp vụ chi tiết**:
  - Khi container ECS Fargate nhận tín hiệu `SIGTERM`:
    1. Đánh dấu container ở trạng thái `DRAINING`. Không nhận thêm phòng mới từ ALB.
    2. Với các kết nối Ingest WebSocket đang có: Đợi diễn giả dứt câu hiện tại (`isFinal = true`).
    3. Gửi sự kiện Text Control qua WebSocket:
       ```json
       {
         "event": "PREPARE_HANDOVER",
         "resumeFromSeq": 1450,
         "reason": "TASK_DRAINING"
       }
       ```
    4. Client nhận sự kiện, lập tức mở kết nối WebSocket mới sang container dự phòng. Khi kết nối mới sẵn sàng, Client chuyển luồng gửi sang kết nối mới và đóng kết nối cũ.
- **Tiêu chí nghiệm thu (AC)**: Rolling update phiên bản backend mới trong giờ cao điểm không làm rớt từ nói nào của Host.

### `TASK-OPS-02`: Tự Động Phục Hồi Luồng Nói Sau Khi Container Crash (Crash Replay Failover)
- **Mã chức năng**: `FR-601.1` | **Scope**: `Backend & Client Failover`
- **Nghiệp vụ chi tiết**:
  - Trường hợp container đang xử lý bị Crash đột ngột (OOM, lỗi phần cứng):
    1. Speaker Client phát hiện mất bản tin ACK trong `300ms` -> Tự động kết nối lại qua ALB sang container khác.
    2. Container mới đọc vị trí đã chốt an toàn gần nhất từ Redis `last_committed_seq`.
    3. Trả về cho Client: `RESUME_FROM_SEQ = last_committed_seq + 1`.
    4. Client lấy các frame tương ứng từ **Client Local Ring Buffer 5s** và bơm tốc độ cao (burst) lên container mới.
    5. Container mới bơm tiếp vào Transcribe để hoàn thiện câu đang nói dở.
    6. 1.000 người nghe không bị rớt mạng và không nhận thấy sự cố.
- **Tiêu chí nghiệm thu (AC)**: Phục hồi xong trong $< 500ms$, không lặp lại câu đã dịch.

### `TASK-OPS-03`: Endpoint Deep Health Check cho ALB Target Group
- **Mã chức năng**: `FR-603.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/health`.
  - Kiểm tra sâu:
    - PostgreSQL: Thực thi `SELECT 1` kiểm tra pool kết nối.
    - Redis: Gửi `PING` kiểm tra độ trễ (latency $< 5ms$).
    - AWS Credentials: Kiểm tra quyền gọi Transcribe/Translate/Polly.
  - Nếu tất cả OK -> Trả về `200 OK`.
  - Nếu PostgreSQL hoặc Redis mất kết nối -> Trả về `503 Service Unavailable` để ALB tự động rút container ra khỏi Target Group.
- **Tiêu chí nghiệm thu (AC)**: Phản hồi trong $< 10ms$, cảnh báo chính xác khi phụ thuộc bị ngắt.

### `TASK-OPS-04`: Bảng Điều khiển Giám sát CloudWatch & Cảnh báo Slack/SNS
- **Mã chức năng**: `FR-603.2` | **Scope**: `AWS CloudWatch & DevOps`
- **Nghiệp vụ chi tiết**:
  - Thiết lập CloudWatch Custom Metrics:
    - `ActiveRoomsCount`, `TotalListenersCount`.
    - `SttLatencyP95`, `MtLatencyP95`, `TtsLatencyP95`, `EndToEndLatencyP95`.
    - `BillingDeductionErrorsCount`.
  - Cấu hình CloudWatch Alarm: Nếu `EndToEndLatencyP95 > 1500ms` trong 3 phút liên tục -> Gửi cảnh báo khẩn cấp qua SNS tới kênh Slack cứu hộ.
- **Tiêu chí nghiệm thu (AC)**: Cảnh báo tự động kích hoạt khi hệ thống có dấu hiệu nghẽn mạng hoặc quá tải.

### `TASK-OPS-05`: API Admin Quản trị Bảng Giá Cước Hệ thống Động (Pricing Config)
- **Mã chức năng**: `FR-604.1` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - Endpoint Admin `GET /api/v1/admin/pricing` & `PUT /api/v1/admin/pricing`.
  - Cho phép Admin điều chỉnh đơn giá cước STT ($/phút), MT ($/triệu ký tự), TTS ($/triệu ký tự), Người nghe ($/giờ).
  - Lưu cấu hình vào Redis và PostgreSQL. Có hiệu lực ngay lập tức với các chu kỳ tính cước tiếp theo mà không cần khởi động lại máy chủ.
- **Tiêu chí nghiệm thu (AC)**: Đổi bảng giá xong, chu kỳ 10s sau tính theo giá mới ngay lập tức.

### `TASK-OPS-06`: API Admin Quản lý Mã Khuyến Mãi (Admin Promo Codes)
- **Mã chức năng**: `FR-604.2` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/admin/promos`: Tạo mã khuyến mãi mới (Code, số tiền tặng, giới hạn số lượt, ngày hết hạn).
  - Endpoint `GET /api/v1/admin/promos`: Danh sách các mã khuyến mãi kèm thống kê số lượt đã dùng và tổng tiền đã tặng.
  - Endpoint `PATCH /api/v1/admin/promos/{id}/toggle`: Bật/Tắt hiệu lực mã khuyến mãi.
- **Tiêu chí nghiệm thu (AC)**: Quản lý mã khuyến mãi trực quan, kiểm soát chặt chẽ ngân sách marketing.

### `TASK-OPS-07`: API Admin Điều chỉnh Số dư Ví Thủ công có Audit Log
- **Mã chức năng**: `FR-604.4` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/admin/wallets/{hostId}/adjust`.
  - Nhận `amount` (dương để cộng bù tiền sự cố, âm để thu hồi), `reason` (lý do bắt buộc).
  - Cập nhật số dư trong `wallets`.
  - Tạo bản ghi `payment_transactions (type = 'ADMIN_ADJUSTMENT', amount = amount, status = 'SUCCEEDED', raw_webhook_meta = { admin_id, reason })`.
- **Tiêu chí nghiệm thu (AC)**: Mọi thao tác can thiệp tài chính đều có dấu vết kiểm toán (Audit Trail) rõ ràng.

### `TASK-OPS-08`: API Admin Thống kê Doanh thu, COGS & Gross Margin Toàn sàn (`ADM-01`)
- **Mã chức năng**: `FR-604` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/admin/stats/overview` (lọc ngày/tuần/tháng): tổng doanh thu Stripe/VietQR, tổng Credit cấp/dùng/hết hạn (`Breakage`), tổng AWS/Azure COGS, tính **Gross Margin %** (cảnh báo `< 55%`), số phòng `ACTIVE`, người nghe online và DAU/MAU.
- **Tiêu chí nghiệm thu (AC)**: Số liệu khớp 100% `payment_transactions` và `usage_ledger`.

### `TASK-OPS-09`: Migration `0003_admin_portal`, Dependency `require_admin` & Audit Log Bất biến
- **Mã chức năng**: `FR-604`, `FR-609` | **Scope**: `Backend Models, Security & Alembic`
- **Nghiệp vụ chi tiết**:
  - Migration tạo bảng `pricing_configs` (lưu phiên bản đơn giá Credit + tỷ giá VND) và `admin_audit_logs` (append-only: `admin_id`, `action`, `target_type`, `target_id`, `before_json`, `after_json`, `reason`, `ip_address`, `created_at`).
  - Dependency `require_admin` kiểm tra `user.role == 'ADMIN'`; helper ghi Audit Log bắt buộc `reason` trên mọi endpoint ghi của `/api/v1/admin/*`.
- **Tiêu chí nghiệm thu (AC)**: Host thường gọi `/api/v1/admin/*` bị chặn `403 Forbidden`; mọi thao tác ghi đều có bản ghi `admin_audit_logs`.

### `TASK-OPS-10`: API Admin Quản lý Host 360°, Khóa Tài khoản, Gán Gói B2B & Anti-Abuse (`ADM-02`, `ADM-03`)
- **Mã chức năng**: `FR-605`, `FR-606` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - `GET /admin/hosts` & `GET /admin/hosts/{hostId}` (360° view).
  - `POST /admin/hosts/{hostId}/status` (`SUSPENDED` -> `GlobalSignOut` + đóng an toàn phòng đang chạy); `POST /admin/hosts/{hostId}/subscription` (gán/gia hạn gói tay B2B).
  - `GET/PUT /admin/anti-abuse/domains` (quản lý blocklist email rác) & `GET/PUT /admin/{plans,credit-packs}/{code}` (sửa gói/entitlements + invalidate cache Redis).
- **Tiêu chí nghiệm thu (AC)**: Khóa tài khoản ngắt phiên tức thì; đổi `entitlements` có hiệu lực `< 1s`.

### `TASK-OPS-11`: API Admin Tra cứu Giao dịch & Khớp lệnh VietQR Thủ công (`ADM-04`)
- **Mã chức năng**: `FR-607` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - `GET /api/v1/admin/transactions` (tra cứu toàn sàn theo cổng, trạng thái, `tx_id`/`txCode`).
  - `POST /api/v1/admin/transactions/{txId}/reconcile`: Admin nhập `bankRefCode` và `reason` để khớp tay các giao dịch VietQR khách quên ghi đúng mã `TRxxxxxx` (khóa dòng `FOR UPDATE` idempotent, kích hoạt gói hoặc cộng `topup_credits` + ghi `credit_ledger` & `admin_audit_logs`).
- **Tiêu chí nghiệm thu (AC)**: Không thể khớp trùng 1 giao dịch 2 lần.

### `TASK-OPS-12`: API Admin Giám sát Phòng Live, Force End Room & AI Provider Kill-switch (`ADM-06`)
- **Mã chức năng**: `FR-609` | **Scope**: `Backend Admin API & Redis`
- **Nghiệp vụ chi tiết**:
  - `GET /api/v1/admin/rooms/live` & `POST /api/v1/admin/rooms/{roomId}/force-end` (`reason` -> đóng khẩn cấp phòng treo/vi phạm, flush giây lẻ cuối cùng).
  - `GET/PUT /api/v1/admin/ai-providers/killswitch`: theo dõi tỷ lệ lỗi `5xx` của AWS AI & Azure Speech (`vi-VN`), bật/tắt cờ `ai:provider:killswitch` trên Redis để hạ nhanh ngôn ngữ/provider sang `Text-only`.
- **Tiêu chí nghiệm thu (AC)**: Force End đóng phòng `< 1s`; Kill-switch áp dụng ngay câu nói kế tiếp.

### `TASK-OPS-13`: API Admin Tra cứu Nhật ký Kiểm toán Bất biến (`ADM-06`)
- **Mã chức năng**: `FR-609` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - `GET /api/v1/admin/audit-logs` (phân trang, lọc theo `adminId`, `action`, `targetType`, khoảng thời gian, trả `beforeJson`/`afterJson`/`reason`/`ipAddress`).
- **Tiêu chí nghiệm thu (AC)**: Chỉ đọc (read-only), không có endpoint sửa/xóa audit log.

---

## Phân hệ 12: Màn hình Giao diện Người dùng Web (Next.js 15 UI Screens)

### `TASK-UI-01`: SCR-01 Form Đăng ký Host kèm Password Meter & OTP Input `[DONE]`
- **Mã chức năng**: `SCR-01.1` | **Scope**: `Frontend Next.js App Router`
- **Nghiệp vụ chi tiết**:
  - Trang `/register`:
    - Form nhập Email, Họ tên, Mật khẩu.
    - Component `PasswordMeter`: Đo độ mạnh mật khẩu theo thời gian thực (Đỏ/Vàng/Xanh).
    - Nút Đăng ký gọi API `TASK-AUTH-01`.
  - Trang xác thực `/verify-otp`:
    - Component `OtpInput6`: 6 ô nhập mã OTP tự động nhảy tiêu điểm (auto-focus), tự động dán từ clipboard.
    - Đồng hồ đếm ngược 60 giây và nút Gửi lại mã OTP (`TASK-AUTH-03`).
- **Tiêu chí nghiệm thu (AC)**: Form validate mượt mà bằng Zod, tự động chuyển trang khi nhập xong OTP 6 số.

### `TASK-UI-02`: SCR-01 Form Đăng nhập Email/Password & Social SSO `[DONE]` *(Email/Password; SSO chờ `TASK-AUTH-05..06`)*
- **Mã chức năng**: `SCR-01.2` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/login`:
    - Form nhập Email và Mật khẩu, checkbox "Ghi nhớ đăng nhập".
    - Cụm nút Social SSO: Đăng nhập với Google, Đăng nhập với Apple.
    - Link chuyển tới màn hình Quên mật khẩu và Đăng ký.
- **Tiêu chí nghiệm thu (AC)**: Đăng nhập thành công lưu token và chuyển hướng ngay về `/dashboard`.

### `TASK-UI-03`: SCR-01 Form Quên mật khẩu & Đặt lại mật khẩu `[DONE]`
- **Mã chức năng**: `SCR-01.3` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/forgot-password`: Nhập email nhận mã OTP khôi phục.
  - Trang `/reset-password`: Nhập mã OTP nhận được + Mật khẩu mới + Xác nhận mật khẩu mới.
- **Tiêu chí nghiệm thu (AC)**: Đặt lại mật khẩu xong tự động chuyển về trang Đăng nhập kèm thông báo thành công.

### `TASK-UI-04`: Trang Hồ sơ Cá nhân, Cài đặt & Tải lên Avatar
- **Mã chức năng**: `SCR-02.1` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/dashboard/profile`:
    - Khu vực Avatar: Bấm chọn ảnh từ máy tính -> Gọi API lấy Presigned URL -> Upload trực tiếp lên S3 -> Cập nhật avatar tức thì.
    - Form Thông tin cá nhân: Họ tên, số điện thoại, múi giờ.
    - Form Cài đặt Dịch thuật mặc định: Chọn ngôn ngữ nguồn và các ngôn ngữ đích quen dùng.
    - Form Thông tin Xuất hóa đơn VAT: Tên công ty, Mã số thuế, Địa chỉ công ty.
    - Form Đổi mật khẩu tài khoản.
- **Tiêu chí nghiệm thu (AC)**: Upload avatar mượt mà, lưu thông tin hóa đơn chuẩn xác.

### `TASK-UI-05`: SCR-02 Host Dashboard & Thẻ Ví Nạp tiền Nhanh
- **Mã chức năng**: `SCR-02.2` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/dashboard`:
    - **Thẻ Số dư Ví (Wallet Card)**: Hiển thị số dư khả dụng to bản, cờ Auto Top-up, nút **"Nạp tiền nhanh"** mở Modal nạp tiền.
    - **Nút "Tạo phòng mới"** nổi bật.
    - **Bảng Phòng gần đây**: Hiển thị danh sách các phòng vừa diễn ra, trạng thái, thời lượng, chi phí và nút vào xem Lịch sử / Tóm tắt AI.
- **Tiêu chí nghiệm thu (AC)**: Số dư ví cập nhật tức thì khi nạp tiền thành công.

### `TASK-UI-06`: SCR-02 Modal Tạo Phòng Dịch Đa Ngôn ngữ
- **Mã chức năng**: `SCR-02.3` | **Scope**: `Frontend Next.js Component`
- **Nghiệp vụ chi tiết**:
  - Modal tạo phòng:
    - Tiêu đề phòng họp.
    - Chế độ: `1-on-1` hoặc `Broadcast Hội thảo`.
    - Dropdown chọn Ngôn ngữ nguồn (gốc).
    - Grid chọn tối đa 10 Ngôn ngữ đích kèm cờ quốc gia.
    - Ô nhập Mật khẩu phòng (tùy chọn).
    - Checkbox "Cho phép người nghe tải biên bản dịch" và "Tự động tắt TTS khi cạn ví".
    - Dropdown chọn Bộ từ điển chuyên ngành.
    - **Thanh đo chi phí ước tính**: Hiển thị tốc độ đốt tiền ước tính ($/phút) và cảnh báo ngay nếu số dư ví không đủ 10 phút.
- **Tiêu chí nghiệm thu (AC)**: Khóa nút "Mở phòng" nếu ví không đủ tiền và hiển thị nút nạp tiền trực tiếp.

### `TASK-UI-07`: SCR-03 Màn hình Host Studio (Phát biểu & Điều khiển Live)
- **Mã chức năng**: `SCR-03.1` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/rooms/[roomId]/host`:
    - **Thanh Trạng thái & Đồng hồ Cước**: Số người đang nghe online, tốc độ đốt tiền ($/phút), số phút còn lại dự kiến.
    - **Khu vực Thu âm Micro**:
      - Nút Bật/Tắt Mic to bản.
      - Canvas biểu đồ sóng âm (Waveform) 60fps kèm đèn VAD.
      - Nút Tạm dừng và Kết thúc phòng.
    - **Khung Phụ đề Trực tiếp**: Hiển thị câu đang nói dở (Partial) và chốt (Final) song song với bản dịch.
    - **Popup Nạp tiền Nhanh tại chỗ (In-room Top-up)**: Tự động bật lên khi nhận cảnh báo số dư thấp dưới 5 phút mà không làm gián đoạn bài nói.
- **Tiêu chí nghiệm thu (AC)**: Giao diện trực quan, sóng âm chuyển động mượt mà, đồng hồ cước nhảy đều đặn.

### `TASK-UI-08`: SCR-03 Modal Chia sẻ Phòng Họp & Mã QR Chiếu Hội trường
- **Mã chức năng**: `SCR-03.2` | **Scope**: `Frontend Next.js Component`
- **Nghiệp vụ chi tiết**:
  - Modal chiếu toàn màn hình (Full-screen Projector Mode):
    - Mã QR Code kích thước lớn sắc nét để người ngồi cuối hội trường cũng quét được.
    - Mã phòng 6 số to rõ ràng.
    - Nút Copy Link tham gia nhanh.
- **Tiêu chí nghiệm thu (AC)**: Hiển thị đẹp mắt trên máy chiếu và màn hình LED hội trường.

### `TASK-UI-09`: SCR-04 Màn hình Người nghe Di động (Mobile Listener View)
- **Mã chức năng**: `SCR-04.1` | **Scope**: `Frontend Next.js (Mobile Optimized)`
- **Nghiệp vụ chi tiết**:
  - Trang `/r/[roomCode]`:
    - Thiết kế tối ưu cho điện thoại di động (Mobile-first).
    - **Không cần đăng nhập**: Tự động kết nối vào nghe.
    - **Thanh Công cụ Nổi (Floating Bar)**:
      - Dropdown đổi ngôn ngữ nhận phụ đề tức thì (`< 200ms`).
      - Nút Bật/Tắt Loa (Nghe giọng đọc dịch TTS).
      - Chế độ xem: Đơn ngữ hoặc Song ngữ.
      - Nút Tải biên bản (nếu Host cho phép).
    - **Khung Phụ đề Cuộn Tự động Thông minh**:
      - Hiển thị phụ đề chạy mượt, tự động cuộn xuống câu mới nhất.
      - Nếu người dùng vuốt ngược lên để đọc lại câu cũ: Tự động tạm ngắt auto-scroll; có nút bấm "Cuộn xuống mới nhất".
- **Tiêu chí nghiệm thu (AC)**: Giao diện mượt mà trên iPhone/Safari và Android/Chrome; âm thanh dịch phát liên tục.

### `TASK-UI-10`: SCR-05 Màn hình Lịch sử Dịch thuật, AI Tóm tắt & Session Analytics
- **Mã chức năng**: `SCR-05.1`, `FR-408` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/dashboard/rooms/[roomId]/history`:
    - **Tab 1 — Toàn bộ Biên bản (Full Transcript)**: Đọc lại theo từng câu, tìm kiếm từ khóa, đổi ngôn ngữ, cụm nút tải theo `exportFormats` của gói, nút **Xóa biên bản (GDPR)**.
    - **Tab 2 — Tóm tắt Cuộc họp AI (AI Summary)**: Nút "✨ Tóm tắt AI" (`15 Cr` Pro / `25 Cr` Business+), bấm mốc `[mm:ss]` nhảy tới câu tương ứng ở Tab 1, đổi ngôn ngữ, tải `.MD`.
    - **Tab 3 — Phân tích & Chi phí Phiên (Chỉ Host thấy)**: Biểu đồ phân bố ngôn ngữ, đỉnh người nghe (`GET /rooms/{id}/analytics`, xuất CSV/PDF theo gói) và bóc tách Credit tiêu thụ theo từng giây.
- **Tiêu chí nghiệm thu (AC)**: Bấm mốc thời gian nhảy đúng câu; xuất báo cáo theo đúng quyền gói.

### `TASK-UI-11`: SCR-06 Màn hình Gói Dịch vụ, Ví Credit, Lịch sử Nạp & Lịch sử Sử dụng (4 Tab)
- **Mã chức năng**: `SCR-06.1` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/dashboard/billing` với **4 Tab**:
    1. **Gói dịch vụ (Plans)**: So sánh 4 gói `FREE`/`PRO`/`BUSINESS`/`ENTERPRISE`, Nâng cấp / Hủy gia hạn.
    2. **Mua thêm Credit (Top-up Packs)**: Chọn `PACK_S`/`M`/`L` hiển thị rõ `+Bonus%` theo gói + nhập Promo Code + cài đặt Auto Top-up (`BUSINESS+`).
    3. **Lịch sử Nạp tiền (`topup-history`)**: Phân trang, lọc loại/cổng/ngày, nút tải hóa đơn PDF VAT.
    4. **Lịch sử Sử dụng (`usage-history`)**: Bảng `credit_ledger` theo từng phiên / AI Summary / hết hạn; bấm từng dòng mở Drawer bóc tách chi tiết từng giây & xuất CSV.
- **Tiêu chí nghiệm thu (AC)**: 4 tab đồng bộ real-time, đối soát minh bạch từng ngăn Credit.

### `TASK-UI-12`: SCR-ADM-01..03 Giao diện Admin Dashboard, Quản lý Host 360° & Gói/Bảng Giá
- **Mã chức năng**: `SCR-ADM-01..03` | **Scope**: `Frontend Next.js (apps/web/src/app/(admin)/admin/*)`
- **Nghiệp vụ chi tiết**:
  - Layout Admin kèm `AdminGuard` (`role === 'ADMIN'`) và Confirm Modal bắt buộc nhập `reason`.
  - `/admin` (Doanh thu, COGS, Gross Margin %, phòng live, độ trễ P95), `/admin/hosts` & `/admin/hosts/[id]` (Hồ sơ 360°, Khóa, Gán gói B2B, Cộng/Trừ Credit 3 ngăn, Anti-Abuse), `/admin/plans-pricing` (Chỉnh 4 gói + JSON `entitlements`, 3 Top-up Packs, đơn giá Credit & tỷ giá VND).
- **Tiêu chí nghiệm thu (AC)**: User `HOST` truy cập `/admin/*` bị redirect về `/dashboard`; mọi thao tác ghi yêu cầu nhập `reason`.

### `TASK-UI-13`: SCR-ADM-04..06 Giao diện Admin Đối soát VietQR/Hoàn tiền, Promo & Vận hành Live/Audit
- **Mã chức năng**: `SCR-ADM-04..06` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - `/admin/payments` (Tra cứu giao dịch, Modal Khớp tay VietQR & Modal Hoàn tiền), `/admin/promos` (CRUD mã Promo & hiệu quả chiến dịch), `/admin/operations` (Live Rooms + Force End, AI Provider Kill-switch cho AWS/Azure Speech `vi-VN`, bảng tra cứu `admin_audit_logs` xem diff `before`/`after`).
- **Tiêu chí nghiệm thu (AC)**: Hiển thị mượt diff Audit Log, thao tác cứu hộ & khớp lệnh rõ ràng không bấm nhầm.

---

## 4. Kế hoạch Thực hiện Tuần tự theo Chặng (Execution Stages)

> Chi tiết phân tầng ưu tiên phát hành **`P0 (MVP v1.0)` / `P1 (Growth v1.1)` / `P2 (Enterprise v2.0)`** xem tại [epics-and-sub-epics.md](file:///D:/code/ws-translation-realtime/docs/tasks/epics-and-sub-epics.md).

```text
[Chặng 1: Nền tảng Core & Database] (TASK-DB-01 .. TASK-DB-03) [DONE]
     │
[Chặng 2: Xác thực & Hồ sơ Cá nhân] (TASK-AUTH-01..11 [8/11 DONE], TASK-PROF-01..06)
     │
[Chặng 3: 4 Gói cố định, Entitlements, Ví Credit 3 Ngăn & Thanh toán] (TASK-PLAN-01..04, TASK-WAL-01..07, TASK-PAY-01..07)
     │
[Chặng 4: Từ điển, Quản lý Phòng, Mic Check & Tính năng Theo Gói] (TASK-VOC-01..08, TASK-ROOM-01..15)
     │
[Chặng 5: Thu âm & WebSocket Nhị phân] (TASK-AUD-01..08)
     │
[Chặng 6: Pipeline AI Streaming, Multi-Provider TTS (vi-VN) & Fan-out] (TASK-AI-01..11)
     │
[Chặng 7: Động cơ Tính cước Theo Từng Giây & Cạn Credit] (TASK-MET-01..07)
     │
[Chặng 8: Đóng gói S3, GDPR, Bedrock Summary & Analytics] (TASK-TRN-01..10)
     │
[Chặng 9: Màn hình Giao diện Next.js 15] (TASK-UI-01..11 [3/11 DONE])
     │
[Chặng 10: HA, Handover 0ms, Observability & Admin Portal] (TASK-OPS-01..08)
```
