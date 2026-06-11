"""
WSGI entry point for production server (Render.com)
ใช้: waitress-serve wsgi:application
"""
import os
import sys

# เพิ่ม app folder เข้า Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# เปลี่ยน working directory เป็น app folder เพื่อให้ database path ใช้งานได้
os.chdir(os.path.join(os.path.dirname(__file__), 'app'))

# Import Flask app
from main import app as application

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 5000))
    serve(application, host='0.0.0.0', port=port)
