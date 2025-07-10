from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

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
    driver.get(url)

    try:
        close_popup = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='close'], button[class*='accept'], div[class*='popup'] button"))
        )
        driver.execute_script("arguments[0].click();", close_popup)
        print("Đã đóng pop-up hoặc dialog đồng ý")
    except:
        print("Không tìm thấy pop-up, tiếp tục...")

    try:
        choose_area = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.d-inline-flex[onclick*='unit-choosed']"))
        )
        driver.execute_script("arguments[0].click();", choose_area)
        print("Đã kích hoạt chọn khu vực")
    except Exception as e:
        print(f"Lỗi khi kích hoạt chọn khu vực: {e}")
        raise

    province_trigger = WebDriverWait(driver, 40).until(
        EC.element_to_be_clickable((By.ID, "province_home"))
    )
    driver.execute_script("arguments[0].click();", province_trigger)
    time.sleep(2)

    province_options = WebDriverWait(driver, 40).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#group-select-unit .item-address-main"))
    )
    provinces = [(opt.find_element(By.CSS_SELECTOR, "span.font-14").text, opt.get_attribute("id")) for opt in province_options]
    print(f"Tìm thấy {len(provinces)} tỉnh/thành: {provinces}")

    results = []

    for province_name, province_id in provinces:
        province_trigger = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.ID, "province_home"))
        )
        driver.execute_script("arguments[0].click();", province_trigger)
        province_elem = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.ID, province_id))
        )
        driver.execute_script("arguments[0].click();", province_elem)
        print(f"Đang xử lý tỉnh: {province_name}")
        time.sleep(2)

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
                print(f"Không tìm thấy quận/huyện tại {province_name}, có thể không có dữ liệu")
            else:
                print(f"Tìm thấy {len(districts)} quận/huyện: {districts}")
        except Exception as e:
            print(f"Lỗi khi lấy quận/huyện tại {province_name}: {e}")
            districts = []

        for district_name, district_id in districts:
            district_trigger = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, "district_home"))
            )
            driver.execute_script("arguments[0].click();", district_trigger)
            district_elem = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, district_id))
            )
            driver.execute_script("arguments[0].click();", district_elem)
            print(f"Đang xử lý quận/huyện: {district_name}")
            time.sleep(2)

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
                    print(f"Không tìm thấy xã/phường tại {province_name}/{district_name}, có thể không có dữ liệu")
                else:
                    print(f"Tìm thấy {len(wards)} xã/phường: {wards}")
            except Exception as e:
                print(f"Lỗi khi lấy xã/phường tại {province_name}/{district_name}: {e}")
                wards = []

            for ward_name, ward_id in wards:
                ward_trigger = WebDriverWait(driver, 40).until(
                    EC.element_to_be_clickable((By.ID, "ward_home"))
                )
                driver.execute_script("arguments[0].click();", ward_trigger)
                try:
                    ward_elem = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, ward_id))
                    )
                    driver.execute_script("arguments[0].click();", ward_elem)
                except Exception as e:
                    print(f"Không tìm thấy {ward_id}, scrape trực tiếp: {e}")
                print(f"Đang xử lý xã/phường: {ward_name}")
                time.sleep(2)

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
                    except Exception as e:
                        print(f"Lỗi khi lấy địa chỉ cửa hàng tại {province_name}/{district_name}/{ward_name}: {e}")
                        continue

                print(f"Đã lấy {len(store_items)} cửa hàng tại {province_name}/{district_name}/{ward_name}")

        province_trigger = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.ID, "province_home"))
        )
        driver.execute_script("arguments[0].click();", province_trigger)
        first_province_elem = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.ID, provinces[0][1]))
        )
        driver.execute_script("arguments[0].click();", first_province_elem)
        time.sleep(2)

    timestamp = int(time.time())
    with open(f"concung_stores_{timestamp}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Tỉnh", "Quận/Huyện", "Xã/Phường", "Địa Chỉ"])
        writer.writerows(results)

    print(f"Đã lưu {len(results)} cửa hàng vào concung_stores_{timestamp}.csv")

finally:
    driver.quit()
