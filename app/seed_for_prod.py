"""
Seed database for production (idempotent — safe to run multiple times)

ใช้ตอน Render deploy ครั้งแรก: รัน auto ผ่าน wsgi.py
"""
import os
import sys
import sqlite3
import random
import datetime

DB_PATH = os.environ.get('DATABASE_PATH', '/tmp/agency.db')


def auto_seed():
    """ตรวจและ seed ถ้ายังว่าง (idempotent)"""
    print(f'🔍 Checking DB at: {DB_PATH}')
    print(f'   exists: {os.path.exists(DB_PATH)}')

    # สร้าง DB + tables ผ่าน init_db ของ models
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from models import init_db, get_db
    init_db()

    conn = get_db()
    user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()['c']
    project_count = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()['c']
    conn.close()

    print(f'   users: {user_count}, projects: {project_count}')

    if user_count > 0:
        print('✅ DB already seeded — skip')
        return

    print('🌱 First run — seeding database (this takes ~10 seconds)...')
    _do_seed()

    # Verify
    conn = get_db()
    final_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()['c']
    final_projects = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()['c']
    conn.close()
    print(f'✅ Seed complete! {final_users} users, {final_projects} projects')


def _do_seed():
    """Seed users + projects"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import seed_demo
    # seed_demo.py จะ:
    # 1. ลบ DB เก่า (ถ้ามี)
    # 2. init_db() ใหม่
    # 3. seed users + projects + scopes + stats


if __name__ == '__main__':
    auto_seed()
