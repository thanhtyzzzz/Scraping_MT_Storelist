import requests
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

# API endpoint
try:
    url = 'https://api-gateway.pharmacity.vn/api/v1/seo_stores'
    res = requests.get(url)
    res.raise_for_status()
except Exception as e:
    error_message = f"Lỗi khi gửi request API: {e}"
    log_error("Storelist_Pharmacity.py", error_message)
    raise

# Truy cập đúng vào danh sách cửa hàng
try:
    data = res.json()
    items = data.get('data', {}).get('items', [])
    print(f"🔍 Tổng số cửa hàng SEO stores: {len(items)} mục")
except Exception as e:
    error_message = f"Lỗi khi parse JSON: {e}"
    log_error("Storelist_Pharmacity.py", error_message)
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
    except Exception as e:
        error_message = f"Lỗi khi xử lý cửa hàng: {e}"
        log_error("Storelist_Pharmacity.py", error_message)
        continue

# Export ra XLSX
try:
    df = pd.DataFrame(store_list, columns=[
        'Tên cửa hàng', 'Địa chỉ', 'Tỉnh', 'Quận/Huyện', 'Phường/Xã',
        'Vĩ độ', 'Kinh độ', 'Google Maps', 'Giờ mở cửa', 'Giờ đóng cửa',
        'SĐT', 'Zalo URL'
    ])
    df.to_excel('pharmacity_all_stores.xlsx', index=False, engine='openpyxl')
    print(f"Đã lưu {len(store_list)} cửa hàng vào pharmacity_all_stores.xlsx")
except Exception as e:
    error_message = f"Lỗi khi lưu file pharmacity_all_stores.xlsx: {e}"
    log_error("Storelist_Pharmacity.py", error_message)
    raise