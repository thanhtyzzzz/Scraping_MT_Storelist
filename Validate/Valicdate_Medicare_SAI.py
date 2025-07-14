import pandas as pd
import re
import unicodedata

# Hàm bỏ dấu + in hoa
def remove_accents_upper(text):
    if pd.isna(text):
        return ''
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).upper()

# Hàm tách tên Tỉnh/Thành phố từ địa chỉ
def extract_city_province(address):
    if pd.isna(address):
        return ''
    
    # Ưu tiên tìm "Tỉnh ..." và "Thành phố ..." từ cuối địa chỉ
    patterns = [
        r'(Tỉnh)\s+([A-Za-zÀ-Ỵà-ỹ\s\.\-]+)',
        r'(Thành phố|TP\.?)\s+([A-Za-zÀ-Ỵà-ỹ\s\.\-]+)',
    ]
    
    for pattern in reversed(patterns):  # Ưu tiên tỉnh nếu đứng sau
        matches = re.findall(pattern, address)
        if matches:
            last_match = matches[-1][1]
            return remove_accents_upper(last_match)
    
    return ''

# === BƯỚC 1: Đọc file Excel ===
df = pd.read_excel('Medicare_Storelist.xlsx') 

# === BƯỚC 2: Tạo cột CITY ===
df['CITY'] = df['ADDRESS'].apply(extract_city_province)

# === BƯỚC 3: Ghi lại file Excel mới ===
df.to_excel('Medicare_Storelist_final.xlsx', index=False)

print("✅ Đã xử lý xong. File mới: output_with_city.xlsx")
