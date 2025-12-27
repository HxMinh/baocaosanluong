# Khắc Phục Lỗi Quota Exceeded

## 🔍 Vấn đề

Báo cáo sản lượng gặp lỗi **"quota exceeded"** từ Google Sheets API. Sau khi reboot lại thì hoạt động bình thường, nhưng sau một thời gian lại bị lỗi.

### Nguyên nhân:

1. **Cache TTL quá ngắn (5 phút)** → Mỗi 5 phút app sẽ đọc lại TẤT CẢ dữ liệu từ Google Sheets
2. **Đọc song song 8 sheets cùng lúc** → Tạo ra hàng chục API calls đồng thời
3. **Batch reading không có delay** → API calls liên tiếp không có khoảng nghỉ
4. **Không có retry logic** → Khi gặp lỗi quota thì fail ngay lập tức

## ✅ Giải pháp đã áp dụng

### 1. Tăng Cache TTL (30 phút)

**Trước:**
```python
@st.cache_data(ttl=300)  # 5 phút
def read_gckt_data():
    ...
```

**Sau:**
```python
@st.cache_data(ttl=1800)  # 30 phút
def read_gckt_data():
    ...
```

**Lợi ích:** Giảm tần suất đọc dữ liệu từ 12 lần/giờ xuống 2 lần/giờ → Giảm 83% API calls

---

### 2. Thêm Retry Logic với Exponential Backoff

**Thêm hàm mới:**
```python
def retry_with_backoff(func, max_retries=5, initial_delay=1):
    """
    Retry a function with exponential backoff when encountering quota errors
    
    - Lần 1: Đợi 1 giây
    - Lần 2: Đợi 2 giây
    - Lần 3: Đợi 4 giây
    - Lần 4: Đợi 8 giây
    - Lần 5: Đợi 16 giây
    """
    for attempt in range(max_retries):
        try:
            result = func()
            time.sleep(0.5)  # Delay nhỏ giữa các calls thành công
            return result
        except Exception as e:
            if 'quota' in str(e).lower():
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    st.warning(f"⚠️ Quota exceeded, đang chờ {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    st.error("❌ Vượt quota sau 5 lần thử")
                    raise
            else:
                raise
```

**Áp dụng cho tất cả API calls:**
```python
# Trước
data = worksheet.get_all_values()

# Sau
data = retry_with_backoff(lambda: worksheet.get_all_values())
```

**Lợi ích:** 
- Tự động retry khi gặp lỗi quota
- Không cần reboot thủ công
- Tăng độ tin cậy của app

---

### 3. Giảm Parallel Workers (8 → 3)

**Trước:**
```python
with ThreadPoolExecutor(max_workers=8) as executor:
    # Đọc 8 sheets cùng lúc
```

**Sau:**
```python
with ThreadPoolExecutor(max_workers=3) as executor:
    # Đọc tối đa 3 sheets cùng lúc
```

**Lợi ích:** Giảm số lượng API calls đồng thời → Tránh vượt quota

---

### 4. Thêm Delay giữa Batch Reads

**Trong hàm `read_gckt_data`:**
```python
for start_row in range(2, row_count + 1, batch_size):
    batch_data = retry_with_backoff(
        lambda: worksheet.get_values(f'A{start_row}:...')
    )
    if batch_data:
        all_data.extend(batch_data)
    
    # Thêm delay 1 giây giữa các batch
    time.sleep(1)
```

**Lợi ích:** Tránh spam API calls liên tiếp

---

## 📊 Kết quả

| Metric | Trước | Sau | Cải thiện |
|--------|-------|-----|-----------|
| Cache TTL | 5 phút | 30 phút | **6x** |
| API calls/giờ | ~12 lần | ~2 lần | **-83%** |
| Parallel workers | 8 | 3 | **-62%** |
| Retry logic | ❌ Không | ✅ Có | **Auto-recovery** |
| Delay giữa batches | ❌ Không | ✅ 1s | **Tránh spam** |

---

## 🚀 Cách sử dụng

### Khi gặp lỗi quota:

1. **Không cần reboot** - App sẽ tự động retry
2. Chờ thông báo: `⚠️ Quota exceeded, đang chờ Xs...`
3. App sẽ tự động thử lại sau vài giây

### Nếu vẫn gặp lỗi sau 5 lần retry:

1. Đợi **5-10 phút** để quota reset
2. Nhấn nút **"🔄 Làm mới dữ liệu"** trong sidebar
3. Hoặc reload trang

### Tối ưu hóa thêm:

- **Tránh spam nút "Làm mới"** - Chỉ dùng khi thực sự cần
- **Cache sẽ tự động refresh sau 30 phút** - Không cần refresh thủ công
- **Nếu nhiều người dùng cùng lúc** - Có thể tăng cache TTL lên 3600 (1 giờ)

---

## 🔧 Điều chỉnh nếu cần

### Tăng cache TTL lên 1 giờ:

Trong `dashboard_production.py`, thay đổi:
```python
@st.cache_data(ttl=1800)  # 30 phút
```

Thành:
```python
@st.cache_data(ttl=3600)  # 1 giờ
```

### Giảm số lượng parallel workers:

Trong hàm `load_all_data_parallel()`:
```python
with ThreadPoolExecutor(max_workers=2) as executor:  # Giảm từ 3 xuống 2
```

### Tăng delay giữa API calls:

Trong hàm `retry_with_backoff()`:
```python
time.sleep(1)  # Tăng từ 0.5s lên 1s
```

---

## 📝 Ghi chú

- **Google Sheets API quota:** 100 requests/100 seconds/user
- **Với 8 sheets + batch reading:** Có thể tạo ra 50+ requests trong vài giây
- **Giải pháp này giảm xuống còn ~15-20 requests** → An toàn hơn nhiều

---

## ✅ Checklist triển khai

- [x] Tăng cache TTL lên 1800 giây (30 phút)
- [x] Thêm retry logic với exponential backoff
- [x] Giảm parallel workers từ 8 xuống 3
- [x] Thêm delay 1s giữa batch reads
- [x] Thêm delay 0.5s giữa successful API calls
- [x] Test trên local
- [ ] Deploy lên Streamlit Cloud
- [ ] Monitor trong 24h để đảm bảo không còn lỗi quota

---

**Tác giả:** Antigravity AI  
**Ngày:** 2025-12-27  
**Version:** 1.0
