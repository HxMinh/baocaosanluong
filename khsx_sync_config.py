# -*- coding: utf-8 -*-
"""
Configuration for KHSX TONG Excel to Google Sheets Sync
"""

CONFIG = {
    # Excel file settings
    'excel_file_path': r'\\servert8\Kế hoạch\KẾ HOẠCH SẢN XUẤT\KHSX TONG.xlsx',
    'excel_password': '1985',
    
    # Google Sheets settings
    'google_credentials': 'api-agent-471608-912673253587.json',
    'google_sheet_url': 'https://docs.google.com/spreadsheets/d/1F2NzTR50kXzGx9Pc5KdBwwqnIRXGvViPv6mgw8YMNW0/edit',
    'target_sheet_name': 'KHSX_TONG',
    
    # Target sheets to sync (only these sheets will be read from Excel)
    'target_sheets': ['KHSX', 'KHSX NB', 'GCKT_GPKT', 'PHTCV', 'giao_kho_vp'],
    
    # Sync settings
    'sync_interval_seconds': 3600,  # 1 hour
    'debounce_seconds': 30,  # Wait 30s after last file change
    'log_file': 'khsx_sync.log',
    
    # Retry settings
    'max_retries': 3,
    'retry_delay_seconds': 5,
}
