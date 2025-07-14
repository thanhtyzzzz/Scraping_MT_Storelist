from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
import openpyxl

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

# === CONFIGURE BROWSER ===
options = Options()
options.add_argument("--start-maximized")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(service=Service(), options=options)
wait = WebDriverWait(driver, 20)

# === ACCESS WEBSITE ===
try:
    driver.get("https://www.bachhoaxanh.com/he-thong-cua-hang")
    time.sleep(5)
except Exception as e:
    error_message = f"Lỗi khi truy cập trang web: {e}"
    log_error("Storelist_BHX_Selenium.py", error_message)
    raise

# === CLICK 'XEM THÊM' UNTIL NO MORE BUTTONS ===
def click_see_more_until_end(province):
    print(f"Đang bấm 'Xem thêm' cho {province}...")
    while True:
        try:
            see_more = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'py-4 text-center cursor-pointer')]/span[contains(text(), 'Xem thêm')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", see_more)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", see_more)
            time.sleep(2)
        except Exception as e:
            error_message = f"Đã bấm hết tất cả nút 'Xem thêm' cho {province} hoặc gặp lỗi: {str(e)}"
            log_error("Storelist_BHX_Selenium.py", error_message)
            break

# === GET STORE NAMES AND ADDRESSES ===
def get_store_addresses(province):
    print(f"Đang lấy danh sách cửa hàng cho {province}...")
    stores = driver.find_elements(By.XPATH, "//ul/li//span[contains(@class, 'mr-2 font-bold')]")
    results = []

    for store in stores:
        try:
            text = store.text.strip()
            if "(" in text:
                name = text.split("(", 1)[0].strip()
                address = text.split("(", 1)[1].replace(")", "").strip()
            else:
                name = text
                address = ""
            results.append([name, address, province])
        except Exception as e:
            error_message = f"Lỗi khi xử lý cửa hàng: {text}, lỗi: {str(e)}"
            log_error("Storelist_BHX_Selenium.py", error_message)
            continue

    try:
        store_count = driver.find_element(By.XPATH, "//p[contains(text(), 'Có')]//span[@class='font-bold']").text
        print(f"Tỉnh {province} có {store_count} cửa hàng, lấy được {len(results)} cửa hàng")
    except:
        error_message = f"Không tìm thấy số lượng cửa hàng cho {province}"
        log_error("Storelist_BHX_Selenium.py", error_message)

    return results

# === GET ALL PROVINCES AND SCRAPE STORES ===
def scrape_all_provinces():
    all_store_data = []

    print("Xử lý tỉnh/thành phố: TP. Hồ Chí Minh (mặc định)")
    click_see_more_until_end("TP. Hồ Chí Minh")
    store_data = get_store_addresses("TP. Hồ Chí Minh")
    all_store_data.extend(store_data)

    # Locate and open the province dropdown
    try:
        province_dropdown = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'icon-triangle')]//span[contains(@class, 'line-clamp-1')]"))
        )
        print("Đã tìm thấy dropdown tỉnh/thành phố")
        driver.execute_script("arguments[0].click();", province_dropdown)
        time.sleep(3)
    except Exception as e:
        error_message = f"Lỗi khi tìm hoặc mở dropdown tỉnh/thành phố: {str(e)}"
        log_error("Storelist_BHX_Selenium.py", error_message)
        driver.refresh()
        time.sleep(5)
        return all_store_data

    # Get all province options
    try:
        province_options = driver.find_elements(By.XPATH, "//div[contains(@class, 'bhx-scroll')]//div[contains(@class, 'flex items-center')]")
        provinces = [option.text.strip() for option in province_options if option.text.strip() and option.text.strip() != "TP. Hồ Chí Minh"]
        print(f"Tìm thấy {len(provinces)} tỉnh/thành phố (ngoại trừ TP. Hồ Chí Minh): {provinces}")

        if not provinces:
            error_message = "Không tìm thấy tỉnh/thành phố nào, kiểm tra HTML dropdown"
            log_error("Storelist_BHX_Selenium.py", error_message)
    except Exception as e:
        error_message = f"Lỗi khi lấy danh sách tỉnh/thành phố: {str(e)}"
        log_error("Storelist_BHX_Selenium.py", error_message)
        driver.refresh()
        time.sleep(5)
        return all_store_data

    for province in provinces:
        print(f"Xử lý tỉnh/thành phố: {province}")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                province_dropdown = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'icon-triangle')]//span[contains(@class, 'line-clamp-1')]"))
                )
                driver.execute_script("arguments[0].click();", province_dropdown)
                time.sleep(2)

                province_option = wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'bhx-scroll')]//div[contains(@class, 'flex items-center') and contains(text(), '{province}')]"))
                )
                driver.execute_script("arguments[0].click();", province_option)
                time.sleep(4)
                break
            except Exception as e:
                error_message = f"Lỗi khi chọn tỉnh {province} (thử {attempt + 1}/{max_retries}): {str(e)}"
                log_error("Storelist_BHX_Selenium.py", error_message)
                if attempt == max_retries - 1:
                    error_message = f"Bỏ qua tỉnh {province} sau {max_retries} lần thử"
                    log_error("Storelist_BHX_Selenium.py", error_message)
                    break
                time.sleep(2)
        else:
            continue

        click_see_more_until_end(province)
        store_data = get_store_addresses(province)
        all_store_data.extend(store_data)

    return all_store_data

# === RUN THE PROCESS ===
try:
    store_data = scrape_all_provinces()

    try:
        df = pd.DataFrame(store_data, columns=["Tên Cửa Hàng", "Địa Chỉ", "Tỉnh/Thành Phố"])
        df.to_excel("bachhoaxanh_stores.xlsx", index=False, engine='openpyxl')
        print("Đã lưu vào bachhoaxanh_stores.xlsx")
    except Exception as e:
        error_message = f"Lỗi khi lưu file bachhoaxanh_stores.xlsx: {e}"
        log_error("Storelist_BHX_Selenium.py", error_message)
        raise

finally:
    driver.quit()