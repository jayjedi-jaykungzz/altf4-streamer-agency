"""
Seed 50 โปรเจคสมมติ + scopes + stat reports (เพิ่มจาก seed_demo 25 โปรเจค)

ใช้: cd app && python seed_more.py
"""
import os
import random
import datetime

from models import (
    init_db, get_db, get_db_path,
    create_project, create_stat_report,
    STREAMER_ROSTER
)

DB_PATH = get_db_path()
print(f'📁 Database: {DB_PATH}')

# Init DB (ถ้ายังไม่มี)
init_db()

conn = get_db()
existing = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()['c']
conn.close()
print(f'📊 Existing projects: {existing}')

# ===== ลูกค้าไทยใหม่ 50 ราย =====
NEW_CLIENTS = [
    # Food & Beverage (10)
    ('ไทยเบฟเวอเรจ', 'เปิดตัวเบียร์ช้าง EDGE'),
    ('เนสท์เล่ (ไทย)', 'แคมเปญนมตราหมี B-Active'),
    ('ยูนิลีเวอร์', 'รีวิวไอศกรีมวอลล์'),
    ('เป๊ปซี่ (ไทย)', 'เปิดตัวรสชาติใหม่ 7-Eleven'),
    ('MG (ไทย)', 'Test drive MG4 EV'),
    ('เซ็นทรัล ฟู้ด ฮอลล์', 'Taste of Thai campaign'),
    ('ซีพีเอฟ (CPF)', 'ไก่สดแช่แข็ง Easy Cook'),
    ('ทิปโก้', 'น้ำผลไม้ Cold Press'),
    ('อิชิตัน', 'ชาดำเย็น zero sugar'),
    ('โค้ก (ไทย)', 'แคมเปญ แบ่งปันความสุข'),

    # Fashion & Beauty (10)
    ('เซ็นทรัล เด็partment สโตร์', 'Mega Sale Mid-Year'),
    ('อิเกีย IKEA', 'IKEA After Dark'),
    ('ออฟฟิศเมท', 'Back to School campaign'),
    ('H&M Thailand', 'Spring collection 2026'),
    ('Zara Thailand', 'SS26 Launch'),
    ('บิวตี้บลอนเดอร์', 'ครีมบำรุงผิวหน้า'),
    ('ลอรีอัล (ไทย)', 'เมคอัพ Spring 2026'),
    ('แม็ค (MAC)', 'Valentine limited edition'),
    ('เคที่ เพอร์รี่', 'แคมเปญซัมเมอร์'),
    ('ซิสเล่ (Sisley)', 'Anti-aging skincare'),

    # Tech & Electronics (10)
    ('Xiaomi Thailand', 'Redmi Note 14 Pro launch'),
    ('OPPO Thailand', 'Reno13 Series'),
    ('Vivo Thailand', 'V40 Pro review'),
    ('realme Thailand', 'GT Neo 6 gaming phone'),
    ('Honor Thailand', 'Magic V3 folding phone'),
    ('JBL Thailand', 'Tune 770NC headphones'),
    ('Sony Thailand', 'WF-1000XM5 review'),
    ('Bose Thailand', 'QuietComfort Ultra'),
    ('Dell Thailand', 'XPS 13 Plus review'),
    ('HP Thailand', 'OMEN gaming laptop'),

    # Auto & Mobility (5)
    ('เมอร์เซเดส-เบนซ์ (ไทย)', 'EQE SUV test drive'),
    ('BMW Thailand', 'iX1 launch'),
    ('มาสด้า (ไทย)', 'CX-30 Carbon Edition'),
    ('นิสสัน (ไทย)', 'Kicks e-POWER review'),
    ('เอ็มจี (ไทย)', 'ZS EV+ family car'),

    # Lifestyle & Travel (10)
    ('Agoda (ไทย)', 'Summer travel deals'),
    ('Booking.com', 'EAS 2026 campaign'),
    ('Traveloka', 'Hotel mega sale'),
    ('AirAsia (ไทย)', 'Free seat campaign'),
    ('Nok Air', 'Midnight flash sale'),
    ('โรงแรมเซ็นทารา', 'Weekend getaway package'),
    ('แอนดาแมน ภูเก็ต', 'Beachfront villa review'),
    ('Centara Grand', 'Sunday brunch'),
    ('สยามพารากอน', 'Songkran festival 2026'),
    ('ไอคอนสยาม', 'Chao Phraya Art Festival'),

    # Banking & Finance (5)
    ('กสิกรไทย (KBANK)', 'K-Plus app update'),
    ('ไทยพาณิชย์ (SCB)', 'Make the Change campaign'),
    ('กรุงเทพ (BBL)', 'Bualuang mBanking'),
    ('ทรู มันนี่ (TrueMoney)', 'Pay it Easy'),
    ('ShopeePay', 'Mega Sale 6.6'),
]

