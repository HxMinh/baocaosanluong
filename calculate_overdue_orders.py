# -*- coding: utf-8 -*-
"""
Overdue and Due Soon Order Calculator - CORRECTED VBA LOGIC
Step 1: Filter by VBA conditions (Date+10, Field 41 empty, Field 17 not empty)
Step 2: Apply SUMIF logic (TODAY+5 for overdue/due soon)
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def authenticate_google_sheets(credentials_file: str):
    """Authenticate with Google Sheets API"""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return gspread.authorize(creds)


def get_vba_filtered_orders(
    sheet_url: str,
    credentials_file: str,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> pd.DataFrame:
    """
    STEP 1: Get VBA-filtered orders
    
    Filters (exactly as VBA macro):
    - Field 14 (TH mới khách hàng) <= Date + 10
    - Field 41 (Ngày giao QLCL) = empty
    - Field 17 (Ngày giao phôi sx AMJ) <> empty
    
    Returns DataFrame with all filtered orders
    """
    # Authenticate
    client = authenticate_google_sheets(credentials_file)
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Get all data
    all_data = worksheet.get_all_values()
    
    # Get headers and data
    headers = all_data[header_row - 1]
    data_rows = all_data[data_start_row - 1:]
    df = pd.DataFrame(data_rows, columns=headers)
    
    # Column indices
    idx_so_luong = 10        # K (col 11): Số lượng ĐH
    idx_kh = 11              # L (col 12): KH
    idx_thoi_han = 13        # N (col 14): TH mới khách hàng
    idx_ngay_giao_phoi = 16  # Q (col 17): Ngày giao phôi sx AMJ
    idx_ngay_giao_qlcl = 40  # AO (col 41): Ngày giao QLCL
    
    # Calculate date threshold (VBA uses Date + 10)
    today = datetime.now().date()
    vba_date_threshold = today + timedelta(days=10)
    
    # FILTER 1: Field 41 (Ngày giao QLCL) is empty
    mask1 = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() == ''
    
    # FILTER 2: Field 17 (Ngày giao phôi) is NOT empty  
    mask2 = df.iloc[:, idx_ngay_giao_phoi].astype(str).str.strip() != ''
    
    # FILTER 3: Field 14 (TH mới khách hàng) <= Date + 10
    thoi_han_values = df.iloc[:, idx_thoi_han].astype(str).str.strip()
    mask3 = pd.Series([False] * len(df), index=df.index)
    
    for idx, th_str in thoi_han_values.items():
        if th_str and th_str != '':
            try:
                th_date = pd.to_datetime(th_str, format='%d/%m/%Y', errors='coerce')
                if pd.notna(th_date):
                    mask3.loc[idx] = th_date.date() <= vba_date_threshold
            except:
                pass
    
    # Combine all 3 VBA filters
    mask_all = mask1 & mask2 & mask3
    filtered_df = df[mask_all].copy()
    
    # Prepare result
    result_df = pd.DataFrame({
        'So_luong': filtered_df.iloc[:, idx_so_luong],
        'KH': filtered_df.iloc[:, idx_kh],
        'TH_moi_khach_hang': filtered_df.iloc[:, idx_thoi_han]
    })
    
    # Convert So_luong to numeric
    result_df['So_luong'] = pd.to_numeric(
        result_df['So_luong'].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    
    # Parse TH_moi_khach_hang dates
    result_df['TH_date'] = pd.to_datetime(
        result_df['TH_moi_khach_hang'],
        format='%d/%m/%Y',
        errors='coerce'
    )
    
    return result_df


def calculate_overdue_orders(
    sheet_url: str,
    credentials_file: str,
    days_ahead: int = 5,
    customer_type: str = 'RRC',
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate overdue orders (Quá hạn)
    
    2-STEP PROCESS:
    Step 1: Get VBA filtered orders (Field 14 <= Date+10, Field 41 empty, Field 17 not empty)
    Step 2: Apply SUMIF logic (TH mới khách hàng <= TODAY()+5)
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        days_ahead: Number of days ahead to consider overdue (default: 5)
        customer_type: 'RRC' or 'EXTERNAL'
        
    Returns:
        Dictionary with calculation results
    """
    # Step 1: Get VBA filtered orders
    filtered_df = get_vba_filtered_orders(
        sheet_url=sheet_url,
        credentials_file=credentials_file,
        worksheet_name=worksheet_name,
        header_row=header_row,
        data_start_row=data_start_row
    )
    
    # Step 2: Filter by customer type
    if customer_type == 'RRC':
        df_customer = filtered_df[filtered_df['KH'].str.strip() == 'RRC'].copy()
    else:
        df_customer = filtered_df [filtered_df['KH'].str.strip() != 'RRC'].copy()
    
    # Step 2: Apply SUMIF logic - TH mới khách hàng <= TODAY() + days_ahead
    today = datetime.now().date()
    threshold = today + timedelta(days=days_ahead)
    
    df_overdue = df_customer[
        df_customer['TH_date'].notna() & 
        (df_customer['TH_date'].dt.date <= threshold)
    ].copy()
    
    total_overdue = df_overdue['So_luong'].sum()
    
    return {
        'total': int(total_overdue),
        'count': len(df_overdue),
        'customer_type': customer_type,
        'deadline_threshold': threshold.strftime('%d/%m/%Y')
    }


