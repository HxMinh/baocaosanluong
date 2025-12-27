# -*- coding: utf-8 -*-
"""
Streamlit Dashboard - Báo cáo tổng hợp từ nhiều nguồn
- KHSX từ Excel trên NAS
- Nhân sự từ Google Sheet
- Sản lượng từ Google Sheet
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# Cấu hình trang
st.set_page_config(
    page_title="Báo cáo Sản xuất",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ============= CẤU HÌNH =============
CONFIG = {
    'nas_path': r"\\servert8\Kế hoạch\KẾ HOẠCH SẢN XUẤT",
    'excel_file': "KHSX TONG.xlsx",
    'excel_password': None,  # Thay bằng mật khẩu nếu có
    
    # Google Sheets
    'google_credentials': 'api-agent-471608-912673253587.json',
    'google_sheet_url': 'https://docs.google.com/spreadsheets/d/1F2NzTR50kXzGx9Pc5KdBwwqnIRXGvViPv6mgw8YMNW0/edit',
    'google_worksheets': {
        'phtcv': 'PHTCV',
        'gckt_gpkt': 'GCKT_GPKT',
        'machine_list': 'machine_list',
        'trien_khai_3d': 'trien_khai_3d_laze',
        'thoi_gian_ht': 'thoi_gian_hoan_thanh',
        'nhan_su': '__HR_SYSTEM__Daily Head Counts'
    },
}

# ============= FUNCTIONS =============

# Google Sheets Functions
@st.cache_resource
def authenticate_google_sheets():
    """Xác thực với Google Sheets API"""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        creds = Credentials.from_service_account_file(
            CONFIG['google_credentials'],
            scopes=scopes
        )
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Lỗi xác thực Google Sheets: {e}")
        return None

@st.cache_data(ttl=300)  # Cache 5 phút
def read_google_sheet(worksheet_name):
    """Đọc dữ liệu từ Google Sheet worksheet"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        # Mở spreadsheet
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        
        # Lấy worksheet
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Đọc tất cả dữ liệu
        data = worksheet.get_all_values()
        
        # Chuyển thành DataFrame
        if data and len(data) > 1:
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            
            # Loại bỏ các dòng hoàn toàn trống
            df = df.dropna(axis=0, how='all')
            
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Lỗi đọc Google Sheet '{worksheet_name}': {e}")
        return None

