# 📦 DANH SÁCH FILE ĐÃ UPLOAD LÊN GITHUB

## ✅ CÁC FILE ĐÃ UPLOAD (25 files)

### 📄 File cấu hình
- `.gitignore` - Cấu hình file cần bỏ qua
- `requirements.txt` - Danh sách thư viện Python

### 📚 File hướng dẫn
- `HUONG_DAN_DEPLOY_GITHUB.md` - Hướng dẫn chi tiết deploy
- `HUONG_DAN_SYNC.md` - Hướng dẫn sync Excel
- `QUICK_START.md` - Hướng dẫn nhanh
- `setup_google_sheets.md` - Hướng dẫn setup Google Sheets
- `column_mapping.txt` - Mapping cột dữ liệu

### 🎯 File dashboard chính
- `dashboard_production.py` - Dashboard chính (file main)
- `dashboard_capacity.py` - Dashboard công suất
- `app.py` - App phụ

### 🔧 File tính toán metrics
- `calculate_all_inventory_metrics.py` - Tính toán tồn kho
- `calculate_all_overdue_metrics.py` - Tính toán quá hạn
- `calculate_overdue_orders.py` - Tính toán đơn hàng quá hạn
- `calculate_pkt_overdue_orders.py` - Tính toán PKT quá hạn
- `calculate_rrc_inventory.py` - Tính toán tồn kho RRC
- `qc_capacity_helper.py` - Helper cho QC capacity

### 🔄 File sync Excel
- `khsx_excel_reader.py` - Đọc Excel KHSX
- `khsx_sheets_updater.py` - Cập nhật Google Sheets
- `khsx_sync_config.py` - Cấu hình sync
- `khsx_sync_manager.py` - Quản lý sync
- `upload_khsx_with_progress.py` - Upload với progress bar

### 🛠️ File utility
- `generate_streamlit_secrets.py` - Tạo Streamlit Secrets
- `show_service_account_email.py` - Hiển thị service account email
- `run_khsx_sync.bat` - Batch file chạy sync
- `setup_auto_sync.ps1` - PowerShell setup auto sync

---

## ❌ CÁC FILE KHÔNG UPLOAD (Được bỏ qua bởi .gitignore)

### 🔐 File bảo mật (QUAN TRỌNG - KHÔNG upload)
- `api-agent-471608-912673253587.json` - Google Service Account credentials
- Tất cả file `*.json` khác

### 📊 File Excel (Dữ liệu đã sync lên Google Sheets)
- `File tổng hợp hàng ngày.vba.xlsm`
- `nhật ký máy 16.12.xlsm`
- Tất cả file `*.xlsx`, `*.xlsm`, `*.xls`, `*.xlsb`

### 🗂️ File hệ thống
- `__pycache__/` - Python cache
- `*.pyc`, `*.pyo`, `*.pyd` - Python compiled files
- `*.log` - Log files (như `khsx_sync.log`)
- `*.lnk` - Windows shortcuts (như `KHSX TONG - Shortcut.lnk`)
- `excel_sync/` - Thư mục sync local

### 🧪 File debug/test
- Tất cả file `debug_*.py`
- Tất cả file `test_*.py`
- Tất cả file `check_*.py`

---

## 🎯 TỔNG KẾT

**Tổng số file trong project:** ~35 files  
**Số file upload lên GitHub:** 25 files  
**Số file bị ignore:** ~10 files (bảo mật + dữ liệu + cache)

---

## 📍 REPOSITORY GITHUB

**URL:** https://github.com/HxMinh/baocaosanluong  
**Branch:** main  
**Visibility:** Public (có thể đổi sang Private trong Settings)

---

## ⚠️ LƯU Ý BẢO MẬT

File `api-agent-471608-912673253587.json` chứa thông tin nhạy cảm và **ĐÃ ĐƯỢC BẢO VỆ** bởi `.gitignore`.

Thay vào đó, bạn sẽ cấu hình credentials này trên Streamlit Cloud qua **Secrets** (xem hướng dẫn trong `HUONG_DAN_DEPLOY_GITHUB.md`).

---

## 🔄 CẬP NHẬT SAU NÀY

Khi bạn sửa code, chỉ cần chạy:
```bash
git add .
git commit -m "Mo ta thay doi"
git push
```

GitHub sẽ tự động cập nhật và Streamlit Cloud sẽ tự động deploy lại!
