# 🔍 KIỂM TRA VÀ SỬA LỖI DEPLOYMENT

## ❌ LỖI HIỆN TẠI

Từ ảnh bạn gửi, tôi thấy lỗi:
```
Không thể tải dữ liệu GCKT_GPKT
```

## 🔧 NGUYÊN NHÂN VÀ CÁCH SỬA

### Nguyên nhân 1: Google Sheets chưa được share với Service Account

**Kiểm tra:**
1. Mở Google Sheet có tên chứa "GCKT" hoặc "GPKT"
2. Bấm nút **Share** (góc trên phải)
3. Kiểm tra xem email này có trong danh sách chưa:
   ```
   api-streamlit@api-agent-471608.iam.gserviceaccount.com
   ```

**Cách sửa:**
1. Nếu chưa có → Bấm **Share**
2. Paste email: `api-streamlit@api-agent-471608.iam.gserviceaccount.com`
3. Chọn quyền: **Editor**
4. Bỏ tick "Notify people"
5. Bấm **Share**
6. Vào Streamlit Cloud → **Reboot app**

---

### Nguyên nhân 2: Tên worksheet trong Google Sheets không đúng

**Kiểm tra:**
Dashboard đang tìm worksheet tên: `GCKT_GPKT`

1. Mở Google Sheet
2. Xem các tab ở dưới cùng
3. Có tab tên chính xác là `GCKT_GPKT` không?

**Lưu ý:** 
- Tên phải khớp CHÍNH XÁC (phân biệt hoa thường)
- Không có khoảng trắng thừa
- Không có ký tự đặc biệt

**Cách sửa:**
- Nếu tên tab khác → Đổi tên tab thành `GCKT_GPKT`
- Hoặc sửa code để khớp với tên tab thực tế

---

### Nguyên nhân 3: Google Sheet ID không đúng trong code

**Kiểm tra:**
Code đang dùng Google Sheet ID nào để load dữ liệu GCKT_GPKT?

**Cách kiểm tra:**
1. Mở Google Sheet chứa dữ liệu GCKT_GPKT
2. Xem URL, copy phần ID:
   ```
   https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
   ```
3. Kiểm tra trong code `dashboard_production.py` xem ID có đúng không

**Cách sửa:**
- Nếu ID sai → Sửa lại trong code
- Push lên GitHub
- Streamlit sẽ tự động deploy lại

---

### Nguyên nhân 4: Secrets chưa được cấu hình đúng trên Streamlit Cloud

**Kiểm tra:**
1. Vào Streamlit Cloud
2. Chọn app của bạn
3. Bấm **Settings** (⚙️) → **Secrets**
4. Kiểm tra xem có nội dung không

**Cách sửa:**
1. Nếu trống hoặc sai → Mở file `streamlit_secrets.toml` trên máy
2. Copy TOÀN BỘ nội dung
3. Paste vào Secrets trên Streamlit Cloud
4. Bấm **Save**
5. Bấm **Reboot app**

---

## 📊 CÁCH KIỂM TRA NHANH

### Kiểm tra Logs trên Streamlit Cloud

1. Vào app trên Streamlit Cloud
2. Bấm vào **Manage app** (góc dưới phải)
3. Xem tab **Logs**
4. Tìm dòng lỗi chi tiết, thường sẽ có:
   - `gspread.exceptions.APIError` → Lỗi permissions
   - `gspread.exceptions.WorksheetNotFound` → Không tìm thấy worksheet
   - `gspread.exceptions.SpreadsheetNotFound` → Không tìm thấy spreadsheet
   - `Unable to load PEM file` → Lỗi Secrets

### Kiểm tra từng Google Sheet

Chạy script này trên máy local để kiểm tra:

```python
import gspread
from google.oauth2.service_account import Credentials

# Load credentials
creds = Credentials.from_service_account_file(
    'api-agent-471608-912673253587.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
client = gspread.authorize(creds)

# Thử mở sheet GCKT_GPKT
try:
    # Thay SHEET_ID bằng ID thực tế
    sheet = client.open_by_key('SHEET_ID')
    worksheet = sheet.worksheet('GCKT_GPKT')
    print(f"✅ Thành công! Tìm thấy worksheet: {worksheet.title}")
    print(f"   Số dòng: {worksheet.row_count}")
    print(f"   Số cột: {worksheet.col_count}")
except Exception as e:
    print(f"❌ Lỗi: {e}")
```

---

## 🎯 HÀNH ĐỘNG NGAY

### Bước 1: Xác định nguyên nhân
Hãy cho tôi biết:
1. **Bạn đã share Google Sheets với service account chưa?**
2. **Tên worksheet trong Google Sheet là gì?** (xem tab ở dưới cùng)
3. **Logs trên Streamlit Cloud hiển thị lỗi gì?** (copy dòng lỗi)

### Bước 2: Sửa lỗi theo hướng dẫn trên

### Bước 3: Reboot app
Sau khi sửa → Vào Streamlit Cloud → Settings → **Reboot app**

---

## 📞 CẦN HỖ TRỢ

Nếu vẫn lỗi, hãy cung cấp:
1. Screenshot logs từ Streamlit Cloud
2. Tên các worksheet trong Google Sheet
3. Xác nhận đã share với service account chưa

---

**Hãy cho tôi biết kết quả kiểm tra để tôi giúp bạn sửa lỗi cụ thể!** 🔍
