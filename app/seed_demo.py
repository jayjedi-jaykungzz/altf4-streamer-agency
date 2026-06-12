"""
Seed 25 โปรเจคสมมติ + scopes + stat reports
"""
import os
import sqlite3
import random
import datetime

# Relative imports (จะรันจาก app/ folder)
from models import init_db, get_db, SCOPE_TYPES, get_db_path

DB_PATH = get_db_path()

# เช็คว่ามี projects อยู่แล้วหรือไม่ (idempotent)
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    existing_p = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()[0]
    conn.close()
    if existing_p > 0:
        print(f'⏭️  DB already has {existing_p} projects — skip seed_demo (use seed_more.py to add more)')
        import sys
        sys.exit(0)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f'🗑️  Old DB removed: {DB_PATH}')

init_db()
print(f'✅ DB initialized: {DB_PATH}')

CLIENTS = [
    ('Nike Thailand', 'Endorsment คอลเลคชั่นใหม่'),
    ('L\'Oreal Paris', 'รีวิวครีมกันแดด UV Defender'),
    ('Coca-Cola', 'Live streaming เปิดตัวรสชาติใหม่'),
    ('Shopee Thailand', 'Mega sale campaign 6.6'),
    ('Lazada Thailand', 'Brand day ส่งเสริมการขาย'),
    ('Samsung Thailand', 'Unpacked Galaxy S25'),
    ('Apple (iStudio)', 'รีวิว iPhone 16 Pro'),
    ('Adidas Thailand', 'แคมเปญ Ultraboost 2026'),
    ('Uniqlo Thailand', 'Spring collection launch'),
    ('KFC Thailand', 'Combo deal campaign'),
    ('McDonald\'s', 'Spicy menu promotion'),
    ('Central World', 'Mid-year sale'),
    ('True Corp', '5G package promotion'),
    ('AIS', 'Roaming package campaign'),
    ('Toyota Thailand', 'Yaris Ativ launch'),
    ('Honda Thailand', 'City Hatchback review'),
    ('Grab Thailand', 'Driver recruitment'),
    ('Foodpanda', 'Free delivery campaign'),
    ('Lazada Live', 'Midnight sale streaming'),
    ('Bangkok Airways', 'Domestic route promotion'),
    ('Klook Thailand', 'Travel deals campaign'),
    ('Watsons Thailand', 'Beauty festival'),
    ('Mistine', 'Sun protection campaign'),
    ('Cute Press', 'New makeup line launch'),
    ('Sunsu', 'Skincare product launch'),
]

STREAMERS = [
    'เจ้าซิม', 'Aiirki Ch', 'Dango Meaw', 'iSong', 'Jorjoy', 'Junqko',
    'Jz Oracle', 'Kael Pk', 'Mobydick', 'MrCast', 'Shipdont',
    'ท็อฟฟี่เป็นตุ๊ดซ่อมคอม', 'LaewTaeTon', 'RizingFaze', 'Zickarr',
    'FZK Frozenkiss', 'Naklas', 'xLapisLazulix', 'Iammaii', '4em Channel',
    'Dianoon', 'มินตันดิ๊งด่อง', 'PoP Chanal', 'AdK ก้องไก่กุ้กๆ',
    'AdAofTV', 'Total / month', 'มีอาร์', 'Plathong Ch', 'HookHuukGaming',
    'TrinityBigMaster', 'Zatoshi', 'TangTangCH', 'DaddyKim', 'Zealotsx',
    'Sunwaltz', 'Azzing', 'JasperZ', 'Zera', 'Inorin', 'MeMarkz',
    'Jamesmer Studio', 'Ohbigz', 'Khunmayo', 'TanX', 'Ezqelusia',
    'Deerlong', 'Nhooimaim', 'Nuuly', 'Rocklee', 'HybridX', 'Jayop',
    'oPuto', 'OuixZ', 'Apologize CH', 'FATLIPZ', 'TAKO CHAN',
    'Porwor CH', 'Vcartz',
]

PLATFORMS = ['TikTok', 'Facebook', 'Instagram', 'YouTube', 'Twitch']
STATUSES = ['pending', 'in_progress', 'completed', 'cancelled', 'completed', 'completed', 'in_progress']


def make_scopes():
    """สุ่ม scopes ให้ streamer แต่ละคน"""
    n_scopes = random.randint(2, 4)
    available = SCOPE_TYPES.copy()
    selected = random.sample(available, min(n_scopes, len(available)))
    return [(s, random.randint(1, 4)) for s in selected]


