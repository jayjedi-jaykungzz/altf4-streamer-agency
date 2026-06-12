"""
WSGI entry point for production server (Render.com)
ใช้: waitress-serve wsgi:application

Auto-seeds database on first startup (idempotent).
"""
import os
import sys
import sqlite3

# เลือก DB path ตามสภาพแวดล้อม
if os.path.exists('/tmp'):
    os.environ['DATABASE_PATH'] = '/tmp/agency.db'
else:
    # Local dev (Windows) ใช้ app/agency.db
    os.environ['DATABASE_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'agency.db')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
APP_DIR = os.path.join(ROOT_DIR, 'app')
os.chdir(APP_DIR)

print(f'📁 Working dir: {os.getcwd()}')
print(f'📁 Database path: {os.environ.get("DATABASE_PATH")}')

# ===== AUTO-SEED =====
db_path = os.environ['DATABASE_PATH']
needs_seed = False

try:
    conn = sqlite3.connect(db_path)
    user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()[0]
    conn.close()
    if user_count > 0:
        print(f'✅ DB ready ({user_count} users)')
    else:
        print(f'DB exists but empty — seeding...')
        needs_seed = True
except sqlite3.OperationalError:
    print(f'🌱 No DB found — initializing + seeding...')
    needs_seed = True

if needs_seed:
    print('🌱 Seeding database...')
    from seed_for_prod import auto_seed
    auto_seed()
    print('✅ Seed done!')

# ===== Import Flask app =====
print('🔗 Importing Flask app...')
from app.main import app as application
print('🚀 Server ready!')