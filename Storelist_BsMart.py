import requests
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl
from datetime import datetime

# Hàm ghi log lỗi vào file Excel
def log_error(file_name, error_message):
    log_file = "error_log.xlsx"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data = [[timestamp, file_name, error_message]]
    
    try:
        try:
            wb = openpyxl.load_workbook(log_file)
            ws = wb.active
        except FileNotFoundError:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Timestamp", "File", "Error Message"])
        
        ws.append([timestamp, file_name, error_message])
        wb.save(log_file)
        print(f"Đã ghi lỗi vào {log_file}: {error_message}")
    except Exception as e:
        print(f"Lỗi khi ghi log vào {log_file}: {e}")

try:
    URL = 'https://sieuthibsmart.com/he-thong-b-smart/'
    res = requests.get(URL)
    res.raise_for_status()
except Exception as e:
    error_message = f"Lỗi khi gửi request tới {URL}: {e}"
    log_error("Storelist_BsMart.py", error_message)
    raise

# Parse HTML với BeautifulSoup
try:
    soup = BeautifulSoup(res.text, 'html.parser')
except Exception as e:
    error_message = f"Lỗi khi parse HTML: {e}"
    log_error("Storelist_BsMart.py", error_message)
    raise

# Chọn tất cả các khối "accordion-item" đại diện cho mỗi Quận/Huyện
district_blocks = soup.select('.accordion-item')

stores = []

for block in district_blocks:
    try:
        # Lấy tên quận/huyện từ phần <span> trong tiêu đề accordion
        title = block.select_one('a.accordion-title span')
        if not title:
            error_message = "Không tìm thấy tiêu đề quận/huyện"
            log_error("Storelist_BsMart.py", error_message)
            continue
        district_name = title.text.strip()

        # Lấy phần chứa địa chỉ (các <p>) bên trong div.accordion-inner
        inner = block.select_one('.accordion-inner')
        if not inner:
            error_message = f"Không tìm thấy div.accordion-inner cho quận {district_name}"
            log_error("Storelist_BsMart.py", error_message)
            continue

        address_tags = inner.find_all('p')
        for p in address_tags:
            addr = p.text.strip()
            if addr:
                stores.append([district_name, addr])
    except Exception as e:
        error_message = f"Lỗi khi xử lý khối accordion-item: {e}"
        log_error("Storelist_BsMart.py", error_message)
        continue

# Export dữ liệu ra file XLSX
try:
    df = pd.DataFrame(stores, columns=['Quận/Huyện', 'Địa chỉ'])
    df.to_excel('bsmart_stores.xlsx', index=False, engine='openpyxl')
    print(f"Đã thu được {len(stores)} cửa hàng và lưu vào bsmart_stores.xlsx")
except Exception as e:
    error_message = f"Lỗi khi lưu file bsmart_stores.xlsx: {e}"
    log_error("Storelist_BsMart.py", error_message)
    raise