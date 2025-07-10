from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import re

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
    # Truy cập trang chính
    url = "https://www.nhathuocankhang.com/he-thong-nha-thuoc"
    driver.get(url)

    # Đợi danh sách tỉnh
    WebDriverWait(driver, 40).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".opt-tinhthanh span"))
    )

    # Lấy danh sách tỉnh
    province_elements = driver.find_elements(By.CSS_SELECTOR, ".opt-tinhthanh span")
    province_names = []
    for i, elem in enumerate(province_elements):
        name = elem.text.strip()
        if not name:
            name = elem.get_attribute("innerText").strip()
        if not name:
            name = elem.get_attribute("textContent").strip()
        if not name:
            name = f"Tỉnh thứ {i + 1}"
        province_names.append(name)
    
    print(f"📋 Tìm thấy {len(province_names)} tỉnh/thành")

    results = []

    # Duyệt từng tỉnh
    for i, province_name in enumerate(province_names):
        # Làm mới trang để reset trạng thái
        driver.get(url)
        WebDriverWait(driver, 40).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".opt-tinhthanh span"))
        )

        province_elements = driver.find_elements(By.CSS_SELECTOR, ".opt-tinhthanh span")
        if len(province_elements) != len(province_names):
            print(f"Số lượng tỉnh không khớp: {len(province_elements)} vs {len(province_names)}")
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
                print(f"Lỗi click tỉnh {province_name} (lần {attempt + 1}): {e}")
                if attempt == retry_count - 1:
                    print(f"Bỏ qua tỉnh {province_name} sau {retry_count} lần thử")
                    break
                time.sleep(3)

        if not click_success:
            continue  # Bỏ qua tỉnh nếu click thất bại

        # Kiểm tra xem có nhà thuốc hay không
        no_store_message = driver.find_elements(By.CSS_SELECTOR, ".no-results, .empty-message, [class*='no-store'], [class*='empty'], [class*='error'], [class*='no-data']")
        if no_store_message:
            print(f"Tỉnh {province_name} không có nhà thuốc (thông báo: {no_store_message[0].text}).")
            continue

        # Bấm load more nhiều lần
        see_more_attempts = 0
        max_attempts = 20  # Tăng giới hạn để đảm bảo lấy hết
        while see_more_attempts < max_attempts:
            try:
                prev_count = len(driver.find_elements(By.CSS_SELECTOR, "ul.listing-store.zl-list li"))
                see_more = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.seemore"))
                )
                # Kiểm tra văn bản nút "Xem thêm"
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
            except:
                print(f"Kết thúc nhấn 'Xem thêm' tại {province_name} sau {see_more_attempts} lần")
                break

        # Lấy danh sách nhà thuốc
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
                print(f"Lỗi khi lấy thông tin nhà thuốc tại {province_name}: {e}")
                continue

        print(f"Đã lấy {store_count} nhà thuốc tại {province_name}")

    # Lưu kết quả ra CSV
    timestamp = int(time.time())
    with open(f"ankhang_stores_{timestamp}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Tỉnh", "Tên Nhà Thuốc", "Địa Chỉ"])
        writer.writerows(results)

    print(f"Đã lưu {len(results)} nhà thuốc vào ankhang_stores_{timestamp}.csv")

finally:
    driver.quit() 