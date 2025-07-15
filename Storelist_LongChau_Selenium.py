from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import sqlite3
from retrying import retry
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
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

# Khởi tạo WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
options.add_argument("--disable-web-security")
options.add_argument("--disable-site-isolation-trials")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    url = "https://nhathuoclongchau.com.vn/he-thong-cua-hang/"
    log_to_sqlite("LongChau.py", "Pending", f"Bắt đầu truy cập {url}")
    driver.get(url)
    log_to_sqlite("LongChau.py", "Succeeded", f"Truy cập {url} thành công")
except Exception as e:
    log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi truy cập trang web: {e}")
    driver.quit()
    exit()

# Chờ dropdown tỉnh/thành
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.w-full.dropdown-input"))
    )
    log_to_sqlite("LongChau.py", "Succeeded", "Tải dropdown tỉnh/thành thành công")
except Exception as e:
    log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi chờ dropdown: {e}")
    driver.quit()
    exit()

all_addresses = []

try:
    # Thử click vào div hoặc span để mở dropdown
    try:
        dropdown = driver.find_element(By.CSS_SELECTOR, "div.w-full.dropdown-input")
        dropdown.click()
        log_to_sqlite("LongChau.py", "Succeeded", "Click dropdown thành công")
    except:
        try:
            print("Không click được div, thử click span...")
            dropdown = driver.find_element(By.CSS_SELECTOR, "span.dropdown-icon")
            dropdown.click()
            log_to_sqlite("LongChau.py", "Succeeded", "Click span dropdown thành công")
        except Exception as e:
            log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi click dropdown: {e}")
            driver.quit()
            exit()
    
    print("Đã click dropdown, kiểm tra trạng thái...")
    
    # Chờ danh sách tỉnh/thành xuất hiện
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
        )
        print("Dropdown đã mở, kiểm tra input tìm kiếm...")
        log_to_sqlite("LongChau.py", "Succeeded", "Dropdown tỉnh/thành đã mở")
        try:
            search_input = driver.find_element(By.CSS_SELECTOR, "div.dropdown-menu input[placeholder='Nhập tìm Tỉnh/Thành phố']")
            search_input.clear()
            print("Đã xóa input tìm kiếm.")
            log_to_sqlite("LongChau.py", "Succeeded", "Xóa input tìm kiếm thành công")
        except:
            print("Không tìm thấy input tìm kiếm, tiếp tục...")
            log_to_sqlite("LongChau.py", "Failed", "Không tìm thấy input tìm kiếm")
    except Exception as e:
        log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi chờ danh sách tỉnh/thành: {e}")
        driver.quit()
        exit()

    # Scroll dropdown để tải hết tỉnh/thành
    province_elements = []
    retry_count = 0
    while retry_count < 3:
        try:
            driver.execute_script("document.querySelector('div.dropdown-menu').scrollBy(0, 1000);")
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dropdown-item"))
            )
            new_provinces = driver.find_elements(By.CSS_SELECTOR, "div.dropdown-item")
            print(f"Tìm được {len(new_provinces)} phần tử tỉnh/thành")
            if len(new_provinces) == len(province_elements):
                break
            province_elements = new_provinces
            time.sleep(1)
            log_to_sqlite("LongChau.py", "Succeeded", f"Tìm được {len(new_provinces)} phần tử tỉnh/thành")
        except Exception as e:
            log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi scroll dropdown (lần {retry_count + 1}): {e}")
            retry_count += 1
            if retry_count == 3:
                log_to_sqlite("LongChau.py", "Failed", "Không thể scroll dropdown sau 3 lần thử")
                break
    
    provinces = [elem.text.strip() for elem in province_elements if elem.text.strip()]
    print(f"Tìm được {len(provinces)} tỉnh/thành: {provinces}")
    log_to_sqlite("LongChau.py", "Succeeded", f"Tìm được {len(provinces)} tỉnh/thành")

    if not provinces:
        try:
            dropdown.click()
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dropdown-item"))
            )
            province_elements = driver.find_elements(By.CSS_SELECTOR, "div.dropdown-item")
            provinces = [elem.text.strip() for elem in province_elements if elem.text.strip()]
            print(f"Thử lại: Tìm được {len(provinces)} tỉnh/thành: {provinces}")
            log_to_sqlite("LongChau.py", "Succeeded", f"Thử lại: Tìm được {len(provinces)} tỉnh/thành")
        except Exception as e:
            log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi thử lại lấy tỉnh/thành: {e}")
            driver.quit()
            exit()

    if not provinces:
        log_to_sqlite("LongChau.py", "Failed", "Vẫn không tìm được tỉnh/thành, kiểm tra HTML hoặc kết nối mạng")
        driver.quit()
        exit()

    previous_province_addresses = set()
    for province in provinces:
        print(f"\nĐang xử lý tỉnh/thành: {province}")
        log_to_sqlite("LongChau.py", "Pending", f"Bắt đầu xử lý tỉnh/thành: {province}")
        retry_count = 0
        while retry_count < 5:
            try:
                dropdown_state = driver.find_element(By.CSS_SELECTOR, "div.w-full.dropdown-input").get_attribute("data-state")
                if dropdown_state != "open":
                    dropdown.click()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
                    )
                province_option = driver.find_element(By.XPATH, f"//div[contains(@class, 'dropdown-item') and contains(text(), '{province}')]")
                driver.execute_script("arguments[0].scrollIntoView(true);", province_option)
                province_option.click()
                time.sleep(1)
                log_to_sqlite("LongChau.py", "Succeeded", f"Chọn tỉnh {province} thành công")
                break
            except Exception as e:
                log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi chọn tỉnh {province} (lần {retry_count + 1}): {e}")
                retry_count += 1
                if retry_count == 5:
                    log_to_sqlite("LongChau.py", "Failed", f"Bỏ qua tỉnh {province} sau 5 lần thử")
                    break
                time.sleep(2)
        if retry_count == 5:
            continue

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-body2.text-gray-10"))
            )
            time.sleep(2)
            log_to_sqlite("LongChau.py", "Succeeded", f"Tải danh sách nhà thuốc cho {province} thành công")
        except Exception as e:
            log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi chờ danh sách nhà thuốc cho {province}: {e}")
            continue

        province_addresses = []
        @retry(stop_max_attempt_number=5, wait_fixed=3000)
        def click_show_more():
            show_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Xem thêm nhà thuốc')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
            show_more_button.click()

        while True:
            try:
                address_elements = driver.find_elements(By.CSS_SELECTOR, "p.text-body2.text-gray-10")
                old_count = len(province_addresses)
                addresses = []
                for element in address_elements:
                    try:
                        address = element.text.strip()
                        if address and address not in province_addresses and address not in previous_province_addresses:
                            addresses.append(address)
                    except StaleElementReferenceException:
                        log_to_sqlite("LongChau.py", "Failed", f"Stale element khi lấy địa chỉ ở {province}, thử lại...")
                        break
                province_addresses.extend(addresses)
                for address in addresses:
                    all_addresses.append((province, address))
                    log_to_sqlite("LongChau.py", "Succeeded", f"Lấy địa chỉ tại {province}: {address}")

                print(f"Hiện tại: {len(province_addresses)} địa chỉ ở {province}")

                if len(province_addresses) == old_count:
                    print(f"Không tìm thêm được địa chỉ ở {province}, thoát vòng lặp.")
                    log_to_sqlite("LongChau.py", "Succeeded", f"Không tìm thêm được địa chỉ ở {province}, thoát vòng lặp")
                    break

                try:
                    click_show_more()
                    WebDriverWait(driver, 30).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, "p.text-body2.text-gray-10")) > old_count
                    )
                    print(f"Nhấn 'Xem thêm' thành công, tìm thêm địa chỉ ở {province}...")
                    log_to_sqlite("LongChau.py", "Succeeded", f"Nhấn 'Xem thêm' thành công, tìm thêm địa chỉ ở {province}")
                    time.sleep(1)
                except TimeoutException:
                    print(f"Hết địa chỉ hoặc lỗi khi nhấn 'Xem thêm' ở {province}.")
                    log_to_sqlite("LongChau.py", "Failed", f"Hết địa chỉ hoặc lỗi khi nhấn 'Xem thêm' ở {province}")
                    break
            except StaleElementReferenceException:
                log_to_sqlite("LongChau.py", "Failed", f"Stale element khi lấy danh sách địa chỉ ở {province}, thử lại...")
                time.sleep(1)
                continue
            except Exception as e:
                log_to_sqlite("LongChau.py", "Failed", f"Lỗi khác khi lấy địa chỉ ở {province}: {e}")
                break

        previous_province_addresses = set(province_addresses)
        time.sleep(2)

finally:
    log_to_sqlite("LongChau.py", "Pending", "Bắt đầu lưu file longchau_all_addresses.xlsx")
    try:
        df = pd.DataFrame(all_addresses, columns=['Tỉnh/Thành', 'Địa chỉ'])
        df.insert(0, 'STT', range(1, len(df) + 1))
        df.to_excel("longchau_all_addresses.xlsx", index=False, engine='openpyxl')
        print(f"\nTổng số địa chỉ tìm được: {len(all_addresses)}")
        print(f"Danh sách địa chỉ tổng được lưu vào longchau_all_addresses.xlsx")
        log_to_sqlite("LongChau.py", "Succeeded", f"Đã lưu {len(all_addresses)} địa chỉ vào longchau_all_addresses.xlsx")
    except Exception as e:
        log_to_sqlite("LongChau.py", "Failed", f"Lỗi khi lưu file longchau_all_addresses.xlsx: {e}")

    driver.quit()