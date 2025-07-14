import pandas as pd
from unidecode import unidecode

# ====== PHIÊN BẢN ĐỌC FILE CSV ======
# Đường dẫn file CSV đầu vào
file_path = 'longchau_all_addresses.csv'

# Đọc file CSV (KHÔNG cần engine)
try:
    df = pd.read_csv(file_path)
    print(f"✅ Đọc file CSV thành công: {file_path}")
except Exception as e:
    print(f"⛔ Lỗi khi đọc file CSV: {e}")
    exit()

# ====== (BẠN CÓ THỂ DÙNG PHIÊN BẢN NÀY ĐỂ ĐỌC FILE EXCEL: .xlsx) ======
# file_path = 'longchau_all_addresses.xlsx'
# try:
#     df = pd.read_excel(file_path, engine='openpyxl')
#     print(f"✅ Đọc file Excel thành công: {file_path}")
# except Exception as e:
#     print(f"⛔ Lỗi khi đọc file Excel: {e}")
#     exit()

# Hàm chuyển tên tỉnh thành in hoa, không dấu
def convert_city_name(city):
    if pd.isna(city):
        return ''
    return unidecode(str(city)).upper()

# Tạo cột CITY từ cột TINH
if 'TINH' not in df.columns:
    print("⛔ Không tìm thấy cột 'TINH' trong dữ liệu.")
    exit()

df['CITY'] = df['TINH'].apply(convert_city_name)

# Xuất ra file Excel mới
output_path = 'longchau_all_addresses_1.xlsx'
df.to_excel(output_path, index=False, engine='openpyxl')
print(f"✅ Đã tạo file Excel: {output_path}")
