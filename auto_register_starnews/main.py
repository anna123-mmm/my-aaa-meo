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
    username, domain, full_email = generate_random_email()
    print(f"[+] Tạo email mới: {full_email}")

    # 1. Chỉ bật Display trên Linux (Render), Windows bỏ qua
    display = None
    if os.name != "nt":
        from pyvirtualdisplay import Display

        display = Display(visible=0, size=(1920, 1080))
        display.start()

    # 2. Cấu hình undetected_chromedriver
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Bỏ version_main=151 để uc.Chrome tự phát hiện version Chrome đã cài trong Docker
    driver = uc.Chrome(options=options)

    try:
        starnews_url = "https://member.starnewskorea.com/join/email"
        driver.get(starnews_url)

        wait = WebDriverWait(driver, 15)

        # 1. Nhập Email
        email_input = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[contains(@placeholder, '이메일')]")
            )
        )
        email_input.clear()
        email_input.send_keys(full_email)
        time.sleep(1)

        # 2. Bấm nút gửi OTP (인증요청)
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

        # 3. Đóng Popup Alert nếu xuất hiện
        try:
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            print("[+] Đã đóng popup thông báo.")
        except Exception:
            pass

        # 4. Lấy OTP từ TempMail API
        otp_code = fetch_otp_from_api(username, domain)
        if not otp_code:
            raise Exception("Không nhận được mã OTP từ API Email!")

        # 5. Nhập OTP và xác nhận (인증확인)
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

        # 6. Nhập Mật khẩu
        pass_inputs = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//input[@type='password']")
            )
        )
        pass_inputs[0].send_keys(custom_password)
        pass_inputs[1].send_keys(custom_password)
        time.sleep(1)

        # 7. Tích chọn "Đồng ý tất cả điều khoản" qua JavaScript
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

        # 8. Bấm nút Hoàn tất đăng ký (가입완료)
        btn_submit = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), '가입완료')]")
            )
        )
        btn_submit.click()
        time.sleep(3)

        # 9. Giải Turnstile Captcha nếu bị đẩy sang trang Login
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
        print(f"[-] Lỗi tiến trình đăng ký: {e}")
        raise e

    finally:
        time.sleep(2)
        try:
            driver.quit()
        except Exception:
            pass

        # Dọn dẹp tiến trình màn hình ảo Xvfb để giải phóng bộ nhớ RAM
        if display:
            display.stop()