# Danh mục Chức năng & Bảng Phân rã Task Chi tiết (Granular Task Breakdown & Technical Roadmap)

- **Mã tài liệu**: `DOC-05-TASKS`
- **Phiên bản**: `2.0` (Phân rã chi tiết mức nguyên tử - Atomic Features & CRUD Tasks)
- **Ngày cập nhật**: 2026-11-12
- **Tài liệu tham chiếu**:
  - [01-business-requirements-and-billing.md](file:///D:/code/ws-translation-realtime/docs/specs/01-business-requirements-and-billing.md)
  - [02-functional-specifications.md](file:///D:/code/ws-translation-realtime/docs/specs/02-functional-specifications.md)
  - [03-system-architecture-and-techstack.md](file:///D:/code/ws-translation-realtime/docs/specs/03-system-architecture-and-techstack.md)
  - [04-api-websocket-and-ui-specs.md](file:///D:/code/ws-translation-realtime/docs/specs/04-api-websocket-and-ui-specs.md)
  - [2026-11-12-backend-clean-architecture-postgres-redesign.md](file:///D:/code/ws-translation-realtime/docs/superpowers/specs/2026-11-12-backend-clean-architecture-postgres-redesign.md)

---

## Mục lục Phân hệ (12 Phân hệ - 107 Chức năng Nguyên tử)

1. [Phân hệ 1: Xác thực & Quản lý Tài khoản (Authentication & Accounts)](#phân-hệ-1-xác-thực--quản-lý-tài-khoản-authentication--accounts) (11 Tasks)
2. [Phân hệ 2: Hồ sơ Cá nhân & Cài đặt Doanh nghiệp (User Profile & Settings)](#phân-hệ-2-hồ-sơ-cá-nhân--cài-đặt-doanh-nghiệp-user-profile--settings) (6 Tasks)
3. [Phân hệ 3: Quản lý Ví Điện tử Cá nhân (CRUD Ví & Quản lý Tài chính)](#phân-hệ-3-quản-lý-ví-điện-tử-cá-nhân-crud-ví--quản-lý-tài-chính) (7 Tasks)
4. [Phân hệ 4: Cổng Thanh toán & Nạp tiền (Top-up, Stripe, VietQR & Promo)](#phân-hệ-4-cổng-thanh-toán--nạp-tiền-top-up-stripe-vietqr--promo) (7 Tasks)
5. [Phân hệ 5: Quản lý Bộ Từ điển Chuyên ngành (Custom Vocabularies CRUD & AWS Sync)](#phân-hệ-5-quản-lý-bộ-từ-điển-chuyên-ngành-custom-vocabularies-crud--aws-sync) (8 Tasks)
6. [Phân hệ 6: Quản lý Phòng & Phiên dịch (Room & Session Lifecycle)](#phân-hệ-6-quản-lý-phòng--phiên-dịch-room--session-lifecycle) (13 Tasks)
7. [Phân hệ 7: Thu âm & Giao thức Nhị phân (Audio Ingest & Worklets)](#phân-hệ-7-thu-âm--giao-thức-nhị-phân-audio-ingest--worklets) (8 Tasks)
8. [Phân hệ 8: Nhận diện, Dịch thuật & Tổng hợp Giọng nói AI (Streaming AI Pipeline)](#phân-hệ-8-nhận-diện-dịch-thuật--tổng-hợp-giọng-nói-ai-streaming-ai-pipeline) (11 Tasks)
9. [Phân hệ 9: Đo đếm & Tính cước 10 giây (Realtime Micro-Billing Engine)](#phân-hệ-9-đo-đếm--tính-cước-10-giây-realtime-micro-billing-engine) (7 Tasks)
10. [Phân hệ 10: Biên bản Dịch thuật & AI Tóm tắt qua Bedrock (Transcripts & AI Summary)](#phân-hệ-10-biên-bản-dịch-thuật--ai-tóm-tắt-qua-bedrock-transcripts--ai-summary) (10 Tasks)
11. [Phân hệ 11: Hạ tầng, Độ sẵn sàng cao & Quản trị Hệ thống (HA, Failover & Admin Portal)](#phân-hệ-11-hạ-tầng-độ-sẵn-sàng-cao--quản-trị-hệ-thống-ha-failover--admin-portal) (8 Tasks)
12. [Phân hệ 12: Màn hình Giao diện Người dùng Web (Next.js 15 UI Screens)](#phân-hệ-12-màn-hình-giao-diện-người-dùng-web-nextjs-15-ui-screens) (11 Tasks)

---

## Phân hệ 1: Xác thực & Quản lý Tài khoản (Authentication & Accounts)

### `TASK-AUTH-01`: Đăng ký tài khoản Host bằng Email & Password
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

### `TASK-AUTH-02`: Xác thực mã OTP kích hoạt tài khoản & Khởi tạo Ví/Profile
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
  1. Client gửi `POST /api/v1/auth/confirm-register` với `email`, `otpCode`.
  2. Backend gọi Cognito `ConfirmSignUp`.
  3. Lấy thông tin `sub` từ Cognito `AdminGetUser`.
  4. Thực thi transaction PostgreSQL khởi tạo 3 bảng.
  5. Trả về `200 OK` thông báo tài khoản kích hoạt thành công kèm ví đã nạp $2.00 credit.
- **Input / Output**:
  - Input: `{"email": "host@domain.com", "otpCode": "123456"}`
  - Output: `{"message": "Account activated successfully", "walletBalance": 2.00, "currency": "USD"}`
- **Bảng DB tác động**: `users`, `user_profiles`, `wallets`, `payment_transactions`.
- **Tiêu chí nghiệm thu (AC)**: 100% tài khoản xác thực OTP thành công đều có bản ghi `wallets` với số dư `$2.00`.

### `TASK-AUTH-03`: Gửi lại mã OTP kích hoạt (Resend OTP)
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

### `TASK-AUTH-04`: Đăng nhập Host bằng Email & Mật khẩu (SRP Auth)
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

### `TASK-AUTH-07`: Làm mới Access Token ngầm (Silent Token Refresh)
- **Mã chức năng**: `FR-102.4` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/auth/refresh`.
  - Nhận `refreshToken`.
  - Gọi AWS Cognito `InitiateAuth` với `AuthFlow = REFRESH_TOKEN_AUTH`.
  - Nhận `AccessToken` mới và `IdToken` mới.
  - Đảm bảo phiên làm việc của Host không bị ngắt quãng khi đang chủ trì phòng họp kéo dài nhiều giờ.
- **Tiêu chí nghiệm thu (AC)**: Cấp lại AccessToken hợp lệ mà không bắt user nhập lại mật khẩu.

### `TASK-AUTH-08`: Đăng xuất tài khoản & Thu hồi Token (Logout / Revoke Session)
- **Mã chức năng**: `FR-105.1` | **Scope**: `Backend API & Security`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/auth/logout`.
  - Nhận `accessToken` và tham số tùy chọn `global = true/false`.
  - Nếu `global = false`: Gọi Cognito `RevokeToken` cho refresh token tương ứng.
  - Nếu `global = true`: Gọi Cognito `GlobalSignOut` để đăng xuất user khỏi tất cả các thiết bị.
  - Xóa cookie phiên tại Client.
- **Tiêu chí nghiệm thu (AC)**: Token sau khi đăng xuất không thể tiếp tục gọi API bảo mật.

### `TASK-AUTH-09`: Yêu cầu mã OTP Quên mật khẩu (Forgot Password)
- **Mã chức năng**: `FR-103.1` | **Scope**: `Backend API & Cognito`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/auth/forgot-password`.
  - Nhận `email`.
  - Kiểm tra Rate-limit trên Redis (tối đa 3 lần/15 phút).
  - Gọi AWS Cognito `ForgotPassword`. SES gửi mã OTP 6 số về email người dùng.
- **Tiêu chí nghiệm thu (AC)**: Gửi mã OTP thành công; giới hạn chống spam hoạt động chuẩn xác.

### `TASK-AUTH-10`: Xác nhận đặt lại mật khẩu mới bằng OTP (Reset Password)
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

### `TASK-WAL-01`: Lấy thông tin Chi tiết Số dư Ví (Read Wallet)
- **Mã chức năng**: `FR-504.1` | **Scope**: `Backend API & Redis`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/wallets/me`.
  - Đọc số dư từ PostgreSQL `wallets`:
    - `balance`: Số dư khả dụng định dạng `NUMERIC(12, 4)`.
    - `currency`: Đơn vị tiền tệ (mặc định `USD`).
    - `autoDegradeTts`: Trạng thái tự động hạ cấp TTS.
    - `autoTopupEnabled`: Trạng thái bật tự động nạp.
    - `autoTopupThreshold`: Ngưỡng kích hoạt nạp ngầm (e.g. `$5.00`).
    - `autoTopupAmount`: Số tiền nạp mỗi lần (e.g. `$20.00`).
  - Nếu Host đang có phòng hoạt động, đồng bộ số dư với key Redis `wallet:{hostId}:balance`.
- **Tiêu chí nghiệm thu (AC)**: Số dư trả về chính xác tới 4 chữ số thập phân, thời gian phản hồi `< 20ms`.

### `TASK-WAL-02`: Cập nhật Cài đặt Tiết kiệm & Tự động Hạ cấp TTS
- **Mã chức năng**: `FR-507.2` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PATCH /api/v1/wallets/me/settings`.
  - Nhận `autoDegradeTts: boolean`.
  - Cập nhật trường `wallets.auto_degrade_tts`.
  - Ý nghĩa nghiệp vụ: Nếu bật `true`, khi phòng dịch còn dưới 1 phút chi phí, hệ thống sẽ tự động tắt giọng đọc Polly (chỉ giữ dịch chữ) để tiết kiệm 70% chi phí duy trì phòng.
- **Tiêu chí nghiệm thu (AC)**: Cập nhật cờ thành công và có hiệu lực ngay trong chu kỳ tính cước tiếp theo.

### `TASK-WAL-03`: Bật / Tắt và Cấu hình Ngưỡng Tự động Nạp tiền (Auto Top-up Settings)
- **Mã chức năng**: `FR-503.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `PUT /api/v1/wallets/me/auto-topup`.
  - Nhận:
    - `enabled: boolean`.
    - `thresholdUsd: number` (Ngưỡng kích hoạt, tối thiểu `$2.00`, tối đa `$50.00`).
    - `amountUsd: number` (Số tiền nạp thêm, tối thiểu `$10.00`, tối đa `$500.00`).
  - Kiểm tra điều kiện: Host bắt buộc phải có phương thức thẻ thanh toán mặc định (`default_payment_method_id` không được null) mới cho phép bật `enabled = true`.
  - Cập nhật vào bảng `wallets`.
- **Tiêu chí nghiệm thu (AC)**: Không có thẻ lưu mà cố bật Auto Top-up sẽ bị trả về `400 Bad Request: Please add a payment card first`.

### `TASK-WAL-04`: Quản lý Phương thức Thanh toán Thẻ đã lưu (Stripe SetupIntent)
- **Mã chức năng**: `FR-503.2` | **Scope**: `Backend API & Stripe`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/wallets/me/payment-methods/setup-intent`:
    - Tạo Stripe `SetupIntent` gắn với `stripe_customer_id` của Host.
    - Trả về `clientSecret` cho Frontend Stripe Elements thu thập thông tin thẻ an toàn (PCI-DSS compliant, backend không bao giờ chạm số thẻ thô).
  - Endpoint `POST /api/v1/wallets/me/payment-methods/confirm`:
    - Nhận `paymentMethodId` từ Stripe sau khi client nhập thẻ xong.
    - Đặt làm thẻ mặc định: Lưu vào `wallets.default_payment_method_id` và `user_profiles.stripe_customer_id`.
  - Endpoint `GET /api/v1/wallets/me/payment-methods`:
    - Liệt kê thông tin thẻ đã lưu (4 số cuối, thương hiệu Visa/Mastercard, tháng/năm hết hạn).
  - Endpoint `DELETE /api/v1/wallets/me/payment-methods/{id}`:
    - Xóa thẻ đã lưu trên Stripe và cập nhật `default_payment_method_id = NULL`. Tự động tắt `auto_topup_enabled = false`.
- **Tiêu chí nghiệm thu (AC)**: Lưu và xóa thẻ an toàn, tuyệt đối không lưu PAN/CVV trong DB.

### `TASK-WAL-05`: Xem Danh sách Biến động Số dư Ví (Transactions History)
- **Mã chức năng**: `FR-508.1` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/wallets/me/transactions`.
  - Query params: `page`, `limit` (mặc định 20), `type` (`TOP_UP`, `AUTO_TOP_UP`, `PROMO_CREDIT`, `SESSION_USAGE`, `REFUND`), `startDate`, `endDate`.
  - Truy vấn bảng `payment_transactions` kết hợp phân trang (`OFFSET ... LIMIT ...`).
  - Trả về danh sách: `id`, `transactionId`, `type`, `provider`, `amount`, `currency`, `status`, `createdAt`, `completedAt`, `invoicePdfUrl`.
- **Tiêu chí nghiệm thu (AC)**: Lọc đúng loại giao dịch, phân trang chuẩn xác.

### `TASK-WAL-06`: Bảng Kê Đối soát Chi phí Chi tiết của 1 Phiên dịch (Session Usage Breakdown)
- **Mã chức năng**: `FR-508.2` | **Scope**: `Backend API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/wallets/me/sessions/{roomId}/breakdown`.
  - Truy vấn toàn bộ các bản ghi trong `usage_ledger` của `roomId`:
    - Tổng số giây có tiếng nói (`totalAudioSeconds`).
    - Tổng ký tự dịch thuật (`totalTranslatedChars`).
    - Tổng ký tự đọc Polly (`totalTtsChars`).
    - Lượng người nghe cao nhất và trung bình (`peakListeners`, `avgListeners`).
    - Bóc tách chi phí thành 4 khoản: Phí STT ($), Phí Dịch ($), Phí Giọng đọc ($), Phí Người nghe ($).
    - Biểu đồ tiêu thụ theo từng cửa sổ 10 giây (chuỗi thời gian để vẽ đồ thị).
- **Tiêu chí nghiệm thu (AC)**: Tổng 4 khoản chi phí khớp 100% với `rooms.total_cost`.

### `TASK-WAL-07`: Tải Biên lai / Hóa đơn Điện tử Nạp tiền (Receipt PDF Download)
- **Mã chức năng**: `FR-508.3` | **Scope**: `Backend API & PDF Generator`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/wallets/transactions/{transactionId}/receipt`.
  - Kiểm tra giao dịch thuộc sở hữu của Host và có `status == 'SUCCEEDED'`.
  - Đọc thông tin công ty từ `user_profiles` (Tên công ty, MST, Địa chỉ).
  - Render template HTML hóa đơn chuẩn và xuất file PDF (sử dụng `weasyprint` hoặc thư viện sinh PDF).
  - Trả về file PDF đính kèm hoặc tải qua S3 Presigned URL.
- **Tiêu chí nghiệm thu (AC)**: File PDF sắc nét, hiển thị đầy đủ mã giao dịch, số tiền nạp và thông tin thuế.

---

## Phân hệ 4: Cổng Thanh toán & Nạp tiền (Top-up, Stripe, VietQR & Promo)

### `TASK-PAY-01`: Tạo Lệnh Nạp tiền Quốc tế qua Stripe Checkout
- **Mã chức năng**: `FR-501.1` | **Scope**: `Backend API & Stripe`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/wallets/topup/stripe`.
  - Nhận `amountUsd` (tối thiểu `$5.00`, tối đa `$2,000.00`).
  - Sinh mã giao dịch nội bộ: `txId = "st_" + uuid7()`.
  - Gọi Stripe API tạo `Checkout Session`:
    - `line_items`: Nạp tiền ví phiên dịch ($amountUsd).
    - `mode`: `payment`.
    - `metadata`: `{"host_id": hostId, "tx_id": txId}`.
    - `success_url`: `https://domain.com/dashboard/billing?status=success&tx={txId}`.
    - `cancel_url`: `https://domain.com/dashboard/billing?status=cancelled`.
  - Tạo bản ghi `payment_transactions (host_id = hostId, transaction_id = txId, type = 'TOP_UP', provider = 'STRIPE', amount = amountUsd, status = 'PENDING')`.
  - Trả về `checkoutUrl` cho frontend điều hướng sang Stripe.
- **Tiêu chí nghiệm thu (AC)**: Tạo thành công session Stripe, lưu bản ghi `PENDING` vào DB.

### `TASK-PAY-02`: Xử lý Webhook Stripe & Cộng tiền Nguyên tử (Stripe Webhook IPN)
- **Mã chức năng**: `FR-502.1` | **Scope**: `Backend Webhook & PostgreSQL`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/webhooks/payment/stripe`.
  - Xác thực chữ ký header `stripe-signature` với `STRIPE_WEBHOOK_SECRET`. Nếu sai chữ ký, trả về ngay `400 Bad Request`.
  - Lọc sự kiện `checkout.session.completed` hoặc `payment_intent.succeeded`.
  - Lấy `txId = event.data.object.metadata.tx_id`.
  - **Transaction Bất biến (Idempotent DB Lock)**:
    ```sql
    SELECT * FROM payment_transactions WHERE transaction_id = :txId FOR UPDATE;
    ```
    - Nếu `status == 'SUCCEEDED'`: Đã xử lý trước đó -> Bỏ qua và trả về `200 OK`.
    - Nếu `status == 'PENDING'`:
      - Cập nhật `payment_transactions.status = 'SUCCEEDED'`, `completed_at = now()`.
      - Cộng tiền vào ví: `UPDATE wallets SET balance = balance + :amount, updated_at = now() WHERE host_id = :hostId`.
      - Cập nhật cache Redis: `INCRBYFLOAT wallet:{hostId}:balance {amount}`.
- **Tiêu chí nghiệm thu (AC)**: Bắn trùng lặp 5 lần webhook cùng 1 `txId` -> Tiền trong ví chỉ tăng đúng 1 lần duy nhất.

### `TASK-PAY-03`: Tạo Mã VietQR Động cho Chuyển khoản Ngân hàng Nội địa
- **Mã chức năng**: `FR-501.2` | **Scope**: `Backend API & VietQR`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/wallets/topup/vietqr`.
  - Nhận `amountUsd` (tối thiểu `$5.00`).
  - Quy đổi sang VND theo tỷ giá cố định/cập nhật hàng ngày (ví dụ `1 USD = 25,400 VND`).
    $$Amount_{VND} = \text{round}(amountUsd \times 25400, -3)$$
  - Sinh mã giao dịch duy nhất 6-8 ký tự: `txCode = "TR" + random_digits(6)` (ví dụ `TR849201`).
  - Sinh chuỗi VietQR chuẩn NAPAS EMVCo chứa STK ngân hàng thụ hưởng, mã ngân hàng (BIN), số tiền VND và nội dung chuyển khoản bắt buộc: `"ROOM " + txCode`.
  - Sinh ảnh Data URL Base64 QR code.
  - Lưu bản ghi `payment_transactions (transaction_id = txCode, type = 'TOP_UP', provider = 'VIETQR', amount = amountUsd, status = 'PENDING')` với hạn hiệu lực 15 phút.
  - Trả về `qrDataUrl`, `txCode`, `amountVnd`, `bankAccount`, `bankName`, `expiresInSec: 900`.
- **Tiêu chí nghiệm thu (AC)**: Quét mã QR bằng App ngân hàng bất kỳ (Vietcombank, MBBank, Techcombank...) tự động điền đúng STK, số tiền và nội dung chuyển khoản.

### `TASK-PAY-04`: Xử lý Webhook Biến động Số dư Ngân hàng (SePay / Casso / VietQR IPN)
- **Mã chức năng**: `FR-502.2` | **Scope**: `Backend Webhook`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/webhooks/payment/vietqr`.
  - Kiểm tra API Key / HMAC Header của cổng SePay/Casso.
  - Phân tích nội dung chuyển khoản (`content`): Dùng regex trích xuất mã giao dịch dạng `TR\d{6}`.
  - Tìm bản ghi `payment_transactions` khớp với mã `txCode`.
  - Kiểm tra số tiền chuyển thực tế: Phải $\ge$ số tiền yêu cầu trong giao dịch (sai số $< 1,000\text{ VND}$).
  - Mở transaction khóa dòng `FOR UPDATE`:
    - Chuyển `status = 'SUCCEEDED'`.
    - Cộng tiền nguyên tử vào `wallets`.
    - Cộng tiền vào Redis `wallet:{hostId}:balance`.
    - Đẩy thông báo WebSocket tới màn hình Host: `{"event": "PAYMENT_CONFIRMED", "balance": newBalance}`.
- **Tiêu chí nghiệm thu (AC)**: Tiền nổi vào ví của Host trong vòng $< 2\text{ giây}$ sau khi chuyển khoản thành công.

### `TASK-PAY-05`: Background Worker Tự động Nạp tiền Ngầm (Stripe Off-session Auto Top-up)
- **Mã chức năng**: `FR-503.3` | **Scope**: `Backend Worker & Stripe`
- **Nghiệp vụ chi tiết**:
  - Được kích hoạt từ `billing_worker` khi số dư ví của Host chạm ngưỡng `balance < auto_topup_threshold`:
    1. Kiểm tra cờ `auto_topup_enabled == true` và có `default_payment_method_id`.
    2. Kiểm tra Redis Lock `lock:auto_topup:{hostId}` (TTL 5 phút) để tránh tạo nhiều lệnh nạp trùng nhau.
    3. Sinh `txId = "auto_" + uuid7()`.
    4. Tạo bản ghi `payment_transactions (status = 'PENDING', type = 'AUTO_TOP_UP', provider = 'STRIPE', amount = auto_topup_amount)`.
    5. Gọi Stripe API:
       ```python
       stripe.PaymentIntent.create(
           amount=int(auto_topup_amount * 100),
           currency="usd",
           customer=stripe_customer_id,
           payment_method=default_payment_method_id,
           off_session=True,
           confirm=True,
           metadata={"tx_id": txId, "host_id": hostId}
       )
       ```
    6. Nếu trừ thẻ thành công: Cập nhật `status = 'SUCCEEDED'`, cộng ví, bắn thông báo cho Host.
    7. Nếu trừ thẻ thất bại (thẻ hết tiền, thẻ khóa): Đánh dấu `status = 'FAILED'`, tạm thời tắt `auto_topup_enabled = false`, gửi cảnh báo khẩn cấp tới Host để nạp thủ công.
- **Tiêu chí nghiệm thu (AC)**: Cuộc họp đang chạy tự nạp thêm tiền mượt mà không bị ngắt quãng âm thanh.

### `TASK-PAY-06`: Kiểm tra & Kích hoạt Mã Khuyến mãi / Tặng Credit (Promo Redeem)
- **Mã chức năng**: `FR-509.1` | **Scope**: `Backend API & PostgreSQL`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/wallets/promo-redeem`.
  - Nhận `code` (chuỗi ký tự, e.g. `WELCOME50`, `AI2026`).
  - Mở Transaction PostgreSQL:
    1. Tìm mã trong `promo_codes WHERE code = :code FOR UPDATE`.
    2. Nếu không tìm thấy hoặc `is_active == false`: Trả về lỗi `404 Promo code not found or inactive`.
    3. Nếu `expires_at < now()`: Trả về lỗi `400 Promo code has expired`.
    4. Nếu `current_uses >= max_uses`: Trả về lỗi `400 Promo code usage limit reached`.
    5. Kiểm tra bảng `promo_redemptions WHERE promo_code_id = :promoId AND user_id = :userId`: Nếu đã có bản ghi -> Trả về lỗi `400 You have already redeemed this promo code`.
    6. Cộng tiền vào ví: `UPDATE wallets SET balance = balance + :credit_amount WHERE host_id = :userId`.
    7. Tăng lượt dùng: `UPDATE promo_codes SET current_uses = current_uses + 1 WHERE id = :promoId`.
    8. Ghi nhận `promo_redemptions (promo_code_id = :promoId, user_id = :userId, credit_applied = :credit_amount)`.
    9. Tạo bản ghi `payment_transactions (type = 'PROMO_CREDIT', provider = 'SYSTEM', amount = :credit_amount, status = 'SUCCEEDED')`.
- **Tiêu chí nghiệm thu (AC)**: Tuyệt đối không thể nhập 1 mã 2 lần; hết hạn hoặc hết lượt bị chặn 100%.

### `TASK-PAY-07`: Xử lý Hoàn tiền Giao dịch Lỗi (Refund Processing)
- **Mã chức năng**: `FR-604.3` | **Scope**: `Backend Admin & Stripe`
- **Nghiệp vụ chi tiết**:
  - Endpoint Admin `POST /api/v1/admin/transactions/{txId}/refund`.
  - Nhận `reason`, `refundAmount` (tùy chọn, mặc định toàn bộ số tiền nạp).
  - Nếu giao dịch gốc là Stripe: Gọi Stripe API `stripe.Refund.create(payment_intent=pi_id, amount=refundAmount)`.
  - Trừ ngược số tiền tương ứng khỏi ví của Host: `UPDATE wallets SET balance = balance - :refundAmount`.
  - Tạo bản ghi `payment_transactions (type = 'REFUND', amount = -refundAmount, status = 'SUCCEEDED')`.
- **Tiêu chí nghiệm thu (AC)**: Hoàn tiền Stripe thành công, số dư ví giảm tương ứng có lưu vết kiểm toán.

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

### `TASK-ROOM-01`: Kiểm tra Số dư Khởi tạo Phòng (Pre-flight Balance Check Algorithm)
- **Mã chức năng**: `FR-201.1` | **Scope**: `Backend Services`
- **Nghiệp vụ chi tiết**:
  - Hàm tính toán chi phí trước khi mở phòng:
    - Input: `sourceLang`, danh sách `targetLangs` ($N$ ngôn ngữ), `autoDegradeTts: bool`.
    - Ước tính cước phí 1 phút hoạt động tối đa:
      $$Cost/min = \$0.024\text{ (STT)} + (N \times \$0.015\text{ MT}) + (N \times \$0.016\text{ TTS}) + (10\text{ listeners} \times \$0.005/60)$$
    - Chi phí tối thiểu bắt buộc để mở phòng:
      $$MinRequiredBalance = Cost/min \times 10\text{ phút}$$
    - Ví dụ: Dịch sang 3 thứ tiếng có TTS -> $Cost/min \approx \$0.12$ -> Yêu cầu số dư ví tối thiểu $\ge \$1.20$.
  - Nếu số dư trong `wallets.balance < MinRequiredBalance`: Chặn mở phòng, trả về `402 Payment Required` kèm số tiền còn thiếu.
- **Tiêu chí nghiệm thu (AC)**: Không thể tạo phòng khi ví không đủ tiền chạy 10 phút.

### `TASK-ROOM-02`: Tạo Phòng Dịch Mới (Create Room)
- **Mã chức năng**: `FR-201.2` | **Scope**: `Backend API & PostgreSQL`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms`.
  - Nhận: `title`, `mode` (`1_ON_1` hoặc `BROADCAST`), `sourceLang`, `targetLangs` (mảng 1-10 mã), `passcode` (tùy chọn), `allowListenerDownload` (mặc định `false`), `vocabularyId` (tùy chọn).
  - Chạy `TASK-ROOM-01` kiểm tra số dư.
  - Sinh mã phòng ngẫu nhiên duy nhất gồm 6 chữ số: `roomCode` dạng `XXX-XXX` (e.g. `849-201`).
  - Nếu có `passcode`: Băm mật khẩu bằng Bcrypt/Argon2id -> lưu `password_hash`.
  - Giới hạn người nghe mặc định: `1_ON_1` = 2 người; `BROADCAST` = 1.000 người.
  - Lưu vào bảng `rooms` với trạng thái `status = 'CREATED'`.
  - Khởi tạo key metadata trên Redis: `HSET room:{roomId}:meta status CREATED host_id {hostId}`.
  - Trả về: `roomId`, `roomCode`, `joinUrl`, `estimatedBurnRatePerMin`.
- **Tiêu chí nghiệm thu (AC)**: Tạo phòng thành công trong $< 100ms$, sinh mã phòng 6 số duy nhất.

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

### `TASK-AI-05`: Kiểm tra Biến đếm Người nghe Bật loa (Demand-driven TTS Guard)
- **Mã chức năng**: `FR-305.1` | **Scope**: `Backend Services & Redis`
- **Nghiệp vụ chi tiết**:
  - Trước khi gọi Amazon Polly cho ngôn ngữ `lang`:
    - Đọc Redis: `count = HGET room:{roomId}:tts_count {lang}`.
    - **Quy tắc bảo vệ chi phí nghiêm ngặt**:
      - Nếu `count == 0` hoặc key không tồn tại -> **Tuyệt đối không gọi Polly**, bỏ qua khâu sinh audio cho ngôn ngữ đó.
      - Nếu `count > 0` -> Đưa vào danh sách cần sinh giọng đọc.
- **Tiêu chí nghiệm thu (AC)**: Tiết kiệm $100\%$ chi phí Polly cho mọi ngôn ngữ không có người bấm nghe loa.

### `TASK-AI-06`: Tổng hợp Giọng đọc Amazon Polly Neural & Upload S3 CDN
- **Mã chức năng**: `FR-305.2` | **Scope**: `Backend Integrations & AWS Polly`
- **Nghiệp vụ chi tiết**:
  - Với các ngôn ngữ có `tts_count > 0`:
    - Gọi Amazon Polly: `Engine = "neural"`, `OutputFormat = "mp3"`, `VoiceId` phù hợp với ngôn ngữ và giới tính đã cấu hình.
    - Đẩy luồng audio `.mp3` lên S3: `s3://.../tts/{roomId}/{segmentId}_{lang}.mp3` (S3 Lifecycle xóa sau 24h).
    - Tạo CDN URL: `https://cdn.domain.com/tts/{roomId}/{segmentId}_{lang}.mp3`.
- **Tiêu chí nghiệm thu (AC)**: Sinh xong file âm thanh và có URL CloudFront trong $< 400ms$.

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

## Phân hệ 9: Đo đếm & Tính cước 10 giây (Realtime Micro-Billing Engine)

### `TASK-MET-01`: Đo đếm Lưu lượng Phòng theo Cửa sổ 10 Giây
- **Mã chức năng**: `FR-505.1` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Trong mỗi cửa sổ 10 giây, worker tổng hợp số liệu tiêu thụ của từng phòng `ACTIVE`:
    - `audioSeconds`: Số giây có tiếng nói thực tế (`vad_flag == 1`).
    - `translatedChars`: Tổng số ký tự văn bản gửi dịch qua Amazon Translate.
    - `ttsChars`: Tổng số ký tự văn bản gửi đọc qua Amazon Polly.
    - `listenerCount`: Số lượng người nghe trung bình trong 10 giây.
  - Reset bộ đếm chu kỳ trên Redis để chuẩn bị cho 10 giây tiếp theo.
- **Tiêu chí nghiệm thu (AC)**: Thu thập số liệu đo lường chính xác, không thất thoát lưu lượng.

### `TASK-MET-02`: Tính toán Chi phí Vi mô 10s theo Công thức Chuẩn hóa
- **Mã chức năng**: `FR-506.1` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Áp dụng công thức 4 thành phần:
    $$\text{Cost}_{10s} = \text{Fee}_{STT} + \text{Fee}_{MT} + \text{Fee}_{TTS} + \text{Fee}_{Listener}$$
    - $\text{Fee}_{STT} = (\text{audioSeconds} / 60) \times \$0.024$
    - $\text{Fee}_{MT} = (\text{translatedChars} / 1,000,000) \times \$15.00$
    - $\text{Fee}_{TTS} = (\text{ttsChars} / 1,000,000) \times \$16.00$
    - $\text{Fee}_{Listener} = (\text{listenerCount} \times 10 / 3600) \times \$0.005$
  - Làm tròn chi phí đến 4 chữ số thập phân (`NUMERIC(10, 4)`).
- **Tiêu chí nghiệm thu (AC)**: Tính toán khớp 100% theo bảng giá cấu hình, sai số $< 0.01\%$.

### `TASK-MET-03`: Khấu trừ Ví Nguyên tử & Ghi Sổ cái PostgreSQL (Atomic Ledger)
- **Mã chức năng**: `FR-506.2` | **Scope**: `Backend Database Transaction`
- **Nghiệp vụ chi tiết**:
  - Mở Transaction PostgreSQL:
    1. Trừ tiền nguyên tử trong `wallets`:
       ```sql
       UPDATE wallets 
       SET balance = balance - :cost, updated_at = now() 
       WHERE host_id = :hostId AND balance >= :cost 
       RETURNING balance;
       ```
    2. Ghi bản ghi bất biến vào `usage_ledger`:
       ```sql
       INSERT INTO usage_ledger (room_id, host_id, window_timestamp, audio_seconds, translated_chars, tts_chars, listener_count, cost_amount, balance_after)
       VALUES (:roomId, :hostId, now(), :audioSec, :mtChars, :ttsChars, :listeners, :cost, :newBalance);
       ```
    3. Cập nhật tổng chi phí phòng: `UPDATE rooms SET total_cost = total_cost + :cost WHERE id = :roomId`.
- **Tiêu chí nghiệm thu (AC)**: Cam kết số dư ví không bao giờ bị âm; mọi khoản trừ đều có dòng đối soát trong `usage_ledger`.

### `TASK-MET-04`: Đồng bộ Số dư lên Redis & Phát Bản tin BILLING_TICK
- **Mã chức năng**: `FR-504.2` | **Scope**: `Backend WebSocket & Redis`
- **Nghiệp vụ chi tiết**:
  - Cập nhật số dư mới nhất vào Redis: `SET wallet:{hostId}:balance {newBalance}`.
  - Tính tốc độ đốt tiền ước tính mỗi phút (`burnRatePerMin`) và số phút còn lại (`remainingMinutes`).
  - Gửi gói tin WebSocket `BILLING_TICK` về màn hình Host:
    ```json
    {
      "event": "BILLING_TICK",
      "balanceUsd": 4.20,
      "sessionCostUsd": 1.85,
      "burnRatePerMinUsd": 0.15,
      "estimatedRemainingMinutes": 28.0,
      "warningLevel": "NONE"
    }
    ```
- **Tiêu chí nghiệm thu (AC)**: Màn hình Host cập nhật mượt mà đồng hồ cước mỗi 10 giây.

### `TASK-MET-05`: Xử lý Cảnh báo Số dư Thấp dưới 5 Phút (LOW_BALANCE_WARNING)
- **Mã chức năng**: `FR-507.1` | **Scope**: `Backend Billing & Frontend Modal`
- **Nghiệp vụ chi tiết**:
  - Khi `remainingMinutes < 5.0` phút:
    - Gửi gói tin `BILLING_TICK` với cờ `warningLevel = "LOW_BALANCE_WARNING"`.
    - Phía Frontend tự động hiển thị Banner vàng cảnh báo số dư thấp.
    - Mở Popup Nạp tiền nhanh tại chỗ (`In-room Top-up Modal`) cho phép Host quét QR hoặc bấm thẻ nạp thêm mà không cần thoát khỏi phòng.
- **Tiêu chí nghiệm thu (AC)**: Cảnh báo kịp thời trước 5 phút để Host nạp tiền tiếp.

### `TASK-MET-06`: Tự động Hạ cấp Dịch vụ Tắt TTS khi Dưới 1 Phút (GRACEFUL_DEGRADATION)
- **Mã chức năng**: `FR-507.3` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Khi `remainingMinutes < 1.0` phút VÀ `wallets.auto_degrade_tts == true`:
    - Gửi gói tin `warningLevel = "GRACEFUL_DEGRADATION"`.
    - Hệ thống tự động đặt `tts_count = 0` cho toàn bộ ngôn ngữ trên Redis.
    - Ngắt hoàn toàn việc gọi Amazon Polly. Chỉ duy trì nhận diện giọng nói và dịch phụ đề text để tiết kiệm 70% chi phí.
    - Thông báo cho Host và người nghe: *"Đã tạm tắt giọng đọc để kéo dài thời gian hiển thị phụ đề"*.
- **Tiêu chí nghiệm thu (AC)**: Kéo dài thời gian duy trì phòng thêm gấp 3 lần khi sắp cạn ví.

### `TASK-MET-07`: Tự động Đóng Phòng An toàn khi Hết Số dư (QUOTA_EXHAUSTED)
- **Mã chức năng**: `FR-507.4` | **Scope**: `Backend Billing Worker`
- **Nghiệp vụ chi tiết**:
  - Khi `balance <= 0.00`:
    - Đợi diễn giả dứt câu đang nói (`isFinal = true`).
    - Gửi bản tin `QUOTA_EXHAUSTED` tới Host và toàn bộ Người nghe.
    - Chuyển trạng thái phòng sang `ENDED`.
    - Đóng kết nối WebSocket và kích hoạt đóng gói biên bản S3.
- **Tiêu chí nghiệm thu (AC)**: Phòng đóng an toàn, không bị mất câu nói cuối cùng, không âm tiền ví.

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

### `TASK-TRN-06`: API Tải File Biên bản Dịch với Phân quyền Bảo mật
- **Mã chức năng**: `FR-406.5` | **Scope**: `Backend API & S3 Presigned URL`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/rooms/{roomId}/transcripts/export`.
  - Query params: `format` (`srt`, `vtt`, `txt`, `csv`, `json`), `lang`.
  - **Kiểm tra quyền**:
    - Host: Luôn luôn có quyền tải.
    - Listener: Kiểm tra `rooms.allow_listener_download`. Nếu `false` -> Trả về `403 Forbidden: Host has disabled transcript downloads for listeners`.
  - Sinh Amazon S3 Presigned URL GET thời hạn 60 phút.
  - Trả về `downloadUrl`.
- **Tiêu chí nghiệm thu (AC)**: Listener không thể tải lậu file nếu Host không cho phép; URL tải trực tiếp từ S3.

### `TASK-TRN-07`: Host Kích hoạt Tóm tắt Cuộc họp AI qua Amazon Bedrock
- **Mã chức năng**: `FR-407.1` | **Scope**: `Backend API & Amazon Bedrock`
- **Nghiệp vụ chi tiết**:
  - Endpoint `POST /api/v1/rooms/{roomId}/summary`.
  - Chỉ Host có quyền gọi.
  - Gọi Background Task sinh tóm tắt bằng Amazon Bedrock (`Claude 3.5 Haiku` hoặc `Nova Lite`):
    - Đọc nội dung `master.json` từ S3.
    - Prompt trích xuất:
      1. `overview`: Tóm tắt tổng quan chủ đề cốt lõi cuộc họp.
      2. `keyTakeaways`: Các luận điểm chính kèm mốc thời gian `timestamp` định dạng `[mm:ss]`.
      3. `actionItems`: Danh sách các quyết định hoặc việc cần làm được nhắc tới trong bài nói.
    - Tính chi phí Bedrock thực tế (khoảng `$0.01` – `$0.02`), trừ phí 1 lần duy nhất vào ví của Host.
    - Lưu file `summary.json` lên S3 và cập nhật `room_transcripts.summary_status = 'READY'`.
- **Tiêu chí nghiệm thu (AC)**: Sinh xong tóm tắt chất lượng cao cho cuộc họp 1 giờ trong $< 8\text{ giây}$.

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

### `TASK-OPS-08`: API Admin Thống kê Doanh thu & Chi phí Toàn sàn (Admin Overview Stats)
- **Mã chức năng**: `FR-604.5` | **Scope**: `Backend Admin API`
- **Nghiệp vụ chi tiết**:
  - Endpoint `GET /api/v1/admin/stats/overview`.
  - Thống kê:
    - Tổng tiền nạp của người dùng trong ngày / tháng.
    - Tổng tiền cước đã trừ (`usage_ledger`).
    - Tổng số phút dịch thuật đã thực hiện.
    - Ước tính chi phí AWS phát sinh thực tế và lợi nhuận gộp.
- **Tiêu chí nghiệm thu (AC)**: Trả về số liệu tổng quan kinh doanh chính xác phục vụ ban quản trị.

---

## Phân hệ 12: Màn hình Giao diện Người dùng Web (Next.js 15 UI Screens)

### `TASK-UI-01`: SCR-01 Form Đăng ký Host kèm Password Meter & OTP Input
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

### `TASK-UI-02`: SCR-01 Form Đăng nhập Email/Password & Social SSO
- **Mã chức năng**: `SCR-01.2` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/login`:
    - Form nhập Email và Mật khẩu, checkbox "Ghi nhớ đăng nhập".
    - Cụm nút Social SSO: Đăng nhập với Google, Đăng nhập với Apple.
    - Link chuyển tới màn hình Quên mật khẩu và Đăng ký.
- **Tiêu chí nghiệm thu (AC)**: Đăng nhập thành công lưu token và chuyển hướng ngay về `/dashboard`.

### `TASK-UI-03`: SCR-01 Form Quên mật khẩu & Đặt lại mật khẩu
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

### `TASK-UI-10`: SCR-05 Màn hình Lịch sử Dịch thuật & AI Tóm tắt Cuộc họp
- **Mã chức năng**: `SCR-05.1` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/dashboard/rooms/[roomId]/history`:
    - **Tab 1 — Toàn bộ Biên bản (Full Transcript)**: Đọc lại toàn bộ nội dung từng câu, ô tìm kiếm từ khóa, đổi ngôn ngữ đối chiếu, cụm nút tải file: `.TXT`, `.SRT`, `.VTT`, `.CSV`.
    - **Tab 2 — Tóm tắt Cuộc họp AI (AI Summary)**:
      - Nút "✨ Tóm tắt nội dung bằng AI" (kèm chi phí ước tính).
      - Hiển thị trực quan 3 phần: **Chủ đề cốt lõi**, **Các luận điểm chính kèm mốc thời gian [mm:ss] bấm vào nhảy ngay tới câu tương ứng trong Tab 1**, **Đầu việc cần làm Action Items**.
      - Dropdown đổi ngôn ngữ tóm tắt, nút tải file Markdown.
    - **Tab 3 — Chi phí Phiên (Chỉ Host thấy)**: Đồ thị cột bóc tách 4 khoản phí theo từng 10 giây.
- **Tiêu chí nghiệm thu (AC)**: Bấm vào mốc thời gian trong tóm tắt AI tự động cuộn và highlight câu nói tương ứng.

### `TASK-UI-11`: SCR-06 Màn hình Quản lý Ví, Thanh toán & Mã Khuyến mãi
- **Mã chức năng**: `SCR-06.1` | **Scope**: `Frontend Next.js`
- **Nghiệp vụ chi tiết**:
  - Trang `/dashboard/billing`:
    - Bảng Lịch sử giao dịch ví: Phân trang, lọc theo nạp tiền / trừ cước / khuyến mãi, nút tải biên lai PDF.
    - Cụm Cài đặt Tự động Nạp tiền (Auto Top-up): Bật/tắt, đặt ngưỡng tiền, quản lý thẻ tín dụng đã lưu.
    - Form Nhập Mã Khuyến Mãi (Promo Code): Ô nhập mã + nút "Áp dụng", cộng tiền ngay lập tức.
- **Tiêu chí nghiệm thu (AC)**: Nhập mã promo cộng tiền ngay; tải biên lai PDF hiển thị chuẩn thông tin công ty.

---

## 4. Kế hoạch Thực hiện Tuần tự theo Chặng (Execution Stages)

```text
[Chặng 1: Nền tảng Core & Database] (TASK-DB-01 .. TASK-DB-03)
     │
[Chặng 2: Xác thực & Hồ sơ Cá nhân] (TASK-AUTH-01 .. 11, TASK-PROF-01 .. 06)
     │
[Chặng 3: CRUD Ví, Nạp tiền & Promo] (TASK-WAL-01 .. 07, TASK-PAY-01 .. 07)
     │
[Chặng 4: Từ điển & Quản lý Phòng] (TASK-VOC-01 .. 08, TASK-ROOM-01 .. 13)
     │
[Chặng 5: Thu âm & WebSocket Nhị phân] (TASK-AUD-01 .. 08)
     │
[Chặng 6: Pipeline AI Streaming & Fanout] (TASK-AI-01 .. 11)
     │
[Chặng 7: Động cơ Tính cước 10s & Cạn ví] (TASK-MET-01 .. 07)
     │
[Chặng 8: Đóng gói S3 & AI Bedrock Summary] (TASK-TRN-01 .. 10)
     │
[Chặng 9: Màn hình Giao diện Next.js 15] (TASK-UI-01 .. 11)
     │
[Chặng 10: HA, Handover 0ms & Admin Portal] (TASK-OPS-01 .. 08)
```
