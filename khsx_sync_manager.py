# -*- coding: utf-8 -*-
"""
KHSX TONG Sync Manager - Main orchestrator for Excel to Google Sheets sync
Combines file watcher + hourly fallback
"""

import time
import logging
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

from khsx_sync_config import CONFIG
from khsx_excel_reader import read_excel_with_password
from khsx_sheets_updater import update_google_sheet


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['log_file'], encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ExcelFileHandler(FileSystemEventHandler):
    """Handle file system events for Excel file"""
    
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        self.last_modified = None
        self.debounce_timer = None
    
    def on_modified(self, event):
        """Called when file is modified"""
        if event.is_directory:
            return
        
        # Check if it's our target file
        if event.src_path.endswith('KHSX TONG.xlsx'):
            logger.info(f"[FILE] File modified: {event.src_path}")
            
            # Cancel previous timer
            if self.debounce_timer:
                self.debounce_timer.cancel()
            
            # Start new debounce timer
            self.debounce_timer = threading.Timer(
                CONFIG['debounce_seconds'],
                self.sync_manager.sync_now
            )
            self.debounce_timer.start()
            logger.info(f"[TIMER] Debounce timer started ({CONFIG['debounce_seconds']}s)")


class SyncManager:
    """Main sync manager - orchestrates file watcher + hourly fallback"""
    
    def __init__(self):
        self.last_sync_time = None
        self.observer = None
        self.running = False
        self.sync_lock = threading.Lock()
    
    def sync_now(self):
        """Perform sync operation"""
        with self.sync_lock:
            try:
                logger.info("="*80)
                logger.info("[SYNC] Starting sync...")
                
                # Read Excel
                logger.info(f"[EXCEL] Reading Excel file: {CONFIG['excel_file_path']}")
                logger.info(f"[SHEETS] Target sheets: {CONFIG['target_sheets']}")
                sheets = read_excel_with_password(
                    CONFIG['excel_file_path'],
                    CONFIG['excel_password'],
                    CONFIG['target_sheets']
                )
                
                if not sheets:
                    logger.error("[ERROR] Failed to read Excel file")
                    return False
                
                logger.info(f"[OK] Read {len(sheets)} sheets from Excel")
                
                # Upload to Google Sheets
                logger.info(f"[UPLOAD] Uploading to Google Sheets...")
                success = update_google_sheet(
                    CONFIG['google_sheet_url'],
                    CONFIG['target_sheet_name'],
                    sheets,
                    CONFIG['google_credentials'],
                    CONFIG['max_retries']
                )
                
                if success:
                    self.last_sync_time = datetime.now()
                    logger.info(f"[OK] Sync completed successfully at {self.last_sync_time.strftime('%H:%M:%S')}")
                    logger.info("="*80)
                    return True
                else:
                    logger.error("[ERROR] Sync failed")
                    logger.info("="*80)
                    return False
                    
            except Exception as e:
                logger.error(f"[ERROR] Sync error: {e}")
                logger.info("="*80)
                return False
    
    def check_hourly_sync(self):
        """Check if hourly sync is needed"""
        if self.last_sync_time is None:
            return True
        
        time_since_last_sync = datetime.now() - self.last_sync_time
        return time_since_last_sync.total_seconds() >= CONFIG['sync_interval_seconds']
    
    def start(self):
        """Start the sync manager"""
        self.running = True
        logger.info("="*80)
        logger.info("[START] KHSX TONG Sync Manager Started")
        logger.info("="*80)
        logger.info(f"[EXCEL] Excel file: {CONFIG['excel_file_path']}")
        logger.info(f"[GSHEET] Google Sheet: {CONFIG['google_sheet_url']}")
        logger.info(f"[TIMER] Sync interval: {CONFIG['sync_interval_seconds']}s ({CONFIG['sync_interval_seconds']//3600}h)")
        logger.info(f"[TIMER] Debounce: {CONFIG['debounce_seconds']}s")
        logger.info("="*80)
        
        # Initial sync
        logger.info("[SYNC] Performing initial sync...")
        self.sync_now()
        
        # Setup file watcher
        import os
        watch_dir = os.path.dirname(CONFIG['excel_file_path'])
        
        event_handler = ExcelFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, watch_dir, recursive=False)
        self.observer.start()
        
        logger.info(f"[WATCH] File watcher started on: {watch_dir}")
        logger.info("="*80)
        
        try:
            while self.running:
                # Check if hourly sync is needed
                if self.check_hourly_sync():
                    logger.info("[TIMER] Hourly sync triggered")
                    self.sync_now()
                
                # Sleep for a bit
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("\n[STOP] Received stop signal")
            self.stop()
    
    def stop(self):
        """Stop the sync manager"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logger.info("[STOP] Sync manager stopped")


if __name__ == "__main__":
    manager = SyncManager()
    manager.start()
