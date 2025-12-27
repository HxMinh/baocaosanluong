# 🚀 HƯỚNG DẪN NHANH - DEPLOY LÊN STREAMLIT CLOUD

## Bước 1: Tạo nội dung Secrets
Chạy lệnh sau để tạo nội dung Secrets:
```bash
python generate_streamlit_secrets.py
```

Copy toàn bộ output (từ `[gcp_service_account]` đến hết).

---

## Bước 2: Push code lên GitHub

### Lần đầu tiên:
```bash
git init
git add .
git commit -m "Initial commit - Dashboard production"
git branch -M main
git remote add origin https://github.com/TEN_CUA_BAN/bao-cao-san-luong.git
git push -u origin main
```

### Các lần sau (khi cập nhật code):
```bash
git add .
git commit -m "Mo ta thay doi"
git push
```

---

## Bước 3: Deploy trên Streamlit Cloud

1. Vào https://share.streamlit.io/
2. Đăng nhập bằng GitHub
3. Bấm **New app**
4. Chọn repository: `TEN_CUA_BAN/bao-cao-san-luong`
5. Branch: `main`
6. Main file: `dashboard_production.py`
7. **QUAN TRỌNG:** Bấm **Advanced settings**
8. Paste nội dung Secrets từ Bước 1 vào mục **Secrets**
9. Bấm **Deploy!**

---

## ✅ Checklist

- [ ] File `.gitignore` đã cấu hình
- [ ] Đã chạy `generate_streamlit_secrets.py` và copy output
- [ ] Code đã push lên GitHub
- [ ] Secrets đã paste vào Streamlit Cloud
- [ ] Google Sheets đã share với: `api-streamlit@api-agent-471608.iam.gserviceaccount.com`

---

## 🔧 Xử lý lỗi

### Lỗi "Unable to load PEM file"
→ Kiểm tra format `private_key` trong Secrets (phải có `"""..."""`)

### Lỗi "Permission denied" khi push
→ Tạo Personal Access Token trên GitHub

### Dashboard không hiển thị dữ liệu
→ Kiểm tra đã share Google Sheets với Service Account email chưa

---

Xem chi tiết: `HUONG_DAN_DEPLOY_GITHUB.md`
