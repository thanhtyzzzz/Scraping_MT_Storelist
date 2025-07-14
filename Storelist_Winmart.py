import requests
import pandas as pd
import time
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
    url_provinces = 'https://api-crownx.winmart.vn/mt/api/web/v1/provinces/all-winmart'
    res = requests.get(url_provinces)
    res.raise_for_status()
    provinces_data = res.json()
except Exception as e:
    error_message = f"Lỗi khi gọi API tỉnh/thành: {e}"
    log_error("Storelist_WinMart.py", error_message)
    raise

store_list = []

# Duyệt từng tỉnh/thành
for province in provinces_data['data']:
    province_code = province.get('code')
    province_name = province.get('description')
    print(f'Đang xử lý: {province_name} ({province_code})')

    # Gọi API lấy cửa hàng theo tỉnh
    try:
        url = f'https://api-crownx.winmart.vn/mt/api/web/v1/store-by-province?PageNumber=1&PageSize=1000&ProvinceCode={province_code}'
        res_store = requests.get(url)
        res_store.raise_for_status()
        store_data = res_store.json().get('data', [])
    except Exception as e:
        error_message = f"Lỗi khi gọi API cửa hàng cho tỉnh {province_name}: {e}"
        log_error("Storelist_WinMart.py", error_message)
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
                except Exception as e:
                    error_message = f"Lỗi khi xử lý cửa hàng tại {province_name}: {e}"
                    log_error("Storelist_WinMart.py", error_message)
                    continue

    time.sleep(0.3)

# Export ra XLSX
try:
    df = pd.DataFrame(store_list, columns=['Tên cửa hàng', 'Địa chỉ', 'Tỉnh', 'Quận/Huyện', 'Phường/Xã', 'Trạng thái'])
    df.to_excel('winmart_stores_full.xlsx', index=False, engine='openpyxl')
    print(f'Đã lấy {len(store_list)} cửa hàng và lưu vào winmart_stores_full.xlsx')
except Exception as e:
    error_message = f"Lỗi khi lưu file winmart_stores_full.xlsx: {e}"
    log_error("Storelist_WinMart.py", error_message)
    raise