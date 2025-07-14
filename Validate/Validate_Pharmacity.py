import pandas as pd
import unicodedata

# Hàm loại bỏ dấu tiếng Việt và chuyển thành in hoa
def remove_accents_upper(text):
    if pd.isna(text):
        return ''
    nfkd_form = unicodedata.normalize('NFKD', text)
    no_accent = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    return no_accent.upper()

# Đọc dữ liệu từ file (ví dụ 'data.xlsx' hoặc 'data.csv')
df = pd.read_csv('Pharmacity_Storelist.csv', encoding='utf-8')

# Thêm cột CITY (không dấu + in hoa)
df['CITY'] = df['CITY_1'].apply(remove_accents_upper)

# Ghi lại file (tuỳ bạn muốn Excel hay CSV)
df.to_excel('Pharmacity_Storelist_final.xlsx', index=False)  
