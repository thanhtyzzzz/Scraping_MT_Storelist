import pandas as pd
import unicodedata

# Hàm bỏ dấu và in hoa
def remove_accents_upper(text):
    if pd.isna(text):
        return ''
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).upper()

# Hàm lấy phần sau dấu phẩy cuối cùng
def extract_city(address):
    if pd.isna(address):
        return ''
    parts = address.split(',')
    last_part = parts[-1].strip()
    return remove_accents_upper(last_part)

# === Đọc file Excel ===
df = pd.read_excel('CPFreshShop_Storelist.xlsx')  

# === Tạo cột CITY từ cột ADDRESS ===
df['CITY'] = df['ADDRESS'].apply(extract_city)

# === Ghi file mới ===
df.to_excel('CPFreshShop_Storelist_1.xlsx', index=False)

print("✅ Đã xử lý xong. File mới: KidsPlaza_Storelist_1.xlsx")
