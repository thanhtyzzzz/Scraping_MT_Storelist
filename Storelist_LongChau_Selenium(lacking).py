from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

# Khởi tạo WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Mở trang web
url = "https://nhathuoclongchau.com.vn/he-thong-cua-hang/"
driver.get(url)

# Chờ phần tử chứa danh sách nhà thuốc xuất hiện
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.mb-\\[12px\\]"))
    )
except Exception as e:
    print(f"Lỗi khi chờ phần tử: {e}")
    driver.quit()
    exit()

# Danh sách để lưu địa chỉ
addresses = []

try:
    while True:
        # Lấy danh sách địa chỉ trên trang hiện tại
        address_elements = driver.find_elements(By.CSS_SELECTOR, "p.text-body2.text-gray-10")
        for element in address_elements:
            address = element.text.strip()
            if address and address not in addresses:  # Tránh trùng lặp
                addresses.append(address)

        # Kiểm tra nút "Xem thêm nhà thuốc"
        try:
            show_more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Xem thêm nhà thuốc')]"))
            )
            # Cuộn đến nút
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
            time.sleep(1)  
            show_more_button.click()
            time.sleep(2)  
        except:
            # Không còn nút "Xem thêm", thoát vòng lặp
            break

finally:
    # In danh sách địa chỉ
    print(f"Tổng số địa chỉ tìm được: {len(addresses)}")
    for i, address in enumerate(addresses, 1):
        print(f"{i}. {address}")

    # Lưu vào file CSV với mã hóa UTF-8-SIG để tránh lỗi font
    csv_file = "longchau_addresses.csv"
    try:
        with open(csv_file, mode='w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            # Ghi tiêu đề
            writer.writerow(['STT', 'Địa chỉ'])
            # Ghi dữ liệu
            for i, address in enumerate(addresses, 1):
                writer.writerow([i, address])
        print(f"Danh sách địa chỉ đã được lưu vào {csv_file}")
    except Exception as e:
        print(f"Lỗi khi lưu file CSV: {e}")

    # Đóng trình duyệt
    driver.quit()