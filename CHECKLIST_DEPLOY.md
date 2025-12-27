# ✅ CHECKLIST DEPLOY STREAMLIT CLOUD

## PHẦN 1: CHUẨN BỊ ✅ (ĐÃ HOÀN THÀNH)

- [x] Cấu hình `.gitignore` để bảo vệ file nhạy cảm
- [x] Commit code lên Git local
- [x] Kết nối với GitHub repository
- [x] Push code lên GitHub thành công
- [x] Tạo script `generate_streamlit_secrets.py`

---

## PHẦN 2: CẤU HÌNH SECRETS ⏳ (ĐANG CHỜ)

### Bước 1: Tạo nội dung Secrets
Chạy lệnh sau trong terminal:
```bash
python generate_streamlit_secrets.py
```

### Bước 2: Copy output
Copy toàn bộ nội dung từ `[gcp_service_account]` đến hết.

**Output mẫu đã có sẵn từ lần chạy trước:**
```toml
[gcp_service_account]
type = "service_account"
project_id = "api-agent-471608"
private_key_id = "9126732535871a54e35cb50b134418bcb1a49ae4"
private_key = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC5UY6Nqvhr0kZ4
...
-----END PRIVATE KEY-----
"""
client_email = "api-streamlit@api-agent-471608.iam.gserviceaccount.com"
...
```

- [ ] Đã chạy script và copy output

---

## PHẦN 3: DEPLOY LÊN STREAMLIT CLOUD ⏳ (ĐANG CHỜ)

### Bước 1: Truy cập Streamlit Cloud
- [ ] Vào https://share.streamlit.io/
- [ ] Đăng nhập bằng tài khoản GitHub (HxMinh)

### Bước 2: Tạo App mới
- [ ] Bấm nút **New app** (góc trên phải)
- [ ] Chọn **Use existing repo**

### Bước 3: Điền thông tin
- [ ] Repository: `HxMinh/baocaosanluong`
- [ ] Branch: `main`
- [ ] Main file path: `dashboard_production.py`

### Bước 4: Cấu hình Secrets (QUAN TRỌNG!)
- [ ] Bấm **Advanced settings**
- [ ] Tìm mục **Secrets**
- [ ] Paste nội dung từ PHẦN 2 vào ô Secrets
- [ ] Kiểm tra kỹ format `private_key` (phải có `"""..."""`)

### Bước 5: Deploy
- [ ] Bấm **Deploy!**
- [ ] Chờ 2-5 phút để Streamlit cài đặt và khởi chạy

---

## PHẦN 4: KIỂM TRA VÀ XÁC NHẬN ⏳ (SAU KHI DEPLOY)

### Kiểm tra deployment
- [ ] App đã deploy thành công (không có lỗi)
- [ ] Dashboard hiển thị đúng layout
- [ ] Dữ liệu từ Google Sheets hiển thị chính xác
- [ ] Các tab hoạt động bình thường
- [ ] Charts/graphs hiển thị đúng

### Kiểm tra Google Sheets permissions
- [ ] Tất cả Google Sheets đã share với: `api-streamlit@api-agent-471608.iam.gserviceaccount.com`
- [ ] Service account có quyền **Editor**

### Kiểm tra logs (nếu có lỗi)
- [ ] Xem logs trên Streamlit Cloud
- [ ] Xác định lỗi (thường là Secrets hoặc permissions)
- [ ] Sửa lỗi và reboot app

---

## PHẦN 5: SAU KHI DEPLOY THÀNH CÔNG 🎉

### Lưu thông tin
- [ ] Lưu URL của app Streamlit
- [ ] Bookmark URL để truy cập nhanh
- [ ] Chia sẻ URL với team (nếu cần)

### Cập nhật code sau này
Khi cần sửa code:
```bash
git add .
git commit -m "Mo ta thay doi"
git push
```
Streamlit Cloud sẽ tự động deploy lại sau 1-2 phút.

- [ ] Đã test quy trình cập nhật code

---

## 🔧 XỬ LÝ LỖI THƯỜNG GẶP

### ❌ Lỗi: "Unable to load PEM file"
**Nguyên nhân:** Format `private_key` sai trong Secrets

**Giải pháp:**
1. Vào Streamlit Cloud → App settings → Secrets
2. Kiểm tra `private_key` phải bọc trong `"""..."""`
3. Không có ký tự escape `\n`
4. Save và reboot app

### ❌ Lỗi: "Permission denied" hoặc "403 Forbidden"
**Nguyên nhân:** Chưa share Google Sheets với Service Account

**Giải pháp:**
1. Mở từng Google Sheet cần dùng
2. Bấm **Share**
3. Paste email: `api-streamlit@api-agent-471608.iam.gserviceaccount.com`
4. Cho quyền **Editor**
5. Reboot app trên Streamlit Cloud

### ❌ Lỗi: "Module not found"
**Nguyên nhân:** Thiếu thư viện trong `requirements.txt`

**Giải pháp:**
1. Kiểm tra file `requirements.txt` có đầy đủ thư viện
2. Nếu thiếu, thêm vào và push lên GitHub
3. Streamlit Cloud sẽ tự động cài đặt lại

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề:
1. Xem logs chi tiết trên Streamlit Cloud
2. Kiểm tra file `HUONG_DAN_DEPLOY_GITHUB.md`
3. Xem phần "XỬ LÝ SỰ CỐ THƯỜNG GẶP" trong hướng dẫn

---

**Repository GitHub:** https://github.com/HxMinh/baocaosanluong  
**Service Account Email:** api-streamlit@api-agent-471608.iam.gserviceaccount.com

---

**Cập nhật lần cuối:** 2025-12-27