# Excel NAS Functions
def read_excel_from_nas(nas_path, file_name, password=None, sheet_name=0):
    """Đọc file Excel từ NAS"""
    try:
        full_path = os.path.join(nas_path, file_name)
        
        if not os.path.exists(full_path):
            st.error(f"Không tìm thấy file: {full_path}")
            return None
        
        # Phương pháp 1: Thử đọc bằng pandas với các engine khác nhau
        if not password:
            engines = ['openpyxl', 'xlrd', None]
            
            for engine in engines:
                try:
                    if engine:
                        df = pd.read_excel(full_path, sheet_name=sheet_name, engine=engine)
                    else:
                        df = pd.read_excel(full_path, sheet_name=sheet_name)
                    st.success(f"✅ Đọc file thành công bằng engine: {engine or 'default'}")
                    return df
                except Exception as e:
                    continue
        
        # Phương pháp 2: Sử dụng win32com (Excel application)
        st.info("Đang thử đọc file bằng Microsoft Excel...")
        try:
            # Import và khởi tạo COM
            import pythoncom
            import pywintypes
            import win32com.client
            import tempfile
            
            # Khởi tạo COM
            pythoncom.CoInitialize()
            
            try:
                excel = win32com.client.Dispatch("Excel.Application")
                excel.Visible = False
                excel.DisplayAlerts = False
                
                # Mở workbook
                if password:
                    wb = excel.Workbooks.Open(full_path, Password=password)
                else:
                    wb = excel.Workbooks.Open(full_path)
                
                # Lấy sheet
                if isinstance(sheet_name, int):
                    ws = wb.Worksheets(sheet_name + 1)  # Excel index starts from 1
                else:
                    ws = wb.Worksheets(sheet_name)
                
                # Đọc dữ liệu trực tiếp từ Excel thay vì qua CSV
                # Lấy vùng dữ liệu đã sử dụng
                used_range = ws.UsedRange
                data = used_range.Value
                
                # Đóng Excel
                wb.Close(False)
                excel.Quit()
                
                # Chuyển đổi thành DataFrame
                if data and len(data) > 3:
                    # Luôn luôn bỏ qua 2 dòng đầu, dòng thứ 3 (index 2) là header
                    headers = list(data[2])
                    rows = data[3:]  # Dữ liệu bắt đầu từ dòng thứ 4
                    
                    # Xử lý duplicate column names
                    seen = {}
                    for i, col in enumerate(headers):
                        if col is None or col == '':
                            headers[i] = f'Unnamed_{i}'
                        else:
                            col_str = str(col)
                            if col_str in seen:
                                seen[col_str] += 1
                                headers[i] = f'{col_str}_{seen[col_str]}'
                            else:
                                seen[col_str] = 0
                    
                    df = pd.DataFrame(rows, columns=headers)
                    
                    # Loại bỏ các cột hoàn toàn trống
                    df = df.dropna(axis=1, how='all')
                    
                    # Loại bỏ các dòng hoàn toàn trống
                    df = df.dropna(axis=0, how='all')
                    
                    # Reset index để bắt đầu từ 0
                    df = df.reset_index(drop=True)
                else:
                    df = pd.DataFrame()
                
                st.success("✅ Đọc file thành công bằng Microsoft Excel!")
                return df
                
            finally:
                # Luôn uninitialize COM
                pythoncom.CoUninitialize()
            
        except Exception as e:
            st.error(f"Lỗi đọc file bằng Excel: {str(e)}")
            try:
                excel.Quit()
            except:
                pass
            try:
                pythoncom.CoUninitialize()
            except:
                pass
        
        return None
    
    except Exception as e:
        st.error(f"Lỗi đọc file Excel: {str(e)}")
        return None

@st.cache_data(ttl=300)
def read_google_sheet(sheet_url, sheet_name=None):
    """Đọc dữ liệu từ Google Sheet"""
    try:
        # Placeholder - sẽ implement sau
        st.warning("Chức năng Google Sheet đang được phát triển")
        return None
    except Exception as e:
        st.error(f"Lỗi đọc Google Sheet: {str(e)}")
        return None

