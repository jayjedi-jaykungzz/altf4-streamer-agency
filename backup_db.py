#!/usr/bin/env python
"""Auto backup ALTF4 database.
วิธีใช้: python backup_db.py
เก็บ backup ล่าสุด 7 วัน ลบอันเก่าอัตโนมัติ
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = ROOT / 'app' / 'agency.db'
BACKUP_DIR = ROOT / 'app' / 'backups'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = BACKUP_DIR / f'agency_{timestamp}.db'

# ใช้ SQLite backup API (ปลอดภัยแม้ขณะเซิร์ฟรัน)
src = sqlite3.connect(str(DB_PATH))
dst = sqlite3.connect(str(backup_path))
src.backup(dst)
dst.close()
src.close()

size_kb = backup_path.stat().st_size / 1024
print(f'✅ Backup saved: {backup_path.name} ({size_kb:.1f} KB)')

# ลบ backup เก่าเกิน 7 วัน
import time
now = time.time()
for f in BACKUP_DIR.glob('agency_*.db'):
    if (now - f.stat().st_mtime) > 7 * 86400:  # 7 days
        f.unlink()
        print(f'🗑️  Removed old backup: {f.name}')
