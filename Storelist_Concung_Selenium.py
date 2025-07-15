from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import sqlite3
from datetime import datetime

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
    finally:
        conn.close()

# Khởi tạo driver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    url = "https://concung.com/tim-sieu-thi.html?srsltid=AfmBOorRe18HD45B1Oq9e7yNAzKJBopKdDjoO1vOHTVHrpJnQN5YFLzt"
    log_to_sqlite("ConCung.py", "Pending", f"Bắt đầu truy cập {url}")
    driver.get(url)

    try:
        close_popup = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='close'], button[class*='accept'], div[class*='popup'] button"))
        )
        driver.execute_script("arguments[0].click();", close_popup)
        log_to_sqlite("ConCung.py", "Succeeded", "Đã đóng pop-up hoặc dialog đồng ý")
    except Exception as e:
        log_to_sqlite("ConCung.py", "Failed", f"Không tìm thấy pop-up, tiếp tục...: {e}")

    try:
        choose_area = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.d-inline-flex[onclick*='unit-choosed']"))
        )
        driver.execute_script("arguments[0].click();", choose_area)
        log_to_sqlite("ConCung.py", "Succeeded", "Đã kích hoạt chọn khu vực")
    except Exception as e:
        log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi kích hoạt chọn khu vực: {e}")
        raise

    province_trigger = WebDriverWait(driver, 40).until(
        EC.element_to_be_clickable((By.ID, "province_home"))
    )
    driver.execute_script("arguments[0].click();", province_trigger)
    time.sleep(2)
    log_to_sqlite("ConCung.py", "Succeeded", "Mở dropdown tỉnh thành công")

    try:
        province_options = WebDriverWait(driver, 40).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#group-select-unit .item-address-main"))
        )
        provinces = [(opt.find_element(By.CSS_SELECTOR, "span.font-14").text, opt.get_attribute("id")) for opt in province_options]
        print(f"Tìm thấy {len(provinces)} tỉnh/thành: {provinces}")
        log_to_sqlite("ConCung.py", "Succeeded", f"Tìm thấy {len(provinces)} tỉnh/thành")
    except Exception as e:
        log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi lấy danh sách tỉnh: {e}")
        raise

    results = []

    for province_name, province_id in provinces:
        log_to_sqlite("ConCung.py", "Pending", f"Bắt đầu xử lý tỉnh: {province_name}")
        try:
            province_trigger = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, "province_home"))
            )
            driver.execute_script("arguments[0].click();", province_trigger)
            province_elem = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, province_id))
            )
            driver.execute_script("arguments[0].click();", province_elem)
            print(f"Đang xử lý tỉnh: {province_name}")
            log_to_sqlite("ConCung.py", "Succeeded", f"Chọn tỉnh {province_name} thành công")
            time.sleep(2)
        except Exception as e:
            log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi chọn tỉnh {province_name}: {e}")
            continue

        try:
            district_trigger = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, "district_home"))
            )
            driver.execute_script("arguments[0].click();", district_trigger)
            time.sleep(3)
            district_options = WebDriverWait(driver, 40).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#group-select-unit .item-address-main"))
            )
            districts = [(opt.find_element(By.CSS_SELECTOR, "span.font-14").text, opt.get_attribute("id")) for opt in district_options]
            if not districts:
                log_to_sqlite("ConCung.py", "Failed", f"Không tìm thấy quận/huyện tại {province_name}, có thể không có dữ liệu")
            else:
                print(f"Tìm thấy {len(districts)} quận/huyện: {districts}")
                log_to_sqlite("ConCung.py", "Succeeded", f"Tìm thấy {len(districts)} quận/huyện tại {province_name}")
        except Exception as e:
            log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi lấy quận/huyện tại {province_name}: {e}")
            districts = []

        for district_name, district_id in districts:
            log_to_sqlite("ConCung.py", "Pending", f"Bắt đầu xử lý quận/huyện: {district_name}")
            try:
                district_trigger = WebDriverWait(driver, 40).until(
                    EC.element_to_be_clickable((By.ID, "district_home"))
                )
                driver.execute_script("arguments[0].click();", district_trigger)
                district_elem = WebDriverWait(driver, 40).until(
                    EC.element_to_be_clickable((By.ID, district_id))
                )
                driver.execute_script("arguments[0].click();", district_elem)
                print(f"Đang xử lý quận/huyện: {district_name}")
                log_to_sqlite("ConCung.py", "Succeeded", f"Chọn quận/huyện {district_name} thành công")
                time.sleep(2)
            except Exception as e:
                log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi chọn quận/huyện {district_name}: {e}")
                continue

            try:
                ward_trigger = WebDriverWait(driver, 40).until(
                    EC.element_to_be_clickable((By.ID, "ward_home"))
                )
                driver.execute_script("arguments[0].click();", ward_trigger)
                time.sleep(3)
                ward_options = WebDriverWait(driver, 40).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#group-select-unit .item-address-main"))
                )
                wards = [(opt.find_element(By.CSS_SELECTOR, "span.font-14").text, opt.get_attribute("id")) for opt in ward_options]
                if not wards:
                    log_to_sqlite("ConCung.py", "Failed", f"Không tìm thấy xã/phường tại {province_name}/{district_name}, có thể không có dữ liệu")
                else:
                    print(f"Tìm thấy {len(wards)} xã/phường: {wards}")
                    log_to_sqlite("ConCung.py", "Succeeded", f"Tìm thấy {len(wards)} xã/phường tại {province_name}/{district_name}")
            except Exception as e:
                log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi lấy xã/phường tại {province_name}/{district_name}: {e}")
                wards = []

            for ward_name, ward_id in wards:
                log_to_sqlite("ConCung.py", "Pending", f"Bắt đầu xử lý xã/phường: {ward_name}")
                try:
                    ward_trigger = WebDriverWait(driver, 40).until(
                        EC.element_to_be_clickable((By.ID, "ward_home"))
                    )
                    driver.execute_script("arguments[0].click();", ward_trigger)
                    ward_elem = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, ward_id))
                    )
                    driver.execute_script("arguments[0].click();", ward_elem)
                    print(f"Đang xử lý xã/phường: {ward_name}")
                    log_to_sqlite("ConCung.py", "Succeeded", f"Chọn xã/phường {ward_name} thành công")
                    time.sleep(2)
                except Exception as e:
                    log_to_sqlite("ConCung.py", "Failed", f"Không tìm thấy {ward_id}, scrape trực tiếp: {e}")

                group_select_unit = WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.ID, "group-select-unit"))
                )
                last_height = driver.execute_script("return arguments[0].scrollHeight", group_select_unit)
                store_count = 0
                max_scrolls = 20
                scroll_count = 0

                while scroll_count < max_scrolls:
                    store_items = group_select_unit.find_elements(By.CSS_SELECTOR, ".store-item-show")
                    current_count = len(store_items)
                    if current_count > store_count:
                        store_count = current_count
                        print(f"Đã load {store_count} cửa hàng")
                        log_to_sqlite("ConCung.py", "Succeeded", f"Đã load {store_count} cửa hàng tại {province_name}/{district_name}/{ward_name}")

                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", group_select_unit)
                    time.sleep(2)
                    new_height = driver.execute_script("return arguments[0].scrollHeight", group_select_unit)
                    if new_height == last_height:
                        break
                    last_height = new_height
                    scroll_count += 1

                store_items = group_select_unit.find_elements(By.CSS_SELECTOR, ".store-item-show")
                for item in store_items:
                    try:
                        address_elem = item.find_element(By.CSS_SELECTOR, ".store_address span.font-15.font-medium")
                        address = address_elem.text.strip()
                        sub_info = item.find_element(By.CSS_SELECTOR, ".store_address .color-text-main").text.strip()
                        hours = item.find_element(By.CSS_SELECTOR, "span[style*='color:#8F3A72']").text.strip()
                        full_address = f"{address} ({sub_info}) - Giờ: {hours}"
                        if address:
                            results.append([province_name, district_name, ward_name, full_address])
                            log_to_sqlite("ConCung.py", "Succeeded", f"Lấy cửa hàng tại {province_name}/{district_name}/{ward_name}: {full_address}")
                    except Exception as e:
                        log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi lấy địa chỉ cửa hàng tại {province_name}/{district_name}/{ward_name}: {e}")
                        continue

                print(f"Đã lấy {len(store_items)} cửa hàng tại {province_name}/{district_name}/{ward_name}")
                log_to_sqlite("ConCung.py", "Succeeded", f"Đã lấy {len(store_items)} cửa hàng tại {province_name}/{district_name}/{ward_name}")

        try:
            province_trigger = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, "province_home"))
            )
            driver.execute_script("arguments[0].click();", province_trigger)
            first_province_elem = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, provinces[0][1]))
            )
            driver.execute_script("arguments[0].click();", first_province_elem)
            time.sleep(2)
            log_to_sqlite("ConCung.py", "Succeeded", "Reset về tỉnh đầu tiên thành công")
        except Exception as e:
            log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi reset về tỉnh đầu tiên: {e}")

    log_to_sqlite("ConCung.py", "Pending", "Bắt đầu lưu file concung_stores.xlsx")
    try:
        df = pd.DataFrame(results, columns=["Tỉnh", "Quận/Huyện", "Xã/Phường", "Địa Chỉ"])
        df.to_excel("concung_stores.xlsx", index=False, engine='openpyxl')
        print(f"Đã lưu {len(results)} cửa hàng vào concung_stores.xlsx")
        log_to_sqlite("ConCung.py", "Succeeded", f"Đã lưu {len(results)} cửa hàng vào concung_stores.xlsx")
    except Exception as e:
        log_to_sqlite("ConCung.py", "Failed", f"Lỗi khi lưu file concung_stores.xlsx: {e}")
        raise

finally:
    driver.quit()