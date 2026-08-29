import os
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import SITE_KEY_CLOUDFLARE
from email_captcha_api import (
    fetch_otp_from_api,
    generate_random_email,
    solve_cloudflare,
)


def run_registration(custom_password="Password123!"):
    display = None
    driver = None

    try:
        username, domain, full_email = generate_random_email()
        print(f"[+] Tạo email mới: {full_email}")

        # 1. Bật màn hình ảo Xvfb chỉ khi chạy trên Linux (Streamlit Cloud Server)
        if os.name != "nt":
            from pyvirtualdisplay import Display

            display = Display(visible=0, size=(1920, 1080))
            display.start()
            print("[+] Đã kích hoạt Virtual Display (Xvfb) trên Linux Server.")

        # 2. Cấu hình Chrome Options tối ưu bộ nhớ
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")

        # 3. Phân chia đường dẫn khởi tạo theo môi trường
        if os.name == "nt":
            # Local Windows: Ép dùng phiên bản khớp với Chrome máy nhà
            driver = uc.Chrome(options=options, version_main=151)
        else:
            # Streamlit Cloud (Linux): Dùng đường dẫn Chromium được cài qua packages.txt
            driver = uc.Chrome(
                options=options,
                browser_executable_path="/usr/bin/chromium",
            )

        starnews_url = "https://member.starnewskorea.com/join/email"
        driver.get(starnews_url)

        wait = WebDriverWait(driver, 15)

        # Step 1: Nhập Email
        email_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[contains(@placeholder, '이메일')]")
            )
        )
        email_input.clear()
        email_input.send_keys(full_email)
        time.sleep(1)

        # Step 2: Bấm nút gửi OTP (인증요청)
        btn_send_otp = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[text()='인증요청' or contains(text(), '인증요청')]",
                )
            )
        )
        btn_send_otp.click()
        print("[+] Đã bấm gửi mã OTP.")

        # Step 3: Đóng Popup Alert nếu xuất hiện
        try:
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("[+] Đã đóng popup thông báo.")
        except Exception:
            pass

        # Step 4: Lấy OTP từ TempMail API
        otp_code = fetch_otp_from_api(username, domain)
        if not otp_code:
            raise Exception("Không nhận được mã OTP từ API Email!")

        # Step 5: Nhập OTP và xác nhận (인증확인)
        otp_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[contains(@placeholder, '6자리')]")
            )
        )
        otp_input.send_keys(otp_code)
        time.sleep(1)

        btn_confirm_otp = driver.find_element(
            By.XPATH, "//button[text()='인증확인' or contains(text(), '인증확인')]"
        )
        btn_confirm_otp.click()
        time.sleep(1)

        # Step 6: Nhập Mật khẩu
        pass_inputs = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//input[@type='password']")
            )
        )
        pass_inputs[0].send_keys(custom_password)
        pass_inputs[1].send_keys(custom_password)
        time.sleep(1)

        # Step 7: Tích chọn "Đồng ý tất cả điều khoản" qua JavaScript
        chk_all = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[contains(text(), '모두 동의') or contains(text(),"
                    " '모두동의')]",
                )
            )
        )
        driver.execute_script("arguments[0].click();", chk_all)
        time.sleep(1)

        # Step 8: Bấm nút Hoàn tất đăng ký (가입완료)
        btn_submit = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), '가입완료')]")
            )
        )
        btn_submit.click()
        time.sleep(3)

        # Step 9: Giải Turnstile Captcha nếu bị chuyển hướng sang Login
        if "login" in driver.current_url:
            print("[+] Đang tiến hành giải Turnstile Captcha...")
            token = solve_cloudflare(driver.current_url, SITE_KEY_CLOUDFLARE)
            if token:
                driver.execute_script(
                    'document.querySelector("[name=cf-turnstile-response]").value'
                    f'="{token}";'
                )

        print(f"[+] Đăng ký thành công: {full_email}")
        return full_email

    except Exception as e:
        print(f"[-] Lỗi trong tiến trình đăng ký: {e}")
        return None

    finally:
        # Bắt buộc đóng Driver và giải phóng bộ nhớ Display
        time.sleep(2)
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        if display:
            try:
                display.stop()
            except Exception:
                pass