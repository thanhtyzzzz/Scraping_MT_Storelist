import requests
import csv

# API endpoint
url = 'https://api-gateway.pharmacity.vn/api/v1/seo_stores'
res = requests.get(url)
res.raise_for_status()

# Truy cập đúng vào danh sách cửa hàng
data = res.json()
items = data.get('data', {}).get('items', [])

print(f"🔍 Tổng số cửa hàng SEO stores: {len(items)} mục")

# Danh sách lưu trữ kết quả
store_list = []

# Lặp từng cửa hàng
for store in items:
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

# Ghi ra CSV (chuẩn Excel, không lỗi font)
with open('pharmacity_all_stores.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow([
        'Tên cửa hàng', 'Địa chỉ', 'Tỉnh', 'Quận/Huyện', 'Phường/Xã',
        'Vĩ độ', 'Kinh độ', 'Google Maps', 'Giờ mở cửa', 'Giờ đóng cửa',
        'SĐT', 'Zalo URL'
    ])
    writer.writerows(store_list)

print(f"✅ Đã lưu {len(store_list)} cửa hàng vào pharmacity_all_stores.csv")
