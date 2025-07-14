import pandas as pd
import re
from unidecode import unidecode
import openpyxl
from datetime import datetime

input_files = [
    {"file": "ankhang_stores.xlsx", "brand": "AnKhang"},
    {"file": "bachhoaxanh_stores.xlsx", "brand": "BachHoaXanh"},
    {"file": "bsmart_stores.xlsx", "brand": "BSmart"},
    {"file": "concung_stores.xlsx", "brand": "ConCung"},
    {"file": "longchau_all_addresses.xlsx", "brand": "LongChau"},
    {"file": "pharmacity_all_stores.xlsx", "brand": "Pharmacity"},
    {"file": "winmart_stores_full.xlsx", "brand": "WinMart"}
]

# Hàm chuẩn hóa tên tỉnh/thành phố
def normalize_city(city):
    # Xóa "Tỉnh", "Thành phố", "TP.", "T."
    city = re.sub(r'^(Tỉnh|Thành phố|TP\.|T\.) ', '', city.strip())
    # Chuyển thành in hoa không dấu
    city = unidecode(city).upper()
    # 
    city = city.replace('-', ' ')
    return city.strip()

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

# Hàm đọc dữ liệu từ file XLSX
def read_file(file_path):
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        headers = df.columns.tolist()
        data = df.values.tolist()
        return headers, data
    except Exception as e:
        error_message = f"Lỗi khi đọc file {file_path}: {e}"
        log_error("Storelist_combine.py", error_message)
        raise


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
                try:
                    city = normalize_city(str(row[0]))  # Tỉnh, chuyển thành str để tránh lỗi None
                    address = str(row[2]).strip()  # Địa Chỉ, chuyển thành str
                    combined_data.append([address, city, brand])
                except Exception as e:
                    error_message = f"Lỗi khi xử lý dòng trong {file_path}: {e}"
                    log_error("Storelist_combine.py", error_message)
                    continue

        elif "bachhoaxanh_stores" in file_path:
            # ["Tên Cửa Hàng", "Địa Chỉ", "Tỉnh/Thành Phố"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = str(row[1]).strip()  # Địa Chỉ, chuyển thành str
                    city = normalize_city(str(row[2]))  # Tỉnh/Thành Phố, chuyển thành str
                    combined_data.append([address, city, brand])
                except Exception as e:
                    error_message = f"Lỗi khi xử lý dòng trong {file_path}: {e}"
                    log_error("Storelist_combine.py", error_message)
                    continue

        elif "bsmart_stores" in file_path:
            # ["Quận/Huyện", "Địa chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = str(row[1]).strip()  # Địa chỉ, chuyển thành str
                    city = "HO CHI MINH"  # Gán cố định
                    combined_data.append([address, city, brand])
                except Exception as e:
                    error_message = f"Lỗi khi xử lý dòng trong {file_path}: {e}"
                    log_error("Storelist_combine.py", error_message)
                    continue

        elif "concung_stores" in file_path:
            # ["Tỉnh", "Quận/Huyện", "Xã/Phường", "Địa Chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    city = normalize_city(str(row[0]))  # Tỉnh, chuyển thành str
                    address = re.sub(r' - Giờ:.*$', '', str(row[3]).strip())  # Địa Chỉ, xóa phần "- Giờ:..."
                    combined_data.append([address, city, brand])
                except Exception as e:
                    error_message = f"Lỗi khi xử lý dòng trong {file_path}: {e}"
                    log_error("Storelist_combine.py", error_message)
                    continue

        elif "longchau_all_addresses" in file_path:
            # ["STT", "Tỉnh/Thành", "Địa chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    city = normalize_city(str(row[1]))  # Tỉnh/Thành, chuyển thành str
                    address = str(row[2]).strip()  # Địa chỉ, chuyển thành str
                    combined_data.append([address, city, brand])
                except Exception as e:
                    error_message = f"Lỗi khi xử lý dòng trong {file_path}: {e}"
                    log_error("Storelist_combine.py", error_message)
                    continue

        elif "pharmacity_all_stores" in file_path:
            # ["Tên cửa hàng", "Địa chỉ", "Tỉnh", "Quận/Huyện", ...] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = f"{str(row[1]).strip()}, {str(row[3]).strip()}, {str(row[2]).strip()}"  # Gộp Địa chỉ + Quận/Huyện + Tỉnh
                    city = normalize_city(str(row[2]))  # Tỉnh, chuyển thành str
                    combined_data.append([address, city, brand])
                except Exception as e:
                    error_message = f"Lỗi khi xử lý dòng trong {file_path}: {e}"
                    log_error("Storelist_combine.py", error_message)
                    continue

        elif "winmart_stores_full" in file_path:
            # ["Tên cửa hàng", "Địa chỉ", "Tỉnh", "Quận/Huyện", ...] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = str(row[1]).strip()  # Địa chỉ, chuyển thành str
                    city = normalize_city(str(row[2]))  # Tỉnh, chuyển thành str
                    combined_data.append([address, city, brand])
                except Exception as e:
                    error_message = f"Lỗi khi xử lý dòng trong {file_path}: {e}"
                    log_error("Storelist_combine.py", error_message)
                    continue

        print(f"Đã xử lý {len(data)} dòng từ {file_path}")

    except FileNotFoundError:
        error_message = f"Không tìm thấy file {file_path}, bỏ qua..."
        log_error("Storelist_combine.py", error_message)
        continue
    except Exception as e:
        error_message = f"Lỗi khi xử lý file {file_path}: {e}"
        log_error("Storelist_combine.py", error_message)
        continue

# Lưu file hợp nhất
output_file = "Storelist_combine.xlsx"
try:
    df = pd.DataFrame(combined_data, columns=["ADDRESS", "CITY", "BRAND_STORE"])
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\nĐã lưu {len(combined_data)} dòng vào {output_file}")
except Exception as e:

    error_message = f"Lỗi khi lưu file {output_file}: {e}"
    log_error("Storelist_combine.py", error_message)
    raise
