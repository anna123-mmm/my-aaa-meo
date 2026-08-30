import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from email_captcha_api import fetch_otp_from_api, generate_random_email


def run_registration(custom_password="Password123!"):
  driver = None

  try:
    username, domain, full_email = generate_random_email()
    print(f"[+] Tạo email mới: {full_email}", flush=True)

    # 1. Cấu hình undetected-chromedriver ngụy trang Chrome thật (Chống Cloudflare phát hiện)
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")

    # Giả lập User-Agent Windows chuẩn của Chrome thật
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    # Giả lập đồ họa WebGL để vượt qua Browser Fingerprinting
    options.add_argument("--enable-webgl")
    options.add_argument("--use-gl=swiftshader")
    options.add_argument("--enable-unsafe-swiftshader")

    # Tắt các cờ báo hiệu Selenium/Automation
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")

    # Chạy ẩn (Headless) nếu trên server Linux
    is_headless = os.name != "nt"
    if is_headless:
      print(
          "[+] Đang chạy ở chế độ Chrome Headless (Linux Server).", flush=True
      )

    # Khởi tạo Undetected Driver với cơ chế tự động xử lý lệch phiên bản Chrome (151 / 152)
    try:
      driver = uc.Chrome(options=options, headless=is_headless)
    except Exception as err:
      err_str = str(err)
      if "version" in err_str.lower() or "151" in err_str:
        print(
            "[!] Lệch version trình duyệt trên Server, ép dùng driver"
            " version_main=151...",
            flush=True,
        )
        driver = uc.Chrome(
            options=options, headless=is_headless, version_main=151
        )
      else:
        raise err

    print(
        "[+] Khởi tạo Chrome (Undetected) thành công! Đang truy cập trang"
        " web...",
        flush=True,
    )

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
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[text()='인증요청' or contains(text(), '인증요청')]",
        ))
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
            "//input[contains(@placeholder, '6') or contains(@placeholder,"
            " '인증') or @name='code' or @type='number']",
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

    # Step 6: Nhập Mật khẩu
    print("[+] Đang nhập mật khẩu...", flush=True)
    pass_inputs = driver.find_elements(By.XPATH, "//input[@type='password']")
    if len(pass_inputs) >= 2:
      pass_inputs[0].clear()
      pass_inputs[0].send_keys(custom_password)
      pass_inputs[1].clear()
      pass_inputs[1].send_keys(custom_password)
      print("[+] Đã nhập xong mật khẩu.", flush=True)
    else:
      print(
          "[-] Không tìm thấy 2 ô nhập mật khẩu qua type=password, thử tìm"
          " lại...",
          flush=True,
      )
      pass_inputs = wait.until(
          EC.presence_of_all_elements_located(
              (By.XPATH, "//input[@type='password']")
          )
      )
      pass_inputs[0].send_keys(custom_password)
      pass_inputs[1].send_keys(custom_password)

    time.sleep(1)

    # Step 7: Tích chọn "Đồng ý tất cả điều khoản"
    print("[+] Đang tích chọn đồng ý tất cả điều khoản...", flush=True)
    try:
      chk_all = driver.find_element(
          By.XPATH,
          "//*[contains(text(), '모두 동의') or contains(text(), '모두동의') or"
          " @id='agreeAll' or contains(@class, 'all')]",
      )
      driver.execute_script("arguments[0].click();", chk_all)
    except Exception:
      checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
      if checkboxes:
        driver.execute_script("arguments[0].click();", checkboxes[0])
    print("[+] Đã tích chọn đồng ý điều khoản.", flush=True)
    time.sleep(1)

    # Step 8: Chờ Cloudflare Turnstile tự động xác thực (Ngụy trang trình duyệt sạch)
    print(
        "[+] Tiến hành kiểm tra và chờ Cloudflare Turnstile tự xác thực...",
        flush=True,
    )
    time.sleep(3)  # Chờ 3 giây để Cloudflare tự nhận diện môi trường sạch

   # Step 9: Bấm nút Hoàn tất đăng ký (Hỗ trợ nhiều XPATH & click JS để tránh Timeout)
    print("[+] Đang bấm hoàn tất đăng ký...", flush=True)
    try:
      # Thử các XPATH phổ biến cho nút đăng ký hoàn tất
      btn_submit = wait.until(
          EC.presence_of_element_located((
              By.XPATH,
              "//button[contains(text(), '가입완료')] |"
              " //button[contains(text(), '회원가입')] | //button[@type='submit']"
              " | //a[contains(text(), '가입완료')]",
          ))
      )
      driver.execute_script("arguments[0].scrollIntoView(true);", btn_submit)
      time.sleep(1)
      driver.execute_script("arguments[0].click();", btn_submit)
    except Exception as submit_err:
      print(
          f"[-] Không tìm thấy nút bằng WebDriverWait, thử click bằng JS tất cả"
          f" submit button: {submit_err}",
          flush=True,
      )
      # Fallback: Click vào button type submit bất kỳ trên form
      submits = driver.find_elements(
          By.XPATH, "//button[@type='submit'] | //button"
      )
      if submits:
        driver.execute_script("arguments[0].click();", submits[-1])

    # Step 10: Kiểm tra xác nhận từ Server & Chuyển hướng
    print("[+] Đang chờ kiểm tra kết quả phản hồi từ Server...", flush=True)
    start_wait = time.time()
    success = False

    while time.time() - start_wait < 12:
      current_url = driver.current_url

      # Bắt trang Đăng nhập hoặc trang Hoàn tất đăng ký (일반 회원가입 완료)
      if any(
          k in current_url for k in ["login", "complete", "success", "result"]
      ) or "완료" in driver.page_source:
        success = True
        print(
            "[+] Đã phát hiện trang Đăng ký thành công (일반 회원가입"
            " 완료)!",
            flush=True,
        )

        # Thao tác bấm nút màu đỏ "로그인으로 이동" nếu nút này xuất hiện
        try:
          btn_go_login = driver.find_element(
              By.XPATH,
              "//button[contains(text(), '로그인으로 이동')] |"
              " //a[contains(text(), '로그인으로 이동')]",
          )
          driver.execute_script("arguments[0].click();", btn_go_login)
          print("[+] Đã ấn nút màu đỏ chuyển hướng về đăng nhập.", flush=True)
        except Exception:
          pass
        break

      time.sleep(1)

    # Nếu sau 12 giây vẫn ở trang form đăng ký (join) -> Báo lỗi
    if not success and "join" in driver.current_url:
      raise Exception(
          "Đăng ký thất bại! Server không chuyển trang (Bị kẹt tại form)."
      )

    print(
        f"[+] Đã xác nhận Đăng ký thành công trên Server: {full_email}",
        flush=True,
    )
    return full_email

  except Exception as e:
    print(
        f"[-] Lỗi trong tiến trình đăng ký ({type(e).__name__}): {e}",
        flush=True,
    )
    raise e

  finally:
    time.sleep(1)
    if driver:
      try:
        driver.quit()
      except Exception:
        pass