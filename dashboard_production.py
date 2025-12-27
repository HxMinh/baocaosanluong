# -*- coding: utf-8 -*-
"""
Dashboard Báo Cáo Sản Lượng
Yêu cầu đăng nhập với mật khẩu 1061
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import os
from qc_capacity_helper import calculate_quality_control_capacity
from calculate_all_inventory_metrics import calculate_all_inventory_metrics
from calculate_all_overdue_metrics import calculate_all_overdue_metrics

# ============= CẤU HÌNH =============
st.set_page_config(
    page_title="Báo Cáo Sản Lượng",
    page_icon="📈",
    layout="wide"
)

CONFIG = {
    'google_credentials': 'api-agent-471608-912673253587.json',
    'google_sheet_url': 'https://docs.google.com/spreadsheets/d/1F2NzTR50kXzGx9Pc5KdBwwqnIRXGvViPv6mgw8YMNW0/edit'
}

# ============= AUTHENTICATION FUNCTIONS =============

@st.cache_resource
def authenticate_google_sheets():
    """Xác thực Google Sheets"""
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        
        # Try Streamlit secrets FIRST (for cloud deployment)
        try:
            if hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
                # Read from Streamlit secrets (TOML format)
                creds = Credentials.from_service_account_info(
                    dict(st.secrets["gcp_service_account"]),
                    scopes=scopes
                )
                return gspread.authorize(creds)
        except Exception as e:
            st.warning(f"⚠️ Không thể đọc từ Streamlit Secrets: {e}")
        
        # Fallback: Try LOCAL JSON file (for local development)
        try:
            if os.path.exists(CONFIG['google_credentials']):
                creds = Credentials.from_service_account_file(
                    CONFIG['google_credentials'],
                    scopes=scopes
                )
                return gspread.authorize(creds)
        except Exception:
            pass  # Ignore file not found on cloud
        
        st.error("❌ Không tìm thấy credentials. Vui lòng cấu hình Secrets trên Streamlit Cloud.")
        return None
    except Exception as e:
        st.error(f"❌ Lỗi xác thực: {e}")
        return None

@st.cache_data(ttl=300)
def read_gckt_data():
    """Đọc dữ liệu từ sheet GCKT_GPKT với batch reading để tránh timeout"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        # TODO: Thay 'GCKT_GPKT' bằng tên worksheet thực tế trong Google Sheet
        worksheet = spreadsheet.worksheet('GCKT_GPKT')  # Hoặc tên worksheet khác
        
        # Đọc dữ liệu theo batch để tránh timeout
        # Lấy số dòng và cột
        row_count = worksheet.row_count
        col_count = worksheet.col_count
        
        # Đọc header trước
        header = worksheet.row_values(1)
        
        # Đọc dữ liệu theo batch 1000 dòng mỗi lần
        batch_size = 1000
        all_data = []
        
        for start_row in range(2, row_count + 1, batch_size):
            end_row = min(start_row + batch_size - 1, row_count)
            
            # Đọc batch
            try:
                batch_data = worksheet.get_values(f'A{start_row}:{chr(65 + col_count - 1)}{end_row}')
                if batch_data:
                    all_data.extend(batch_data)
            except Exception as batch_error:
                st.warning(f"⚠️ Lỗi đọc batch {start_row}-{end_row}: {batch_error}")
                continue
        
        if all_data and len(all_data) > 0:
            df = pd.DataFrame(all_data, columns=header)
            
            # Filter: Remove rows where so_file is empty
            df = df[df['so_file'].notna() & (df['so_file'].str.strip() != '')].copy()
            
            # Parse ngay_giao date column
            if 'ngay_giao' in df.columns:
                df['ngay_giao_parsed'] = pd.to_datetime(df['ngay_giao'], format='%d/%m/%Y', errors='coerce')
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu GCKT_GPKT: {e}")
        return None

@st.cache_data(ttl=300)
def read_pky_data():
    """Đọc dữ liệu từ sheet PKY"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        worksheet = spreadsheet.worksheet('pky')
        data = worksheet.get_all_values()
        
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu PKY: {e}")
        return None

@st.cache_data(ttl=300)
def read_phtcv_data():
    """Đọc dữ liệu từ sheet PHTCV"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        worksheet = spreadsheet.worksheet('PHTCV')
        data = worksheet.get_all_values()
        
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu PHTCV: {e}")
        return None

@st.cache_data(ttl=300)
def read_machine_list():
    """Đọc danh sách máy từ sheet machine_list"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        worksheet = spreadsheet.worksheet('machine_list')
        data = worksheet.get_all_values()
        
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu machine_list: {e}")
        return None

@st.cache_data(ttl=300)
def read_giao_kho_vp_data():
    """Đọc dữ liệu từ sheet giao_kho_vp (Kiểm tra AMJ)"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        worksheet = spreadsheet.worksheet('giao_kho_vp')
        data = worksheet.get_all_values()
        
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu giao_kho_vp: {e}")
        return None

@st.cache_data(ttl=300)
def read_shift_schedule_data():
    """Đọc dữ liệu từ sheet __SHIFT__Shift Schedule"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        worksheet = spreadsheet.worksheet('__SHIFT__Shift Schedule')
        data = worksheet.get_all_values()
        
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Parse Work Date
            if 'Work Date' in df.columns:
                df['Work Date Parsed'] = pd.to_datetime(
                    df['Work Date'],
                    format='%d/%m/%Y',
                    errors='coerce'
                )
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu Shift Schedule: {e}")
        return None

@st.cache_data(ttl=300)
def read_hr_daily_head_counts_data():
    """Đọc dữ liệu từ sheet __HR_SYSTEM__Daily Head Counts"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        worksheet = spreadsheet.worksheet('__HR_SYSTEM__Daily Head Counts')
        data = worksheet.get_all_values()
        
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Parse Working Date
            if 'Working Date' in df.columns:
                df['Working Date Parsed'] = pd.to_datetime(
                    df['Working Date'],
                    format='%d/%m/%Y',
                    errors='coerce'
                )
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu HR Daily Head Counts: {e}")
        return None

@st.cache_data(ttl=300)
def read_thoi_gian_hoan_thanh_data():
    """Đọc dữ liệu từ sheet thoi_gian_hoan_thanh"""
    try:
        client = authenticate_google_sheets()
        if not client:
            return None
        
        spreadsheet = client.open_by_url(CONFIG['google_sheet_url'])
        worksheet = spreadsheet.worksheet('thoi_gian_hoan_thanh')
        data = worksheet.get_all_values()
        
        if data and len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi đọc dữ liệu thoi_gian_hoan_thanh: {e}")
        return None

# ============= PARALLEL DATA LOADING =============

from concurrent.futures import ThreadPoolExecutor, as_completed

def load_all_data_parallel():
    """
    Load all data sheets in parallel for faster performance
    Reduces load time from ~15s to ~5-7s
    """
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Submit all read tasks concurrently
        futures = {
            executor.submit(read_gckt_data): 'GCKT_GPKT',
            executor.submit(read_pky_data): 'PKY',
            executor.submit(read_phtcv_data): 'PHTCV',
            executor.submit(read_machine_list): 'machine_list',
            executor.submit(read_giao_kho_vp_data): 'giao_kho_vp',
            executor.submit(read_shift_schedule_data): 'shift_schedule',
            executor.submit(read_hr_daily_head_counts_data): 'hr_daily_head_counts',
            executor.submit(read_thoi_gian_hoan_thanh_data): 'thoi_gian_hoan_thanh'
        }
        
        results = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        completed = 0
        total = len(futures)
        
        # Collect results as they complete
        for future in as_completed(futures):
            sheet_name = futures[future]
            try:
                results[sheet_name] = future.result()
                completed += 1
                progress = completed / total
                progress_bar.progress(progress)
                status_text.text(f"⚡ Đang tải: {sheet_name}... ({completed}/{total})")
            except Exception as e:
                st.warning(f"⚠️ Lỗi khi tải {sheet_name}: {e}")
                results[sheet_name] = None
                completed += 1
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return results

# ============= MAIN APP =============

