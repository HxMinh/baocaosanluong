# -*- coding: utf-8 -*-
"""
Combined Inventory Calculator - All-in-One
Calculates all 4 inventory metrics in ONE API call instead of 4
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime


def calculate_all_inventory_metrics(
    sheet_url: str,
    credentials_file: str = None,
    gspread_client=None,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate ALL inventory metrics in one pass:
    - RRC inventory (Sản xuất)
    - External inventory (Sản xuất)
    - RRC PKT inventory (Kiểm tra)
    - External PKT inventory (Kiểm tra)
    
    Returns dict with all 4 metrics
    
    Args:
        sheet_url: Google Sheets URL
        credentials_file: Path to JSON credentials (optional, for local)
        gspread_client: Pre-authenticated gspread client (optional, for cloud)
    """
    # Use provided client OR authenticate with file
    if gspread_client is not None:
        client = gspread_client
    elif credentials_file:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
    else:
        raise ValueError("Either gspread_client or credentials_file must be provided")
    
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Read data ONCE
    all_data = worksheet.get_all_values()
    headers = all_data[header_row - 1]
    data_rows = all_data[data_start_row - 1:]
    df = pd.DataFrame(data_rows, columns=headers)
    
    # Column indices
    idx_so_luong = 10        # K (col 11): Số lượng ĐH
    idx_kh = 11              # L (col 12): KH
    idx_ngay_giao_phoi = 16  # Q (col 17): Ngày giao phôi sx AMJ
    idx_field_w = 22         # W (col 23): Field W
    idx_ngay_giao_qlcl = 40  # AO (col 41): Ngày giao QLCL
    idx_field_as = 44        # AS (col 45): Field AS
    
    results = {}
    
    # =====================================================================
    # RRC Inventory (Sản xuất)
    # Excel: AO = empty, Q ≠ empty (ISNUMBER), L = RRC
    # ISNUMBER means Q must be a valid date, not just non-empty string
    # =====================================================================
    
    # Parse Q as date (ISNUMBER check)
    df['q_parsed'] = pd.to_datetime(
        df.iloc[:, idx_ngay_giao_phoi],
        format='%d/%m/%Y',
        errors='coerce'
    )
    
    mask_rrc_sx = (
        (df.iloc[:, idx_kh].astype(str).str.strip() == 'RRC') &
        (df['q_parsed'].notna()) &  # ISNUMBER - must be valid date
        (df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() == '')
    )
    
    df_rrc_sx = df[mask_rrc_sx].copy()
    df_rrc_sx['So_luong'] = pd.to_numeric(
        df_rrc_sx.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    
    results['rrc_inventory'] = int(df_rrc_sx['So_luong'].sum())
    
    # =====================================================================
    # External Inventory (Sản xuất)
    # Excel: AO = empty, Q ≠ empty (ISNUMBER), L ≠ RRC
    # =====================================================================
    mask_ext_sx = (
        (df.iloc[:, idx_kh].astype(str).str.strip() != 'RRC') &
        (df['q_parsed'].notna()) &  # ISNUMBER - must be valid date
        (df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() == '')
    )
    
    df_ext_sx = df[mask_ext_sx].copy()
    df_ext_sx['So_luong'] = pd.to_numeric(
        df_ext_sx.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    
    results['external_inventory'] = int(df_ext_sx['So_luong'].sum())
    
    # =====================================================================
    # RRC PKT Inventory (Kiểm tra)
    # Excel: AO ≠ empty, AS = empty, W = empty, L = RRC
    # =====================================================================
    mask_rrc_pkt = (
        (df.iloc[:, idx_kh].astype(str).str.strip() == 'RRC') &
        (df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() != '') &
        (df.iloc[:, idx_field_as].astype(str).str.strip() == '') &
        (df.iloc[:, idx_field_w].astype(str).str.strip() == '')
    )
    
    df_rrc_pkt = df[mask_rrc_pkt].copy()
    df_rrc_pkt['So_luong'] = pd.to_numeric(
        df_rrc_pkt.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    
    results['rrc_pkt_inventory'] = int(df_rrc_pkt['So_luong'].sum())
    
    # =====================================================================
    # External PKT Inventory (Kiểm tra)
    # Excel: AO ≠ empty, AS = empty, W = empty, L ≠ RRC
    # =====================================================================
    mask_ext_pkt = (
        (df.iloc[:, idx_kh].astype(str).str.strip() != 'RRC') &
        (df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() != '') &
        (df.iloc[:, idx_field_as].astype(str).str.strip() == '') &
        (df.iloc[:, idx_field_w].astype(str).str.strip() == '')
    )
    
    df_ext_pkt = df[mask_ext_pkt].copy()
    df_ext_pkt['So_luong'] = pd.to_numeric(
        df_ext_pkt.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    
    results['external_pkt_inventory'] = int(df_ext_pkt['So_luong'].sum())
    
    return results


if __name__ == "__main__":
    from khsx_sync_config import CONFIG
    
    print("="*70)
    print("COMBINED INVENTORY CALCULATOR")
    print("="*70)
    print()
    
    import time
    start_time = time.time()
    
    results = calculate_all_inventory_metrics(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials']
    )
    
    elapsed = time.time() - start_time
    
    print("RESULTS (calculated in one pass):")
    print("="*70)
    print()
    print(f"RRC Inventory (SX):      {results['rrc_inventory']:>6,}")
    print(f"External Inventory (SX): {results['external_inventory']:>6,}")
    print(f"RRC PKT Inventory:       {results['rrc_pkt_inventory']:>6,}")
    print(f"External PKT Inventory:  {results['external_pkt_inventory']:>6,}")
    print()
    print(f"Total SX:  {results['rrc_inventory'] + results['external_inventory']:>6,}")
    print(f"Total PKT: {results['rrc_pkt_inventory'] + results['external_pkt_inventory']:>6,}")
    print(f"Grand Total: {sum(results.values()):>6,}")
    print()
    print("="*70)
    print(f"[FAST] Total time: {elapsed:.2f} seconds")
    print("="*70)
