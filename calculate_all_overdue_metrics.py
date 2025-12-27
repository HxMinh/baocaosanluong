# -*- coding: utf-8 -*-
"""
Optimized All-in-One Overdue/Due Soon Calculator
Calculates all metrics in one pass to avoid multiple Google Sheets reads
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


def calculate_all_overdue_metrics(
    sheet_url: str,
    credentials_file: str,
    worksheet_name: str = 'KHSX_KHSX',
    header_row: int = 4,
    data_start_row: int = 5
) -> dict:
    """
    Calculate ALL overdue/due soon metrics in one pass:
    - SX AMJ: RRC & External (Overdue & Due Soon)
    - PKT AMJ: RRC & External (Overdue & Due Soon)
    
    Returns dict with all 8 metrics
    """
    # Authenticate ONCE
    client = authenticate_google_sheets(credentials_file)
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.worksheet(worksheet_name)
    
    # Read data ONCE
    all_data = worksheet.get_all_values()
    headers = all_data[header_row - 1]
    data_rows = all_data[data_start_row - 1:]
    df = pd.DataFrame(data_rows, columns=headers)
    
    # Column indices
    idx_so_luong = 10        # K
    idx_kh = 11              # L
    idx_thoi_han = 13        # N
    idx_ngay_giao_phoi = 16  # Q
    idx_field_w = 22         # W
    idx_ngay_giao_qlcl = 40  # AO
    idx_field_as = 44        # AS
    
    today = datetime.now().date()
    
    # =====================================================================
    # STEP 1: Filter for SX AMJ (Production)
    # =====================================================================
    vba_sx_threshold = today + timedelta(days=10)
    
    mask_sx_1 = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() == ''
    mask_sx_2 = df.iloc[:, idx_ngay_giao_phoi].astype(str).str.strip() != ''
    
    thoi_han_values = df.iloc[:, idx_thoi_han].astype(str).str.strip()
    mask_sx_3 = pd.Series([False] * len(df), index=df.index)
    
    for idx, th_str in thoi_han_values.items():
        if th_str and th_str != '':
            try:
                th_date = pd.to_datetime(th_str, format='%d/%m/%Y', errors='coerce')
                if pd.notna(th_date):
                    mask_sx_3.loc[idx] = th_date.date() <= vba_sx_threshold
            except:
                pass
    
    df_sx_filtered = df[mask_sx_1 & mask_sx_2 & mask_sx_3].copy()
    
    # Parse dates and quantities for SX
    df_sx_filtered['So_luong'] = pd.to_numeric(
        df_sx_filtered.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    
    df_sx_filtered['TH_date'] = pd.to_datetime(
        df_sx_filtered.iloc[:, idx_thoi_han],
        format='%d/%m/%Y',
        errors='coerce'
    )
    
    df_sx_filtered['KH'] = df_sx_filtered.iloc[:, idx_kh].astype(str).str.strip()
    
    # =====================================================================
    # STEP 2: Filter for PKT AMJ (Quality Control)
    # =====================================================================
    vba_pkt_threshold = today + timedelta(days=8)
    
    mask_pkt_1 = pd.Series([False] * len(df), index=df.index)
    for idx, th_str in thoi_han_values.items():
        if th_str and th_str != '':
            try:
                th_date = pd.to_datetime(th_str, format='%d/%m/%Y', errors='coerce')
                if pd.notna(th_date):
                    mask_pkt_1.loc[idx] = th_date.date() <= vba_pkt_threshold
            except:
                pass
    
    mask_pkt_2 = df.iloc[:, idx_ngay_giao_qlcl].astype(str).str.strip() != ''
    mask_pkt_3 = df.iloc[:, idx_field_as].astype(str).str.strip() == ''
    mask_pkt_4 = df.iloc[:, idx_field_w].astype(str).str.strip() == ''
    
    df_pkt_temp = df[mask_pkt_1 & mask_pkt_2 & mask_pkt_3 & mask_pkt_4].copy()
    
    # Get DISTINCT orders for PKT
    df_pkt_filtered = df_pkt_temp.drop_duplicates(subset=[df_pkt_temp.columns[4]], keep='first')  # ORKD column
    
    # Parse dates and quantities for PKT
    df_pkt_filtered['So_luong'] = pd.to_numeric(
        df_pkt_filtered.iloc[:, idx_so_luong].astype(str).str.replace(',', ''),
        errors='coerce'
    ).fillna(0).astype(int)
    
    df_pkt_filtered['TH_date'] = pd.to_datetime(
        df_pkt_filtered.iloc[:, idx_thoi_han],
        format='%d/%m/%Y',
        errors='coerce'
    )
    
    df_pkt_filtered['KH'] = df_pkt_filtered.iloc[:, idx_kh].astype(str).str.strip()
    
    # =====================================================================
    # STEP 3: Calculate ALL metrics with SUMIF logic
    # =====================================================================
    sx_threshold = today + timedelta(days=5)  # SX uses TODAY+5 (PREDICTED)
    pkt_threshold = today + timedelta(days=3)  # PKT uses TODAY+3 (PREDICTED)
    
    results = {}
    
    # --- SX AMJ Metrics (PREDICTED - for Section 3) ---
    # RRC Overdue
    sx_rrc_overdue_df = df_sx_filtered[
        (df_sx_filtered['KH'] == 'RRC') &
        df_sx_filtered['TH_date'].notna() &
        (df_sx_filtered['TH_date'].dt.date <= sx_threshold)
    ]
    results['sx_rrc_overdue'] = int(sx_rrc_overdue_df['So_luong'].sum())
    
    # RRC Due Soon
    sx_rrc_due_soon_df = df_sx_filtered[
        (df_sx_filtered['KH'] == 'RRC') &
        df_sx_filtered['TH_date'].notna() &
        (df_sx_filtered['TH_date'].dt.date > sx_threshold)
    ]
    results['sx_rrc_due_soon'] = int(sx_rrc_due_soon_df['So_luong'].sum())
    
    # External Overdue
    sx_ext_overdue_df = df_sx_filtered[
        (df_sx_filtered['KH'] != 'RRC') &
        df_sx_filtered['TH_date'].notna() &
        (df_sx_filtered['TH_date'].dt.date <= sx_threshold)
    ]
    results['sx_ext_overdue'] = int(sx_ext_overdue_df['So_luong'].sum())
    
    # External Due Soon
    sx_ext_due_soon_df = df_sx_filtered[
        (df_sx_filtered['KH'] != 'RRC') &
        df_sx_filtered['TH_date'].notna() &
        (df_sx_filtered['TH_date'].dt.date > sx_threshold)
    ]
    results['sx_ext_due_soon'] = int(sx_ext_due_soon_df['So_luong'].sum())
    
    # --- PKT AMJ Metrics (PREDICTED - for Section 3) ---
    # RRC Overdue
    pkt_rrc_overdue_df = df_pkt_filtered[
        (df_pkt_filtered['KH'] == 'RRC') &
        df_pkt_filtered['TH_date'].notna() &
        (df_pkt_filtered['TH_date'].dt.date <= pkt_threshold)
    ]
    results['pkt_rrc_overdue'] = int(pkt_rrc_overdue_df['So_luong'].sum())
    
    # RRC Due Soon
    pkt_rrc_due_soon_df = df_pkt_filtered[
        (df_pkt_filtered['KH'] == 'RRC') &
        df_pkt_filtered['TH_date'].notna() &
        (df_pkt_filtered['TH_date'].dt.date > pkt_threshold)
    ]
    results['pkt_rrc_due_soon'] = int(pkt_rrc_due_soon_df['So_luong'].sum())
    
    # External Overdue
    pkt_ext_overdue_df = df_pkt_filtered[
        (df_pkt_filtered['KH'] != 'RRC') &
        df_pkt_filtered['TH_date'].notna() &
        (df_pkt_filtered['TH_date'].dt.date <= pkt_threshold)
    ]
    results['pkt_ext_overdue'] = int(pkt_ext_overdue_df['So_luong'].sum())
    
    # External Due Soon
    pkt_ext_due_soon_df = df_pkt_filtered[
        (df_pkt_filtered['KH'] != 'RRC') &
        df_pkt_filtered['TH_date'].notna() &
        (df_pkt_filtered['TH_date'].dt.date > pkt_threshold)
    ]
    results['pkt_ext_due_soon'] = int(pkt_ext_due_soon_df['So_luong'].sum())
    
    # =====================================================================
    # STEP 4: Calculate ACTUAL overdue (for Section 4)
    # Using TODAY() only (no offset) - matches Excel SUMIF formulas
    # =====================================================================
    
    # --- SX AMJ ACTUAL Overdue (RRC only) ---
    # Excel: =SUMIF('Hàng quá hạn và tới hạn SX AMJ'!$H$7:$H$21;"<="&TODAY();'Hàng quá hạn và tới hạn SX AMJ'!$F$7:$F$21)
    sx_rrc_actual_overdue_df = df_sx_filtered[
        (df_sx_filtered['KH'] == 'RRC') &
        df_sx_filtered['TH_date'].notna() &
        (df_sx_filtered['TH_date'].dt.date <= today)  # TODAY, no offset!
    ]
    results['sx_rrc_actual_overdue'] = int(sx_rrc_actual_overdue_df['So_luong'].sum())
    
    # Calculate actual due soon = total - actual overdue
    rrc_total = results['sx_rrc_overdue'] + results['sx_rrc_due_soon']
    results['sx_rrc_actual_due_soon'] = rrc_total - results['sx_rrc_actual_overdue']
    
    # --- PKT AMJ ACTUAL Overdue (RRC only) ---
    # Excel: =SUMIF('Hàng quá hạn và tới hạn PKT AMJ'!$H$7:$H$1048576;"<="&TODAY();'Hàng quá hạn và tới hạn PKT AMJ'!$F$7:$F$1048576)
    pkt_rrc_actual_overdue_df = df_pkt_filtered[
        (df_pkt_filtered['KH'] == 'RRC') &
        df_pkt_filtered['TH_date'].notna() &
        (df_pkt_filtered['TH_date'].dt.date <= today)  # TODAY, no offset!
    ]
    results['pkt_rrc_actual_overdue'] = int(pkt_rrc_actual_overdue_df['So_luong'].sum())
    
    # Calculate actual due soon = total - actual overdue
    pkt_rrc_total = results['pkt_rrc_overdue'] + results['pkt_rrc_due_soon']
    results['pkt_rrc_actual_due_soon'] = pkt_rrc_total - results['pkt_rrc_actual_overdue']
    
    return results



if __name__ == "__main__":
    from khsx_sync_config import CONFIG
    
    print("="*70)
    print("OPTIMIZED ALL-IN-ONE OVERDUE/DUE SOON CALCULATOR")
    print("="*70)
    print()
    
    import time
    start_time = time.time()
    
    results = calculate_all_overdue_metrics(
        sheet_url=CONFIG['google_sheet_url'],
        credentials_file=CONFIG['google_credentials']
    )
    
    elapsed = time.time() - start_time
    
    print("="*70)
    print("RESULTS (calculated in one pass)")
    print("="*70)
    print()
    print("SX AMJ (Production):")
    print(f"  RRC Overdue:      {results['sx_rrc_overdue']:>6,}")
    print(f"  RRC Due Soon:     {results['sx_rrc_due_soon']:>6,}")
    print(f"  External Overdue: {results['sx_ext_overdue']:>6,}")
    print(f"  External Due Soon:{results['sx_ext_due_soon']:>6,}")
    print()
    print("PKT AMJ (Quality Control):")
    print(f"  RRC Overdue:      {results['pkt_rrc_overdue']:>6,}")
    print(f"  RRC Due Soon:     {results['pkt_rrc_due_soon']:>6,}")
    print(f"  External Overdue: {results['pkt_ext_overdue']:>6,}")
    print(f"  External Due Soon:{results['pkt_ext_due_soon']:>6,}")
    print()
    print("="*70)
    print("ACTUAL OVERDUE (for Section 4 - filtered by TODAY only)")
    print("="*70)
    print()
    print("SX AMJ (Production) - RRC only:")
    print(f"  RRC Actual Overdue:    {results['sx_rrc_actual_overdue']:>6,}")
    print(f"  RRC Actual Due Soon:   {results['sx_rrc_actual_due_soon']:>6,}")
    print(f"  Total RRC:             {results['sx_rrc_actual_overdue'] + results['sx_rrc_actual_due_soon']:>6,}")
    print()
    print("PKT AMJ (Quality Control) - RRC only:")
    print(f"  RRC Actual Overdue:    {results['pkt_rrc_actual_overdue']:>6,}")
    print(f"  RRC Actual Due Soon:   {results['pkt_rrc_actual_due_soon']:>6,}")
    print(f"  Total RRC:             {results['pkt_rrc_actual_overdue'] + results['pkt_rrc_actual_due_soon']:>6,}")
    print()
    print("="*70)
    print(f"[FAST] Total time: {elapsed:.2f} seconds")
    print("="*70)

