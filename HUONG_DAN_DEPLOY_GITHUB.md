# 🚀 HƯỚNG DẪN ĐẨY DỮ LIỆU LÊN STREAMLIT QUA GITHUB

## 📋 TỔNG QUAN
Hướng dẫn này sẽ giúp bạn:
1. Upload code lên GitHub
2. Cấu hình Google Sheets API credentials an toàn
3. Deploy ứng dụng lên Streamlit Cloud
4. Cập nhật code khi có thay đổi

---

## PHẦN 1: CHUẨN BỊ FILE TRƯỚC KHI UPLOAD

### ✅ Kiểm tra file `.gitignore`
File này đảm bảo các file nhạy cảm KHÔNG bị upload lên GitHub:

```gitignore
# Credentials - KHÔNG upload lên GitHub
api-agent-*.json
*.json

# Excel files - Không cần thiết trên cloud
*.xlsx
*.xlsm
*.xls

# Python cache
__pycache__/
*.pyc
*.pyo

# Logs
*.log

# Local config
.env
```

### 🔐 Chuẩn bị Google Sheets Credentials
**QUAN TRỌNG:** File `api-agent-471608-912673253587.json` chứa thông tin nhạy cảm và KHÔNG được upload lên GitHub.

Thay vào đó, bạn sẽ cấu hình nó trên Streamlit Cloud ở **PHẦN 4**.

---

## PHẦN 2: TẠO REPOSITORY TRÊN GITHUB

