"""
Database models สำหรับ Streamer Agency
- users: admin + staff (ไม่มี streamer login แล้ว)
- projects: งาน 1 งาน
- project_streamers: many-to-many (cost แยก)
- stat_reports: รายงานผลงาน (กรอกโดย staff/admin)
"""
import sqlite3
import os
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'agency.db'))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===== Streamer roster (ไม่ใช่ user — แค่รายชื่อในโปรเจ็ค) =====
STREAMER_ROSTER = [
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


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users — มีแค่ admin/staff
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
            display_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Projects
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            client_name TEXT NOT NULL,
            agency_fee_percent REAL NOT NULL DEFAULT 30,
            sale_price_override REAL,
            status TEXT NOT NULL DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # project_streamers (many-to-many + cost แยก)
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_streamers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            streamer_name TEXT NOT NULL,
            cost REAL NOT NULL DEFAULT 0,
            UNIQUE(project_id, streamer_name),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    ''')

    # project_streamer_scopes — 1 streamer มีหลาย scope
    # เช่น เจ้าซิม: livestream x3, short vdo x2, long vdo x1 (แต่ละ scope มี cost แยก)
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_streamer_scopes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_streamer_id INTEGER NOT NULL,
            scope_type TEXT NOT NULL,
            scope_count INTEGER NOT NULL DEFAULT 1,
            cost_per_unit REAL NOT NULL DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (project_streamer_id) REFERENCES project_streamers(id) ON DELETE CASCADE
        )
    ''')

    # stat_reports — เพิ่ม scope_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS stat_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            project_streamer_id INTEGER NOT NULL,
            scope_id INTEGER,
            platform TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            engagement REAL DEFAULT 0,
            extra_data TEXT,
            submitted_by INTEGER NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (project_streamer_id) REFERENCES project_streamers(id) ON DELETE CASCADE,
            FOREIGN KEY (scope_id) REFERENCES project_streamer_scopes(id) ON DELETE SET NULL,
            FOREIGN KEY (submitted_by) REFERENCES users(id)
        )
    ''')

    # Seed default users
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        for u in [
            ('admin1', 'admin123', 'admin', 'Admin #1'),
            ('admin2', 'admin123', 'admin', 'Admin #2'),
            ('staff1', 'staff123', 'staff', 'Staff #1'),
            ('staff2', 'staff123', 'staff', 'Staff #2'),
        ]:
            c.execute(
                "INSERT INTO users (username, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
                (u[0], generate_password_hash(u[1]), u[2], u[3])
            )

    conn.commit()
    conn.close()


# ===== User helpers =====
def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def get_user_by_username(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user


def verify_user(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None


def list_staff():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users WHERE role = 'staff' ORDER BY display_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== Streamer roster (ไม่ใช่ user) =====
def add_streamer_to_roster(name):
    """เพิ่มสตรีมเมอร์ใหม่เข้า roster (ถ้ายังไม่มี)"""
    name = name.strip()
    if not name:
        return False
    if name in STREAMER_ROSTER:
        return True
    STREAMER_ROSTER.append(name)
    return True


# ===== Projects =====
def list_projects(sort_by='date_desc', status_filter=None, group_by_status=False):
    """
    sort_by: date_desc / date_asc / name_asc / name_desc
    status_filter: pending/in_progress/completed/cancelled/None
    group_by_status: ถ้า True จะคืน dict grouped by status
    """
    order_clauses = {
        'date_desc': 'p.created_at DESC',
        'date_asc': 'p.created_at ASC',
        'name_asc': 'p.name COLLATE NOCASE ASC',
        'name_desc': 'p.name COLLATE NOCASE DESC',
        'client_asc': 'p.client_name COLLATE NOCASE ASC',
    }
    order = order_clauses.get(sort_by, 'p.created_at DESC')

    base_query = f'''
        SELECT p.*,
               (SELECT GROUP_CONCAT(ps.streamer_name, ', ')
                FROM project_streamers ps
                WHERE ps.project_id = p.id) AS streamer_names,
               (SELECT COUNT(*) FROM project_streamers WHERE project_id = p.id) AS streamer_count,
               (SELECT COALESCE(SUM(cost), 0) FROM project_streamers WHERE project_id = p.id) AS total_cost
        FROM projects p
    '''

    params = []
    where = ''
    if status_filter:
        where = 'WHERE p.status = ?'
        params.append(status_filter)

    conn = get_db()
    if group_by_status:
        # คืน dict grouped by status (เรียงตาม sort_by ภายใน group)
        rows = conn.execute(f'{base_query} {where} ORDER BY {order}', params).fetchall()
        projects = [dict(r) for r in rows]
        grouped = {'pending': [], 'in_progress': [], 'completed': [], 'cancelled': []}
        for p in projects:
            grouped.setdefault(p['status'], []).append(p)
        # ลบ group ว่าง
        grouped = {k: v for k, v in grouped.items() if v}
        conn.close()
        return grouped
    else:
        rows = conn.execute(f'{base_query} {where} ORDER BY {order}', params).fetchall()
        conn.close()
        return [dict(r) for r in rows]


# ===== Scope of Work =====
SCOPE_TYPES = [
    'Livestream',
    'Short VDO',
    'Long VDO',
    'Post Promote',
    'Event Offline',
    'Reels',
    'Story',
    'Podcast',
    'Review',
    'Unboxing',
    'อื่นๆ',
]

# ===== Project Status =====
# code (DB) → label (UI)  เก็บ code เดิม เพื่อ backward compatible
STATUS_LABELS = {
    'pending': 'เสนอราคา',
    'in_progress': 'ดำเนินงาน',
    'completed': 'เสร็จสิ้น',
    'cancelled': 'ยกเลิก',
}
STATUS_CODES = list(STATUS_LABELS.keys())


def get_scope_types():
    return SCOPE_TYPES


def create_project(name, client_name, agency_fee_percent, streamer_scopes, notes=''):
    """
    streamer_scopes: list of dicts:
        {
            'name': 'เจ้าซิม',
            'cost': 10000,  # ต้นทุนรวม (optional, ถ้าไม่ใส่จะคำนวนจาก scope)
            'scopes': [('Livestream', 3, 3000), ('Short VDO', 2, 2000), ...]
                      # (scope_type, count, cost_per_unit)
        }
    """
    agency_fee_percent = float(agency_fee_percent)
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        INSERT INTO projects (name, client_name, agency_fee_percent, sale_price_override, notes)
        VALUES (?, ?, ?, NULL, ?)
    ''', (name, client_name, agency_fee_percent, notes))
    project_id = c.lastrowid

    for s in streamer_scopes:
        sname = s['name'].strip()
        # คำนวน cost รวมของ streamer จาก scopes (ถ้าไม่ระบุ cost ตรงๆ)
        scopes_data = []
        computed_cost = 0
        for scope_type, scope_count, cost_per_unit in s.get('scopes', []):
            cost_per_unit = float(cost_per_unit)
            scope_count = int(scope_count)
            scopes_data.append((scope_type, scope_count, cost_per_unit))
            computed_cost += cost_per_unit * scope_count
        # ถ้ามี cost ระบุเอง ใช้ค่านั้น (อาจมี overhead หรือค่าอื่นๆ)
        # ถ้าไม่มี ใช้ computed_cost
        total_cost = float(s.get('cost', 0)) if s.get('cost') else computed_cost

        c.execute('''
            INSERT INTO project_streamers (project_id, streamer_name, cost) VALUES (?, ?, ?)
        ''', (project_id, sname, total_cost))
        ps_id = c.lastrowid

        for scope_type, scope_count, cost_per_unit in scopes_data:
            c.execute('''
                INSERT INTO project_streamer_scopes (project_streamer_id, scope_type, scope_count, cost_per_unit, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (ps_id, scope_type, scope_count, cost_per_unit, s.get('notes', '')))

    conn.commit()
    conn.close()
    return project_id


def add_scopes_to_streamer(project_streamer_id, scopes):
    """เพิ่ม scope ให้ streamer ที่มีอยู่ (ใช้ตอน edit)"""
    conn = get_db()
    c = conn.cursor()
    for scope_type, scope_count, cost_per_unit in scopes:
        c.execute('''
            INSERT INTO project_streamer_scopes (project_streamer_id, scope_type, scope_count, cost_per_unit, notes)
            VALUES (?, ?, ?, ?, '')
        ''', (project_streamer_id, scope_type, int(scope_count), float(cost_per_unit)))
    conn.commit()
    conn.close()


def get_project(project_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    if not row:
        conn.close()
        return None
    project = dict(row)
    # ดึง streamer + scopes
    ps_rows = conn.execute('''
        SELECT * FROM project_streamers WHERE project_id = ? ORDER BY streamer_name
    ''', (project_id,)).fetchall()
    streamers = []
    for ps in ps_rows:
        ps_dict = dict(ps)
        scopes = conn.execute('''
            SELECT * FROM project_streamer_scopes WHERE project_streamer_id = ? ORDER BY id
        ''', (ps_dict['id'],)).fetchall()
        ps_dict['scopes'] = [dict(s) for s in scopes]
        ps_dict['scope_count_total'] = sum(s['scope_count'] for s in ps_dict['scopes'])
        ps_dict['scope_total_cost'] = sum(
            s['cost_per_unit'] * s['scope_count'] for s in ps_dict['scopes']
        )
        streamers.append(ps_dict)
    project['streamers'] = streamers
    project['total_cost'] = sum(s['cost'] for s in streamers)
    conn.close()
    return project


def update_project_sale(project_id, sale_price):
    conn = get_db()
    conn.execute("UPDATE projects SET sale_price_override = ? WHERE id = ?", (float(sale_price), project_id))
    conn.commit()
    conn.close()


def update_project_status(project_id, status):
    conn = get_db()
    conn.execute("UPDATE projects SET status = ? WHERE id = ?", (status, project_id))
    conn.commit()
    conn.close()


# ===== Annual Report =====
# Status ที่นับรวมในผลประกอบการ (revenue/cost/profit)
REVENUE_STATUSES = ('in_progress', 'completed')


def get_annual_report(year):
    """คืนค่า P&L รวม + แยกตาม streamer + แยกตาม client สำหรับปีที่ระบุ
    นับเฉพาะ status = in_progress / completed (เสนอราคา + ยกเลิก ไม่นับ)
    """
    conn = get_db()
    year_str = str(year)
    # โปรเจคที่เกิดในปีนี้ (ตาม created_at) และ status ที่นับรวม
    pattern = f'{year_str}-%'
    placeholders_status = ','.join('?' * len(REVENUE_STATUSES))
    rows = conn.execute(f'''
        SELECT * FROM projects
        WHERE created_at LIKE ?
          AND status IN ({placeholders_status})
        ORDER BY created_at
    ''', (pattern, *REVENUE_STATUSES)).fetchall()
    projects = [dict(r) for r in rows]

    if not projects:
        # นับ project ทั้งหมด (รวมเสนอราคา/ยกเลิก) เพื่อบอก user
        total_rows = conn.execute(f'''
            SELECT COUNT(*) AS cnt FROM projects WHERE created_at LIKE ?
        ''', (pattern,)).fetchone()
        conn.close()
        return {
            'year': year,
            'project_count': 0,
            'total_projects_all_status': total_rows['cnt'] if total_rows else 0,
            'total_cost': 0,
            'total_revenue': 0,
            'total_profit': 0,
            'by_streamer': {},
            'by_client': {},
            'by_status': {},
            'projects': [],
        }

    project_ids = [p['id'] for p in projects]

    # นับ project ทั้งหมดในปีนี้ (รวมเสนอราคา/ยกเลิก) เพื่อบอก user
    total_all_status = conn.execute('''
        SELECT COUNT(*) AS cnt FROM projects WHERE created_at LIKE ?
    ''', (pattern,)).fetchone()
    total_projects_all_status = total_all_status['cnt'] if total_all_status else 0

    # รวบรวม streamers (จาก project_streamers)
    placeholders = ','.join('?' * len(project_ids))
    ps_rows = conn.execute(f'''
        SELECT ps.*, p.client_name, p.agency_fee_percent, p.sale_price_override, p.status
        FROM project_streamers ps
        JOIN projects p ON ps.project_id = p.id
        WHERE ps.project_id IN ({placeholders})
        ORDER BY p.created_at, ps.streamer_name
    ''', project_ids).fetchall()

    # รวม scope ต่อ streamer (เพื่อ breakdown ตาม scope)
    scope_rows = conn.execute(f'''
        SELECT sc.*, ps.streamer_name, ps.project_id, p.client_name
        FROM project_streamer_scopes sc
        JOIN project_streamers ps ON sc.project_streamer_id = ps.id
        JOIN projects p ON ps.project_id = p.id
        WHERE ps.project_id IN ({placeholders})
        ORDER BY ps.streamer_name, sc.scope_type
    ''', project_ids).fetchall()

    # ----- คำนวน P&L รวม -----
    total_cost = sum(p['total_cost'] if False else 0 for p in projects)  # คำนวนจาก ps
    total_cost = 0
    total_revenue = 0
    by_streamer = {}     # {streamer_name: {cost, revenue, profit, projects: [...]}}
    by_client = {}       # {client_name: {cost, revenue, profit, project_count}}
    by_status = {}       # {status_code: {count, cost, revenue, profit}}
    by_streamer_scope = {}  # {streamer_name: {scope_type: {cost, revenue, profit, count}}}

    for ps in ps_rows:
        ps = dict(ps)
        sname = ps['streamer_name']
        client = ps['client_name']
        status = ps['status']
        fee = ps['agency_fee_percent'] / 100.0
        cost = ps['cost']
        # revenue = cost * (1 + fee)  (ถ้ามี sale_price_override ที่ project level จะคำนวนต่างหาก)
        revenue = cost * (1 + fee)

        # by_streamer
        if sname not in by_streamer:
            by_streamer[sname] = {'cost': 0, 'revenue': 0, 'profit': 0, 'projects': [], 'project_count': 0, 'scope_count': 0}
        by_streamer[sname]['cost'] += cost
        by_streamer[sname]['revenue'] += revenue
        by_streamer[sname]['profit'] += revenue - cost
        if ps['project_id'] not in [pr['id'] for pr in by_streamer[sname]['projects']]:
            by_streamer[sname]['projects'].append({'id': ps['project_id'], 'name': next((p['name'] for p in projects if p['id'] == ps['project_id']), ''), 'client': client, 'status': status})
            by_streamer[sname]['project_count'] += 1

        # by_client
        if client not in by_client:
            by_client[client] = {'cost': 0, 'revenue': 0, 'profit': 0, 'project_count': 0}
        by_client[client]['cost'] += cost
        by_client[client]['revenue'] += revenue
        by_client[client]['profit'] += revenue - cost
        # project_count: นับ unique project_id
        if not any(p.get('added') for p in by_client[client].get('_seen', [])):
            pass
        # ใช้ set เก็บ project_id ที่นับแล้ว
        by_client[client].setdefault('_seen_ids', set()).add(ps['project_id'])

        # by_status
        if status not in by_status:
            by_status[status] = {'count': 0, 'cost': 0, 'revenue': 0, 'profit': 0, 'project_ids': set()}
        by_status[status]['cost'] += cost
        by_status[status]['revenue'] += revenue
        by_status[status]['profit'] += revenue - cost
        by_status[status]['project_ids'].add(ps['project_id'])

        total_cost += cost
        total_revenue += revenue

    # คำนวน project_count ของ by_client + เปลี่ยน set → count
    for cname in by_client:
        by_client[cname]['project_count'] = len(by_client[cname].pop('_seen_ids'))

    # นับ project count ใน by_status
    for sc in by_status:
        by_status[sc]['count'] = len(by_status[sc].pop('project_ids'))

    # ----- by_streamer x project (แทน by_streamer x scope เดิม) -----
    # โครงสร้าง: {streamer_name: [{project_id, project_name, client_name, status, cost, revenue, profit, scope_count, scope_summary}, ...]}
    by_streamer_project = {}  # {streamer_name: [project_dict, ...]}
    streamer_project_set = {}  # เก็บ unique (streamer, project_id) เพื่อหลีกเลี่ยงนับซ้ำ

    # scope_rows เดิมเก็บ 1 row = 1 scope
    # เปลี่ยนเป็น group by (streamer, project) แล้วรวม scope เป็น summary string
    for sc in scope_rows:
        sc = dict(sc)
        sname = sc['streamer_name']
        project_id = sc['project_id']
        client = sc['client_name']
        proj = next((p for p in projects if p['id'] == project_id), None)
        if not proj: continue
        fee = proj['agency_fee_percent'] / 100.0

        key = (sname, project_id)
        if key not in streamer_project_set:
            streamer_project_set[key] = {
                'project_id': project_id,
                'project_name': proj['name'],
                'client_name': client,
                'status': proj['status'],
                'cost': 0, 'revenue': 0, 'profit': 0,
                'scope_count': 0,
                'scope_summary': [],
            }
        entry = streamer_project_set[key]
        scope_cost = (sc['cost_per_unit'] or 0) * sc['scope_count']
        entry['cost'] += scope_cost
        entry['revenue'] += scope_cost * (1 + fee)
        entry['scope_count'] += sc['scope_count']
        entry['scope_summary'].append(f"{sc['scope_type']} ×{sc['scope_count']}")

    # คำนวน profit และจัดกลุ่มตาม streamer
    for (sname, pid), entry in streamer_project_set.items():
        entry['profit'] = entry['revenue'] - entry['cost']
        entry['scope_summary_str'] = ', '.join(entry['scope_summary'])
        by_streamer_project.setdefault(sname, []).append(entry)

    # เรียงตาม profit มาก → น้อย
    for sname in by_streamer_project:
        by_streamer_project[sname].sort(key=lambda x: x['profit'], reverse=True)

    # scope_count รวมต่อ streamer
    for sname in by_streamer_project:
        by_streamer[sname]['scope_count'] = sum(e['scope_count'] for e in by_streamer_project[sname])

    # ----- Top performers -----
    top_streamers = sorted(by_streamer.items(), key=lambda x: x[1]['profit'], reverse=True)
    top_clients = sorted(by_client.items(), key=lambda x: x[1]['revenue'], reverse=True)

    # ----- Monthly breakdown -----
    monthly = {}
    for p in projects:
        month = p['created_at'][:7]  # '2026-01'
        if month not in monthly:
            monthly[month] = {'cost': 0, 'revenue': 0, 'profit': 0, 'project_count': 0}
        monthly[month]['project_count'] += 1

    # รวม cost/revenue ต่อเดือน
    for ps in ps_rows:
        ps = dict(ps)
        p = next((p for p in projects if p['id'] == ps['project_id']), None)
        if not p: continue
        month = p['created_at'][:7]
        fee = ps['agency_fee_percent'] / 100.0
        monthly[month]['cost'] += ps['cost']
        monthly[month]['revenue'] += ps['cost'] * (1 + fee)
    for m in monthly:
        monthly[m]['profit'] = monthly[m]['revenue'] - monthly[m]['cost']

    conn.close()
    return {
        'year': year,
        'project_count': len(projects),
        'total_projects_all_status': total_projects_all_status,
        'total_cost': total_cost,
        'total_revenue': total_revenue,
        'total_profit': total_revenue - total_cost,
        'profit_margin': (total_revenue - total_cost) / total_revenue * 100 if total_revenue > 0 else 0,
        'by_streamer': by_streamer,
        'by_client': by_client,
        'by_status': by_status,
        'by_streamer_project': by_streamer_project,
        'top_streamers': top_streamers,
        'top_clients': top_clients,
        'monthly': monthly,
        'projects': projects,
    }


def list_years_with_projects():
    """คืนค่าปีทั้งหมดที่มีโปรเจค"""
    conn = get_db()
    rows = conn.execute('''
        SELECT DISTINCT substr(created_at, 1, 4) AS year FROM projects
        ORDER BY year DESC
    ''').fetchall()
    conn.close()
    return [r['year'] for r in rows]


def auto_cancel_stale_quotes(months=5):
    """ยกเลิกอัตโนมัติ: โปรเจคที่อยู่ในสถานะ 'เสนอราคา' (pending) นานเกิน X เดือน
    โดยไม่มีการอัพเดตสถานะ
    Returns: list of project dicts ที่ถูกยกเลิก
    """
    conn = get_db()
    # คำนวนวันที่ตัด (5 เดือนย้อนหลัง)
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=months * 30)).isoformat(sep=' ')

    # หาโปรเจค pending ที่ created_at เก่ากว่า cutoff
    rows = conn.execute('''
        SELECT id, name, client_name, status, created_at
        FROM projects
        WHERE status = 'pending' AND created_at < ?
        ORDER BY created_at
    ''', (cutoff,)).fetchall()
    if not rows:
        conn.close()
        return []

    cancelled = [dict(r) for r in rows]
    ids = [c['id'] for c in cancelled]
    placeholders = ','.join('?' * len(ids))
    conn.execute(f'''
        UPDATE projects SET status = 'cancelled' WHERE id IN ({placeholders})
    ''', ids)
    conn.commit()
    conn.close()
    return cancelled


# ===== Stats =====
def create_stat_report(project_id, project_streamer_id, scope_id, platform, views, likes, shares, comments, engagement, extra_data, submitted_by):
    conn = get_db()
    conn.execute('''
        INSERT INTO stat_reports
        (project_id, project_streamer_id, scope_id, platform, views, likes, shares, comments, engagement, extra_data, submitted_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (project_id, project_streamer_id, scope_id, platform, int(views), int(likes), int(shares), int(comments), float(engagement), extra_data, submitted_by))
    conn.commit()
    conn.close()


def list_stats_for_project(project_id):
    conn = get_db()
    rows = conn.execute('''
        SELECT s.*, ps.streamer_name, sc.scope_type, sc.scope_count,
               u.display_name AS submitter_name
        FROM stat_reports s
        JOIN project_streamers ps ON s.project_streamer_id = ps.id
        LEFT JOIN project_streamer_scopes sc ON s.scope_id = sc.id
        JOIN users u ON s.submitted_by = u.id
        WHERE s.project_id = ?
        ORDER BY s.submitted_at DESC
    ''', (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_stat_report(stat_id):
    conn = get_db()
    conn.execute("DELETE FROM stat_reports WHERE id = ?", (stat_id,))
    conn.commit()
    conn.close()


def aggregate_project_stats(project_id):
    """สรุป stats รวมของ project — สำหรับหน้า report"""
    stats = list_stats_for_project(project_id)
    if not stats:
        return None
    agg = {
        'total_views': sum(s['views'] for s in stats),
        'total_likes': sum(s['likes'] for s in stats),
        'total_shares': sum(s['shares'] for s in stats),
        'total_comments': sum(s['comments'] for s in stats),
        'avg_engagement': sum(s['engagement'] for s in stats) / len(stats),
        'platforms': list(set(s['platform'] for s in stats)),
        'streamer_count': len(set(s['streamer_name'] for s in stats)),
        'report_count': len(stats),
    }
    # per-platform
    by_platform = {}
    for s in stats:
        p = s['platform']
        if p not in by_platform:
            by_platform[p] = {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0, 'count': 0}
        by_platform[p]['views'] += s['views']
        by_platform[p]['likes'] += s['likes']
        by_platform[p]['shares'] += s['shares']
        by_platform[p]['comments'] += s['comments']
        by_platform[p]['count'] += 1
    agg['by_platform'] = by_platform
    # per-streamer
    by_streamer = {}
    for s in stats:
        key = s['streamer_name']
        if key not in by_streamer:
            by_streamer[key] = {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0, 'platforms': set()}
        by_streamer[key]['views'] += s['views']
        by_streamer[key]['likes'] += s['likes']
        by_streamer[key]['shares'] += s['shares']
        by_streamer[key]['comments'] += s['comments']
        by_streamer[key]['platforms'].add(s['platform'])
    for v in by_streamer.values():
        v['platforms'] = list(v['platforms'])
    agg['by_streamer'] = by_streamer
    # per-scope
    by_scope = {}
    for s in stats:
        key = s.get('scope_type') or 'ไม่ระบุ scope'
        if key not in by_scope:
            by_scope[key] = {'views': 0, 'likes': 0, 'shares': 0, 'comments': 0, 'count': 0}
        by_scope[key]['views'] += s['views']
        by_scope[key]['likes'] += s['likes']
        by_scope[key]['shares'] += s['shares']
        by_scope[key]['comments'] += s['comments']
        by_scope[key]['count'] += 1
    agg['by_scope'] = by_scope
    return agg
