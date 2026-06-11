"""
WSGI entry point for production server (Render.com)
ใช้: waitress-serve wsgi:application

Auto-seeds database on first startup (idempotent).
"""
import os
import sys

# บังคับ DATABASE_PATH ก่อน import models
os.environ.setdefault('DATABASE_PATH', '/tmp/agency.db')

# เพิ่ม ROOT (ที่มี app/ folder) เข้า Python path — เพื่อให้ import app.main ได้
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# เปลี่ยน working directory เป็น app folder
APP_DIR = os.path.join(ROOT_DIR, 'app')
os.chdir(APP_DIR)

print(f'📁 Working dir: {os.getcwd()}')
print(f'📁 Database path: {os.environ.get("DATABASE_PATH")}')

# Auto-seed on first startup
try:
    from seed_for_prod import auto_seed
    auto_seed()
except Exception as e:
    print(f'⚠️  Seed error: {e}', file=sys.stderr)
    import traceback
    traceback.print_exc()

# Import Flask app ผ่าน app.main package — work กับ relative import
from app.main import app as application

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Starting waitress on port {port}')
    serve(application, host='0.0.0.0', port=port)
