# Hướng Dẫn Sync KHSX TONG → Google Sheets

## ⚠️ VẤN ĐỀ PERFORMANCE ĐÃ PHÁT HIỆN

### Nguyên Nhân Đọc Lâu (10-25 phút)

**File Excel trên network drive:**
```
\\servert8\Kế hoạch\KẾ HOẠCH SẢN XUẤT\KHSX TONG.xlsx
```

**3 yếu tố gây chậm:**

1. **Network latency** 
   - Đọc file qua mạng LAN/SMB protocol
   - Tốc độ phụ thuộc vào băng thông mạng

2. **File encryption** 
   - File có password `1985`
   - Phải decrypt toàn bộ file vào memory trước khi đọc

3. **Kích thước file lớn**
   - File KHSX TONG có nhiều sheets
   - Mỗi sheet `KHSX` và `KHSX NB` có thể có hàng ngàn dòng

### ⚡ GIẢI PHÁP: Copy File về Local Trước

**Lợi ích:** Giảm thời gian từ **15 phút → 1-2 phút**

## 🚀 Cách Chạy

### Option 1: Test Nhanh (Copy về local)
```bash
cd "C:\Users\Admin\OneDrive\computer\làm báo cáo trên streamlit"
python test_local_copy.py
```

### Option 2: Test Trực Tiếp (Chậm - 15 phút)
```bash
python khsx_sheets_updater.py
```

### Option 3: Sync Tự Động
```bash
python khsx_sync_manager.py
```

## 📋 Kiểm Tra Kết Quả

Google Sheets: https://docs.google.com/spreadsheets/d/1F2NzTR50kXzGx9Pc5KdBwwqnIRXGvViPv6mgw8YMNW0/edit

Sẽ thấy 2 tabs:
- `KHSX_KHSX`
- `KHSX_KHSX NB`

## 🔧 Cấu Hình

File: `khsx_sync_config.py`

```python
CONFIG = {
    'sync_interval_seconds': 3600,  # 1 giờ
    'debounce_seconds': 30,         # Chờ 30s sau khi file thay đổi
}
```
