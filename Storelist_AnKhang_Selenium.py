from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import re
import openpyxl
from datetime import datetime

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

# Khởi tạo driver
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=Service(), options=chrome_options)

try:
    url = "https://www.nhathuocankhang.com/he-thong-nha-thuoc"
    driver.get(url)

    # Đợi danh sách tỉnh
    try:
        WebDriverWait(driver, 40).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".opt-tinhthanh span"))
        )
    except Exception as e:
        error_message = f"Lỗi khi chờ danh sách tỉnh: {e}"
        log_error("Storelist_AnKhang_Selenium.py", error_message)
        raise

    # Lấy danh sách tỉnh
    province_elements = driver.find_elements(By.CSS_SELECTOR, ".opt-tinhthanh span")
    province_names = []
    for i, elem in enumerate(province_elements):
        try:
            name = elem.text.strip()
            if not name:
                name = elem.get_attribute("innerText").strip()
            if not name:
                name = elem.get_attribute("textContent").strip()
            if not name:
                name = f"Tỉnh thứ {i + 1}"
            province_names.append(name)
        except Exception as e:
            error_message = f"Lỗi khi lấy tên tỉnh thứ {i + 1}: {e}"
            log_error("Storelist_AnKhang_Selenium.py", error_message)
    
    print(f"📋 Tìm thấy {len(province_names)} tỉnh/thành")

    results = []

    # Duyệt từng tỉnh
    for i, province_name in enumerate(province_names):
        driver.get(url)
        try:
            WebDriverWait(driver, 40).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".opt-tinhthanh span"))
            )
        except Exception as e:
            error_message = f"Lỗi khi làm mới trang cho tỉnh {province_name}: {e}"
            log_error("Storelist_AnKhang_Selenium.py", error_message)
            continue

        province_elements = driver.find_elements(By.CSS_SELECTOR, ".opt-tinhthanh span")
        if len(province_elements) != len(province_names):
            error_message = f"Số lượng tỉnh không khớp: {len(province_elements)} vs {len(province_names)}"
            log_error("Storelist_AnKhang_Selenium.py", error_message)
            continue

        province_elem = province_elements[i]
        print(f"Đang xử lý tỉnh: {province_name}")

        # Thử click tỉnh với retry
        retry_count = 5
        click_success = False
        for attempt in range(retry_count):
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", province_elem)
                driver.execute_script("arguments[0].click();", province_elem)
                WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.listing-store.zl-list li, .no-results, .empty-message, [class*='no-store'], [class*='empty'], [class*='error'], [class*='no-data']"))
                )
                click_success = True
                break
            except Exception as e:
                error_message = f"Lỗi click tỉnh {province_name} (lần {attempt + 1}): {e}"
                log_error("Storelist_AnKhang_Selenium.py", error_message)
                if attempt == retry_count - 1:
                    error_message = f"Bỏ qua tỉnh {province_name} sau {retry_count} lần thử"
                    log_error("Storelist_AnKhang_Selenium.py", error_message)
                    break
                time.sleep(3)

        if not click_success:
            continue  

        # Cehck xem có Store không
        no_store_message = driver.find_elements(By.CSS_SELECTOR, ".no-results, .empty-message, [class*='no-store'], [class*='empty'], [class*='error'], [class*='no-data']")
        if no_store_message:
            error_message = f"Tỉnh {province_name} không có nhà thuốc (thông báo: {no_store_message[0].text})"
            log_error("Storelist_AnKhang_Selenium.py", error_message)
            continue

        # Bấm load more nhiều lần
        see_more_attempts = 0
        max_attempts = 20
        while see_more_attempts < max_attempts:
            try:
                prev_count = len(driver.find_elements(By.CSS_SELECTOR, "ul.listing-store.zl-list li"))
                see_more = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.seemore"))
                )
                see_more_text = see_more.get_attribute("innerHTML")
                remaining_stores = re.search(r'Xem thêm <b>(\d+)</b> nhà thuốc', see_more_text)
                if remaining_stores:
                    print(f"Nút 'Xem thêm' tại {province_name} còn {remaining_stores.group(1)} nhà thuốc")
                
                driver.execute_script("arguments[0].scrollIntoView(true);", see_more)
                driver.execute_script("arguments[0].click();", see_more)
                see_more_attempts += 1
                WebDriverWait(driver, 30).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "ul.listing-store.zl-list li")) > prev_count
                )
                current_count = len(driver.find_elements(By.CSS_SELECTOR, "ul.listing-store.zl-list li"))
                print(f"Nhấn 'Xem thêm' lần {see_more_attempts} tại {province_name}, hiện có {current_count} nhà thuốc")
                time.sleep(1)
            except Exception as e:
                error_message = f"Kết thúc nhấn 'Xem thêm' tại {province_name} sau {see_more_attempts} lần: {e}"
                log_error("Storelist_AnKhang_Selenium.py", error_message)
                break

        # Lấy danh sách Store
        store_items = driver.find_elements(By.CSS_SELECTOR, "ul.listing-store.zl-list li")
        store_count = 0
        for item in store_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, ".txt-shortname").text.strip()
                address = item.find_element(By.CSS_SELECTOR, ".txtl").text.strip()
                if name and address:
                    results.append([province_name, name, address])
                    store_count += 1
            except Exception as e:
                error_message = f"Lỗi khi lấy thông tin nhà thuốc tại {province_name}: {e}"
                log_error("Storelist_AnKhang_Selenium.py", error_message)
                continue

        print(f"Đã lấy {store_count} nhà thuốc tại {province_name}")

    # Lưu kết quả ra XLSX
    try:
        df = pd.DataFrame(results, columns=["Tỉnh", "Tên Nhà Thuốc", "Địa Chỉ"])
        df.to_excel("ankhang_stores.xlsx", index=False, engine='openpyxl')
        print(f"Đã lưu {len(results)} nhà thuốc vào ankhang_stores.xlsx")
    except Exception as e:
        error_message = f"Lỗi khi lưu file ankhang_stores.xlsx: {e}"
        log_error("Storelist_AnKhang_Selenium.py", error_message)
        raise

finally:
    driver.quit()