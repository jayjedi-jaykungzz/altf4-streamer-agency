"""
Seed database for production (idempotent — safe to run many times)
ใช้: wsgi.py เรียกจาก startup
"""
import os
import sys
import sqlite3


def auto_seed():
    """Seed DB ถ้ายังว่าง (idempotent)"""
    from models import init_db, get_db, get_db_path

    db_path = get_db_path()
    print(f'🔍 Checking DB at: {db_path}')
    print(f'   exists: {os.path.exists(db_path)}')

    try:
        conn = sqlite3.connect(db_path)
        user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()[0]
        conn.close()
        if user_count > 0:
            print(f'✅ DB already seeded ({user_count} users) — skip')
            return
    except sqlite3.OperationalError:
        print(f'🌱 No DB found — initializing...')

    print('🌱 Seeding database...')
    init_db()
    # Import seed_demo เพื่อ seed ข้อมูล
    import seed_demo

    conn = sqlite3.connect(db_path)
    user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()[0]
    project_count = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()[0]
    conn.close()
    print(f'✅ Seed complete! {user_count} users, {project_count} projects')


if __name__ == '__main__':
    auto_seed()