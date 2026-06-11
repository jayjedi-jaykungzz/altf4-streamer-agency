# ALTF4 Streamer Agency

Flask + SQLite web app สำหรับบริหารจัดการโปรเจคของ Streamer Agency

## 🚀 Deploy ขึ้น Render.com (ฟรี)

### 1. เตรียม GitHub Repo

```bash
# สร้าง repo บน GitHub: https://github.com/new
# ตั้งชื่อ: altf4-streamer-agency (Private)
# แล้ว push:
cd "C:/Users/Jedi PC/streamer-agency"
git remote set-url origin https://github.com/YOUR_USERNAME/altf4-streamer-agency.git
git push -u origin main
```

### 2. สมัคร Render

ไปที่ https://render.com → Sign up with GitHub

### 3. สร้าง Web Service

1. คลิก **"New"** → **"Web Service"**
2. เชื่อมต่อ repo: `altf4-streamer-agency`
3. ตั้งค่า:
   - **Name:** `altf4-streamer-agency`
   - **Region:** Singapore
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `waitress-serve --host=0.0.0.0 --port=$PORT app.main:app`
   - **Plan:** Free

### 4. ตั้ง Environment Variables

ในหน้า Web Service → **Environment**:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | (random string ยาวๆ เช่น `my-altf4-secret-2026-change-this`) |
| `DATABASE_PATH` | `/tmp/agency.db` |
| `PYTHON_VERSION` | `3.11.9` |

### 5. Deploy!

คลิก **"Create Web Service"** → Render จะ build และ deploy อัตโนมัติ

ใช้เวลา ~3-5 นาที แล้วจะได้ URL:
`https://altf4-streamer-agency.onrender.com`

### 6. Init Database (ครั้งแรกครั้งเดียว)

หลัง deploy เสร็จ เปิด Shell (Dashboard → Shell):
```bash
cd app && python seed_demo.py
```

หรือเปิด `https://altf4-streamer-agency.onrender.com/init` (ถ้ามี endpoint)

---

## ⚠️ ข้อจำกัด Render Free Tier

- **Sleep mode:** ถ้าไม่มีคนใช้ 15 นาที จะหลับ — request แรกหลังตื่นใช้เวลา ~30 วิ
- **Database:** SQLite ที่ `/tmp` จะหายเมื่อ deploy ใหม่! ใช้ **External DB** แทน (ดูด้านล่าง)
- **750 ชั่วโมง/เดือน** (พอใช้งานส่วนตัว/ทีมเล็กๆ)

## 💾 Database ถาวร (แนะนำ)

ใช้ **Supabase** หรือ **Neon** (PostgreSQL ฟรี):
1. สร้าง account ที่ supabase.com
2. สร้าง project → copy connection string
3. เพิ่ม env var: `DATABASE_URL=postgresql://...`
4. แก้ `models.py` ให้ใช้ `psycopg2` แทน `sqlite3`

## 🔧 รัน Local

```bash
cd "C:/Users/Jedi PC/streamer-agency"
source venv/Scripts/activate
cd app
python main.py
```

เปิด: http://127.0.0.1:5000

Login:
- Admin: `admin1` / `admin123`
- Staff: `staff1` / `staff123`

## 💾 Backup Database

```bash
python backup_db.py
```

เก็บ backup ที่ `app/backups/` (ลบอันเกิน 7 วันอัตโนมัติ)
