import requests
import pandas as pd
import sqlite3
from datetime import datetime

# Hàm ghi log vào SQLite
def log_to_sqlite(file_name, status, message):
    log_file = "storelist_logs.db"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        conn = sqlite3.connect(log_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                LogID INTEGER PRIMARY KEY AUTOINCREMENT,
                Timestamp TEXT,
                File TEXT,
                Status TEXT,
                Message TEXT
            )
        ''')
        
        cursor.execute('''
            INSERT INTO logs (Timestamp, File, Status, Message)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, file_name, status, message))
        
        conn.commit()
        print(f"Đã ghi log vào {log_file}: {status} - {message}")
    except Exception as e:
        print(f"Lỗi khi ghi log vào {log_file}: {e}")
    finally:
        conn.close()

# API endpoint
try:
    url = 'https://api-gateway.pharmacity.vn/api/v1/seo_stores'
    log_to_sqlite("Pharmacity.py", "Pending", f"Bắt đầu gửi request API tới {url}")
    res = requests.get(url)
    res.raise_for_status()
    log_to_sqlite("Pharmacity.py", "Succeeded", f"Gửi request API tới {url} thành công")
except Exception as e:
    log_to_sqlite("Pharmacity.py", "Failed", f"Lỗi khi gửi request API: {e}")
    raise

# Truy cập đúng vào danh sách cửa hàng
try:
    data = res.json()
    items = data.get('data', {}).get('items', [])
    print(f"🔍 Tổng số cửa hàng SEO stores: {len(items)} mục")
    log_to_sqlite("Pharmacity.py", "Succeeded", f"Tổng số cửa hàng SEO stores: {len(items)} mục")
except Exception as e:
    log_to_sqlite("Pharmacity.py", "Failed", f"Lỗi khi parse JSON: {e}")
    raise

store_list = []

# Lặp từng cửa hàng
for store in items:
    try:
        store_list.append([
            store.get('name', ''),
            store.get('address', ''),
            store.get('province', ''),
            store.get('district', ''),
            store.get('ward', ''),
            store.get('latitude', ''),
            store.get('longitude', ''),
            store.get('url_maps', ''),
            store.get('open_time', ''),
            store.get('close_time', ''),
            store.get('phone', ''),
            store.get('zalo_url', '')
        ])
        log_to_sqlite("Pharmacity.py", "Succeeded", f"Lấy cửa hàng: {store.get('name', '')}, {store.get('address', '')}")
    except Exception as e:
        log_to_sqlite("Pharmacity.py", "Failed", f"Lỗi khi xử lý cửa hàng: {e}")
        continue

# Export ra XLSX
log_to_sqlite("Pharmacity.py", "Pending", "Bắt đầu lưu file pharmacity_all_stores.xlsx")
try:
    df = pd.DataFrame(store_list, columns=[
        'Tên cửa hàng', 'Địa chỉ', 'Tỉnh', 'Quận/Huyện', 'Phường/Xã',
        'Vĩ độ', 'Kinh độ', 'Google Maps', 'Giờ mở cửa', 'Giờ đóng cửa',
        'SĐT', 'Zalo URL'
    ])
    df.to_excel('pharmacity_all_stores.xlsx', index=False, engine='openpyxl')
    print(f"Đã lưu {len(store_list)} cửa hàng vào pharmacity_all_stores.xlsx")
    log_to_sqlite("Pharmacity.py", "Succeeded", f"Đã lưu {len(store_list)} cửa hàng vào pharmacity_all_stores.xlsx")
except Exception as e:
    log_to_sqlite("Pharmacity.py", "Failed", f"Lỗi khi lưu file pharmacity_all_stores.xlsx: {e}")
    raise