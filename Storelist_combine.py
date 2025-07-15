import pandas as pd
import re
from unidecode import unidecode
import sqlite3
from datetime import datetime

# Danh sách file input và thông tin Brand store
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
    # Giữ nguyên dấu gạch ngang
    return city.strip()

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
        log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi ghi log vào {log_file}: {e}")
    finally:
        conn.close()

# Hàm đọc dữ liệu từ file XLSX
def read_file(file_path):
    log_to_sqlite("Storelist_combine.py", "Pending", f"Bắt đầu đọc file {file_path}")
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        headers = df.columns.tolist()
        data = df.values.tolist()
        log_to_sqlite("Storelist_combine.py", "Succeeded", f"Đọc thành công file {file_path}")
        return headers, data
    except Exception as e:
        log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi đọc file {file_path}: {e}")
        raise

# Hàm tạo bảng SQLite và lưu dữ liệu
def save_to_sqlite(combined_data):
    log_to_sqlite("Storelist_combine.py", "Pending", "Bắt đầu lưu dữ liệu vào SQLite")
    try:
        # Kết nối SQLite
        conn = sqlite3.connect("storelist_combine.db")
        cursor = conn.cursor()
        
        # Tạo bảng stores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT,
                city TEXT,
                brand_store TEXT
            )
        ''')
        
        # Lưu dữ liệu
        cursor.executemany('''
            INSERT INTO stores (address, city, brand_store)
            VALUES (?, ?, ?)
        ''', combined_data)
        
        conn.commit()
        log_to_sqlite("Storelist_combine.py", "Succeeded", f"Lưu thành công {len(combined_data)} dòng vào SQLite database")
    except Exception as e:
        log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi lưu vào SQLite: {e}")
        raise
    finally:
        conn.close()

# Danh sách lưu trữ dữ liệu hợp nhất
combined_data = []

# Xử lý từng file
for input_file in input_files:
    file_path = input_file["file"]
    brand = input_file["brand"]
    print(f"Đang xử lý file: {file_path}")
    log_to_sqlite("Storelist_combine.py", "Pending", f"Bắt đầu xử lý file {file_path}")

    try:
        headers, data = read_file(file_path)

        if "ankhang_stores" in file_path:
            # ["Tỉnh", "Tên Nhà Thuốc", "Địa Chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    city = normalize_city(str(row[0]))  # Tỉnh
                    address = str(row[2]).strip()  # Địa Chỉ
                    combined_data.append([address, city, brand])
                    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Xử lý dòng trong {file_path}: {address}")
                except Exception as e:
                    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý dòng trong {file_path}: {e}")
                    continue

        elif "bachhoaxanh_stores" in file_path:
            # ["Tên Cửa Hàng", "Địa Chỉ", "Tỉnh/Thành Phố"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = str(row[1]).strip()  # Địa Chỉ
                    city = normalize_city(str(row[2]))  # Tỉnh/Thành Phố
                    combined_data.append([address, city, brand])
                    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Xử lý dòng trong {file_path}: {address}")
                except Exception as e:
                    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý dòng trong {file_path}: {e}")
                    continue

        elif "bsmart_stores" in file_path:
            # ["Quận/Huyện", "Địa chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = str(row[1]).strip()  # Địa chỉ
                    city = "HO CHI MINH"  # Gán cố định
                    combined_data.append([address, city, brand])
                    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Xử lý dòng trong {file_path}: {address}")
                except Exception as e:
                    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý dòng trong {file_path}: {e}")
                    continue

        elif "concung_stores" in file_path:
            # ["Tỉnh", "Quận/Huyện", "Xã/Phường", "Địa Chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    city = normalize_city(str(row[0]))  # Tỉnh
                    address = re.sub(r' - Giờ:.*$', '', str(row[3]).strip())  # Địa Chỉ, xóa phần "- Giờ:..."
                    combined_data.append([address, city, brand])
                    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Xử lý dòng trong {file_path}: {address}")
                except Exception as e:
                    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý18:49:34, 4/12/2023.000000", f"Lỗi khi xử lý dòng trong {file_path}: {e}")
                    continue

        elif "longchau_all_addresses" in file_path:
            # ["STT", "Tỉnh/Thành", "Địa chỉ"] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    city = normalize_city(str(row[1]))  # Tỉnh/Thành
                    address = str(row[2]).strip()  # Địa chỉ
                    combined_data.append([address, city, brand])
                    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Xử lý dòng trong {file_path}: {address}")
                except Exception as e:
                    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý dòng trong {file_path}: {e}")
                    continue

        elif "pharmacity_all_stores" in file_path:
            # ["Tên cửa hàng", "Địa chỉ", "Tỉnh", "Quận/Huyện", ...] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = f"{str(row[1]).strip()}, {str(row[3]).strip()}, {str(row[2]).strip()}"  # Gộp Địa chỉ + Quận/Huyện + Tỉnh
                    city = normalize_city(str(row[2]))  # Tỉnh
                    combined_data.append([address, city, brand])
                    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Xử lý dòng trong {file_path}: {address}")
                except Exception as e:
                    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý dòng trong {file_path}: {e}")
                    continue

        elif "winmart_stores_full" in file_path:
            # ["Tên cửa hàng", "Địa chỉ", "Tỉnh", "Quận/Huyện", ...] -> ["ADDRESS", "CITY", "BRAND_STORE"]
            for row in data:
                try:
                    address = str(row[1]).strip()  # Địa chỉ
                    city = normalize_city(str(row[2]))  # Tỉnh
                    combined_data.append([address, city, brand])
                    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Xử lý dòng trong {file_path}: {address}")
                except Exception as e:
                    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý dòng trong {file_path}: {e}")
                    continue

        print(f"Đã xử lý {len(data)} dòng từ {file_path}")
        log_to_sqlite("Storelist_combine.py", "Succeeded", f"Đã xử lý {len(data)} dòng từ {file_path}")

    except FileNotFoundError:
        log_to_sqlite("Storelist_combine.py", "Failed", f"Không tìm thấy file {file_path}, bỏ qua...")
        continue
    except Exception as e:
        log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi xử lý file {file_path}: {e}")
        continue

# Lưu file hợp nhất vào Excel
output_file = "Storelist_combine.xlsx"
log_to_sqlite("Storelist_combine.py", "Pending", f"Bắt đầu lưu dữ liệu vào {output_file}")
try:
    df = pd.DataFrame(combined_data, columns=["ADDRESS", "CITY", "BRAND_STORE"])
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\nĐã lưu {len(combined_data)} dòng vào {output_file}")
    log_to_sqlite("Storelist_combine.py", "Succeeded", f"Đã lưu {len(combined_data)} dòng vào {output_file}")
except Exception as e:
    log_to_sqlite("Storelist_combine.py", "Failed", f"Lỗi khi lưu file {output_file}: {e}")
    raise

# Lưu dữ liệu vào SQLite
save_to_sqlite(combined_data)