def calculate_due_soon_orders(
    sheet_url: str,
    credentials_file: str,
    days_ahead: int = 5,
    customer_type: str = 'RRC',
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate due soon orders (Tới hạn)
    
    2-STEP PROCESS:
    Step 1: Get VBA filtered orders (Field 14 <= Date+10, Field 41 empty, Field 17 not empty)
    Step 2: Apply SUMIF logic (TH mới khách hàng > TODAY()+5)
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        days_ahead: Number of days ahead threshold (default: 5)
        customer_type: 'RRC' or 'EXTERNAL'
        
    Returns:
        Dictionary with calculation results
    """
    # Step 1: Get VBA filtered orders
    filtered_df = get_vba_filtered_orders(
        sheet_url=sheet_url,
        credentials_file=credentials_file,
        worksheet_name=worksheet_name,
        header_row=header_row,
        data_start_row=data_start_row
    )
    
    # Step 2: Filter by customer type
    if customer_type == 'RRC':
        df_customer = filtered_df[filtered_df['KH'].str.strip() == 'RRC'].copy()
    else:
        df_customer = filtered_df[filtered_df['KH'].str.strip() != 'RRC'].copy()
    
    # Step 2: Apply SUMIF logic - TH mới khách hàng > TODAY() + days_ahead
    today = datetime.now().date()
    threshold = today + timedelta(days=days_ahead)
    
    df_due_soon = df_customer[
        df_customer['TH_date'].notna() & 
        (df_customer['TH_date'].dt.date > threshold)
    ].copy()
    
    total_due_soon = df_due_soon['So_luong'].sum()
    
    return {
        'total': int(total_due_soon),
        'count': len(df_due_soon),
        'customer_type': customer_type,
        'deadline_threshold': threshold.strftime('%d/%m/%Y')
    }


if __name__ == "__main__":
    from khsx_sync_config import CONFIG
    
    print("=" * 70)
    print("OVERDUE AND DUE SOON CALCULATOR - CORRECTED VBA LOGIC")
    print("=" * 70)
    print()
    
    # Calculate RRC Overdue
    print("1. RRC - OVERDUE")
    print("-" * 70)
    rrc_overdue = calculate_overdue_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='RRC'
    )
    
    # Calculate RRC Due Soon
    print()
    print("2. RRC - DUE SOON")
    print("-" * 70)
    rrc_due_soon = calculate_due_soon_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='RRC'
    )
    
    # Calculate External Overdue
    print()
    print("3. EXTERNAL - OVERDUE")
    print("-" * 70)
    ext_overdue = calculate_overdue_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='EXTERNAL'
    )
    
    # Calculate External Due Soon
    print()
    print("4. EXTERNAL - DUE SOON")
    print("-" * 70)
    ext_due_soon = calculate_due_soon_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='EXTERNAL'
    )
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY - SAN XUAT AMJ")
    print("=" * 70)
    print()
    print(f"RRC:")
    print(f"  Overdue:  {rrc_overdue['total']:>6,} ({rrc_overdue['count']} orders)")
    print(f"  Due Soon: {rrc_due_soon['total']:>6,} ({rrc_due_soon['count']} orders)")
    print()
    print(f"External:")
    print(f"  Overdue:  {ext_overdue['total']:>6,} ({ext_overdue['count']} orders)")
    print(f"  Due Soon: {ext_due_soon['total']:>6,} ({ext_due_soon['count']} orders)")
    print()
    print(f"Total:")
    print(f"  Overdue:  {rrc_overdue['total'] + ext_overdue['total']:>6,}")
    print(f"  Due Soon: {rrc_due_soon['total'] + ext_due_soon['total']:>6,}")
    print(f"  Grand Total: {rrc_overdue['total'] + rrc_due_soon['total'] + ext_overdue['total'] + ext_due_soon['total']:>6,}")
    print("=" * 70)
