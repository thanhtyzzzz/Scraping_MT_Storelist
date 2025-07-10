import requests
import csv
import time

# Gọi API lấy danh sách tỉnh/thành
url_provinces = 'https://api-crownx.winmart.vn/mt/api/web/v1/provinces/all-winmart'
res = requests.get(url_provinces)
provinces_data = res.json()

store_list = []

# Duyệt từng tỉnh/thành
for province in provinces_data['data']:
    province_code = province.get('code')
    province_name = province.get('description')
    print(f'Đang xử lý: {province_name} ({province_code})')

    # Gọi API lấy cửa hàng theo tỉnh
    url = f'https://api-crownx.winmart.vn/mt/api/web/v1/store-by-province?PageNumber=1&PageSize=1000&ProvinceCode={province_code}'
    res_store = requests.get(url)
    store_data = res_store.json().get('data', [])

    # Lấy danh sách cửa hàng
    for district in store_data:
        for ward in district.get('wardStores', []):
            for store in ward.get('stores', []):
                store_list.append([
                    store.get('storeName', ''),
                    store.get('officeAddress', ''),
                    store.get('provinceName', ''),
                    store.get('districtName', ''),
                    store.get('wardName', ''),
                    store.get('activeStatus', '')
                ])

    time.sleep(0.3)  

# Export ra CSV
with open('winmart_stores_full.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Tên cửa hàng', 'Địa chỉ', 'Tỉnh', 'Quận/Huyện', 'Phường/Xã', 'Trạng thái'])
    writer.writerows(store_list)

print(f'Đã lấy {len(store_list)} cửa hàng và lưu vào winmart_stores_full.csv')
