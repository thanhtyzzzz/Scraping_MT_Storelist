import csv
import re
from unidecode import unidecode
import openpyxl
import os

# Danh sách file input và thông tin thương hiệu
input_files = [
    {"file": "ankhang_stores.xlsx", "brand": "AnKhang"},
    {"file": "bachhoaxanh_stores.csv", "brand": "BachHoaXanh"},
    {"file": "bsmart_stores.csv", "brand": "BSmart"},
    {"file": "concung_stores.csv", "brand": "ConCung"},
    {"file": "longchau_all_addresses.csv", "brand": "LongChau"},
    {"file": "pharmacity_all_stores.csv", "brand": "Pharmacity"},
    {"file": "winmart_stores_full.csv", "brand": "WinMart"}
]

# Hàm chuẩn hóa tên tỉnh/thành phố
def normalize_city(city):
    # Xóa "Tỉnh", "Thành phố", "TP.", "T."
    city = re.sub(r'^(Tỉnh|Thành phố|TP\.|T\.) ', '', city.strip())
    # Chuyển thành in hoa không dấu
    city = unidecode(city).upper()
    # Thay dấu gạch ngang bằng khoảng trắng
    city = city.replace('-', ' ')
    return city.strip()

# Hàm đọc dữ liệu từ file (CSV hoặc XLSX)
def read_file(file_path):
    if file_path.endswith('.csv'):
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Lấy header
            data = list(reader)
        return headers, data
    elif file_path.endswith('.xlsx'):
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        data = []
        headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
        for row in sheet.iter_rows(min_row=2):
            data.append([cell.value if cell.value is not None else '' for cell in row])
        return headers, data
    else:
        raise ValueError(f"Định dạng file không hỗ trợ: {file_path}")

# Danh sách lưu trữ dữ liệu hợp nhất
combined_data = []

# Xử lý từng file
for input_file in input_files:
    file_path = input_file["file"]
    brand = input_file["brand"]
    print(f"Đang xử lý file: {file_path}")

    try:
        headers, data = read_file(file_path)

        if "ankhang_stores" in file_path:
            # ["Tỉnh", "Tên Nhà Thuốc", "Địa Chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                city = normalize_city(row[0])  # Tỉnh
                address = row[2].strip()  # Địa Chỉ
                combined_data.append([address, city, brand])

        elif "bachhoaxanh_stores" in file_path:
            # ["Tên Cửa Hàng", "Địa Chỉ", "Tỉnh/Thành Phố"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                address = row[1].strip()  # Địa Chỉ
                city = normalize_city(row[2])  # Tỉnh/Thành Phố
                combined_data.append([address, city, brand])

        elif "bsmart_stores" in file_path:
            # ["Quận/Huyện", "Địa chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                address = row[1].strip()  # Địa chỉ
                city = "HO CHI MINH"  # Gán cố định
                combined_data.append([address, city, brand])

        elif "concung_stores" in file_path:
            # ["Tỉnh", "Quận/Huyện", "Xã/Phường", "Địa Chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                city = normalize_city(row[0])  # Tỉnh
                address = re.sub(r' - Giờ:.*$', '', row[3].strip())  # Địa Chỉ, xóa phần "- Giờ:..."
                combined_data.append([address, city, brand])

        elif "longchau_all_addresses" in file_path:
            # ["STT", "Tỉnh/Thành", "Địa chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                city = normalize_city(row[1])  # Tỉnh/Thành
                address = row[2].strip()  # Địa chỉ
                combined_data.append([address, city, brand])

        elif "pharmacity_all_stores" in file_path:
            # ["Tên cửa hàng", "Địa chỉ", "Tỉnh", "Quận/Huyện", ...] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                address = f"{row[1].strip()}, {row[3].strip()}, {row[2].strip()}"  # Gộp Địa chỉ + Quận/Huyện + Tỉnh
                city = normalize_city(row[2])  # Tỉnh
                combined_data.append([address, city, brand])

        elif "winmart_stores_full" in file_path:
            # ["Tên cửa hàng", "Địa chỉ", "Tỉnh", "Quận/Huyện", ...] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                address = row[1].strip()  # Địa chỉ
                city = normalize_city(row[2])  # Tỉnh
                combined_data.append([address, city, brand])

        print(f"Đã xử lý {len(data)} dòng từ {file_path}")

    except FileNotFoundError:
        print(f"Không tìm thấy file {file_path}, bỏ qua...")
        continue
    except Exception as e:
        print(f"Lỗi khi xử lý file {file_path}: {e}")
        continue

# Lưu file hợp nhất
output_file = "Storelist_combine.csv"
try:
    with open(output_file, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ADDRESS", "CITY", "BRAND_STORE"])
        writer.writerows(combined_data)
    print(f"\nĐã lưu {len(combined_data)} dòng vào {output_file}")
except Exception as e:
    print(f"Lỗi khi lưu file {output_file}: {e}")