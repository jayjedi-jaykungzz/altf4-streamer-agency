"""
Streamer Agency - Main Flask App
- Admin: full access
- Staff: ดูงาน + กรอก stat + อัพเดทสถานะ (ไม่เห็นราคา/ต้นทุน/ราคาขาย)
"""
import os
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort

from models import (
    init_db, verify_user, get_user_by_id, list_staff,
    STREAMER_ROSTER, get_scope_types, add_scopes_to_streamer,
    list_projects, get_project, create_project, update_project_sale, update_project_status,
    create_stat_report, list_stats_for_project, delete_stat_report,
    aggregate_project_stats,
    STATUS_LABELS, STATUS_CODES,
    get_annual_report, list_years_with_projects,
    auto_cancel_stale_quotes
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production-please-jay-2026')


# ===== Auto cancel stale quotes (เสนอราคา > 5 เดือน → ยกเลิก) =====
_last_auto_cancel_check = None


@app.before_request
def check_stale_quotes():
    """ตรวจสอบ auto-cancel ทุก 1 ชม. (ไม่ทำทุก request)"""
    global _last_auto_cancel_check
    now = datetime.datetime.now()
    if _last_auto_cancel_check is None or (now - _last_auto_cancel_check).total_seconds() > 3600:
        try:
            cancelled = auto_cancel_stale_quotes(months=5)
            if cancelled and session.get('user_id'):
                # แสดง flash เฉพาะเมื่อ user login แล้ว
                names = ', '.join(f"#{p['id']} {p['name']}" for p in cancelled[:3])
                more = f' (และอีก {len(cancelled) - 3})' if len(cancelled) > 3 else ''
                flash(f'⏰ ระบบยกเลิกอัตโนมัติ {len(cancelled)} โปรเจคที่ค้างในสถานะ "เสนอราคา" เกิน 5 เดือน: {names}{more}', 'warning')
            _last_auto_cancel_check = now
        except Exception as e:
            print(f'[auto-cancel] error: {e}')
            _last_auto_cancel_check = now  # ไม่ให้ลูป error ถี่


# ===== Auth helpers =====
def current_user():
    uid = session.get('user_id')
    if uid is None:
        return None
    return get_user_by_id(uid)


def is_admin():
    u = current_user()
    return u and u['role'] == 'admin'


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for('login'))
        if u['role'] != 'admin':
            return abort(403)
        return f(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_user():
    return {
        'current_user': current_user(),
        'STATUS_LABELS': STATUS_LABELS,
        'STATUS_CODES': STATUS_CODES,
    }


# ===== Routes =====
@app.route('/')
def index():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
# ===== Dashboard (ใช้ร่วมกัน) =====
@app.route('/dashboard')
@login_required
def dashboard():
    sort_by = request.args.get('sort', 'date_desc')
    status_filter = request.args.get('status', None)
    view = request.args.get('view', 'list')
    if status_filter and status_filter not in STATUS_CODES:
        status_filter = None

    projects = list_projects(
        sort_by=sort_by,
        status_filter=status_filter,
    )
    total_count = len(projects)
    # นับ status ทั้งหมด (ไม่สน filter)
    all_projects = list_projects(sort_by=sort_by)
    status_counts = {}
    for p in all_projects:
        status_counts[p['status']] = status_counts.get(p['status'], 0) + 1

    return render_template(
        'dashboard.html',
        projects=projects,
        total_count=total_count,
        status_counts=status_counts,
        sort_by=sort_by,
        status_filter=status_filter,
        view=view,
    )


# ===== Project detail (ใช้ร่วมกัน) =====
@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = get_project(project_id)
    if not project:
        return abort(404)
    stats = list_stats_for_project(project_id)
    return render_template('project_detail.html', project=project, stats=stats)


# ===== Stat submission (staff + admin ใช้ได้) =====
@app.route('/project/<int:project_id>/stat/new', methods=['GET', 'POST'])
@login_required
def stat_new(project_id):
    project = get_project(project_id)
    if not project:
        return abort(404)
    if request.method == 'POST':
        project_streamer_id = int(request.form['project_streamer_id'])
        # ตรวจว่า ps_id อยู่ใน project นี้จริง
        if not any(s['id'] == project_streamer_id for s in project['streamers']):
            return abort(400)

        # scope_id อาจว่าง (กรณีไม่ได้เลือก scope)
        scope_id_raw = request.form.get('scope_id', '')
        scope_id = int(scope_id_raw) if scope_id_raw else None

        create_stat_report(
            project_id=project_id,
            project_streamer_id=project_streamer_id,
            scope_id=scope_id,
            platform=request.form['platform'],
            views=request.form.get('views', 0),
            likes=request.form.get('likes', 0),
            shares=request.form.get('shares', 0),
            comments=request.form.get('comments', 0),
            engagement=request.form.get('engagement', 0),
            extra_data=request.form.get('extra_data', ''),
            submitted_by=current_user()['id']
        )
        flash('ส่งรายงาน Stat เรียบร้อย!', 'success')
        return redirect(url_for('project_detail', project_id=project_id))

    return render_template('stat_form.html', project=project)


@app.route('/stat/<int:stat_id>/delete', methods=['POST'])
@login_required
def stat_delete(stat_id):
    # ดึง project_id ก่อนลบ
    conn = __import__('sqlite3').connect(os.path.join(os.path.dirname(__file__), 'agency.db'))
    row = conn.execute("SELECT project_id FROM stat_reports WHERE id = ?", (stat_id,)).fetchone()
    conn.close()
    if row:
        delete_stat_report(stat_id)
        flash('ลบรายงานเรียบร้อย', 'success')
        return redirect(url_for('project_detail', project_id=row[0]))
    return abort(404)


# ===== Status update (staff + admin) =====
@app.route('/project/<int:project_id>/update_status', methods=['POST'])
@login_required
def project_update_status(project_id):
    new_status = request.form['status']
    update_project_status(project_id, new_status)
    flash('อัพเดทสถานะเรียบร้อย', 'success')
    return redirect(url_for('project_detail', project_id=project_id))


# ===== Admin-only =====
@app.route('/project/new', methods=['GET', 'POST'])
@admin_required
def project_new():
    if request.method == 'POST':
        name = request.form['name'].strip()
        client_name = request.form['client_name'].strip()
        agency_fee_percent = float(request.form['agency_fee_percent'])
        notes = request.form.get('notes', '')

        # streamer_scopes: parse จาก form
        # Format: แต่ละ streamer มี fields:
        #   streamer_<idx> = name
        #   cost_<idx> = cost
        #   scope_type_<idx>_<scopeidx> = scope type
        #   scope_count_<idx>_<scopeidx> = count
        #   เก็บเป็น list ของ dict {name, cost, scopes: [(type, count), ...]}

        # รวบรวม indices ของ streamer
        streamer_indices = set()
        for key in request.form:
            if key.startswith('streamer_'):
                idx = key.replace('streamer_', '').split('_')[0]
                streamer_indices.add(idx)

        streamer_scopes = []
        for idx in sorted(streamer_indices, key=lambda x: int(x) if x.isdigit() else 0):
            sname = request.form.get(f'streamer_{idx}', '').strip()
            cost = request.form.get(f'cost_{idx}', '0') or '0'

            # รวบรวม scopes ของ streamer นี้
            scopes = []
            for skey in request.form:
                if skey.startswith(f'scope_type_{idx}_'):
                    scopeidx = skey.replace(f'scope_type_{idx}_', '')
                    stype = request.form.get(skey, '').strip()
                    count = request.form.get(f'scope_count_{idx}_{scopeidx}', '0') or '0'
                    cost_per_unit = request.form.get(f'scope_cost_{idx}_{scopeidx}', '0') or '0'
                    if stype and int(count) > 0:
                        scopes.append((stype, int(count), float(cost_per_unit)))

            # ต้องมีชื่อ streamer และ (cost > 0 หรือ scopes > 0)
            if not sname:
                continue
            if float(cost) <= 0 and not scopes:
                continue

            streamer_scopes.append({
                'name': sname,
                'cost': float(cost),
                'scopes': scopes,
            })

        if not name or not client_name or not streamer_scopes:
            flash('กรุณากรอกข้อมูลให้ครบ และเพิ่มสตรีมเมอร์อย่างน้อย 1 คน', 'error')
            return render_template('project_new.html', roster=STREAMER_ROSTER, scope_types=get_scope_types())

        project_id = create_project(name, client_name, agency_fee_percent, streamer_scopes, notes)
        flash(f'สร้างโปรเจ็ค "{name}" เรียบร้อย', 'success')
        return redirect(url_for('project_detail', project_id=project_id))

    return render_template('project_new.html', roster=STREAMER_ROSTER, scope_types=get_scope_types())


@app.route('/project/<int:project_id>/update_price', methods=['POST'])
@admin_required
def project_update_price(project_id):
    update_project_sale(project_id, request.form['sale_price'])
    flash('อัพเดทราคาขายเรียบร้อย', 'success')
    return redirect(url_for('project_detail', project_id=project_id))


# ===== Public Report (ลูกค้าดู) =====
@app.route('/report/<int:project_id>')
def public_report(project_id):
    project = get_project(project_id)
    if not project:
        return abort(404)
    stats = list_stats_for_project(project_id)
    agg = aggregate_project_stats(project_id)
    return render_template('public_report.html', project=project, stats=stats, agg=agg)


# ===== Inline Status Update (จากหน้า Dashboard) =====
@app.route('/project/<int:project_id>/quick_status', methods=['POST'])
@login_required
def project_quick_status(project_id):
    """เปลี่ยนสถานะจากหน้า Dashboard - admin/staff ใช้ได้"""
    new_status = request.form.get('status')
    if new_status not in STATUS_CODES:
        return abort(400)
    update_project_status(project_id, new_status)
    # ถ้าเป็น AJAX (dashboard) return JSON; else redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'ok': True, 'status': new_status, 'label': STATUS_LABELS[new_status]}
    return redirect(request.referrer or url_for('dashboard'))


# ===== Annual Report (สรุปประจำปี) — admin only =====
@app.route('/annual')
@admin_required
def annual_report():
    year = request.args.get('year', type=int)
    years = list_years_with_projects()
    if not years:
        years = [str(datetime.date.today().year)]
    if not year:
        year = int(years[0])
    report = get_annual_report(year)
    return render_template('annual_report.html', report=report, years=years, selected_year=year)


# ===== Manual trigger: auto-cancel stale quotes =====
@app.route('/admin/auto_cancel_stale')
@admin_required
def admin_auto_cancel():
    """รัน auto-cancel ทันที (admin only) - ใช้ทดสอบ"""
    cancelled = auto_cancel_stale_quotes(months=5)
    if cancelled:
        names = ', '.join(f"#{p['id']} {p['name']} (สร้าง {p['created_at'][:10]})" for p in cancelled)
        flash(f'⏰ ยกเลิกอัตโนมัติ {len(cancelled)} โปรเจค: {names}', 'warning')
    else:
        flash('✅ ไม่มีโปรเจคที่ต้องยกเลิก (เสนอราคาเกิน 5 เดือน)', 'success')
    return redirect(url_for('dashboard'))


# ===== Static upload =====
# (ลบระบบอัพโหลดรูปภาพออกแล้ว)


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
