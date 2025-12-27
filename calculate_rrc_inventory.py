# -*- coding: utf-8 -*-
"""
RRC Inventory Calculator - Read from Google Sheets
Replaces Excel SUMPRODUCT formula with Python logic
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import Optional


def authenticate_google_sheets(credentials_file: str):
    """Authenticate with Google Sheets API"""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return gspread.authorize(creds)


def calculate_rrc_inventory(
    sheet_url: str,
    credentials_file: str,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate RRC inventory from Google Sheets
    
    Equivalent to Excel formula:
    =SUMPRODUCT(
        (K:K) *                    // Số lượng ĐH
        (AO:AO="") *               // Ngày giao QLCL is empty
        (ISNUMBER(Q:Q)) *          // Ngày giao phôi sx AMJ is number/date
        (TRIM(L:L)="RRC")          // KH = "RRC"
    )
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        worksheet_name: Name of worksheet (default: 'KHSX_KHSX')
        header_row: Row number containing headers (default: 4)
        data_start_row: First row of data (default: 5)
        
    Returns:
        Dictionary with calculation results and details
    """
    # Authenticate
    client = authenticate_google_sheets(credentials_file)
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Get all data
    print(f"[INFO] Reading data from '{worksheet_name}'...")
    all_data = worksheet.get_all_values()
    
    # Get headers from specified row
    headers = all_data[header_row - 1]  # Convert to 0-indexed
    
    # Get data rows
    data_rows = all_data[data_start_row - 1:]  # Convert to 0-indexed
    
    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=headers)
    
    print(f"[INFO] Total rows: {len(df)}")
    
    # Column indices (0-indexed)
    # K = col 11 (index 10): Số lượng ĐH
    # L = col 12 (index 11): KH
    # Q = col 17 (index 16): Ngày giao phôi sx AMJ
    # AO = col 41 (index 40): Ngày giao QLCL
    idx_so_luong = 10
    idx_kh = 11
    idx_ngay_giao_phoi = 16
    idx_ngay_giao_qlcl = 40
    
    # Apply filters using iloc
    print(f"[INFO] Applying filters...")
    
    # Filter 1: KH = "RRC" (trim whitespace)
    mask_rrc = df.iloc[:, idx_kh].astype(str).str.strip() == 'RRC'
    print(f"  - KH = 'RRC': {mask_rrc.sum()} rows")
    
    # Filter 2: Ngày giao QLCL is empty
    mask_qlcl_empty = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() == ''
    print(f"  - Ngay giao QLCL empty: {mask_qlcl_empty.sum()} rows")
    
    # Filter 3: ISNUMBER(Ngày giao phôi) - In Excel, dates are numbers
    # We need to check if the cell contains a valid date format (DD/MM/YYYY or DD-MM-YYYY)
    # NOT just "not empty" because some cells have "*" or other text
    def is_valid_date_format(val):
        """Check if value is a valid date format (contains / or -)"""
        val_str = str(val).strip()
        if not val_str or val_str == '':
            return False
        # Must contain date separator and not be just special characters
        return ('/' in val_str or '-' in val_str) and val_str not in ['*', '-', '/']
    
    mask_phoi_is_date = df.iloc[:, idx_ngay_giao_phoi].apply(is_valid_date_format)
    print(f"  - Ngay giao phoi is date (ISNUMBER): {mask_phoi_is_date.sum()} rows")
    
    # Combine all filters
    mask_all = mask_rrc & mask_qlcl_empty & mask_phoi_is_date
    print(f"  - All conditions met: {mask_all.sum()} rows")
    
    # Get filtered data
    filtered_df = df[mask_all].copy()
    
    # Convert Số lượng ĐH to numeric
    filtered_df.iloc[:, idx_so_luong] = pd.to_numeric(
        filtered_df.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0)
    
    # Calculate total
    total_rrc = filtered_df.iloc[:, idx_so_luong].sum()
    
    print(f"\n[RESULT] RRC Inventory: {total_rrc:,.0f}")
    
    # Return detailed results
    details_df = filtered_df.iloc[:, [idx_kh, idx_so_luong, idx_ngay_giao_phoi, idx_ngay_giao_qlcl]]
    details_df.columns = ['KH', 'So_luong_DH', 'Ngay_giao_phoi', 'Ngay_giao_QLCL']
    
    return {
        'total': total_rrc,
        'count': len(filtered_df),
        'details': details_df.to_dict('records')
    }


