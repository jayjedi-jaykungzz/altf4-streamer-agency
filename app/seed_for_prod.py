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

    # เช็คว่า DB มี tables แล้วหรือยัง
    needs_init = False
    needs_basic_seed = False  # users + 25 projects
    needs_more_seed = False   # +50 projects

    try:
        conn = sqlite3.connect(db_path)
        # เช็ค tables
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]

        if 'users' not in table_names:
            needs_init = True
            needs_basic_seed = True
            needs_more_seed = True
        else:
            user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()[0]
            project_count = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()[0]
            print(f'   users: {user_count}, projects: {project_count}')

            if user_count == 0:
                needs_basic_seed = True
            if project_count < 75:  # 25 จาก seed_demo + 50 จาก seed_more
                needs_more_seed = True

        conn.close()
    except sqlite3.OperationalError:
        needs_init = True
        needs_basic_seed = True
        needs_more_seed = True

    if not needs_init and not needs_basic_seed and not needs_more_seed:
        print('✅ DB fully seeded — skip')
        return

    if needs_init:
        print('🌱 Initializing tables...')
        init_db()

    if needs_basic_seed:
        print('🌱 Seeding basic data (25 projects + 4 users)...')
        import seed_demo

    if needs_more_seed:
        print('🌱 Seeding extra 50 realistic projects + stats...')
        try:
            import seed_more
        except Exception as e:
            print(f'⚠️ seed_more error: {e}')
            import traceback
            traceback.print_exc()

    conn = sqlite3.connect(db_path)
    user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()[0]
    project_count = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()[0]
    stat_count = conn.execute("SELECT COUNT(*) AS c FROM stat_reports").fetchone()[0]
    conn.close()
    print(f'✅ Seed complete! {user_count} users, {project_count} projects, {stat_count} stat reports')


if __name__ == '__main__':
    auto_seed()