# -*- coding: utf-8 -*-
"""
Upload KHSX TONG to Google Sheets with Progress Indicators
Handles locked files by copying to local temp first
"""

import os
import sys
import shutil
import time
from datetime import datetime
from khsx_sync_config import CONFIG
from khsx_excel_reader import read_excel_with_password
from khsx_sheets_updater import update_google_sheet

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def print_progress(message, prefix=">>>"):
    """Print progress message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {prefix} {message}")


def copy_file_with_progress(source, dest):
    """Copy file with progress indicator"""
    print_progress("Dang copy file tu network...", "[COPY]")
    print(f"  Nguon: {source}")
    print(f"  Dich: {dest}")
    
    start_time = time.time()
    
    try:
        # Copy file
        shutil.copy2(source, dest)
        
        elapsed = time.time() - start_time
        file_size = os.path.getsize(dest) / (1024 * 1024)  # MB
        
        print_progress(f"[OK] Copy hoan tat: {file_size:.1f}MB trong {elapsed:.1f}s", "[OK]")
        return True
        
    except Exception as e:
        print_progress(f"[ERROR] Loi copy file: {e}", "[ERROR]")
        return False


def main():
    """Main upload process with progress tracking"""
    
    print("=" * 70)
    print("UPLOAD KHSX TONG -> GOOGLE SHEETS")
    print("=" * 70)
    print()
    
    # Step 1: Copy file to local
    print_progress("BUOC 1: Copy file Excel ve local", "[STEP 1]")
    
    source_file = CONFIG['excel_file_path']
    temp_file = os.path.join(
        os.path.dirname(__file__),
        f"temp_KHSX_TONG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    
    if not copy_file_with_progress(source_file, temp_file):
        print()
        print("[ERROR] KHONG THE COPY FILE!")
        print()
        print("Nguyen nhan co the:")
        print("  - File dang duoc mo boi nguoi khac")
        print("  - Khong co quyen truy cap network drive")
        print("  - Duong dan khong ton tai")
        print()
        return False
    
    print()
    
    # Step 2: Read Excel
    print_progress("BUOC 2: Doc du lieu tu Excel", "[STEP 2]")
    print(f"  Doc cac sheet: {', '.join(CONFIG['target_sheets'])}")
    
    start_time = time.time()
    
    try:
        sheets_data = read_excel_with_password(
            temp_file,
            CONFIG['excel_password'],
            CONFIG['target_sheets']
        )
        
        elapsed = time.time() - start_time
        
        if not sheets_data:
            print_progress("[ERROR] Khong doc duoc du lieu tu Excel", "[ERROR]")
            return False
        
        # Print summary
        print_progress(f"[OK] Doc xong trong {elapsed:.1f}s", "[OK]")
        for sheet_name, df in sheets_data.items():
            print(f"    - {sheet_name}: {len(df)} dong x {len(df.columns)} cot")
        
    except Exception as e:
        print_progress(f"[ERROR] Loi doc Excel: {e}", "[ERROR]")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print_progress("[CLEANUP] Da xoa file tam", "[CLEANUP]")
    
    print()
    
    # Step 3: Upload to Google Sheets
    print_progress("BUOC 3: Upload len Google Sheets", "[STEP 3]")
    print(f"  URL: {CONFIG['google_sheet_url']}")
    
    start_time = time.time()
    
    try:
        success = update_google_sheet(
            CONFIG['google_sheet_url'],
            CONFIG['target_sheet_name'],
            sheets_data,
            CONFIG['google_credentials']
        )
        
        elapsed = time.time() - start_time
        
        if success:
            print()
            print("=" * 70)
            print_progress(f"[SUCCESS] UPLOAD THANH CONG! (Tong thoi gian: {elapsed:.1f}s)", "[SUCCESS]")
            print("=" * 70)
            print()
            print("[RESULT] Kiem tra ket qua tai:")
            print(f"   {CONFIG['google_sheet_url']}")
            print()
            print("Cac tab da duoc tao/cap nhat:")
            for sheet_name in sheets_data.keys():
                print(f"   [OK] KHSX_{sheet_name}")
            print()
            return True
        else:
            print_progress("[ERROR] Upload that bai", "[ERROR]")
            return False
            
    except Exception as e:
        print_progress(f"[ERROR] Loi upload: {e}", "[ERROR]")
        return False


if __name__ == "__main__":
    start_total = time.time()
    
    success = main()
    
    total_time = time.time() - start_total
    
    print("=" * 70)
    if success:
        print(f"[DONE] HOAN TAT! Tong thoi gian: {total_time:.1f}s ({total_time/60:.1f} phut)")
    else:
        print(f"[FAILED] THAT BAI sau {total_time:.1f}s")
    print("=" * 70)