def calculate_external_inventory(
    sheet_url: str,
    credentials_file: str,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate External (non-RRC) inventory from Google Sheets
    
    Equivalent to Excel formula:
    =SUMPRODUCT(
        (K:K) *                    // Số lượng ĐH
        (AO:AO="") *               // Ngày giao QLCL is empty
        (Q:Q<>"") *                // Ngày giao phôi not empty
        (TRIM(Q:Q)<>"Đảo lệnh") *  // Q ≠ "Đảo lệnh"
        (TRIM(Q:Q)<>"phôi lỗi") *  // Q ≠ "phôi lỗi"
        (TRIM(L:L)<>"RRC")         // KH ≠ "RRC"
    )
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        worksheet_name: Name of worksheet (default: 'KHSX_KHSX')
        header_row: Row number containing headers (default: 4)
        data_start_row: First row of data (default: 5)
        
    Returns:
        Dictionary with calculation results and details
    """
    # Authenticate
    client = authenticate_google_sheets(credentials_file)
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Get all data
    print(f"[INFO] Reading data from '{worksheet_name}'...")
    all_data = worksheet.get_all_values()
    
    # Get headers from specified row
    headers = all_data[header_row - 1]  # Convert to 0-indexed
    
    # Get data rows
    data_rows = all_data[data_start_row - 1:]  # Convert to 0-indexed
    
    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=headers)
    
    print(f"[INFO] Total rows: {len(df)}")
    
    # Column indices (0-indexed)
    idx_so_luong = 10    # K
    idx_kh = 11          # L
    idx_ngay_giao_phoi = 16  # Q
    idx_ngay_giao_qlcl = 40  # AO
    
    # Apply filters using iloc
    print(f"[INFO] Applying filters...")
    
    # Filter 1: KH ≠ "RRC" (NOT RRC)
    mask_not_rrc = df.iloc[:, idx_kh].astype(str).str.strip() != 'RRC'
    print(f"  - KH != 'RRC': {mask_not_rrc.sum()} rows")
    
    # Filter 2: Ngày giao QLCL is empty
    mask_qlcl_empty = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() == ''
    print(f"  - Ngay giao QLCL empty: {mask_qlcl_empty.sum()} rows")
    
    # Filter 3: Ngày giao phôi not empty
    phoi_values = df.iloc[:, idx_ngay_giao_phoi].astype(str).str.strip()
    mask_phoi_not_empty = phoi_values != ''
    print(f"  - Ngay giao phoi not empty: {mask_phoi_not_empty.sum()} rows")
    
    # Filter 4: Ngày giao phôi ≠ "Đảo lệnh"
    mask_not_dao_lenh = phoi_values != 'Đảo lệnh'
    print(f"  - Ngay giao phoi != 'Dao lenh': {mask_not_dao_lenh.sum()} rows")
    
    # Filter 5: Ngày giao phôi ≠ "phôi lỗi"
    mask_not_phoi_loi = phoi_values != 'phôi lỗi'
    print(f"  - Ngay giao phoi != 'phoi loi': {mask_not_phoi_loi.sum()} rows")
    
    # Combine all filters
    mask_all = mask_not_rrc & mask_qlcl_empty & mask_phoi_not_empty & mask_not_dao_lenh & mask_not_phoi_loi
    print(f"  - All conditions met: {mask_all.sum()} rows")
    
    # Get filtered data
    filtered_df = df[mask_all].copy()
    
    # Convert Số lượng ĐH to numeric
    filtered_df.iloc[:, idx_so_luong] = pd.to_numeric(
        filtered_df.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0)
    
    # Calculate total
    total_external = filtered_df.iloc[:, idx_so_luong].sum()
    
    print(f"\n[RESULT] External Inventory: {total_external:,.0f}")
    
    # Return detailed results
    details_df = filtered_df.iloc[:, [idx_kh, idx_so_luong, idx_ngay_giao_phoi, idx_ngay_giao_qlcl]]
    details_df.columns = ['KH', 'So_luong_DH', 'Ngay_giao_phoi', 'Ngay_giao_QLCL']
    
    return {
        'total': total_external,
        'count': len(filtered_df),
        'details': details_df.to_dict('records')
    }


def calculate_rrc_pkt_inventory(
    sheet_url: str,
    credentials_file: str,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate RRC PKT (Finished Goods) inventory from Google Sheets
    
    Equivalent to Excel formula:
    =SUMPRODUCT(
        (K:K) *                    // Số lượng ĐH
        (AO:AO<>"") *              // Ngày giao QLCL NOT empty
        (AS:AS="") *               // Hàng gói Ok is empty
        (W:W="") *                 // Ngày xuất hàng is empty
        (L:L="RRC")                // KH = "RRC"
    )
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        worksheet_name: Name of worksheet (default: 'KHSX_KHSX')
        header_row: Row number containing headers (default: 4)
        data_start_row: First row of data (default: 5)
        
    Returns:
        Dictionary with calculation results and details
    """
    # Authenticate
    client = authenticate_google_sheets(credentials_file)
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Get all data
    print(f"[INFO] Reading data from '{worksheet_name}'...")
    all_data = worksheet.get_all_values()
    
    # Get headers from specified row
    headers = all_data[header_row - 1]
    data_rows = all_data[data_start_row - 1:]
    df = pd.DataFrame(data_rows, columns=headers)
    
    print(f"[INFO] Total rows: {len(df)}")
    
    # Column indices
    idx_so_luong = 10    # K
    idx_kh = 11          # L
    idx_ngay_xuat_hang = 22  # W (col 23)
    idx_ngay_giao_qlcl = 40  # AO (col 41)
    idx_hang_goi_ok = 44     # AS (col 45)
    
    # Apply filters
    print(f"[INFO] Applying filters...")
    
    # Filter 1: KH = "RRC"
    mask_rrc = df.iloc[:, idx_kh].astype(str).str.strip() == 'RRC'
    print(f"  - KH = 'RRC': {mask_rrc.sum()} rows")
    
    # Filter 2: Ngày giao QLCL NOT empty
    mask_qlcl_not_empty = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() != ''
    print(f"  - Ngay giao QLCL NOT empty: {mask_qlcl_not_empty.sum()} rows")
    
    # Filter 3: Hàng gói Ok is empty
    mask_hang_goi_empty = df.iloc[:, idx_hang_goi_ok].astype(str).str.strip() == ''
    print(f"  - Hang goi Ok empty: {mask_hang_goi_empty.sum()} rows")
    
    # Filter 4: Ngày xuất hàng is empty
    mask_xuat_hang_empty = df.iloc[:, idx_ngay_xuat_hang].astype(str).str.strip() == ''
    print(f"  - Ngay xuat hang empty: {mask_xuat_hang_empty.sum()} rows")
    
    # Combine all filters
    mask_all = mask_rrc & mask_qlcl_not_empty & mask_hang_goi_empty & mask_xuat_hang_empty
    print(f"  - All conditions met: {mask_all.sum()} rows")
    
    # Get filtered data
    filtered_df = df[mask_all].copy()
    
    # Convert to numeric
    filtered_df.iloc[:, idx_so_luong] = pd.to_numeric(
        filtered_df.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0)
    
    # Calculate total
    total_rrc_pkt = filtered_df.iloc[:, idx_so_luong].sum()
    
    print(f"\n[RESULT] RRC PKT Inventory: {total_rrc_pkt:,.0f}")
    
    # Return results
    details_df = filtered_df.iloc[:, [idx_kh, idx_so_luong, idx_ngay_giao_qlcl, idx_hang_goi_ok, idx_ngay_xuat_hang]]
    details_df.columns = ['KH', 'So_luong_DH', 'Ngay_giao_QLCL', 'Hang_goi_Ok', 'Ngay_xuat_hang']
    
    return {
        'total': total_rrc_pkt,
        'count': len(filtered_df),
        'details': details_df.to_dict('records')
    }


def calculate_external_pkt_inventory(
    sheet_url: str,
    credentials_file: str,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate External PKT (Finished Goods) inventory from Google Sheets
    
    Equivalent to Excel formula:
    =SUMPRODUCT(
        (K:K) *                    // Số lượng ĐH
        (AO:AO<>"") *              // Ngày giao QLCL NOT empty
        (AS:AS="") *               // Hàng gói Ok is empty
        (W:W="") *                 // Ngày xuất hàng is empty
        (L:L<>"RRC") *             // KH ≠ "RRC"
        (L:L<>"AMJ")               // KH ≠ "AMJ"
    )
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to credentials JSON
        worksheet_name: Name of worksheet (default: 'KHSX_KHSX')
        header_row: Row number containing headers (default: 4)
        data_start_row: First row of data (default: 5)
        
    Returns:
        Dictionary with calculation results and details
    """
    # Authenticate
    client = authenticate_google_sheets(credentials_file)
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Get all data
    print(f"[INFO] Reading data from '{worksheet_name}'...")
    all_data = worksheet.get_all_values()
    
    # Get headers from specified row
    headers = all_data[header_row - 1]
    data_rows = all_data[data_start_row - 1:]
    df = pd.DataFrame(data_rows, columns=headers)
    
    print(f"[INFO] Total rows: {len(df)}")
    
    # Column indices
    idx_so_luong = 10    # K
    idx_kh = 11          # L
    idx_ngay_xuat_hang = 22  # W (col 23)
    idx_ngay_giao_qlcl = 40  # AO (col 41)
    idx_hang_goi_ok = 44     # AS (col 45)
    
    # Apply filters
    print(f"[INFO] Applying filters...")
    
    kh_values = df.iloc[:, idx_kh].astype(str).str.strip()
    
    # Filter 1: KH ≠ "RRC" AND KH ≠ "AMJ"
    mask_not_rrc_amj = (kh_values != 'RRC') & (kh_values != 'AMJ')
    print(f"  - KH != 'RRC' AND != 'AMJ': {mask_not_rrc_amj.sum()} rows")
    
    # Filter 2: Ngày giao QLCL NOT empty
    mask_qlcl_not_empty = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() != ''
    print(f"  - Ngay giao QLCL NOT empty: {mask_qlcl_not_empty.sum()} rows")
    
    # Filter 3: Hàng gói Ok is empty
    mask_hang_goi_empty = df.iloc[:, idx_hang_goi_ok].astype(str).str.strip() == ''
    print(f"  - Hang goi Ok empty: {mask_hang_goi_empty.sum()} rows")
    
    # Filter 4: Ngày xuất hàng is empty
    mask_xuat_hang_empty = df.iloc[:, idx_ngay_xuat_hang].astype(str).str.strip() == ''
    print(f"  - Ngay xuat hang empty: {mask_xuat_hang_empty.sum()} rows")
    
    # Combine all filters
    mask_all = mask_not_rrc_amj & mask_qlcl_not_empty & mask_hang_goi_empty & mask_xuat_hang_empty
    print(f"  - All conditions met: {mask_all.sum()} rows")
    
    # Get filtered data
    filtered_df = df[mask_all].copy()
    
    # Convert to numeric
    filtered_df.iloc[:, idx_so_luong] = pd.to_numeric(
        filtered_df.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0)
    
    # Calculate total
    total_external_pkt = filtered_df.iloc[:, idx_so_luong].sum()
    
    print(f"\n[RESULT] External PKT Inventory: {total_external_pkt:,.0f}")
    
    # Return results
    details_df = filtered_df.iloc[:, [idx_kh, idx_so_luong, idx_ngay_giao_qlcl, idx_hang_goi_ok, idx_ngay_xuat_hang]]
    details_df.columns = ['KH', 'So_luong_DH', 'Ngay_giao_QLCL', 'Hang_goi_Ok', 'Ngay_xuat_hang']
    
    return {
        'total': total_external_pkt,
        'count': len(filtered_df),
        'details': details_df.to_dict('records')
    }


if __name__ == "__main__":
    from khsx_sync_config import CONFIG
    
    print("=" * 70)
    print("INVENTORY CALCULATOR - ALL TYPES")
    print("=" * 70)
    print()
    
    # Calculate RRC
    print("1. CALCULATING RRC INVENTORY...")
    print("-" * 70)
    result_rrc = calculate_rrc_inventory(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials']
    )
    
    # Calculate External
    print()
    print("2. CALCULATING EXTERNAL INVENTORY...")
    print("-" * 70)
    result_external = calculate_external_inventory(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials']
    )
    
    # Calculate RRC PKT
    print()
    print("3. CALCULATING RRC PKT INVENTORY...")
    print("-" * 70)
    result_rrc_pkt = calculate_rrc_pkt_inventory(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials']
    )
    
    # Calculate External PKT
    print()
    print("4. CALCULATING EXTERNAL PKT INVENTORY...")
    print("-" * 70)
    result_external_pkt = calculate_external_pkt_inventory(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials']
    )
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("HANG TON (Inventory):")
    print(f"  RRC:              {result_rrc['total']:>10,.0f} ({result_rrc['count']} orders)")
    print(f"  External:         {result_external['total']:>10,.0f} ({result_external['count']} orders)")
    print(f"  {'-' * 70}")
    print(f"  Subtotal:         {result_rrc['total'] + result_external['total']:>10,.0f}")
    print()
    print("HANG TON PKT (Finished Goods):")
    print(f"  RRC PKT:          {result_rrc_pkt['total']:>10,.0f} ({result_rrc_pkt['count']} orders)")
    print(f"  External PKT:     {result_external_pkt['total']:>10,.0f} ({result_external_pkt['count']} orders)")
    print(f"  {'-' * 70}")
    print(f"  Subtotal:         {result_rrc_pkt['total'] + result_external_pkt['total']:>10,.0f}")
    print()
    print("=" * 70)
    print(f"GRAND TOTAL:        {result_rrc['total'] + result_external['total'] + result_rrc_pkt['total'] + result_external_pkt['total']:>10,.0f}")
    print("=" * 70)
