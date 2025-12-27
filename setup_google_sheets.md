# Hướng Dẫn Setup Google Sheets API

## 🎯 Mục Đích
Kết nối Streamlit với Google Sheets để đọc dữ liệu real-time.

---

## 📋 Các Bước Thực Hiện

### Bước 1: Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Đăng nhập bằng tài khoản Google của bạn
3. Click **"Select a project"** → **"New Project"**
4. Đặt tên project: `streamlit-dashboard` (hoặc tên bạn thích)
5. Click **"Create"**

### Bước 2: Enable Google Sheets API

1. Trong Google Cloud Console, vào **"APIs & Services"** → **"Library"**
2. Tìm kiếm **"Google Sheets API"**
3. Click vào **"Google Sheets API"**
4. Click **"Enable"**

### Bước 3: Enable Google Drive API (Optional nhưng khuyến nghị)

1. Quay lại **"Library"**
2. Tìm **"Google Drive API"**
3. Click **"Enable"**

### Bước 4: Tạo Service Account

1. Vào **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Điền thông tin:
   - **Service account name**: `streamlit-reader`
   - **Service account ID**: tự động tạo
   - **Description**: "Service account for Streamlit to read Google Sheets"
4. Click **"Create and Continue"**
5. **Grant this service account access to project**: Chọn role **"Viewer"** (hoặc bỏ qua)
6. Click **"Done"**

### Bước 5: Tạo và Download Credentials JSON

1. Trong danh sách **Service Accounts**, click vào service account vừa tạo
2. Chọn tab **"Keys"**
3. Click **"Add Key"** → **"Create new key"**
4. Chọn **"JSON"**
5. Click **"Create"**
6. File JSON sẽ tự động download về máy

### Bước 6: Lưu Credentials File

1. Đổi tên file JSON vừa download thành: `google_credentials.json`
2. Copy file vào thư mục project:
   ```
   c:\Users\Admin\OneDrive\computer\làm báo cáo trên streamlit\google_credentials.json
   ```

### Bước 7: Lấy Service Account Email

1. Mở file `google_credentials.json` bằng Notepad
2. Tìm dòng `"client_email"`:
   ```json
   "client_email": "streamlit-reader@your-project.iam.gserviceaccount.com"
   ```
3. Copy email này (ví dụ: `streamlit-reader@your-project.iam.gserviceaccount.com`)

### Bước 8: Share Google Sheet với Service Account

1. Mở Google Sheet của bạn:
   ```
   https://docs.google.com/spreadsheets/d/1F2NzTR50kXzGx9Pc5KdBwwqnIRXGvViPv6mgw8YMNW0/edit
   ```
2. Click nút **"Share"** (góc trên bên phải)
3. Paste **Service Account Email** vào ô "Add people and groups"
4. Chọn quyền: **"Viewer"** (chỉ đọc)
5. **BỎ TICK** ô "Notify people" (không cần gửi email)
6. Click **"Share"**

---

## ✅ Kiểm Tra

Sau khi hoàn thành, bạn sẽ có:
- ✅ File `google_credentials.json` trong thư mục project
- ✅ Google Sheet đã được share với Service Account email
- ✅ Google Sheets API đã được enable

---

## 🔐 Bảo Mật

> [!WARNING]
> **Quan trọng**: File `google_credentials.json` chứa thông tin nhạy cảm!
> 
> - ❌ KHÔNG commit file này lên Git/GitHub
> - ❌ KHÔNG share file này công khai
> - ✅ Chỉ lưu trên máy local
> - ✅ Thêm vào `.gitignore`

---

## 🚀 Bước Tiếp Theo

Sau khi hoàn thành setup, thông báo cho tôi để:
1. Cài đặt thư viện Python cần thiết
2. Viết code đọc dữ liệu từ Google Sheets
3. Hiển thị dữ liệu trong Streamlit dashboard
