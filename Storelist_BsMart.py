import requests
from bs4 import BeautifulSoup
import csv

# Gửi request để lấy trang HTML
URL = 'https://sieuthibsmart.com/he-thong-b-smart/'
res = requests.get(URL)
res.raise_for_status()

# Parse HTML với BeautifulSoup
soup = BeautifulSoup(res.text, 'html.parser')

# Chọn tất cả các khối "accordion-item" đại diện cho mỗi Quận/Huyện
district_blocks = soup.select('.accordion-item')

stores = []

for block in district_blocks:
    # Lấy tên quận/huyện từ phần <span> trong tiêu đề accordion
    title = block.select_one('a.accordion-title span')
    if not title:
        continue
    district_name = title.text.strip()

    # Lấy phần chứa địa chỉ (các <p>) bên trong div.accordion-inner
    inner = block.select_one('.accordion-inner')
    if not inner:
        continue

    address_tags = inner.find_all('p')
    for p in address_tags:
        addr = p.text.strip()
        if addr:
            stores.append([district_name, addr])

# Export dữ liệu ra file CSV 
with open('bsmart_stores.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['Quận/Huyện', 'Địa chỉ'])
    writer.writerows(stores)

print(f"Đã thu được {len(stores)} cửa hàng và lưu vào bsmart_stores.csv")
