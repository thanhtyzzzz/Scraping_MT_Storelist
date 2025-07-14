import pandas as pd
import unicodedata

# Hàm loại bỏ dấu + in hoa
def remove_accents_upper(text):
    if pd.isna(text):
        return ''
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).upper()

# Hàm lấy phần sau dấu phẩy cuối cùng (Tỉnh/TP)
def extract_city_from_address(address):
    if pd.isna(address):
        return ''
    parts = address.split(',')
    last_part = parts[-1].strip()
    return remove_accents_upper(last_part)

# === Đọc file Excel ===
df = pd.read_excel('Hasaki_Storelist.xlsx')  

# === Tạo cột CITY từ ADDRESS ===
df['CITY'] = df['ADDRESS'].apply(extract_city_from_address)

# === Ghi ra file mới ===
df.to_excel('Hasaki_Storelist_final.xlsx', index=False)

print("✅ Đã tạo cột CITY từ ADDRESS và lưu file mới: Hasaki_Storelist_final.xlsx")