def display_dataframe_info(df, title):
    """Hiển thị thông tin DataFrame"""
    if df is not None:
        st.markdown(f"### {title}")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Số dòng", f"{len(df):,}")
        with col2:
            st.metric("Số cột", len(df.columns))
        with col3:
            st.metric("Kích thước", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

def create_summary_charts(df):
    """Tạo biểu đồ tổng quan"""
    if df is None or df.empty:
        st.warning("Không có dữ liệu để hiển thị biểu đồ")
        return
    
    # Placeholder - sẽ tùy chỉnh theo cấu trúc dữ liệu thực tế
    st.info("Biểu đồ sẽ được tùy chỉnh theo cấu trúc dữ liệu của bạn")

# ============= MAIN APP =============

def main():
    # Header
    st.markdown('<div class="main-header">📊 BÁO CÁO SẢN XUẤT TỔNG HỢP</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        
        # Nút refresh
        if st.button("🔄 Tải lại dữ liệu", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Chọn nguồn dữ liệu
        st.subheader("Nguồn dữ liệu")
        show_khsx = st.checkbox("KHSX (Excel NAS)", value=True)
        show_nhan_su = st.checkbox("Nhân sự (Google Sheet)", value=False)
        show_san_luong = st.checkbox("Sản lượng (Google Sheet)", value=False)
        
        st.markdown("---")
        
        # Thông tin
        st.subheader("📌 Thông tin")
        st.caption(f"Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
        st.caption(f"NAS Path: {CONFIG['nas_path']}")
    
    # Main content
    tabs = st.tabs(["📈 Tổng quan", "📊 KHSX", "👥 Nhân sự", "📦 Sản lượng", "⚙️ Cài đặt"])
    
    # Tab 1: Tổng quan
    with tabs[0]:
        st.header("Tổng quan")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Kế hoạch SX", "Đang tải...", delta="0%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Nhân sự", "Đang tải...", delta="0")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Sản lượng", "Đang tải...", delta="0%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 Nhấn nút 'Tải lại dữ liệu' ở sidebar để cập nhật dữ liệu mới nhất")
    
    # Tab 2: KHSX
    with tabs[1]:
        st.header("📊 Kế hoạch Sản xuất (KHSX)")
        
        if show_khsx:
            with st.spinner("Đang tải dữ liệu từ NAS..."):
                df_khsx = read_excel_from_nas(
                    CONFIG['nas_path'],
                    CONFIG['excel_file'],
                    CONFIG['excel_password']
                )
                
                if df_khsx is not None:
                    st.markdown('<div class="success-box">✅ Tải dữ liệu thành công!</div>', unsafe_allow_html=True)
                    st.markdown("")
                    
                    # Hiển thị thông tin
                    display_dataframe_info(df_khsx, "Thông tin dữ liệu KHSX")
                    
                    # Hiển thị dữ liệu
                    st.markdown("### Dữ liệu chi tiết")
                    
                    # Filter options
                    col1, col2 = st.columns(2)
                    with col1:
                        search = st.text_input("🔍 Tìm kiếm", placeholder="Nhập từ khóa...")
                    with col2:
                        show_rows = st.selectbox("Hiển thị", [10, 25, 50, 100, "Tất cả"], index=1)
                    
                    # Apply filters
                    df_display = df_khsx.copy()
                    if search:
                        mask = df_display.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
                        df_display = df_display[mask]
                    
                    if show_rows != "Tất cả":
                        df_display = df_display.head(show_rows)
                    
                    # Display table
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        height=400
                    )
                    
                    # Download button
                    st.download_button(
                        label="📥 Tải xuống CSV",
                        data=df_khsx.to_csv(index=False).encode('utf-8-sig'),
                        file_name=f"KHSX_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    # Biểu đồ
                    st.markdown("---")
                    create_summary_charts(df_khsx)
                else:
                    st.markdown('<div class="error-box">❌ Không thể tải dữ liệu KHSX</div>', unsafe_allow_html=True)
        else:
            st.info("Bật hiển thị KHSX ở sidebar để xem dữ liệu")
    
    # Tab 3: Nhân sự
    with tabs[2]:
        st.header("👥 Nhân sự")
        
        if show_nhan_su:
            st.warning("🚧 Chức năng đang được phát triển - Cần cấu hình Google Sheet API")
            
            st.markdown("""
            ### Hướng dẫn cấu hình Google Sheet:
            1. Tạo Google Cloud Project
            2. Bật Google Sheets API
            3. Tạo Service Account và tải credentials
            4. Chia sẻ Google Sheet với email Service Account
            5. Cập nhật link Google Sheet vào cấu hình
            """)
        else:
            st.info("Bật hiển thị Nhân sự ở sidebar để xem dữ liệu")
    
    # Tab 4: Sản lượng
    with tabs[3]:
        st.header("📦 Sản lượng")
        
        if show_san_luong:
            st.warning("🚧 Chức năng đang được phát triển - Cần cấu hình Google Sheet API")
        else:
            st.info("Bật hiển thị Sản lượng ở sidebar để xem dữ liệu")
    
    # Tab 5: Cài đặt
    with tabs[4]:
        st.header("⚙️ Cài đặt")
        
        st.subheader("Cấu hình NAS")
        nas_path = st.text_input("Đường dẫn NAS", value=CONFIG['nas_path'])
        excel_file = st.text_input("Tên file Excel", value=CONFIG['excel_file'])
        excel_password = st.text_input("Mật khẩu Excel (nếu có)", type="password")
        
        st.markdown("---")
        
        st.subheader("Cấu hình Google Sheets")
        gsheet_nhan_su = st.text_input("Link Google Sheet Nhân sự")
        gsheet_san_luong = st.text_input("Link Google Sheet Sản lượng")
        
        if st.button("💾 Lưu cấu hình"):
            st.success("Cấu hình đã được lưu! (Chức năng lưu vào file config sẽ được thêm)")

if __name__ == "__main__":
    main()