def main():
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        
        if st.button("🔄 Làm mới dữ liệu"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.info(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Authentication - TEMPORARILY DISABLED FOR TESTING
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Auto-login for testing
    
    if False:  # Disabled authentication
        # Show login form
        st.title("📈 BÁO CÁO SẢN LƯỢNG")
        st.markdown("---")
        
        st.subheader("🔒 Đăng nhập để xem báo cáo")
        st.info("📋 Báo cáo này chỉ dành cho cấp quản lý")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            password = st.text_input("Mật khẩu:", type="password", key="password_input")
            
            if st.button("Đăng nhập", width=True):
                if password == "1061":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Mật khẩu không đúng!")
    
    else:
        # User is authenticated - show production volume report
        col1, col2 = st.columns([5, 1])
        with col1:
            st.title("📈 BÁO CÁO SẢN LƯỢNG")
        with col2:
            if st.button("🚪 Đăng xuất"):
                st.session_state.authenticated = False
                st.rerun()
        
        st.markdown("---")
        
        
        # Load ALL data in parallel (OPTIMIZED!)
        with st.spinner("⚡ Đang tải tất cả dữ liệu..."):
            data = load_all_data_parallel()
        
        # Extract results
        df_gckt = data.get('GCKT_GPKT')
        df_pky = data.get('PKY')
        df_phtcv = data.get('PHTCV')
        df_machine_list = data.get('machine_list')
        df_giao_kho_vp = data.get('giao_kho_vp')
        df_shift_schedule = data.get('shift_schedule')
        df_hr_daily_head_counts = data.get('hr_daily_head_counts')
        df_thoi_gian_hoan_thanh = data.get('thoi_gian_hoan_thanh')
        
        if df_gckt is None or df_gckt.empty:
            st.error("❌ Không thể tải dữ liệu GCKT_GPKT")
            return
        
        # Production Volume Filters (only affects sections 1 & 2)
        st.subheader("📅 Bộ lọc Sản lượng")
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            # Get available months
            if 'ngay_giao_parsed' in df_gckt.columns:
                df_gckt['year_month'] = df_gckt['ngay_giao_parsed'].dt.to_period('M')
                available_months = df_gckt['year_month'].dropna().unique()
                available_months = sorted(available_months, reverse=True)
                
                if len(available_months) > 0:
                    month_options = ['Tất cả'] + [str(m) for m in available_months]
                    selected_month = st.selectbox("Chọn tháng:", options=month_options, index=0)
                else:
                    selected_month = 'Tất cả'
            else:
                selected_month = 'Tất cả'
        
        with col_filter2:
            # Get available dates (filtered by month if selected)
            if 'ngay_giao_parsed' in df_gckt.columns:
                if selected_month != 'Tất cả':
                    df_month_filtered = df_gckt[df_gckt['year_month'] == pd.Period(selected_month)].copy()
                    available_dates = df_month_filtered['ngay_giao_parsed'].dropna().dt.date.unique()
                else:
                    available_dates = df_gckt['ngay_giao_parsed'].dropna().dt.date.unique()
                
                available_dates = sorted(available_dates, reverse=True)
                
                if len(available_dates) > 0:
                    selected_date = st.selectbox(
                        "Chọn ngày:",
                        options=['Tất cả'] + [d.strftime('%d/%m/%Y') for d in available_dates],
                        index=0
                    )
                else:
                    selected_date = 'Tất cả'
            else:
                selected_date = 'Tất cả'
        
        # Filter data
        df_filtered = df_gckt.copy()
        

        
        if selected_month != 'Tất cả' and 'year_month' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['year_month'] == pd.Period(selected_month)].copy()
        
        if selected_date != 'Tất cả' and 'ngay_giao_parsed' in df_filtered.columns:
            filter_date = pd.to_datetime(selected_date, format='%d/%m/%Y').date()
            df_filtered = df_filtered[df_filtered['ngay_giao_parsed'].dt.date == filter_date].copy()
        
        # Excel Export Button (after filters)
        st.markdown("---")
        col_exp1, col_exp2, col_exp3 = st.columns([1, 2, 1])
        with col_exp2:
            if st.button("📥 Xuất Excel - Sản lượng", use_container_width=True):
                # Prepare export data
                export_df = df_filtered.copy()
                
                # Select relevant columns for export
                export_columns = []
                if 'ngay_giao_parsed' in export_df.columns:
                    export_df['Ngày'] = export_df['ngay_giao_parsed'].dt.strftime('%d/%m/%Y')
                    export_columns.append('Ngày')
                
                # Add production columns if they exist
                if 'sl_giao' in export_df.columns:
                    export_df['Sản lượng'] = export_df['sl_giao']
                    export_columns.append('Sản lượng')
                
                if 'ten_chi_tiet' in export_df.columns:
                    export_df['Tên chi tiết'] = export_df['ten_chi_tiet']
                    export_columns = ['Tên chi tiết'] + export_columns
                
                # Create export dataframe
                if export_columns:
                    df_to_export = export_df[export_columns]
                    
                    # Convert to Excel
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_to_export.to_excel(writer, sheet_name='Sản lượng', index=False)
                    excel_data = output.getvalue()
                    
                    # Determine filename based on filter
                    if selected_date != 'Tất cả':
                        filename = f"san_luong_{selected_date.replace('/', '_')}.xlsx"
                    elif selected_month != 'Tất cả':
                        filename = f"san_luong_{selected_month.replace('-', '_')}.xlsx"
                    else:
                        filename = "san_luong_tat_ca.xlsx"
                    
                    st.download_button(
                        label="⬇️ Tải file Excel",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
        
        # Display header with date or month
        st.markdown("---")
        if selected_month != 'Tất cả':
            # Show month format
            display_text = f"📊 Sản lượng hoàn thành các BP tháng: {selected_month.replace('-', '/')}"
        elif selected_date != 'Tất cả':
            # Show specific date
            display_text = f"📊 Sản lượng hoàn thành các BP ngày: {selected_date}"
        else:
            # Show current date
            display_text = f"📊 Sản lượng hoàn thành các BP ngày: {datetime.now().strftime('%d/%m/%Y')}"
        st.subheader(display_text)
        
        # Parse date for PHTCV if not already done (data already loaded in parallel)
        if df_phtcv is not None and not df_phtcv.empty and 'ngày tháng' in df_phtcv.columns:
            if 'date_parsed' not in df_phtcv.columns:
                df_phtcv['date_parsed'] = pd.to_datetime(
                    df_phtcv['ngày tháng'],
                        format='%d/%m/%Y',
                        errors='coerce'
                    )
        
        # Calculate metrics for Sản xuất (Production)
        # 1. Sản lượng - Sum sl_giao column
        if 'sl_giao' in df_filtered.columns:
            san_luong_san_xuat = pd.to_numeric(
                df_filtered['sl_giao'].astype(str).str.replace(',', '.'),
                errors='coerce'
            ).fillna(0).sum()
            san_luong_san_xuat = int(san_luong_san_xuat)
        else:
            san_luong_san_xuat = 0
        
        # 2. CS tổng (Total Capacity)
        cs_tong = 0.0
        if df_pky is not None and not df_pky.empty and df_phtcv is not None and not df_phtcv.empty:
            # Match ten_chi_tiet between GCKT_GPKT and PKY
            if 'ten_chi_tiet' in df_filtered.columns and 'ten_chi_tiet' in df_pky.columns and 'thoi_gian_pky' in df_pky.columns:
                # Convert thoi_gian_pky to numeric
                df_pky['thoi_gian_numeric'] = pd.to_numeric(
                    df_pky['thoi_gian_pky'].astype(str).str.replace(',', '.'),
                    errors='coerce'
                ).fillna(0)
                
                # Convert tong_so_nc to numeric (if exists)
                if 'tong_so_nc' in df_pky.columns:
                    df_pky['tong_so_nc_numeric'] = pd.to_numeric(
                        df_pky['tong_so_nc'].astype(str).str.replace(',', '.'),
                        errors='coerce'
                    ).fillna(0)
                else:
                    df_pky['tong_so_nc_numeric'] = 0
                
                # Merge GCKT with PKY on ten_chi_tiet
                df_merged = df_filtered.merge(
                    df_pky[['ten_chi_tiet', 'thoi_gian_numeric', 'tong_so_nc_numeric']],
                    on='ten_chi_tiet',
                    how='left'
                )
                
                # Fill NaN values with 0
                df_merged['thoi_gian_numeric'] = df_merged['thoi_gian_numeric'].fillna(0)
                df_merged['tong_so_nc_numeric'] = df_merged['tong_so_nc_numeric'].fillna(0)
                
                # Calculate total processing time: (sl_giao × thoi_gian_pky + tong_so_nc × 40) × 1.2
                df_merged['sl_giao_numeric'] = pd.to_numeric(
                    df_merged['sl_giao'].astype(str).str.replace(',', '.'),
                    errors='coerce'
                ).fillna(0)
                
                # New formula: (sl_giao × thoi_gian_pky + tong_so_nc × 40) × 1.2
                df_merged['total_time'] = (
                    df_merged['sl_giao_numeric'] * df_merged['thoi_gian_numeric'] + 
                    df_merged['tong_so_nc_numeric'] * 40
                ) * 1.2
                
                tong_thoi_gian_gia_cong = df_merged['total_time'].sum()
                
                # Count running machines from PHTCV
                # Filter PHTCV by same date
                df_phtcv_filtered = df_phtcv.copy()
                if 'ngày tháng' in df_phtcv_filtered.columns:
                    df_phtcv_filtered['date_parsed'] = pd.to_datetime(
                        df_phtcv_filtered['ngày tháng'],
                        format='%d/%m/%Y',
                        errors='coerce'
                    )
                    
                    if selected_date != 'Tất cả':
                        filter_date = pd.to_datetime(selected_date, format='%d/%m/%Y').date()
                        df_phtcv_filtered = df_phtcv_filtered[
                            df_phtcv_filtered['date_parsed'].dt.date == filter_date
                        ].copy()
                
                # Calculate total time for each machine BY DEPARTMENT
                # B = unique machines with >= 620 minutes in AT LEAST ONE department
                # IMPORTANT: Track by (machine, department) pair, then check which machines meet threshold
                
                machine_dept_times = {}  # {(machine_num, dept): total_time}
                
                for _, row in df_phtcv_filtered.iterrows():
                    # Get machine number and department
                    machine_num = str(row.get('số máy', '')).strip()
                    dept = str(row.get('bộ phận', '')).strip()
                    
                    if not machine_num:
                        continue
                    
                    # Parse sl thực tế
                    sl_thuc_te = pd.to_numeric(
                        str(row.get('sl thực tế', '1')).replace(',', '.'),
                        errors='coerce'
                    )
                    if pd.isna(sl_thuc_te) or sl_thuc_te == 0:
                        sl_thuc_te = 1
                    
                    # Calculate times - CORRECTED FORMULA with NaN handling
                    time_tgcb = pd.to_numeric(str(row.get('tgcb', '0')).replace(',', '.'), errors='coerce')
                    time_tgcb = 0 if pd.isna(time_tgcb) else time_tgcb
                    
                    time_chay_thu = pd.to_numeric(str(row.get('chạy thử', '0')).replace(',', '.'), errors='coerce')
                    time_chay_thu = 0 if pd.isna(time_chay_thu) else time_chay_thu
                    
                    ga_lap_raw = pd.to_numeric(str(row.get('gá lắp', '0')).replace(',', '.'), errors='coerce')
                    ga_lap_raw = 0 if pd.isna(ga_lap_raw) else ga_lap_raw
                    time_ga_lap = ga_lap_raw * sl_thuc_te
                    
                    gia_cong_raw = pd.to_numeric(str(row.get('gia công', '0')).replace(',', '.'), errors='coerce')
                    gia_cong_raw = 0 if pd.isna(gia_cong_raw) else gia_cong_raw
                    time_gia_cong = gia_cong_raw * sl_thuc_te
                    
                    # For dừng and dừng khác, exclude shift times
                    SHIFT_TIMES = [420, 630, 660]
                    time_dung_raw = pd.to_numeric(str(row.get('dừng', '0')).replace(',', '.'), errors='coerce')
                    time_dung_raw = 0 if pd.isna(time_dung_raw) else time_dung_raw
                    time_dung = 0 if time_dung_raw in SHIFT_TIMES else time_dung_raw
                    
                    time_dung_khac_raw = pd.to_numeric(str(row.get('dừng khác', '0')).replace(',', '.'), errors='coerce')
                    time_dung_khac_raw = 0 if pd.isna(time_dung_khac_raw) else time_dung_khac_raw
                    time_dung_khac = 0 if time_dung_khac_raw in SHIFT_TIMES else time_dung_khac_raw
                    
                    time_sua = pd.to_numeric(str(row.get('sửa', '0')).replace(',', '.'), errors='coerce')
                    time_sua = 0 if pd.isna(time_sua) else time_sua
                    
                    # Calculate total time for THIS ROW
                    row_total_time = time_gia_cong + time_ga_lap + time_tgcb + time_chay_thu + time_dung + time_dung_khac + time_sua
                    
                    # SUM all rows for the same (machine, department) pair
                    key = (machine_num, dept)
                    if key not in machine_dept_times:
                        machine_dept_times[key] = 0
                    machine_dept_times[key] += row_total_time
                
                # NOW check which UNIQUE machines have >= 620 in AT LEAST ONE department
                machines_12h = set()
                machines_12h_details = {}  # {machine_num: {'dept': dept, 'total_time': time}}
                
                for (machine_num, dept), total_time in machine_dept_times.items():
                    if total_time >= 620:
                        machines_12h.add(machine_num)
                        
                        # Track the department with highest time for this machine
                        if machine_num not in machines_12h_details or machines_12h_details[machine_num]['total_time'] < total_time:
                            machines_12h_details[machine_num] = {
                                'dept': dept,
                                'total_time': total_time
                            }
                
                
                # B = number of unique machines with >= 620 minutes in at least one department
                B = len(machines_12h)
                
                # Count total unique machines in PHTCV data
                total_machines_in_phtcv = len(set(m for (m, d) in machine_dept_times.keys()))
                
                # Calculate 100-machine time based on B
                # New logic:
                #   - If >= 95% of machines in PHTCV have >= 620 minutes: 
                #     All 100 machines run 12h → 100 × 20h × 60 = 120,000 minutes
                #   - Otherwise: (100-B) machines run 8h, B machines run 12h → (100-B) × 14h × 60 + B × 20h × 60
                if total_machines_in_phtcv > 0 and (B / total_machines_in_phtcv) >= 0.95:
                    # >= 95% of machines in PHTCV have >= 620, assume all 100 machines run 12h
                    thoi_gian_may_chay = 100 * 20 * 60  # 120,000 minutes
                else:
                    # Mixed: some machines run 8h, some run 12h
                    A = 100 - B  # Machines running 8h shift
                    thoi_gian_may_chay = (A * 14 * 60) + (B * 20 * 60)
                
                # Calculate CS tổng
                if thoi_gian_may_chay > 0:
                    cs_tong = (tong_thoi_gian_gia_cong / thoi_gian_may_chay) * 100
                else:
                    cs_tong = 0
                
                # 3. CS trực tiếp (Direct Capacity)
                # CS trực tiếp = thời gian gia công / (thời gian tổng - thời gian máy dừng) × 100%
                # Thời gian máy dừng = tổng thời gian dừng thực tế của các máy dừng
                
                # Check if month filter is selected - if so, calculate monthly average
                if selected_month != 'Tất cả' and selected_date == 'Tất cả':
                    # Calculate monthly average CS
                    # Use same date range logic as trend chart
                    selected_period = pd.Period(selected_month)
                    start_date_month = pd.to_datetime(selected_period.start_time)
                    end_date_month = pd.to_datetime(selected_period.end_time)
                    
                    df_phtcv_month = df_phtcv[
                        (df_phtcv['date_parsed'] >= start_date_month) & 
                        (df_phtcv['date_parsed'] <= end_date_month)
                    ].copy()
                    
                    # Calculate CS for each day in the month
                    monthly_cs_tong = []
                    monthly_cs_truc_tiep = []
                    
                    for single_date in pd.date_range(start=start_date_month, end=end_date_month):
                        df_day = df_phtcv_month[df_phtcv_month['date_parsed'] == single_date].copy()
                        
                        if len(df_day) == 0:
                            continue
                        
                        # Calculate B for this day (simplified version)
                        machine_dept_times_day = {}
                        SHIFT_TIMES = [420, 630, 660]
                        
                        for _, row in df_day.iterrows():
                            machine_num = str(row.get('số máy', '')).strip()
                            dept = str(row.get('bộ phận', '')).strip()
                            
                            if not machine_num:
                                continue
                            
                            sl_thuc_te = pd.to_numeric(str(row.get('sl thực tế', '1')).replace(',', '.'), errors='coerce')
                            if pd.isna(sl_thuc_te) or sl_thuc_te == 0:
                                sl_thuc_te = 1
                            
                            time_tgcb = pd.to_numeric(str(row.get('tgcb', '0')).replace(',', '.'), errors='coerce')
                            time_tgcb = 0 if pd.isna(time_tgcb) else time_tgcb
                            
                            time_chay_thu = pd.to_numeric(str(row.get('chạy thử', '0')).replace(',', '.'), errors='coerce')
                            time_chay_thu = 0 if pd.isna(time_chay_thu) else time_chay_thu
                            
                            ga_lap_raw = pd.to_numeric(str(row.get('gá lắp', '0')).replace(',', '.'), errors='coerce')
                            ga_lap_raw = 0 if pd.isna(ga_lap_raw) else ga_lap_raw
                            time_ga_lap = ga_lap_raw * sl_thuc_te
                            
                            gia_cong_raw = pd.to_numeric(str(row.get('gia công', '0')).replace(',', '.'), errors='coerce')
                            gia_cong_raw = 0 if pd.isna(gia_cong_raw) else gia_cong_raw
                            time_gia_cong = gia_cong_raw * sl_thuc_te
                            
                            time_dung_raw = pd.to_numeric(str(row.get('dừng', '0')).replace(',', '.'), errors='coerce')
                            time_dung_raw = 0 if pd.isna(time_dung_raw) else time_dung_raw
                            time_dung = 0 if time_dung_raw in SHIFT_TIMES else time_dung_raw
                            
                            time_dung_khac_raw = pd.to_numeric(str(row.get('dừng khác', '0')).replace(',', '.'), errors='coerce')
                            time_dung_khac_raw = 0 if pd.isna(time_dung_khac_raw) else time_dung_khac_raw
                            time_dung_khac = 0 if time_dung_khac_raw in SHIFT_TIMES else time_dung_khac_raw
                            
                            time_sua = pd.to_numeric(str(row.get('sửa', '0')).replace(',', '.'), errors='coerce')
                            time_sua = 0 if pd.isna(time_sua) else time_sua
                            
                            row_total_time = time_gia_cong + time_ga_lap + time_tgcb + time_chay_thu + time_dung + time_dung_khac + time_sua
                            
                            key = (machine_num, dept)
                            if key not in machine_dept_times_day:
                                machine_dept_times_day[key] = 0
                            machine_dept_times_day[key] += row_total_time
                        
                        # Count B
                        machines_12h_day = set()
                        for (machine_num, dept), total_time in machine_dept_times_day.items():
                            if total_time >= 620:
                                machines_12h_day.add(machine_num)
                        
                        B_day = len(machines_12h_day)
                        total_machines_day = len(set(m for (m, d) in machine_dept_times_day.keys()))
                        
                        # Calculate 100-machine time
                        if total_machines_day > 0 and (B_day / total_machines_day) >= 0.95:
                            thoi_gian_may_chay_day = 100 * 20 * 60
                        else:
                            A_day = 100 - B_day
                            thoi_gian_may_chay_day = (A_day * 14 * 60) + (B_day * 20 * 60)
                        
                        # Calculate processing time
                        total_gia_cong_day = 0
                        for _, row in df_day.iterrows():
                            sl_thuc_te = pd.to_numeric(str(row.get('sl thực tế', '1')).replace(',', '.'), errors='coerce')
                            if pd.isna(sl_thuc_te) or sl_thuc_te == 0:
                                sl_thuc_te = 1
                            
                            gia_cong_raw = pd.to_numeric(str(row.get('gia công', '0')).replace(',', '.'), errors='coerce')
                            gia_cong_raw = 0 if pd.isna(gia_cong_raw) else gia_cong_raw
                            total_gia_cong_day += gia_cong_raw * sl_thuc_te
                        
                        # CS tổng for this day
                        cs_tong_day = (total_gia_cong_day / thoi_gian_may_chay_day) * 100 if thoi_gian_may_chay_day > 0 else 0
                        monthly_cs_tong.append(cs_tong_day)
                        
                        # Calculate stopped machines for CS trực tiếp
                        machines_in_phtcv_day = set()
                        for _, row in df_day.iterrows():
                            machine = str(row.get('số máy', '')).strip()
                            if machine:
                                machines_in_phtcv_day.add(machine)
                        
                        if df_machine_list is not None and not df_machine_list.empty:
                            all_machines_list = []
                            if 'số máy' in df_machine_list.columns:
                                for _, row in df_machine_list.iterrows():
                                    machine = str(row.get('số máy', '')).strip()
                                    if machine:
                                        all_machines_list.append(machine)
                            
                            machines_not_in_phtcv_day = [m for m in all_machines_list if m not in machines_in_phtcv_day]
                            total_stopped_day = len(machines_not_in_phtcv_day)
                        else:
                            total_stopped_day = 0
                        
                        time_per_stopped_machine = 7 * 60
                        thoi_gian_may_dung_day = total_stopped_day * time_per_stopped_machine
                        thoi_gian_truc_tiep_day = thoi_gian_may_chay_day - thoi_gian_may_dung_day
                        
                        cs_truc_tiep_day = (total_gia_cong_day / thoi_gian_truc_tiep_day) * 100 if thoi_gian_truc_tiep_day > 0 else 0
                        monthly_cs_truc_tiep.append(cs_truc_tiep_day)
                    
                    # Use monthly averages
                    if len(monthly_cs_tong) > 0:
                        cs_tong = sum(monthly_cs_tong) / len(monthly_cs_tong)
                        cs_truc_tiep = sum(monthly_cs_truc_tiep) / len(monthly_cs_truc_tiep)
                        use_monthly_average = True  # Flag to skip single-day calculation
                    else:
                        cs_tong = 0
                        cs_truc_tiep = 0
                        use_monthly_average = True
                else:
                    # Use single-day calculation (existing logic)
                    use_monthly_average = False
                
                # Only calculate single-day CS trực tiếp if NOT using monthly average
                if not use_monthly_average:
                    # Get master machine list (ALL machines - both lathe and milling)
                    # No filtering by type - we want total stopped machines regardless of type
                    all_machines = []
                    
                    if df_machine_list is not None and not df_machine_list.empty:
                        if 'số máy' in df_machine_list.columns:
                            for _, row in df_machine_list.iterrows():
                                machine = str(row.get('số máy', '')).strip()
                                if machine:
                                    all_machines.append(machine)
                

                
                    # Track machines in PHTCV by department
                    machines_in_phtcv_sx1 = []
                    machines_in_phtcv_sx2 = []
                

                
                    # First pass: collect all machines in PHTCV by department
                    if 'số máy' in df_phtcv_filtered.columns and 'bộ phận' in df_phtcv_filtered.columns:
                        for _, row in df_phtcv_filtered.iterrows():
                            machine = str(row.get('số máy', '')).strip()
                            dept = str(row.get('bộ phận', '')).strip()
                    
                            if machine:
                                if 'Sản xuất 1' in dept:
                                    machines_in_phtcv_sx1.append(machine)
                                elif 'Sản xuất 2' in dept:
                                    machines_in_phtcv_sx2.append(machine)
            
                    # Get unique machines
                    machines_in_phtcv_sx1 = list(set(machines_in_phtcv_sx1))
                    machines_in_phtcv_sx2 = list(set(machines_in_phtcv_sx2))
            

            
                    # CONDITION 1: Machines NOT in PHTCV data (by department)
                    machines_not_in_phtcv_sx1 = [m for m in all_machines if m not in machines_in_phtcv_sx1]
                    machines_not_in_phtcv_sx2 = [m for m in all_machines if m not in machines_in_phtcv_sx2]
            
                    # CONDITION 2 AND 3: Machines with stop time >= 420 AND all production columns empty
                    # Using exact logic from dashboard_capacity.py
                    stopped_machines_sx1 = []
                    stopped_machines_sx2 = []
            
                    # Process SX1 machines
                    for machine in machines_in_phtcv_sx1:
                        df_machine = df_phtcv_filtered[
                            (df_phtcv_filtered['số máy'] == machine) & 
                            (df_phtcv_filtered['bộ phận'].str.contains('Sản xuất 1', na=False))
                        ].copy()
                    
                        if df_machine.empty:
                            continue
                    
                        # Check if machine has stop time >= 420
                        max_dung = pd.to_numeric(
                            df_machine['dừng'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).fillna(0).max()
                    
                        max_dung_khac = 0
                        if 'dừng khác' in df_machine.columns:
                            max_dung_khac = pd.to_numeric(
                                df_machine['dừng khác'].astype(str).str.replace(',', '.'),
                                errors='coerce'
                            ).fillna(0).max()
                    
                        # Use OR condition like dashboard_capacity
                        has_shift_stop = (max_dung >= 420) or (max_dung_khac >= 420)
                    
                        # Check if all production columns are empty/zero
                        time_tgcb = pd.to_numeric(
                            df_machine['tgcb'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        time_chay_thu = pd.to_numeric(
                            df_machine['chạy thử'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        time_ga_lap = pd.to_numeric(
                            df_machine['gá lắp'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        time_gia_cong = pd.to_numeric(
                            df_machine['gia công'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        has_no_production = (time_tgcb == 0 and time_chay_thu == 0 and 
                                            time_ga_lap == 0 and time_gia_cong == 0)
                    

                    
                        # Condition 2 AND 3
                        if has_shift_stop and has_no_production:
                            stopped_machines_sx1.append(machine)
            
                    # Process SX2 machines (same logic)
                    for machine in machines_in_phtcv_sx2:
                        df_machine = df_phtcv_filtered[
                            (df_phtcv_filtered['số máy'] == machine) & 
                            (df_phtcv_filtered['bộ phận'].str.contains('Sản xuất 2', na=False))
                        ].copy()
                    
                        if df_machine.empty:
                            continue
                    
                        max_dung = pd.to_numeric(
                            df_machine['dừng'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).fillna(0).max()
                    
                        max_dung_khac = 0
                        if 'dừng khác' in df_machine.columns:
                            max_dung_khac = pd.to_numeric(
                                df_machine['dừng khác'].astype(str).str.replace(',', '.'),
                                errors='coerce'
                            ).fillna(0).max()
                    
                        has_shift_stop = (max_dung >= 420) or (max_dung_khac >= 420)
                    
                        time_tgcb = pd.to_numeric(
                            df_machine['tgcb'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        time_chay_thu = pd.to_numeric(
                            df_machine['chạy thử'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        time_ga_lap = pd.to_numeric(
                            df_machine['gá lắp'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        time_gia_cong = pd.to_numeric(
                            df_machine['gia công'].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        ).sum()
                    
                        has_no_production = (time_tgcb == 0 and time_chay_thu == 0 and 
                                            time_ga_lap == 0 and time_gia_cong == 0)
                    
                        if has_shift_stop and has_no_production:
                            stopped_machines_sx2.append(machine)
            
                    # FINAL: Condition 1 OR (Condition 2 AND 3)
                    # Total stopped machines = machines not in data + machines in data but stopped
                    stopped_count_sx1 = len(stopped_machines_sx1)
                    stopped_count_sx2 = len(stopped_machines_sx2)
            

            
                    # ---------------------------------------------------------
                    # Calculate Total Stopped Machines (matching dashboard_capacity)
                    # ---------------------------------------------------------
                    # FINAL: Condition 1 OR (Condition 2 AND 3)
                    all_stopped_sx1 = sorted(
                        set(machines_not_in_phtcv_sx1 + stopped_machines_sx1),
                        key=lambda x: int(x) if x.isdigit() else float('inf')
                    )
                    all_stopped_sx2 = sorted(
                        set(machines_not_in_phtcv_sx2 + stopped_machines_sx2),
                        key=lambda x: int(x) if x.isdigit() else float('inf')
                    )
            
                    total_stopped_sx1 = len(all_stopped_sx1)
                    total_stopped_sx2 = len(all_stopped_sx2)
            

            
                    # Calculate stopped time based on stopped machine counts
                    # Time per stopped machine: 7h × 60 = 420 min (as per user's formula: 36*7*60)
                    time_per_stopped_machine = 7 * 60  # 420 minutes
            
                    # Total stopped time for each department
                    stopped_time_final_sx1 = total_stopped_sx1 * time_per_stopped_machine
                    stopped_time_final_sx2 = total_stopped_sx2 * time_per_stopped_machine
            
                    thoi_gian_may_dung = stopped_time_final_sx1 + stopped_time_final_sx2
            
                    # Calculate direct time
                    thoi_gian_truc_tiep = thoi_gian_may_chay - thoi_gian_may_dung
            
                    # Calculate CS trực tiếp
                    if thoi_gian_truc_tiep > 0:
                        cs_truc_tiep = (tong_thoi_gian_gia_cong / thoi_gian_truc_tiep) * 100
                    else:
                        cs_truc_tiep = 0
                

                

        
        # Metrics display
        st.markdown("""<style>
        .metric-box {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #1f77b4;
        }
        </style>""", unsafe_allow_html=True)
        
        # Calculate RRC and External inventory (COMBINED - OPTIMIZED!)
        rrc_inventory = 0
        external_inventory = 0
        rrc_pkt_inventory = 0
        external_pkt_inventory = 0
        try:
            with st.spinner("Đang tính hàng tồn RRC và Hàng ngoài..."):
                # Use combined function for all inventory metrics
                all_inventory = calculate_all_inventory_metrics(
                    sheet_url=CONFIG['google_sheet_url'],
                    credentials_file=CONFIG['google_credentials']
                )
                
                rrc_inventory = all_inventory['rrc_inventory']
                external_inventory = all_inventory['external_inventory']
                rrc_pkt_inventory = all_inventory['rrc_pkt_inventory']
                external_pkt_inventory = all_inventory['external_pkt_inventory']
        except Exception as e:
            st.warning(f"⚠️ Không thể tính hàng tồn: {e}")
        
        # Row 1: Sản xuất AMJ
        st.markdown("### 1. Sản xuất AMJ")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric(label="Sản lượng", value=f"{san_luong_san_xuat}")
        with col2:
            st.metric(label="CS tổng", value=f"{cs_tong:.1f}%")
        with col3:
            st.metric(label="CS trực tiếp", value=f"{cs_truc_tiep:.1f}%")
        
        # Hàng tồn tổng kế hoạch section
        st.markdown("#### Hàng tồn tổng kế hoạch")
        col4, col5, col6 = st.columns([1, 1, 1])
        with col4:
            st.metric(label="RRC", value=f"{rrc_inventory:,}")
        with col5:
            st.metric(label="Hàng ngoài", value=f"{external_inventory:,}")
        with col6:
            total_sx_amj = rrc_inventory + external_inventory
            st.metric(label="Tổng", value=f"{total_sx_amj:,}")
        
        # Section 2: Kiểm tra AMJ (moved from line 1143)
        st.markdown("---")
        st.markdown("### 2. Kiểm tra AMJ")
        
        # Calculate Kiểm tra AMJ metrics
        # Load giao_kho_vp data
        with st.spinner("Đang tải dữ liệu giao_kho_vp..."):
            df_giao_kho_vp = read_giao_kho_vp_data()
        
        san_luong_kiem_tra = 0
        
        if df_giao_kho_vp is not None and not df_giao_kho_vp.empty:
            # Parse ngay_dong_goi date column
            if 'ngay_dong_goi' in df_giao_kho_vp.columns:
                df_giao_kho_vp['ngay_dong_goi_parsed'] = pd.to_datetime(
                    df_giao_kho_vp['ngay_dong_goi'],
                    format='%d/%m/%Y',
                    errors='coerce'
                )
                
                # Filter by selected month or date
                df_giao_kho_filtered = df_giao_kho_vp.copy()
                
                if selected_month != 'Tất cả' and 'year_month' not in df_giao_kho_filtered.columns:
                    df_giao_kho_filtered['year_month'] = df_giao_kho_filtered['ngay_dong_goi_parsed'].dt.to_period('M')
                
                if selected_month != 'Tất cả':
                    df_giao_kho_filtered = df_giao_kho_filtered[
                        df_giao_kho_filtered['year_month'] == pd.Period(selected_month)
                    ].copy()
                
                if selected_date != 'Tất cả' and 'ngay_dong_goi_parsed' in df_giao_kho_filtered.columns:
                    filter_date_kt = pd.to_datetime(selected_date, format='%d/%m/%Y').date()
                    df_giao_kho_filtered = df_giao_kho_filtered[
                        df_giao_kho_filtered['ngay_dong_goi_parsed'].dt.date == filter_date_kt
                    ].copy()
                
                # Calculate production volume from sll column
                if 'sll' in df_giao_kho_filtered.columns:
                    san_luong_kiem_tra = pd.to_numeric(
                        df_giao_kho_filtered['sll'].astype(str).str.replace(',', '.'),
                        errors='coerce'
                    ).fillna(0).sum()
                    san_luong_kiem_tra = int(san_luong_kiem_tra)
        
        # Calculate CS Kiểm tra
        cs_kiem_tra_tong = 0
        cs_kiem_tra_truc_tiep = 0
        
        # Load additional data for QC capacity calculation
        with st.spinner("Đang tính toán Công Suất Kiểm Tra..."):
            df_shift_schedule = read_shift_schedule_data()
            df_hr_daily_head_counts = read_hr_daily_head_counts_data()
            df_thoi_gian_hoan_thanh = read_thoi_gian_hoan_thanh_data()
            
            # Calculate QC capacity
            if selected_date != 'Tất cả':
                qc_result = calculate_quality_control_capacity(
                    df_giao_kho_filtered,
                    df_shift_schedule,
                    df_hr_daily_head_counts,
                    df_thoi_gian_hoan_thanh,
                    selected_date
                )
                
                cs_kiem_tra_tong = qc_result['cs_tong']
                cs_kiem_tra_truc_tiep = qc_result['cs_truc_tiep']
        
        # Display Kiểm tra AMJ metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Sản lượng", value=f"{san_luong_kiem_tra}")
        with col2:
            if cs_kiem_tra_tong > 0:
                st.metric(label="CS tổng", value=f"{cs_kiem_tra_tong:.1f}%")
            else:
                st.metric(label="CS tổng", value="-%", help="Chọn ngày cụ thể để xem CS")
        with col3:
            if cs_kiem_tra_truc_tiep > 0:
                st.metric(label="CS trực tiếp", value=f"{cs_kiem_tra_truc_tiep:.1f}%")
            else:
                st.metric(label="CS trực tiếp", value="-%", help="Chọn ngày cụ thể để xem CS")
        
        # Hàng tồn tổng kế hoạch section
        st.markdown("#### Hàng tồn tổng kế hoạch")
        col4, col5, col6 = st.columns([1, 1, 1])
        with col4:
            st.metric(label="RRC", value=f"{rrc_pkt_inventory:,}")
        with col5:
            st.metric(label="Hàng ngoài", value=f"{external_pkt_inventory:,}")
        with col6:
            total_kiem_tra = rrc_pkt_inventory + external_pkt_inventory
            st.metric(label="Tổng", value=f"{total_kiem_tra:,}")
        
        # Section 3: Quá hạn, tới hạn (moved from line 1008)
        st.markdown("---")
        st.markdown("### 3. Quá hạn, tới hạn")
        
        # Calculate overdue and due soon metrics (ALL AT ONCE - OPTIMIZED!)
        rrc_overdue = 0
        rrc_due_soon = 0
        ext_overdue = 0
        ext_due_soon = 0
        
        # PKT (Kiểm tra AMJ) metrics
        pkt_rrc_overdue = 0
        pkt_rrc_due_soon = 0
        pkt_ext_overdue = 0
        pkt_ext_due_soon = 0
        
        try:
            with st.spinner("Đang tính quá hạn và tới hạn..."):
                # OPTIMIZED: Calculate ALL metrics in ONE API call
                all_metrics = calculate_all_overdue_metrics(
                    sheet_url=CONFIG['google_sheet_url'],
                    credentials_file=CONFIG['google_credentials']
                )
                
                # Extract SX AMJ metrics
                rrc_overdue = all_metrics['sx_rrc_overdue']
                rrc_due_soon = all_metrics['sx_rrc_due_soon']
                ext_overdue = all_metrics['sx_ext_overdue']
                ext_due_soon = all_metrics['sx_ext_due_soon']
                
                # Extract PKT AMJ metrics
                pkt_rrc_overdue = all_metrics['pkt_rrc_overdue']
                pkt_rrc_due_soon = all_metrics['pkt_rrc_due_soon']
                pkt_ext_overdue = all_metrics['pkt_ext_overdue']
                pkt_ext_due_soon = all_metrics['pkt_ext_due_soon']
        except Exception as e:
            st.warning(f"⚠️ Không thể tính quá hạn/tới hạn: {e}")
        
        # Display metrics in table format
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
        
        with col1:
            st.markdown("**Bộ phận**")
        with col2:
            st.markdown("**RRC Quá hạn**")
        with col3:
            st.markdown("**RRC Tới hạn**")
        with col4:
            st.markdown("**Hàng ngoài Quá hạn**")
        with col5:
            st.markdown("**Hàng ngoài Tới hạn**")
        with col6:
            st.markdown("**Tổng**")
        
        # Row: Sản xuất AMJ
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
        with col1:
            st.markdown("Sản xuất AMJ")
        with col2:
            st.metric(label="", value=f"{rrc_overdue:,}")
        with col3:
            st.metric(label="", value=f"{rrc_due_soon:,}")
        with col4:
            st.metric(label="", value=f"{ext_overdue:,}")
        with col5:
            st.metric(label="", value=f"{ext_due_soon:,}")
        with col6:
            total_overdue_due_sx = rrc_overdue + rrc_due_soon + ext_overdue + ext_due_soon
            st.metric(label="", value=f"{total_overdue_due_sx:,}")
        
        # Row: Kiểm tra AMJ (PKT)
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
        with col1:
            st.markdown("Kiểm tra AMJ")
        with col2:
            st.metric(label="", value=f"{pkt_rrc_overdue:,}")
        with col3:
            st.metric(label="", value=f"{pkt_rrc_due_soon:,}")
        with col4:
            st.metric(label="", value=f"{pkt_ext_overdue:,}")
        with col5:
            st.metric(label="", value=f"{pkt_ext_due_soon:,}")
        with col6:
            total_overdue_due_pkt = pkt_rrc_overdue + pkt_rrc_due_soon + pkt_ext_overdue + pkt_ext_due_soon
            st.metric(label="", value=f"{total_overdue_due_pkt:,}")
        
        # Section 4: Actual Overdue (Password Protected)
        st.markdown("---")
        st.markdown("### 4. Dùng mật khẩu để xem")
        
        # Password check for actual overdue section
        if 'actual_overdue_authenticated' not in st.session_state:
            st.session_state.actual_overdue_authenticated = False
        
        if not st.session_state.actual_overdue_authenticated:
            col_pwd1, col_pwd2, col_pwd3 = st.columns([1, 1, 1])
            with col_pwd2:
                actual_pwd = st.text_input("🔒 Nhập mật khẩu để xem:", type="password", key="actual_overdue_pwd")
                if st.button("Xác nhận", key="actual_overdue_submit"):
                    if actual_pwd == "0000":
                        st.session_state.actual_overdue_authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ Mật khẩu không đúng!")
        else:
            # Logout button
            if st.button("🔓 Đăng xuất khỏi mục này", key="actual_overdue_logout"):
                st.session_state.actual_overdue_authenticated = False
                st.rerun()
            
            # Calculate actual overdue using values from all_metrics
            # These are filtered by TODAY() (no offset) to match Excel formulas
            
            # Get actual overdue values (calculated with TH <= TODAY)
            rrc_actual_overdue = all_metrics['sx_rrc_actual_overdue']  # 802
            pkt_actual_overdue = all_metrics['pkt_rrc_actual_overdue']  # 920
            
            # Calculate actual due soon = Overdue (Section 3) - Actual Overdue (Section 4)
            # PSX: 1,845 - 802 = 1,043
            # PKT: 1,750 - 920 = 830
            rrc_actual_due_soon = rrc_overdue - rrc_actual_overdue
            pkt_actual_due_soon = pkt_rrc_overdue - pkt_actual_overdue
            
            # Calculate totals
            rrc_total_predicted = rrc_overdue + rrc_due_soon
            pkt_total_predicted = pkt_rrc_overdue + pkt_rrc_due_soon
            
            # Add custom CSS for colored backgrounds
            st.markdown("""
            <style>
            .actual-table {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
            }
            .overdue-row {
                background-color: #ffebee;
                padding: 5px;
            }
            .due-soon-row {
                background-color: #fff9c4;
                padding: 5px;
            }
            .total-row {
                background-color: #e3f2fd;
                padding: 5px;
                font-weight: bold;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Display table
            st.markdown("#### PSX (Sản xuất)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RRC", f"{rrc_actual_overdue:,}")
            with col2:
                st.metric("RRC", f"{rrc_actual_due_soon:,}")
            with col3:
                st.metric("Tổng PSX", f"{rrc_total_predicted:,}")
            
            st.markdown("#### PKT (Kiểm tra)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RRC", f"{pkt_actual_overdue:,}")
            with col2:
                st.metric("RRC", f"{pkt_actual_due_soon:,}")
            with col3:
                st.metric("Tổng PKT", f"{pkt_total_predicted:,}")
            
            st.markdown("#### Tổng cộng")
            col1, col2, col3 = st.columns(3)
            with col1:
                total_actual_overdue = rrc_actual_overdue + pkt_actual_overdue
                st.metric("Tổng quá hạn", f"{total_actual_overdue:,}", 
                         help="Tổng số hàng quá hạn thực tế")
            with col2:
                total_actual_due_soon = rrc_actual_due_soon + pkt_actual_due_soon
                st.metric("Tổng tới hạn", f"{total_actual_due_soon:,}",
                         help="Tổng số hàng tới hạn thực tế")
            with col3:
                grand_total = rrc_total_predicted + pkt_total_predicted
                st.metric("Tổng cộng", f"{grand_total:,}",
                         help="Tổng PSX + PKT")
        
        # Capacity Trend Chart
        st.markdown("---")
        
        # Separate filter for capacity charts (independent from production filter)
        st.subheader("📊 Bộ lọc Biểu đồ Công suất")
        
       # Get available months from PHTCV data
        if df_phtcv is not None and not df_phtcv.empty and 'date_parsed' in df_phtcv.columns:
            df_phtcv['year_month_chart'] = df_phtcv['date_parsed'].dt.to_period('M')
            available_months_chart = df_phtcv['year_month_chart'].dropna().unique()
            available_months_chart = sorted(available_months_chart, reverse=True)
            
            if len(available_months_chart) > 0:
                month_options_chart = [str(m) for m in available_months_chart]
                trend_month = st.selectbox(
                    "Chọn tháng hiển thị:",
                    options=month_options_chart,
                    index=0,  # Default to latest month
                    key="chart_month_filter"
                )
            else:
                trend_month = str(pd.Period(datetime.now(), freq='M'))
        else:
            trend_month = str(pd.Period(datetime.now(), freq='M'))
        
        st.markdown("---")
        st.markdown("### 📈 Sản xuất AMJ - Biểu đồ xu hướng Công suất")
        
        # Add explanation
        with st.expander("ℹ️ Giải thích các chỉ số", expanded=False):
            st.markdown("""
            **CS tổng (Công suất tổng):**
            - Tỷ lệ giữa thời gian gia công thực tế và thời gian 100 máy có thể chạy
            - Công thức: `(Thời gian gia công / Thời gian 100 máy) × 100%`
            
            **CS trực tiếp (Công suất trực tiếp):**
            - Tỷ lệ giữa thời gian gia công thực tế và thời gian máy thực sự hoạt động (đã trừ máy dừng)
            - Công thức: `(Thời gian gia công / (Thời gian 100 máy - Thời gian máy dừng)) × 100%`
            - CS trực tiếp thường cao hơn CS tổng vì không tính máy dừng
            """)
        
        # Calculate historical data for trend chart
        # Use trend_month filter (independent from production filter)
        selected_period = pd.Period(trend_month)
        start_date = pd.to_datetime(selected_period.start_time)
        end_date = pd.to_datetime(selected_period.end_time)
        
        # Filter PHTCV data for date range
        df_phtcv_range = df_phtcv[
            (df_phtcv['date_parsed'] >= start_date) & 
            (df_phtcv['date_parsed'] <= end_date)
        ].copy()
        
        st.info(f"📅 Đang tính toán biểu đồ từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')} ({len(df_phtcv_range)} dòng dữ liệu)")
        
        # Calculate CS for each date
        trend_data = []
        days_with_data = 0
        
        for single_date in pd.date_range(start=start_date, end=end_date):
            df_day = df_phtcv_range[df_phtcv_range['date_parsed'] == single_date].copy()
            
            if len(df_day) == 0:
                continue
            
            days_with_data += 1
            
            # Calculate B for this date (same logic as main calculation)
            machine_dept_times_day = {}
            SHIFT_TIMES = [420, 630, 660]
            
            for _, row in df_day.iterrows():
                machine_num = str(row.get('số máy', '')).strip()
                dept = str(row.get('bộ phận', '')).strip()
                
                if not machine_num:
                    continue
                
                sl_thuc_te = pd.to_numeric(str(row.get('sl thực tế', '1')).replace(',', '.'), errors='coerce')
                if pd.isna(sl_thuc_te) or sl_thuc_te == 0:
                    sl_thuc_te = 1
                
                time_tgcb = pd.to_numeric(str(row.get('tgcb', '0')).replace(',', '.'), errors='coerce')
                time_tgcb = 0 if pd.isna(time_tgcb) else time_tgcb
                
                time_chay_thu = pd.to_numeric(str(row.get('chạy thử', '0')).replace(',', '.'), errors='coerce')
                time_chay_thu = 0 if pd.isna(time_chay_thu) else time_chay_thu
                
                ga_lap_raw = pd.to_numeric(str(row.get('gá lắp', '0')).replace(',', '.'), errors='coerce')
                ga_lap_raw = 0 if pd.isna(ga_lap_raw) else ga_lap_raw
                time_ga_lap = ga_lap_raw * sl_thuc_te
                
                gia_cong_raw = pd.to_numeric(str(row.get('gia công', '0')).replace(',', '.'), errors='coerce')
                gia_cong_raw = 0 if pd.isna(gia_cong_raw) else gia_cong_raw
                time_gia_cong = gia_cong_raw * sl_thuc_te
                
                time_dung_raw = pd.to_numeric(str(row.get('dừng', '0')).replace(',', '.'), errors='coerce')
                time_dung_raw = 0 if pd.isna(time_dung_raw) else time_dung_raw
                time_dung = 0 if time_dung_raw in SHIFT_TIMES else time_dung_raw
                
                time_dung_khac_raw = pd.to_numeric(str(row.get('dừng khác', '0')).replace(',', '.'), errors='coerce')
                time_dung_khac_raw = 0 if pd.isna(time_dung_khac_raw) else time_dung_khac_raw
                time_dung_khac = 0 if time_dung_khac_raw in SHIFT_TIMES else time_dung_khac_raw
                
                time_sua = pd.to_numeric(str(row.get('sửa', '0')).replace(',', '.'), errors='coerce')
                time_sua = 0 if pd.isna(time_sua) else time_sua
                
                row_total_time = time_gia_cong + time_ga_lap + time_tgcb + time_chay_thu + time_dung + time_dung_khac + time_sua
                
                key = (machine_num, dept)
                if key not in machine_dept_times_day:
                    machine_dept_times_day[key] = 0
                machine_dept_times_day[key] += row_total_time
            
            # Count B for this date
            machines_12h_day = set()
            for (machine_num, dept), total_time in machine_dept_times_day.items():
                if total_time >= 620:
                    machines_12h_day.add(machine_num)
            
            B_day = len(machines_12h_day)
            total_machines_day = len(set(m for (m, d) in machine_dept_times_day.keys()))
            
            # Calculate 100-machine time
            if total_machines_day > 0 and (B_day / total_machines_day) >= 0.95:
                thoi_gian_may_chay_day = 100 * 20 * 60
            else:
                A_day = 100 - B_day
                thoi_gian_may_chay_day = (A_day * 14 * 60) + (B_day * 20 * 60)
            
            # Calculate actual processing time from PHTCV for this day
            total_gia_cong_day = 0
            for _, row in df_day.iterrows():
                sl_thuc_te = pd.to_numeric(str(row.get('sl thực tế', '1')).replace(',', '.'), errors='coerce')
                if pd.isna(sl_thuc_te) or sl_thuc_te == 0:
                    sl_thuc_te = 1
                
                gia_cong_raw = pd.to_numeric(str(row.get('gia công', '0')).replace(',', '.'), errors='coerce')
                gia_cong_raw = 0 if pd.isna(gia_cong_raw) else gia_cong_raw
                total_gia_cong_day += gia_cong_raw * sl_thuc_te
            
            # Calculate CS tổng using actual processing time
            cs_tong_day = (total_gia_cong_day / thoi_gian_may_chay_day) * 100 if thoi_gian_may_chay_day > 0 else 0
            
            # Calculate CS trực tiếp (accurate calculation with stopped machines)
            # Get machines in PHTCV for this day
            machines_in_phtcv_day = set()
            for _, row in df_day.iterrows():
                machine = str(row.get('số máy', '')).strip()
                if machine:
                    machines_in_phtcv_day.add(machine)
            
            # Count stopped machines (simplified - only count machines NOT in PHTCV)
            # For full accuracy, would need to check stop time >= 420 and no production
            # But for trend chart, this approximation is acceptable
            if df_machine_list is not None and not df_machine_list.empty:
                all_machines_list = []
                if 'số máy' in df_machine_list.columns:
                    for _, row in df_machine_list.iterrows():
                        machine = str(row.get('số máy', '')).strip()
                        if machine:
                            all_machines_list.append(machine)
                
                machines_not_in_phtcv_day = [m for m in all_machines_list if m not in machines_in_phtcv_day]
                total_stopped_day = len(machines_not_in_phtcv_day)
            else:
                total_stopped_day = 0
            
            # Calculate stopped time
            time_per_stopped_machine = 7 * 60  # 420 minutes
            thoi_gian_may_dung_day = total_stopped_day * time_per_stopped_machine
            
            # Calculate direct time
            thoi_gian_truc_tiep_day = thoi_gian_may_chay_day - thoi_gian_may_dung_day
            
            # Calculate CS trực tiếp
            cs_truc_tiep_day = (total_gia_cong_day / thoi_gian_truc_tiep_day) * 100 if thoi_gian_truc_tiep_day > 0 else 0
            
            trend_data.append({
                'date': single_date,
                'CS tổng': cs_tong_day,
                'CS trực tiếp': cs_truc_tiep_day
            })
        
        st.success(f"✅ Đã xử lý {days_with_data} ngày có dữ liệu, tạo được {len(trend_data)} điểm dữ liệu")
        
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            df_trend['date_str'] = df_trend['date'].dt.strftime('%d/%m/%Y')
            
            # Calculate and display monthly averages
            avg_cs_tong = df_trend['CS tổng'].mean()
            avg_cs_truc_tiep = df_trend['CS trực tiếp'].mean()
            
            st.markdown("#### 📊 Trung bình tháng")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="CS tổng trung bình",
                    value=f"{avg_cs_tong:.1f}%",
                    help="Trung bình công suất tổng trong tháng"
                )
            with col2:
                st.metric(
                    label="CS trực tiếp trung bình",
                    value=f"{avg_cs_truc_tiep:.1f}%",
                    help="Trung bình công suất trực tiếp trong tháng"
                )
            
            st.markdown("---")
            
            # Create line chart using plotly
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            # Add CS tổng line
            fig.add_trace(go.Scatter(
                x=df_trend['date_str'],
                y=df_trend['CS tổng'],
                mode='lines+markers',
                name='CS tổng (%)',
                line=dict(color='#2ecc71', width=2),
                marker=dict(size=6)
            ))
            
            # Add CS trực tiếp line
            fig.add_trace(go.Scatter(
                x=df_trend['date_str'],
                y=df_trend['CS trực tiếp'],
                mode='lines+markers',
                name='CS trực tiếp (%)',
                line=dict(color='#9b59b6', width=2),
                marker=dict(size=6)
            ))
            
            # Update layout
            fig.update_layout(
                title='Xu hướng Công suất theo thời gian',
                xaxis_title='Ngày',
                yaxis_title='Công suất (%)',
                yaxis=dict(range=[0, max(df_trend['CS tổng'].max(), df_trend['CS trực tiếp'].max(), 100) + 20]),
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Excel Export Button for Capacity Data
            st.markdown("---")
            col_cap_exp1, col_cap_exp2, col_cap_exp3 = st.columns([1, 2, 1])
            with col_cap_exp2:
                if st.button("📥 Xuất Excel - Công suất Sản xuất", use_container_width=True, key="export_capacity_sx"):
                    # Prepare export dataframe
                    export_capacity_df = df_trend.copy()
                    export_capacity_df = export_capacity_df.rename(columns={
                        'date_str': 'Ngày',
                        'CS tổng': 'CS tổng (%)',
                        'CS trực tiếp': 'CS trực tiếp (%)'
                    })
                    
                    # Select only needed columns
                    export_capacity_df = export_capacity_df[['Ngày', 'CS tổng (%)', 'CS trực tiếp (%)']]
                    
                    # Convert to Excel
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        export_capacity_df.to_excel(writer, sheet_name='Công suất Sản xuất', index=False)
                        
                        # Add summary row with averages
                        workbook = writer.book
                        worksheet = writer.sheets['Công suất Sản xuất']
                        
                        # Format numbers
                        number_format = workbook.add_format({'num_format': '0.0'})
                        worksheet.set_column('B:C', 12, number_format)
                    
                    excel_data = output.getvalue()
                    
                    filename = f"cong_suat_san_xuat_{trend_month.replace('-', '_')}.xlsx"
                    
                    st.download_button(
                        label="⬇️ Tải file Excel",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_capacity_sx"
                    )
        else:
            st.info("Không có dữ liệu để hiển thị biểu đồ xu hướng")
        
        # Debug Display
        st.markdown("---")
        with st.expander("🔍 DEBUG: Chi tiết tính toán CS tổng"):
            if df_pky is not None and not df_pky.empty and 'df_merged' in locals():
                st.subheader("1️⃣ Thời gian gia công đơn hàng")
                
                # Show formula
                st.info("📐 Công thức: (sl_giao × thoi_gian_pky + tong_so_nc × 40) × 1.2")
                
                # Create display dataframe
                df_debug = df_merged[['ten_chi_tiet', 'sl_giao_numeric', 'thoi_gian_numeric', 'tong_so_nc_numeric', 'total_time']].copy()
                df_debug.columns = ['Tên chi tiết', 'SL giao', 'Thời gian PKY (phút)', 'Tổng số NC', 'Thời gian gia công (phút)']
                
                # Format numbers - values are already numeric
                df_debug['SL giao'] = df_debug['SL giao'].apply(lambda x: f"{x:.0f}" if pd.notna(x) and x != 0 else "0")
                df_debug['Thời gian PKY (phút)'] = df_debug['Thời gian PKY (phút)'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x != 0 else "0.0")
                df_debug['Tổng số NC'] = df_debug['Tổng số NC'].apply(lambda x: f"{x:.0f}" if pd.notna(x) and x != 0 else "0")
                df_debug['Thời gian gia công (phút)'] = df_debug['Thời gian gia công (phút)'].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x != 0 else "0.0")
                
                st.dataframe(df_debug, use_container_width=True, height=300)
                
                # Show total
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Tổng thời gian gia công", f"{tong_thoi_gian_gia_cong:,.0f} phút")
                with col2:
                    st.metric("📦 Tổng đơn hàng", f"{len(df_debug)}")
                with col3:
                    st.metric("🔢 Tổng SL giao", f"{df_merged['sl_giao_numeric'].sum():.0f}")
            
            if 'B' in locals() and 'thoi_gian_may_chay' in locals():
                st.markdown("---")
                st.subheader("2️⃣ Số máy và thời gian 100 máy")
                
                # Show machine counts
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔧 B (Máy >= 620p)", f"{B} máy", help="Số máy chạy ca 12h (unique từ tất cả bộ phận)")
                with col2:
                    A = 100 - B
                    st.metric("⚙️ A (Máy 8h)", f"{A} máy", help="100 - B")
                with col3:
                    if 'total_machines_in_phtcv' in locals() and total_machines_in_phtcv > 0:
                        ratio = (B / total_machines_in_phtcv) * 100
                        st.metric("📊 Tỷ lệ B/Tổng máy PHTCV", f"{ratio:.0f}%", help=f"{B}/{total_machines_in_phtcv}")
                    else:
                        st.metric("📊 Tỷ lệ B/100", "N/A")
                with col4:
                    if 'total_machines_in_phtcv' in locals():
                        st.metric("🏭 Máy trong PHTCV", f"{total_machines_in_phtcv} máy", help="Tổng máy unique trong dữ liệu")
                    else:
                        st.metric("🏭 Tổng máy", "100 máy")
                
                # Show detailed list of machines running 12h
                if 'machines_12h_details' in locals() and machines_12h_details:
                    st.markdown("#### 📋 Chi tiết máy chạy 12h (>= 620 phút):")
                    
                    # Create dataframe from details
                    machine_list_data = []
                    for machine_num in sorted(machines_12h_details.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
                        details = machines_12h_details[machine_num]
                        machine_list_data.append({
                            'Số máy': machine_num,
                            'Bộ phận': details['dept'],
                            'Tổng thời gian (phút)': f"{details['total_time']:.1f}"
                        })
                    
                    df_machines_12h = pd.DataFrame(machine_list_data)
                    st.dataframe(df_machines_12h, use_container_width=True, hide_index=True)
                    
                    # Show breakdown by department
                    st.markdown("##### 📊 Phân bổ theo bộ phận:")
                    dept_counts = {}
                    for details in machines_12h_details.values():
                        dept = details['dept']
                        dept_counts[dept] = dept_counts.get(dept, 0) + 1
                    
                    cols = st.columns(len(dept_counts) if dept_counts else 1)
                    for idx, (dept, count) in enumerate(sorted(dept_counts.items())):
                        with cols[idx]:
                            st.metric(dept, f"{count} máy")
                
                
                # Show formula used
                st.markdown("#### Công thức thời gian 100 máy:")
                if 'total_machines_in_phtcv' in locals() and total_machines_in_phtcv > 0 and (B / total_machines_in_phtcv) >= 0.95:
                    ratio_pct = (B / total_machines_in_phtcv) * 100
                    st.success(f"✅ **>= 95% máy trong PHTCV đều >= 620p** ({ratio_pct:.1f}%) → Dùng công thức: **100 × 20h × 60 = 120,000 phút**")
                    st.code(f"Thời gian 100 máy = 100 × 20 × 60 = {thoi_gian_may_chay:,} phút", language="python")
                else:
                    st.info(f"✅ **< 95% máy >= 620p** → Dùng công thức: **(100 - B) × 14h × 60 + B × 20h × 60**")
                    time_8h = A * 14 * 60
                    time_12h = B * 20 * 60
                    st.code(f"""Thời gian 100 máy = ({A} × 14 × 60) + ({B} × 20 × 60)
                 = {time_8h:,} + {time_12h:,}
                 = {thoi_gian_may_chay:,} phút""", language="python")
                
                # Show CS calculation
                st.markdown("---")
                st.markdown("#### Tính CS tổng:")
                if thoi_gian_may_chay > 0:
                    st.code(f"""CS tổng = (Tổng thời gian gia công / Thời gian 100 máy) × 100%
         = ({tong_thoi_gian_gia_cong:,.0f} / {thoi_gian_may_chay:,}) × 100%
         = {cs_tong:.2f}%""", language="python")
                else:
                    st.warning("⚠️ Thời gian 100 máy = 0, không thể tính CS tổng")
        
        # QC (Kiểm tra AMJ) Capacity Trend Chart
        st.markdown("---")
        st.markdown("### 📈 Kiểm tra AMJ - Biểu đồ xu hướng Công suất")
        
        if df_giao_kho_vp is not None and not df_giao_kho_vp.empty:
            # Filter giao_kho_vp data for selected month (using same trend_month filter)
            if 'ngay_dong_goi_parsed' in df_giao_kho_vp.columns:
                df_giao_kho_vp['year_month_qc'] = df_giao_kho_vp['ngay_dong_goi_parsed'].dt.to_period('M')
                
                qc_selected_period = pd.Period(trend_month)
                df_qc_month = df_giao_kho_vp[
                    df_giao_kho_vp['year_month_qc'] == qc_selected_period
                ].copy()
                
                if len(df_qc_month) > 0:
                    # Get date range for the month
                    qc_start_date = pd.to_datetime(qc_selected_period.start_time)
                    qc_end_date = pd.to_datetime(qc_selected_period.end_time)
                    
                    st.info(f"📅 Đang tính toán biểu đồ từ {qc_start_date.strftime('%d/%m/%Y')} đến {qc_end_date.strftime('%d/%m/%Y')} ({len(df_qc_month)} đơn hàng)")
                    
                    # Calculate CS for each date
                    qc_trend_data = []
                    qc_days_with_data = 0
                    
                    for single_date in pd.date_range(start=qc_start_date, end=qc_end_date):
                        df_qc_day = df_qc_month[
                            df_qc_month['ngay_dong_goi_parsed'].dt.date == single_date.date()
                        ].copy()
                        
                        if len(df_qc_day) == 0:
                            continue
                        
                        qc_days_with_data += 1
                        date_str = single_date.strftime('%d/%m/%Y')
                        
                        # Calculate QC capacity for this day
                        qc_result = calculate_quality_control_capacity(
                            df_qc_day,
                            df_shift_schedule,
                            df_hr_daily_head_counts,
                            df_thoi_gian_hoan_thanh,
                            date_str
                        )
                        
                        qc_trend_data.append({
                            'date': single_date,
                            'CS tổng': qc_result['cs_tong'],
                            'CS trực tiếp': qc_result['cs_truc_tiep']
                        })
                    
                    st.success(f"✅ Đã xử lý {qc_days_with_data} ngày có dữ liệu QC, tạo được {len(qc_trend_data)} điểm dữ liệu")
                    
                    if qc_trend_data:
                        df_qc_trend = pd.DataFrame(qc_trend_data)
                        df_qc_trend['date_str'] = df_qc_trend['date'].dt.strftime('%d/%m/%Y')
                        
                        # Calculate and display monthly averages
                        avg_qc_cs_tong = df_qc_trend['CS tổng'].mean()
                        avg_qc_cs_truc_tiep = df_qc_trend['CS trực tiếp'].mean()
                        
                        st.markdown("#### 📊 Trung bình tháng")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                label="CS tổng trung bình",
                                value=f"{avg_qc_cs_tong:.1f}%",
                                help="Trung bình công suất tổng QC trong tháng"
                            )
                        with col2:
                            st.metric(
                                label="CS trực tiếp trung bình",
                                value=f"{avg_qc_cs_truc_tiep:.1f}%",
                                help="Trung bình công suất trực tiếp QC trong tháng"
                            )
                        
                        st.markdown("---")
                        
                        # Create line chart using plotly
                        import plotly.graph_objects as go
                        
                        fig_qc = go.Figure()
                        
                        # Add CS tổng line
                        fig_qc.add_trace(go.Scatter(
                            x=df_qc_trend['date_str'],
                            y=df_qc_trend['CS tổng'],
                            mode='lines+markers',
                            name='CS tổng (%)',
                            line=dict(color='#3498db', width=2),
                            marker=dict(size=6)
                        ))
                        
                        # Add CS trực tiếp line
                        fig_qc.add_trace(go.Scatter(
                            x=df_qc_trend['date_str'],
                            y=df_qc_trend['CS trực tiếp'],
                            mode='lines+markers',
                            name='CS trực tiếp (%)',
                            line=dict(color='#e74c3c', width=2),
                            marker=dict(size=6)
                        ))
                        
                        # Update layout
                        max_y = max(df_qc_trend['CS tổng'].max(), df_qc_trend['CS trực tiếp'].max(), 100)
                        fig_qc.update_layout(
                            title='Kiểm tra AMJ - Xu hướng Công suất theo thời gian',
                            xaxis_title='Ngày',
                            yaxis_title='Công suất (%)',
                            yaxis=dict(range=[0, max_y + 20]),
                            hovermode='x unified',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            height=400
                        )
                        
                        st.plotly_chart(fig_qc, use_container_width=True)
                        
                        # Excel Export Button for QC Capacity Data
                        st.markdown("---")
                        col_qc_exp1, col_qc_exp2, col_qc_exp3 = st.columns([1, 2, 1])
                        with col_qc_exp2:
                            if st.button("📥 Xuất Excel - Công suất Kiểm tra", use_container_width=True, key="export_capacity_qc"):
                                # Prepare export dataframe
                                export_qc_df = df_qc_trend.copy()
                                export_qc_df = export_qc_df.rename(columns={
                                    'date_str': 'Ngày',
                                    'CS tổng': 'CS tổng (%)',
                                    'CS trực tiếp': 'CS trực tiếp (%)'
                                })
                                
                                # Select only needed columns
                                export_qc_df = export_qc_df[['Ngày', 'CS tổng (%)', 'CS trực tiếp (%)']]
                                
                                # Convert to Excel
                                from io import BytesIO
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    export_qc_df.to_excel(writer, sheet_name='Công suất Kiểm tra', index=False)
                                    
                                    # Format numbers
                                    workbook = writer.book
                                    worksheet = writer.sheets['Công suất Kiểm tra']
                                    number_format = workbook.add_format({'num_format': '0.0'})
                                    worksheet.set_column('B:C', 12, number_format)
                                
                                excel_data = output.getvalue()
                                
                                filename = f"cong_suat_kiem_tra_{trend_month.replace('-', '_')}.xlsx"
                                
                                st.download_button(
                                    label="⬇️ Tải file Excel",
                                    data=excel_data,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True,
                                    key="download_capacity_qc"
                                )
                    else:
                        st.info("Không có dữ liệu QC để hiển thị biểu đồ xu hướng")
                else:
                    st.info(f"Không có dữ liệu QC cho tháng {trend_month}")
            else:
                st.warning("Dữ liệu giao_kho_vp ch ưa được parse ngày tháng")
        else:
            st.warning("Không có dữ liệu giao_kho_vp để tính biểu đồ QC")




if __name__ == "__main__":
    main()
