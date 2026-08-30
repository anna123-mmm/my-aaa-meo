import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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
    driver = None

    try:
        username, domain, full_email = generate_random_email()
        print(f"[+] Tạo email mới: {full_email}", flush=True)

        # 1. Cấu hình Chrome Options
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-popup-blocking")

        # Chạy ẩn (Headless) trên Server Linux
        if os.name != "nt":
            options.add_argument("--headless=new")
            print("[+] Đang chạy ở chế độ Chrome Headless (Linux Server).", flush=True)

        # Giả lập User-Agent Windows
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 2. Khởi tạo Driver
        if os.name == "nt":
            driver = webdriver.Chrome(options=options)
        else:
            options.binary_location = "/usr/bin/chromium"
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)

        print("[+] Khởi tạo Chrome thành công! Đang truy cập trang web...", flush=True)

        starnews_url = "https://member.starnewskorea.com/join/email"
        driver.get(starnews_url)
        print("[+] Đã tải xong trang web!", flush=True)

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
        print("[+] Đã bấm gửi mã OTP.", flush=True)

        # Step 3: Đóng Popup Alert nếu xuất hiện sau khi gửi OTP
        try:
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("[+] Đã đóng popup thông báo gửi OTP.", flush=True)
        except Exception:
            pass

        # Step 4: Lấy OTP từ TempMail API
        otp_code = fetch_otp_from_api(username, domain)
        if not otp_code:
            raise Exception("Không nhận được mã OTP từ API Email!")

        # Step 5: Nhập OTP và xác nhận (인증확인)
        print("[+] Đang nhập mã OTP...", flush=True)
        otp_input = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//input[contains(@placeholder, '6') or contains(@placeholder, '인증') or @name='code' or @type='number']",
            ))
        )
        otp_input.clear()
        otp_input.send_keys(otp_code)
        print(f"[+] Đã nhập OTP thành công: {otp_code}", flush=True)
        time.sleep(1)

        btn_confirm_otp = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[text()='인증확인' or contains(text(), '인증확인')]",
            ))
        )
        driver.execute_script("arguments[0].click();", btn_confirm_otp)
        print("[+] Đã bấm xác nhận OTP.", flush=True)
        time.sleep(1.5)

        # Step 6: Nhập Mật khẩu (Điền trực tiếp vào các ô password)
        print("[+] Đang nhập mật khẩu...", flush=True)
        pass_inputs = driver.find_elements(By.XPATH, "//input[@type='password']")
        if len(pass_inputs) >= 2:
            pass_inputs[0].clear()
            pass_inputs[0].send_keys(custom_password)
            pass_inputs[1].clear()
            pass_inputs[1].send_keys(custom_password)
            print("[+] Đã nhập xong mật khẩu.", flush=True)
        else:
            print("[-] Không tìm thấy 2 ô nhập mật khẩu qua type=password, thử tìm lại...", flush=True)
            pass_inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='password']")))
            pass_inputs[0].send_keys(custom_password)
            pass_inputs[1].send_keys(custom_password)

        time.sleep(1)

        # Step 7: Tích chọn "Đồng ý tất cả điều khoản" (Tìm theo nhiều thuộc tính)
        print("[+] Đang tích chọn đồng ý tất cả điều khoản...", flush=True)
        try:
            chk_all = driver.find_element(
                By.XPATH,
                "//*[contains(text(), '모두 동의') or contains(text(), '모두동의') or @id='agreeAll' or contains(@class, 'all')]"
            )
            driver.execute_script("arguments[0].click();", chk_all)
        except Exception:
            # Nếu không tìm thấy chữ, chọn checkbox đầu tiên trên trang
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            if checkboxes:
                driver.execute_script("arguments[0].click();", checkboxes[0])
        print("[+] Đã tích chọn đồng ý điều khoản.", flush=True)
        time.sleep(1)

        # Step 8: Bấm nút Hoàn tất đăng ký (가입완료)
        print("[+] Đang bấm hoàn tất đăng ký...", flush=True)
        btn_submit = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(), '가입완료') or contains(text(), '가입')]")
            )
        )
        driver.execute_script("arguments[0].click();", btn_submit)
        print("[+] Đã bấm nút đăng ký hoàn tất thành công!", flush=True)
        time.sleep(3)

        # Step 9: Giải Turnstile Captcha nếu bị chuyển hướng sang Login
        if "login" in driver.current_url:
            print("[+] Đang tiến hành giải Turnstile Captcha...", flush=True)
            token = solve_cloudflare(driver.current_url, SITE_KEY_CLOUDFLARE)
            if token:
                driver.execute_script(
                    'document.querySelector("[name=cf-turnstile-response]").value'
                    f'="{token}";'
                )

        print(f"[+] Đăng ký hoàn tất: {full_email}", flush=True)
        return full_email

    except Exception as e:
        print(f"[-] Lỗi trong tiến trình đăng ký ({type(e).__name__}): {e}", flush=True)
        return None

    finally:
        time.sleep(2)
        if driver:
            try:
                driver.quit()
            except Exception:
                pass