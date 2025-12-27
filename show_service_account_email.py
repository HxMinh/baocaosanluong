# -*- coding: utf-8 -*-
"""
Script to display service account email for Google Sheets sharing
"""

import json

# Read credentials file
with open('api-agent-471608-912673253587.json', 'r', encoding='utf-8') as f:
    creds = json.load(f)

print("=" * 70)
print("SERVICE ACCOUNT EMAIL")
print("=" * 70)
print()
print(creds['client_email'])
print()
print("=" * 70)
print("HƯỚNG DẪN:")
print("1. Copy email ở trên")
print("2. Mở Google Sheet:")
print("   https://docs.google.com/spreadsheets/d/1F2NzTR50kXzGx9Pc5KdBwwqnIRXGvViPv6mgw8YMNW0/edit")
print("3. Click nút 'Share' (Chia sẻ)")
print("4. Paste email vào và chọn quyền 'Editor'")
print("5. Bỏ tick 'Notify people'")
print("6. Click 'Share'")
print("=" * 70)
