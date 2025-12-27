# -*- coding: utf-8 -*-
"""
Google Sheets Updater Module - Upload data to Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import Dict, Optional
import time


def authenticate_google_sheets(credentials_file: str):
    """Authenticate with Google Sheets API"""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return gspread.authorize(creds)


def update_google_sheet(
    sheet_url: str,
    sheet_name: str,
    data_dict: Dict[str, pd.DataFrame],
    credentials_file: str,
    max_retries: int = 3
) -> bool:
    """
    Update Google Sheet with data from Excel
    
    Args:
        sheet_url: Google Sheets URL
        sheet_name: Target sheet name (will be created if doesn't exist)
        data_dict: Dictionary of {sheet_name: DataFrame}
        credentials_file: Path to Google credentials
        max_retries: Maximum retry attempts
        
    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # Authenticate
            client = authenticate_google_sheets(credentials_file)
            spreadsheet = client.open_by_url(sheet_url)
            
            # For each Excel sheet, create/update a tab in Google Sheets
            for excel_sheet_name, df in data_dict.items():
                # Create sheet name (prefix with KHSX_)
                target_name = f"KHSX_{excel_sheet_name}"[:100]  # Google Sheets limit
                
                # Try to get existing sheet or create new one
                try:
                    worksheet = spreadsheet.worksheet(target_name)
                    print(f"  Updating existing sheet: {target_name}")
                except gspread.exceptions.WorksheetNotFound:
                    worksheet = spreadsheet.add_worksheet(
                        title=target_name,
                        rows=len(df) + 100,
                        cols=len(df.columns) + 10
                    )
                    print(f"  Created new sheet: {target_name}")
                
                # Clear existing data
                worksheet.clear()
                
                # Prepare data (header + rows)
                data_to_upload = [df.columns.tolist()] + df.fillna('').values.tolist()
                
                # Upload in batches to avoid quota issues
                batch_size = 1000
                for i in range(0, len(data_to_upload), batch_size):
                    batch = data_to_upload[i:i+batch_size]
                    start_row = i + 1
                    
                    # Update batch
                    worksheet.update(
                        f'A{start_row}',
                        batch,
                        value_input_option='RAW'
                    )
                    
                    print(f"    Uploaded rows {start_row} to {start_row + len(batch) - 1}")
                    
                    # Small delay to avoid quota
                    if i + batch_size < len(data_to_upload):
                        time.sleep(0.5)
            
            print(f"[OK] Successfully synced {len(data_dict)} sheets to Google Sheets")
            return True
            
        except Exception as e:
            print(f"[WARNING] Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))  # Exponential backoff
            else:
                print(f"[ERROR] Failed to update Google Sheets after {max_retries} attempts")
                return False
    
    return False


if __name__ == "__main__":
    # Test
    from khsx_sync_config import CONFIG
    from khsx_excel_reader import read_excel_with_password
    
    print("Testing Google Sheets updater...")
    
    # Read Excel
    sheets = read_excel_with_password(
        CONFIG['excel_file_path'],
        CONFIG['excel_password'],
        CONFIG['target_sheets']
    )
    
    if sheets:
        # Upload to Google Sheets
        success = update_google_sheet(
            CONFIG['google_sheet_url'],
            CONFIG['target_sheet_name'],
            sheets,
            CONFIG['google_credentials']
        )
        
        if success:
            print("\n[OK] Test successful!")
        else:
            print("\n[ERROR] Test failed!")
    else:
        print("\n[ERROR] Could not read Excel file")
