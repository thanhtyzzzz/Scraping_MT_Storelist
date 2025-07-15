import requests
import pandas as pd
import time
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

try:
    url_provinces = 'https://api-crownx.winmart.vn/mt/api/web/v1/provinces/all-winmart'
    log_to_sqlite("WinMart.py", "Pending", f"Bắt đầu gọi API tỉnh/thành: {url_provinces}")
    res = requests.get(url_provinces)
    res.raise_for_status()
    provinces_data = res.json()
    log_to_sqlite("WinMart.py", "Succeeded", f"Gọi API tỉnh/thành thành công")
except Exception as e:
    log_to_sqlite("WinMart.py", "Failed", f"Lỗi khi gọi API tỉnh/thành: {e}")
    raise

store_list = []

# Duyệt từng tỉnh/thành
for province in provinces_data['data']:
    province_code = province.get('code')
    province_name = province.get('description')
    print(f'Đang xử lý: {province_name} ({province_code})')
    log_to_sqlite("WinMart.py", "Pending", f"Bắt đầu xử lý tỉnh: {province_name} ({province_code})")

    # Gọi API lấy cửa hàng theo tỉnh
    try:
        url = f'https://api-crownx.winmart.vn/mt/api/web/v1/store-by-province?PageNumber=1&PageSize=1000&ProvinceCode={province_code}'
        log_to_sqlite("WinMart.py", "Pending", f"Gọi API cửa hàng cho tỉnh {province_name}")
        res_store = requests.get(url)
        res_store.raise_for_status()
        store_data = res_store.json().get('data', [])
        log_to_sqlite("WinMart.py", "Succeeded", f"Gọi API cửa hàng cho tỉnh {province_name} thành công")
    except Exception as e:
        log_to_sqlite("WinMart.py", "Failed", f"Lỗi khi gọi API cửa hàng cho tỉnh {province_name}: {e}")
        continue

    # Lấy danh sách cửa hàng
    for district in store_data:
        for ward in district.get('wardStores', []):
            for store in ward.get('stores', []):
                try:
                    store_list.append([
                        store.get('storeName', ''),
                        store.get('officeAddress', ''),
                        store.get('provinceName', ''),
                        store.get('districtName', ''),
                        store.get('wardName', ''),
                        store.get('activeStatus', '')
                    ])
                    log_to_sqlite("WinMart.py", "Succeeded", f"Lấy cửa hàng tại {province_name}: {store.get('storeName', '')}, {store.get('officeAddress', '')}")
                except Exception as e:
                    log_to_sqlite("WinMart.py", "Failed", f"Lỗi khi xử lý cửa hàng tại {province_name}: {e}")
                    continue

    time.sleep(0.3)

# Export ra XLSX
log_to_sqlite("WinMart.py", "Pending", "Bắt đầu lưu file winmart_stores_full.xlsx")
try:
    df = pd.DataFrame(store_list, columns=['Tên cửa hàng', 'Địa chỉ', 'Tỉnh', 'Quận/Huyện', 'Phường/Xã', 'Trạng thái'])
    df.to_excel('winmart_stores_full.xlsx', index=False, engine='openpyxl')
    print(f'Đã lấy {len(store_list)} cửa hàng và lưu vào winmart_stores_full.xlsx')
    log_to_sqlite("WinMart.py", "Succeeded", f"Đã lưu {len(store_list)} cửa hàng vào winmart_stores_full.xlsx")
except Exception as e:
    log_to_sqlite("WinMart.py", "Failed", f"Lỗi khi lưu file winmart_stores_full.xlsx: {e}")
    raise