print(f'➕ Adding {len(NEW_CLIENTS)} new projects...')

# ===== Scope types (ราคาต่อ scope) =====
SCOPE_DATA = {
    'Short VDO':     (10000, 25000),
    'Post Promote':  (5000,  15000),
    'Story':         (3000,  8000),
    'Podcast':       (35000, 80000),
    'Long VDO':      (50000, 150000),
    'อื่นๆ':         (10000, 50000),
    'Review':        (25000, 70000),
    'Livestream':    (15000, 60000),
    'Event Offline': (35000, 120000),
    'Reels':         (5000,  20000),
    'Vlog':          (25000, 60000),
    'TikTok':        (5000,  18000),
}

STATUS_DIST = ['completed'] * 50 + ['in_progress'] * 25 + ['pending'] * 20 + ['cancelled'] * 5

# Cost ratio (ต้นทุนต่อราคา)
def calc_cost(sale_price, scope_type):
    if scope_type in ('Long VDO', 'Podcast', 'Event Offline'):
        return int(sale_price * random.uniform(0.40, 0.55))
    return int(sale_price * random.uniform(0.25, 0.40))


streamers = STREAMER_ROSTER

# เริ่มสร้าง
created = 0
for client_name, topic in NEW_CLIENTS:
    # เลือก streamer 1-3 คน
    n_streamers = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
    project_streamers = random.sample(streamers, n_streamers)

    # เลือก scope 1-4
    n_scopes = random.choices([1, 2, 3, 4], weights=[20, 40, 30, 10])[0]
    project_scopes = random.sample(list(SCOPE_DATA.keys()), n_scopes)

    # คำนวณราคา
    total_sale = 0
    for scope in project_scopes:
        low, high = SCOPE_DATA[scope]
        total_sale += random.randint(low, high)

    agency_fee = random.choice([15, 20, 25, 30])
    project_name = f"{client_name} - {topic}"[:80]

    # วันที่
    days_ago = random.randint(1, 365)
    project_date = (datetime.datetime.now() - datetime.timedelta(days=days_ago)).strftime('%Y-%m-%d')

    # Status
    status = random.choice(STATUS_DIST)

    # สร้าง streamer_scopes (list of dict)
    streamer_scopes = []
    for sname in project_streamers:
        # แต่ละ streamer ทำทุก scope (แบ่งงาน)
        s_cost = 0
        s_scopes = []
        for scope in project_scopes:
            low, high = SCOPE_DATA[scope]
            price_per_unit = random.randint(low, high)
            count = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            s_scopes.append((scope, count, price_per_unit))
            s_cost += price_per_unit * count
        # ต้นทุนรวมของ streamer (จาก cost ratio)
        actual_cost = calc_cost(s_cost, project_scopes[0] if project_scopes else 'Short VDO')

        # ป้องกันชื่อผิด: ตรวจว่า sname อยู่ใน STREAMER_ROSTER
        if sname not in streamers:
            print(f'⚠️  Invalid streamer name: "{sname}" — using fallback')
            sname = random.choice(streamers)

        streamer_scopes.append({
            'name': sname,
            'cost': actual_cost,
            'scopes': s_scopes,
        })

    # สร้างโปรเจค
    project_id = create_project(
        name=project_name,
        client_name=client_name,
        agency_fee_percent=agency_fee,
        streamer_scopes=streamer_scopes,
        notes=topic,
    )

    # ตั้ง status + created_at
    if status != 'pending':
        conn = get_db()
        conn.execute(
            "UPDATE projects SET status = ?, created_at = ? WHERE id = ?",
            (status, project_date, project_id)
        )
        conn.commit()
        conn.close()

    # ===== เพิ่ม stat reports (ถ้า completed/in_progress) =====
    if status in ('completed', 'in_progress'):
        # ดึง project_streamers + scopes
        conn = get_db()
        ps_rows = conn.execute("""
            SELECT ps.id, ps.streamer_name, ps.cost,
                   sc.id AS scope_id, sc.scope_type, sc.scope_count
            FROM project_streamers ps
            LEFT JOIN project_streamer_scopes sc ON sc.project_streamer_id = ps.id
            WHERE ps.project_id = ?
        """, (project_id,)).fetchall()
        conn.close()

        # จัดกลุ่ม scope ตาม streamer
        from collections import defaultdict
        ps_scopes = defaultdict(list)
        for r in ps_rows:
            if r['scope_id']:
                ps_scopes[r['id']].append({
                    'scope_id': r['scope_id'],
                    'scope_type': r['scope_type'],
                    'scope_count': r['scope_count'],
                    'streamer_name': r['streamer_name'],
                })

        # สร้าง stat reports
        n_stats = random.randint(2, 5)
        for _ in range(n_stats):
            if not ps_scopes:
                break
            ps_id = random.choice(list(ps_scopes.keys()))
            scope_info = random.choice(ps_scopes[ps_id])
            scope_type = scope_info['scope_type']

            stat_date = (
                datetime.datetime.strptime(project_date, '%Y-%m-%d') +
                datetime.timedelta(days=random.randint(7, 60))
            ).strftime('%Y-%m-%d')

            # Views / engagement ตาม scope
            if 'Livestream' in scope_type:
                views = random.randint(5000, 50000)
            elif 'Long VDO' in scope_type:
                views = random.randint(20000, 500000)
            elif scope_type in ('Reels', 'Short VDO', 'TikTok'):
                views = random.randint(10000, 300000)
            else:
                views = random.randint(1000, 30000)

            likes = int(views * random.uniform(0.03, 0.15))
            shares = int(views * random.uniform(0.005, 0.02))
            comments = int(views * random.uniform(0.001, 0.03))
            engagement = (likes + shares + comments) / views * 100
            platform = random.choice(['YouTube', 'Facebook', 'Instagram', 'TikTok'])
            submitted_by = random.choice([1, 2, 3, 4])  # users

            try:
                create_stat_report(
                    project_id=project_id,
                    project_streamer_id=ps_id,
                    scope_id=scope_info['scope_id'],
                    platform=platform,
                    views=views,
                    likes=likes,
                    shares=shares,
                    comments=comments,
                    engagement=engagement,
                    extra_data=None,
                    submitted_by=submitted_by,
                )
            except Exception as e:
                print(f'  ⚠️ Stat report failed: {e}')

    created += 1
    if created % 10 == 0:
        print(f'  ✅ Created {created}/{len(NEW_CLIENTS)} projects...')

# สรุป
conn = get_db()
total_p = conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()['c']
total_s = conn.execute("SELECT COUNT(*) AS c FROM stat_reports").fetchone()['c']
conn.close()

print(f'\n🎉 Done! Created {created} new projects')
print(f'   Total projects: {total_p}')
print(f'   Total stat reports: {total_s}')
