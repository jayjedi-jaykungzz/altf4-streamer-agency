"""
Seed database for production (idempotent — safe to run multiple times)

ใช้ 2 วิธี:
1. Auto: import ใน wsgi.py → auto_seed() จะรันตอน start
2. Manual: cd app && python seed_for_prod.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models import init_db, get_db


def auto_seed():
    """ตรวจและ seed ถ้ายังว่าง (เรียกจาก wsgi.py)"""
    init_db()
    conn = get_db()
    user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()['c']
    project_count = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()['c']
    conn.close()

    if user_count > 0:
        print(f'✅ DB ready ({user_count} users, {project_count} projects)')
        return

    print('🌱 First run — seeding database...')
    _do_seed()


def _do_seed():
    """Seed จริงๆ — เรียก seed_demo.py logic"""
    # Patch seed_demo: อย่าลบ DB (มันเช็คอยู่แล้ว แต่ idempotent คือ seed ใหม่ได้)
    import seed_demo


if __name__ == '__main__':
    init_db()
    conn = get_db()
    user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()['c']
    conn.close()

    if user_count > 0:
        print(f'⏭️  DB already has {user_count} users — skip')
    else:
        print('🌱 Seeding database...')
        _do_seed()
        print('✅ Done!')
        print('   Login: admin1 / admin123  (or admin2)')
        print('   Login: staff1 / staff123  (or staff2)')
