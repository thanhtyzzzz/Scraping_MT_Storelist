import requests
from bs4 import BeautifulSoup
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

try:
    URL = 'https://sieuthibsmart.com/he-thong-b-smart/'
    log_to_sqlite("Storelist_BsMart.py", "Pending", f"Bắt đầu gửi request tới {URL}")
    res = requests.get(URL)
    res.raise_for_status()
    log_to_sqlite("Storelist_BsMart.py", "Succeeded", f"Gửi request tới {URL} thành công")
except Exception as e:
    log_to_sqlite("Storelist_BsMart.py", "Failed", f"Lỗi khi gửi request tới {URL}: {e}")
    raise

# Parse HTML với BeautifulSoup
try:
    soup = BeautifulSoup(res.text, 'html.parser')
    log_to_sqlite("Storelist_BsMart.py", "Succeeded", "Parse HTML thành công")
except Exception as e:
    log_to_sqlite("Storelist_BsMart.py", "Failed", f"Lỗi khi parse HTML: {e}")
    raise

# Chọn tất cả các khối "accordion-item" đại diện cho mỗi Quận/Huyện
district_blocks = soup.select('.accordion-item')
stores = []

for block in district_blocks:
    try:
        # Lấy tên quận/huyện từ phần <span> trong tiêu đề accordion
        title = block.select_one('a.accordion-title span')
        if not title:
            log_to_sqlite("Storelist_BsMart.py", "Failed", "Không tìm thấy tiêu đề quận/huyện")
            continue
        district_name = title.text.strip()
        log_to_sqlite("Storelist_BsMart.py", "Succeeded", f"Lấy tên quận/huyện: {district_name}")

        # Lấy phần chứa địa chỉ (các <p>) bên trong div.accordion-inner
        inner = block.select_one('.accordion-inner')
        if not inner:
            log_to_sqlite("Storelist_BsMart.py", "Failed", f"Không tìm thấy div.accordion-inner cho quận {district_name}")
            continue

        address_tags = inner.find_all('p')
        for p in address_tags:
            addr = p.text.strip()
            if addr:
                stores.append([district_name, addr])
                log_to_sqlite("Storelist_BsMart.py", "Succeeded", f"Lấy địa chỉ: {addr} tại {district_name}")
    except Exception as e:
        log_to_sqlite("Storelist_BsMart.py", "Failed", f"Lỗi khi xử lý khối accordion-item: {e}")
        continue

# Export dữ liệu ra file XLSX
log_to_sqlite("Storelist_BsMart.py", "Pending", "Bắt đầu lưu file bsmart_stores.xlsx")
try:
    df = pd.DataFrame(stores, columns=['Quận/Huyện', 'Địa chỉ'])
    df.to_excel('bsmart_stores.xlsx', index=False, engine='openpyxl')
    print(f"Đã thu được {len(stores)} cửa hàng và lưu vào bsmart_stores.xlsx")
    log_to_sqlite("Storelist_BsMart.py", "Succeeded", f"Đã lưu {len(stores)} cửa hàng vào bsmart_stores.xlsx")
except Exception as e:
    log_to_sqlite("Storelist_BsMart.py", "Failed", f"Lỗi khi lưu file bsmart_stores.xlsx: {e}")
    raise