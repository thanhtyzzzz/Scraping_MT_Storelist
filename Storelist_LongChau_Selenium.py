from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
from retrying import retry
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# Khởi tạo WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
options.add_argument("--disable-web-security")
options.add_argument("--disable-site-isolation-trials")
# options.add_argument("--headless")  # Bỏ comment nếu muốn chạy ẩn
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Mở trang web
url = "https://nhathuoclongchau.com.vn/he-thong-cua-hang/"
driver.get(url)

# Chờ dropdown tỉnh/thành
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.w-full.dropdown-input"))
    )
except Exception as e:
    print(f"Lỗi khi chờ dropdown: {e}")
    driver.quit()
    exit()

# Danh sách để lưu địa chỉ
all_addresses = []

try:
    # Thử click vào div hoặc span để mở dropdown
    try:
        dropdown = driver.find_element(By.CSS_SELECTOR, "div.w-full.dropdown-input")
        dropdown.click()
    except:
        print("Không click được div, thử click span...")
        dropdown = driver.find_element(By.CSS_SELECTOR, "span.dropdown-icon")
        dropdown.click()
    
    print("Đã click dropdown, kiểm tra trạng thái...")
    
    # Chờ danh sách tỉnh/thành xuất hiện
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
        )
        print("Dropdown đã mở, kiểm tra input tìm kiếm...")
        # Xóa input tìm kiếm
        try:
            search_input = driver.find_element(By.CSS_SELECTOR, "div.dropdown-menu input[placeholder='Nhập tìm Tỉnh/Thành phố']")
            search_input.clear()
            print("Đã xóa input tìm kiếm.")
        except:
            print("Không tìm thấy input tìm kiếm, tiếp tục...")
    except Exception as e:
        print(f"Lỗi khi chờ danh sách tỉnh/thành: {e}")
        print("HTML trang:", driver.page_source[:1000])
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
            print(f"Lỗi khi scroll dropdown (lần {retry_count + 1}): {e}")
            retry_count += 1
            if retry_count == 3:
                print("Không thể scroll dropdown sau 3 lần thử!")
                break
    
    provinces = [elem.text.strip() for elem in province_elements if elem.text.strip()]
    print(f"Tìm được {len(provinces)} tỉnh/thành: {provinces}")

    if not provinces:
        print("Không tìm được tỉnh/thành, thử click lại dropdown...")
        try:
            dropdown.click()
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dropdown-item"))
            )
            province_elements = driver.find_elements(By.CSS_SELECTOR, "div.dropdown-item")
            provinces = [elem.text.strip() for elem in province_elements if elem.text.strip()]
            print(f"Thử lại: Tìm được {len(provinces)} tỉnh/thành: {provinces}")
        except Exception as e:
            print(f"Lỗi khi thử lại: {e}")
            print("HTML trang:", driver.page_source[:1000])
            driver.quit()
            exit()

    if not provinces:
        print("Vẫn không tìm được tỉnh/thành, kiểm tra HTML hoặc kết nối mạng!")
        driver.quit()
        exit()

    previous_province_addresses = set()  # Lưu địa chỉ của tỉnh trước để kiểm tra trùng lặp
    for province in provinces:
        print(f"\nĐang xử lý tỉnh/thành: {province}")
        # Chọn tỉnh/thành với retry
        retry_count = 0
        while retry_count < 5:
            try:
                # Kiểm tra trạng thái dropdown
                dropdown_state = driver.find_element(By.CSS_SELECTOR, "div.w-full.dropdown-input").get_attribute("data-state")
                if dropdown_state != "open":
                    dropdown.click()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown-menu"))
                    )
                province_option = driver.find_element(By.XPATH, f"//div[contains(@class, 'dropdown-item') and contains(text(), '{province}')]")
                driver.execute_script("arguments[0].scrollIntoView(true);", province_option)
                province_option.click()
                time.sleep(1)  # Delay để đảm bảo tỉnh được chọn
                break
            except Exception as e:
                print(f"Lỗi khi chọn tỉnh {province} (lần {retry_count + 1}): {e}")
                retry_count += 1
                if retry_count == 5:
                    print(f"Bỏ qua tỉnh {province} sau 5 lần thử.")
                    break
                time.sleep(2)
        if retry_count == 5:
            continue

        # Chờ danh sách nhà thuốc tải
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-body2.text-gray-10"))
            )
            # Đợi thêm để đảm bảo danh sách làm mới
            time.sleep(2)
        except Exception as e:
            print(f"Lỗi khi chờ danh sách nhà thuốc cho {province}: {e}")
            continue

        # Thu thập địa chỉ
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
                        # Kiểm tra trùng lặp với tỉnh trước
                        if address and address not in province_addresses and address not in previous_province_addresses:
                            addresses.append(address)
                    except StaleElementReferenceException:
                        print(f"Stale element khi lấy địa chỉ ở {province}, thử lại...")
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
                print(f"Stale element khi lấy danh sách địa chỉ ở {province}, thử lại...")
                time.sleep(1)
                continue
            except Exception as e:
                print(f"Lỗi khác khi lấy địa chỉ ở {province}: {e}")
                break

        # Cập nhật danh sách địa chỉ tỉnh trước
        previous_province_addresses = set(province_addresses)
        
        # Delay giữa các tỉnh để tránh chặn bot
        time.sleep(2)

finally:
    # Lưu file CSV tổng
    csv_file = "longchau_all_addresses.csv"
    try:
        with open(csv_file, mode='w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['STT', 'Tỉnh/Thành', 'Địa chỉ'])
            for i, (province, address) in enumerate(all_addresses, 1):
                writer.writerow([i, province, address])
        print(f"\nTổng số địa chỉ tìm được: {len(all_addresses)}")
        print(f"Danh sách địa chỉ tổng được lưu vào {csv_file}")
    except Exception as e:
        print(f"Lỗi khi lưu file CSV tổng: {e}")

    driver.quit()