1. Truy cập [github.com](https://github.com/) và đăng nhập.
2. Bấm dấu **+** ở góc trên bên phải → chọn **New repository**.
3. Đặt tên Repository (ví dụ: `bao-cao-san-luong`).
4. **QUAN TRỌNG:** Chọn **Private** để bảo mật dữ liệu nội bộ.
5. **KHÔNG** chọn "Add a README file" (vì bạn đã có code sẵn).
6. Bấm **Create repository**.

> 💡 **Lưu ý:** Streamlit Community Cloud hỗ trợ deploy từ Private repository miễn phí!

---

## PHẦN 3: UPLOAD CODE LÊN GITHUB

Mở **Terminal** trong VS Code (`Ctrl + ` ` `) và chạy các lệnh sau:

### Bước 1: Khởi tạo Git (nếu chưa có)
```bash
git init
```

### Bước 2: Thêm tất cả file vào Git
```bash
git add .
```

### Bước 3: Commit (lưu trạng thái)
```bash
git commit -m "Initial commit - Dashboard production"
```

### Bước 4: Tạo nhánh main
```bash
git branch -M main
```

### Bước 5: Kết nối với GitHub
**Thay `TÊN_CỦA_BẠN` và `bao-cao-san-luong` bằng thông tin thực tế:**
```bash
git remote add origin https://github.com/TÊN_CỦA_BẠN/bao-cao-san-luong.git
```

### Bước 6: Đẩy code lên GitHub
```bash
git push -u origin main
```

> 🔑 Nếu GitHub yêu cầu đăng nhập, làm theo hướng dẫn trên pop-up. Bạn có thể cần tạo **Personal Access Token** thay vì dùng mật khẩu.

---

## PHẦN 4: CẤU HÌNH STREAMLIT SECRETS (QUAN TRỌNG!)

### 📝 Chuẩn bị nội dung Secrets

1. Mở file `api-agent-471608-912673253587.json` trên máy tính.
2. Copy toàn bộ nội dung.
3. Chuẩn bị format như sau (thay thế bằng nội dung thực tế):

```toml
[gcp_service_account]
type = "service_account"
project_id = "api-agent-471608"
private_key_id = "912673253587..."
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
(toàn bộ private key, giữ nguyên format nhiều dòng)
-----END PRIVATE KEY-----"""
client_email = "google-sheets-api@api-agent-471608.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

**⚠️ LƯU Ý QUAN TRỌNG về `private_key`:**
- Phải bọc trong `"""..."""` (ba dấu ngoặc kép)
- Giữ nguyên format `-----BEGIN PRIVATE KEY-----` và `-----END PRIVATE KEY-----`
- Không thêm ký tự `\n` hay escape sequence

---

## PHẦN 5: DEPLOY LÊN STREAMLIT CLOUD

### Bước 1: Truy cập Streamlit Cloud
1. Vào [share.streamlit.io](https://share.streamlit.io/)
2. Đăng nhập bằng tài khoản GitHub

### Bước 2: Tạo App mới
1. Bấm **New app** (góc trên phải)
2. Chọn **Use existing repo**
3. Điền thông tin:
   - **Repository:** `TÊN_CỦA_BẠN/bao-cao-san-luong`
   - **Branch:** `main`
   - **Main file path:** `dashboard_production.py`

### Bước 3: Cấu hình Secrets
1. **TRƯỚC KHI** bấm Deploy, bấm vào **Advanced settings**
2. Tìm mục **Secrets**
3. Paste nội dung đã chuẩn bị ở **PHẦN 4** vào ô Secrets
4. Kiểm tra kỹ format, đặc biệt là phần `private_key`

### Bước 4: Deploy!
1. Bấm **Deploy!**
2. Chờ 2-5 phút để Streamlit:
   - Cài đặt dependencies từ `requirements.txt`
   - Khởi chạy ứng dụng
   - Kết nối với Google Sheets

### ✅ Kiểm tra
- Nếu thành công: Dashboard sẽ hiển thị dữ liệu từ Google Sheets
- Nếu lỗi: Xem logs để debug (thường là lỗi format `private_key`)

---

## PHẦN 6: CẬP NHẬT CODE SAU NÀY

Khi bạn sửa code trên máy tính và muốn cập nhật lên Streamlit Cloud:

```bash
# 1. Thêm file đã thay đổi
git add .

# 2. Commit với message mô tả thay đổi
git commit -m "Cap nhat tinh nang ABC"

# 3. Đẩy lên GitHub
git push
```

**Streamlit Cloud sẽ tự động phát hiện và deploy lại sau 1-2 phút!**

---

## 🔧 XỬ LÝ SỰ CỐ THƯỜNG GẶP

### ❌ Lỗi: "Unable to load PEM file"
**Nguyên nhân:** Format `private_key` sai trong Secrets.

**Giải pháp:**
1. Vào Streamlit Cloud → App settings → Secrets
2. Kiểm tra `private_key`:
   - Phải bọc trong `"""..."""`
   - Giữ nguyên `-----BEGIN PRIVATE KEY-----` và `-----END PRIVATE KEY-----`
   - Không có ký tự escape `\n`

### ❌ Lỗi: "Permission denied" khi push
**Nguyên nhân:** Chưa xác thực với GitHub.

**Giải pháp:**
1. Tạo Personal Access Token:
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token → Chọn quyền `repo`
2. Dùng token thay cho mật khẩu khi push

### ❌ Lỗi: "Module not found"
**Nguyên nhân:** Thiếu thư viện trong `requirements.txt`.

**Giải pháp:**
Kiểm tra file `requirements.txt` có đầy đủ:
```txt
streamlit
gspread
google-auth
pandas
plotly
openpyxl
msoffcrypto-tool
```

### ❌ Dashboard không hiển thị dữ liệu
**Nguyên nhân:** Chưa share Google Sheets với Service Account.

**Giải pháp:**
1. Mở file `api-agent-*.json`, copy email trong `client_email`
2. Vào Google Sheets → Share → Paste email → Cho quyền Editor
3. Làm với TẤT CẢ các sheets cần dùng

---

## 📊 DANH SÁCH FILE CẦN THIẾT ĐỂ DEPLOY

✅ **Các file BẮT BUỘC phải có trên GitHub:**
- `dashboard_production.py` - File chính
- `requirements.txt` - Danh sách thư viện
- `calculate_all_overdue_metrics.py`
- `calculate_pkt_overdue_orders.py`
- `qc_capacity_helper.py`
- Các file Python khác được import

❌ **Các file KHÔNG cần/KHÔNG nên upload:**
- `api-agent-*.json` - Cấu hình qua Secrets
- `*.xlsx`, `*.xlsm` - File Excel (dữ liệu đã sync lên Google Sheets)
- `*.log` - File log
- `__pycache__/` - Python cache

---

## 🎯 CHECKLIST TRƯỚC KHI DEPLOY

- [ ] File `.gitignore` đã cấu hình đúng
- [ ] Code chạy thành công trên local
- [ ] File `requirements.txt` đầy đủ
- [ ] Repository đã tạo trên GitHub (Private)
- [ ] Code đã push lên GitHub
- [ ] Secrets đã cấu hình đúng trên Streamlit Cloud
- [ ] Google Sheets đã share với Service Account email
- [ ] Đã test deploy và kiểm tra logs

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề, kiểm tra:
1. **Logs trên Streamlit Cloud** - Xem lỗi chi tiết
2. **GitHub Repository** - Đảm bảo code đã push
3. **Google Sheets permissions** - Kiểm tra quyền truy cập
4. **Secrets format** - Đặc biệt là `private_key`

---

**Chúc bạn deploy thành công! 🚀**