def seed():
    conn = get_db()
    c = conn.cursor()
    project_ids = []
    for i, (client, name) in enumerate(CLIENTS, 1):
        agency_fee = random.choice([25, 30, 30, 35, 35, 40])
        status = STATUSES[i % len(STATUSES)]
        days_ago = random.randint(0, 60)
        hours_ago = random.randint(0, 23)
        date = datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=hours_ago)

        c.execute('''INSERT INTO projects
                     (name, client_name, agency_fee_percent, status, notes, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (name, client, agency_fee, status, f'แคมเปญ {name} สำหรับ {client}', date.isoformat(sep=' ')))
        pid = c.lastrowid
        project_ids.append(pid)

        n_streamers = random.randint(1, 4)
        selected_streamers = random.sample(STREAMERS, n_streamers)
        for sname in selected_streamers:
            cost = random.randint(5000, 20000)
            c.execute('''INSERT INTO project_streamers
                         (project_id, streamer_name, cost) VALUES (?, ?, ?)''',
                      (pid, sname, cost))
            ps_id = c.lastrowid
            # เพิ่ม scopes (พร้อม cost_per_unit แยกตามประเภท)
            scope_costs = {
                'Livestream': random.randint(2000, 6000),
                'Short VDO': random.randint(1500, 4000),
                'Long VDO': random.randint(5000, 15000),
                'Post Promote': random.randint(1000, 3000),
                'Event Offline': random.randint(8000, 30000),
                'Reels': random.randint(1500, 4500),
                'Story': random.randint(500, 2000),
                'Podcast': random.randint(3000, 8000),
                'Review': random.randint(2500, 7000),
                'Unboxing': random.randint(2000, 6000),
                'อื่นๆ': random.randint(1000, 5000),
            }
            for scope_type, scope_count in make_scopes():
                cpu = scope_costs.get(scope_type, 2000)
                c.execute('''INSERT INTO project_streamer_scopes
                             (project_streamer_id, scope_type, scope_count, cost_per_unit, notes)
                             VALUES (?, ?, ?, ?, ?)''',
                          (ps_id, scope_type, scope_count, cpu, ''))

        # stat reports สำหรับ completed/in_progress
        if status in ('pending', 'cancelled'):
            continue
        ps_rows = c.execute('SELECT id FROM project_streamers WHERE project_id = ?', (pid,)).fetchall()
        scope_rows = c.execute('''SELECT ps.id AS ps_id, sc.id AS scope_id, sc.scope_type
                                   FROM project_streamers ps
                                   JOIN project_streamer_scopes sc ON ps.id = sc.project_streamer_id
                                   WHERE ps.project_id = ?''', (pid,)).fetchall()
        n_reports = random.randint(2, 4) if status == 'in_progress' else random.randint(3, 6)
        for _ in range(n_reports):
            ps_id = random.choice(ps_rows)[0]
            matching_scopes = [s for s in scope_rows if s[0] == ps_id]
            if matching_scopes:
                chosen = random.choice(matching_scopes)
                scope_id, scope_type = chosen[0], chosen[1]
            else:
                scope_id, scope_type = None, None
            platform = random.choice(PLATFORMS)
            views = random.randint(10000, 500000)
            likes = int(views * random.uniform(0.02, 0.12))
            shares = int(views * random.uniform(0.001, 0.01))
            comments = int(views * random.uniform(0.002, 0.02))
            engagement = random.uniform(3.0, 12.0)
            c.execute('''INSERT INTO stat_reports
                         (project_id, project_streamer_id, scope_id, platform, views, likes, shares, comments, engagement, extra_data, submitted_by)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (pid, ps_id, scope_id, platform, views, likes, shares, comments, engagement,
                       f'https://{platform.lower()}.com/post/{random.randint(100000,999999)}',
                       random.choice([3, 4])))
        print(f'  ✅ #{pid} {client} | {name} | {n_streamers} streamers | status={status} | {n_reports if status not in ("pending", "cancelled") else 0} stats')

    conn.commit()

    print()
    print('📊 Final count:')
    print(f'  Projects: {c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]}')
    print(f'  Project-streamers: {c.execute("SELECT COUNT(*) FROM project_streamers").fetchone()[0]}')
    print(f'  Scopes: {c.execute("SELECT COUNT(*) FROM project_streamer_scopes").fetchone()[0]}')
    print(f'  Stat reports: {c.execute("SELECT COUNT(*) FROM stat_reports").fetchone()[0]}')
    print()
    print('📈 Status distribution:')
    for r in c.execute('SELECT status, COUNT(*) FROM projects GROUP BY status').fetchall():
        print(f'  {r[0]}: {r[1]}')
    print()
    print('📋 Scope types:')
    for r in c.execute('SELECT scope_type, COUNT(*) FROM project_streamer_scopes GROUP BY scope_type ORDER BY 2 DESC').fetchall():
        print(f'  {r[0]}: {r[1]}')
    conn.close()


if __name__ == '__main__':
    print('🌱 Seeding 25 projects with scopes...')
    seed()
