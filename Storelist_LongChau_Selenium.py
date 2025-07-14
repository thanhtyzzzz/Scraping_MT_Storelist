from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import openpyxl
from retrying import retry
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
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

# Khởi tạo WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
options.add_argument("--disable-web-security")
options.add_argument("--disable-site-isolation-trials")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    url = "https://nhathuoclongchau.com.vn/he-thong-cua-hang/"
    driver.get(url)
except Exception as e:
    error_message = f"Lỗi khi truy cập trang web: {e}"
    log_error("Storelist_LongChau_Selenium.py", error_message)
    driver.quit()
    exit()

# Chờ dropdown tỉnh/thành
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.w-full.dropdown-input"))
    )
except Exception as e:
    error_message = f"Lỗi khi chờ dropdown: {e}"
    log_error("Storelist_LongChau_Selenium.py", error_message)
    driver.quit()
    exit()


all_addresses = []

try:
    # Thử click vào div hoặc span để mở dropdown
    try:
        dropdown = driver.find_element(By.CSS_SELECTOR, "div.w-full.dropdown-input")
        dropdown.click()
    except:
        try:
            print("Không click được div, thử click span...")
            dropdown = driver.find_element(By.CSS_SELECTOR, "span.dropdown-icon")
            dropdown.click()
        except Exception as e:
            error_message = f"Lỗi khi click dropdown: {e}"
            log_error("Storelist_LongChau_Selenium.py", error_message)
            driver.quit()
            exit()
    
    print("Đã click dropdown, kiểm tra trạng thái...")
    
    # Chờ danh sách tỉnh/thành xuất hiện
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
        )
        print("Dropdown đã mở, kiểm tra input tìm kiếm...")
        try:
            search_input = driver.find_element(By.CSS_SELECTOR, "div.dropdown-menu input[placeholder='Nhập tìm Tỉnh/Thành phố']")
            search_input.clear()
            print("Đã xóa input tìm kiếm.")
        except:
            print("Không tìm thấy input tìm kiếm, tiếp tục...")
    except Exception as e:
        error_message = f"Lỗi khi chờ danh sách tỉnh/thành: {e}"
        log_error("Storelist_LongChau_Selenium.py", error_message)
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
        except Exception as e:
            error_message = f"Lỗi khi scroll dropdown (lần {retry_count + 1}): {e}"
            log_error("Storelist_LongChau_Selenium.py", error_message)
            retry_count += 1
            if retry_count == 3:
                error_message = "Không thể scroll dropdown sau 3 lần thử!"
                log_error("Storelist_LongChau_Selenium.py", error_message)
                break
    
    provinces = [elem.text.strip() for elem in province_elements if elem.text.strip()]
    print(f"Tìm được {len(provinces)} tỉnh/thành: {provinces}")

    if not provinces:
        try:
            dropdown.click()
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dropdown-item"))
            )
            province_elements = driver.find_elements(By.CSS_SELECTOR, "div.dropdown-item")
            provinces = [elem.text.strip() for elem in province_elements if elem.text.strip()]
            print(f"Thử lại: Tìm được {len(provinces)} tỉnh/thành: {provinces}")
        except Exception as e:
            error_message = f"Lỗi khi thử lại lấy tỉnh/thành: {e}"
            log_error("Storelist_LongChau_Selenium.py", error_message)
            driver.quit()
            exit()

    if not provinces:
        error_message = "Vẫn không tìm được tỉnh/thành, kiểm tra HTML hoặc kết nối mạng!"
        log_error("Storelist_LongChau_Selenium.py", error_message)
        driver.quit()
        exit()

    previous_province_addresses = set()
    for province in provinces:
        print(f"\nĐang xử lý tỉnh/thành: {province}")
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
                break
            except Exception as e:
                error_message = f"Lỗi khi chọn tỉnh {province} (lần {retry_count + 1}): {e}"
                log_error("Storelist_LongChau_Selenium.py", error_message)
                retry_count += 1
                if retry_count == 5:
                    error_message = f"Bỏ qua tỉnh {province} sau 5 lần thử."
                    log_error("Storelist_LongChau_Selenium.py", error_message)
                    break
                time.sleep(2)
        if retry_count == 5:
            continue

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-body2.text-gray-10"))
            )
            time.sleep(2)
        except Exception as e:
            error_message = f"Lỗi khi chờ danh sách nhà thuốc cho {province}: {e}"
            log_error("Storelist_LongChau_Selenium.py", error_message)
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
                        error_message = f"Stale element khi lấy địa chỉ ở {province}, thử lại..."
                        log_error("Storelist_LongChau_Selenium.py", error_message)
                        break
                province_addresses.extend(addresses)
                for address in addresses:
                    all_addresses.append((province, address))

                print(f"Hiện tại: {len(province_addresses)} địa chỉ ở {province}")

                if len(province_addresses) == old_count:
                    print(f"Không tìm thêm được địa chỉ ở {province}, thoát vòng lặp.")
                    break

                try:
                    click_show_more()
                    WebDriverWait(driver, 30).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, "p.text-body2.text-gray-10")) > old_count
                    )
                    print(f"Nhấn 'Xem thêm' thành công, tìm thêm địa chỉ ở {province}...")
                    time.sleep(1)
                except TimeoutException:
                    print(f"Hết địa chỉ hoặc lỗi khi nhấn 'Xem thêm' ở {province}.")
                    break
            except StaleElementReferenceException:
                error_message = f"Stale element khi lấy danh sách địa chỉ ở {province}, thử lại..."
                log_error("Storelist_LongChau_Selenium.py", error_message)
                time.sleep(1)
                continue
            except Exception as e:
                error_message = f"Lỗi khác khi lấy địa chỉ ở {province}: {e}"
                log_error("Storelist_LongChau_Selenium.py", error_message)
                break

        previous_province_addresses = set(province_addresses)
        time.sleep(2)

finally:
    try:
        df = pd.DataFrame(all_addresses, columns=['Tỉnh/Thành', 'Địa chỉ'])
        df.insert(0, 'STT', range(1, len(df) + 1))
        df.to_excel("longchau_all_addresses.xlsx", index=False, engine='openpyxl')
        print(f"\nTổng số địa chỉ tìm được: {len(all_addresses)}")
        print(f"Danh sách địa chỉ tổng được lưu vào longchau_all_addresses.xlsx")
    except Exception as e:
        error_message = f"Lỗi khi lưu file longchau_all_addresses.xlsx: {e}"
        log_error("Storelist_LongChau_Selenium.py", error_message)

    driver.quit()