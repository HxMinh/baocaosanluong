# -*- coding: utf-8 -*-
"""
PKT (Quality Control) Overdue and Due Soon Calculator
Exactly replicates VBA logic for PKT department
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta


def authenticate_google_sheets(credentials_file: str):
    """Authenticate with Google Sheets API"""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return gspread.authorize(creds)


def get_pkt_vba_filtered_orders(
    sheet_url: str,
    credentials_file: str,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> pd.DataFrame:
    """
    STEP 1: Get VBA-filtered orders for PKT (Quality Control)
    
    Filters (exactly as VBA macro for PKT):
    - Field 14 (TH mới khách hàng) <= Date + 8
    - Field 41 (Ngày giao QLCL) <> empty (NOT empty - different from SX!)
    - Field 45 (AS) = empty
    - Field 23 (W) = empty
    - Get DISTINCT ORKD values only
    
    Returns DataFrame with filtered DISTINCT orders
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
    idx_orkd = 4             # E (col 5): ORKD
    idx_so_luong = 10        # K (col 11): Số lượng ĐH
    idx_kh = 11              # L (col 12): KH
    idx_thoi_han = 13        # N (col 14): TH mới khách hàng
    idx_field_w = 22         # W (col 23): Field 23
    idx_ngay_giao_qlcl = 40  # AO (col 41): Ngày giao QLCL
    idx_field_as = 44        # AS (col 45): Field 45
    
    # Calculate date threshold (VBA uses Date + 8 for PKT)
    today = datetime.now().date()
    vba_date_threshold = today + timedelta(days=8)
    
    print(f"[PKT] Applying VBA filters...")
    print(f"[PKT] Date threshold (Date + 8): {vba_date_threshold.strftime('%d/%m/%Y')}")
    
    # FILTER 1: Field 14 (TH mới khách hàng) <= Date + 8
    thoi_han_values = df.iloc[:, idx_thoi_han].astype(str).str.strip()
    mask1 = pd.Series([False] * len(df), index=df.index)
    
    for idx, th_str in thoi_han_values.items():
        if th_str and th_str != '':
            try:
                th_date = pd.to_datetime(th_str, format='%d/%m/%Y', errors='coerce')
                if pd.notna(th_date):
                    mask1.loc[idx] = th_date.date() <= vba_date_threshold
            except:
                pass
    
    print(f"[PKT] Filter 1 - Field 14 (TH moi khach hang) <= {vba_date_threshold.strftime('%d/%m/%Y')}: {mask1.sum()} rows")
    
    # FILTER 2: Field 41 (Ngày giao QLCL) <> empty (NOT EMPTY!)
    mask2 = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() != ''
    print(f"[PKT] Filter 2 - Field 41 (Ngay giao QLCL) NOT empty: {mask2.sum()} rows")
    
    # FILTER 3: Field 45 (AS) = empty
    mask3 = df.iloc[:, idx_field_as].astype(str).str.strip() == ''
    print(f"[PKT] Filter 3 - Field 45 (AS) empty: {mask3.sum()} rows")
    
    # FILTER 4: Field 23 (W) = empty
    mask4 = df.iloc[:, idx_field_w].astype(str).str.strip() == ''
    print(f"[PKT] Filter 4 - Field 23 (W) empty: {mask4.sum()} rows")
    
    # Combine all 4 VBA filters
    mask_all = mask1 & mask2 & mask3 & mask4
    print(f"[PKT] All filters combined: {mask_all.sum()} rows")
    
    filtered_df = df[mask_all].copy()
    
    # Get DISTINCT ORKD values (VBA uses Dictionary for unique values)
    # For each unique ORKD, we'll take the first occurrence's data
    filtered_df_distinct = filtered_df.drop_duplicates(subset=[filtered_df.columns[idx_orkd]], keep='first')
    
    print(f"[PKT] After removing duplicates: {len(filtered_df_distinct)} DISTINCT orders")
    
    # Prepare result
    result_df = pd.DataFrame({
        'ORKD': filtered_df_distinct.iloc[:, idx_orkd].values,
        'So_luong': filtered_df_distinct.iloc[:, idx_so_luong].values,
        'KH': filtered_df_distinct.iloc[:, idx_kh].values,
        'TH_moi_khach_hang': filtered_df_distinct.iloc[:, idx_thoi_han].values
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


def calculate_pkt_overdue_orders(
    sheet_url: str,
    credentials_file: str,
    days_ahead: int = 3,
    customer_type: str = 'RRC',
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate PKT overdue orders (Quá hạn PKT)
    
    2-STEP PROCESS:
    Step 1: Get VBA filtered orders for PKT (Field 14 <= Date+8, Field 41 NOT empty, etc.)
    Step 2: Apply SUMIF logic (TH mới khách hàng <= TODAY()+3)
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        days_ahead: Number of days ahead to consider overdue (default: 3 for PKT)
        customer_type: 'RRC' or 'EXTERNAL'
        
    Returns:
        Dictionary with calculation results
    """
    # Step 1: Get VBA filtered orders for PKT
    filtered_df = get_pkt_vba_filtered_orders(
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
    
    print(f"\n[PKT] Customer type '{customer_type}': {len(df_customer)} orders")
    
    # Step 2: Apply SUMIF logic - TH mới khách hàng <= TODAY() + days_ahead
    today = datetime.now().date()
    threshold = today + timedelta(days=days_ahead)
    
    print(f"[PKT] Overdue threshold: <= {threshold.strftime('%d/%m/%Y')}")
    
    df_overdue = df_customer[
        df_customer['TH_date'].notna() & 
        (df_customer['TH_date'].dt.date <= threshold)
    ].copy()
    
    total_overdue = df_overdue['So_luong'].sum()
    
    print(f"[PKT] Overdue orders: {len(df_overdue)}, Total quantity: {total_overdue:,}")
    
    return {
        'total': int(total_overdue),
        'count': len(df_overdue),
        'customer_type': customer_type,
        'deadline_threshold': threshold.strftime('%d/%m/%Y')
    }


def calculate_pkt_due_soon_orders(
    sheet_url: str,
    credentials_file: str,
    days_ahead: int = 3,
    customer_type: str = 'RRC',
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate PKT due soon orders (Tới hạn PKT)
    
    2-STEP PROCESS:
    Step 1: Get VBA filtered orders for PKT (Field 14 <= Date+8, Field 41 NOT empty, etc.)
    Step 2: Apply SUMIF logic (TH mới khách hàng > TODAY()+3)
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        days_ahead: Number of days ahead threshold (default: 3 for PKT)
        customer_type: 'RRC' or 'EXTERNAL'
        
    Returns:
        Dictionary with calculation results
    """
    # Step 1: Get VBA filtered orders for PKT
    filtered_df = get_pkt_vba_filtered_orders(
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
    
    print(f"\n[PKT] Customer type '{customer_type}': {len(df_customer)} orders")
    
    # Step 2: Apply SUMIF logic - TH mới khách hàng > TODAY() + days_ahead
    today = datetime.now().date()
    threshold = today + timedelta(days=days_ahead)
    
    print(f"[PKT] Due soon threshold: > {threshold.strftime('%d/%m/%Y')}")
    
    df_due_soon = df_customer[
        df_customer['TH_date'].notna() & 
        (df_customer['TH_date'].dt.date > threshold)
    ].copy()
    
    total_due_soon = df_due_soon['So_luong'].sum()
    
    print(f"[PKT] Due soon orders: {len(df_due_soon)}, Total quantity: {total_due_soon:,}")
    
    return {
        'total': int(total_due_soon),
        'count': len(df_due_soon),
        'customer_type': customer_type,
        'deadline_threshold': threshold.strftime('%d/%m/%Y')
    }


if __name__ == "__main__":
    from khsx_sync_config import CONFIG
    
    print("=" * 70)
    print("PKT (QUALITY CONTROL) OVERDUE & DUE SOON CALCULATOR")
    print("=" * 70)
    print()
    
    # Calculate RRC Overdue (PKT)
    print("1. RRC - OVERDUE (PKT)")
    print("-" * 70)
    rrc_overdue = calculate_pkt_overdue_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='RRC'
    )
    
    # Calculate RRC Due Soon (PKT)
    print()
    print("2. RRC - DUE SOON (PKT)")
    print("-" * 70)
    rrc_due_soon = calculate_pkt_due_soon_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='RRC'
    )
    
    # Calculate External Overdue (PKT)
    print()
    print("3. EXTERNAL - OVERDUE (PKT)")
    print("-" * 70)
    ext_overdue = calculate_pkt_overdue_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='EXTERNAL'
    )
    
    # Calculate External Due Soon (PKT)
    print()
    print("4. EXTERNAL - DUE SOON (PKT)")
    print("-" * 70)
    ext_due_soon = calculate_pkt_due_soon_orders(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials'],
        customer_type='EXTERNAL'
    )
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY - PKT AMJ")
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
