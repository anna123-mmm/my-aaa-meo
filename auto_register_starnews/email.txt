import time
import random
import string
import re
import requests
from config import API_KEY_2CAPTCHA

# Header giả lập trình duyệt thực để API tempmail.plus không chặn request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest"
}

def generate_random_email():
    """Tạo username ngẫu nhiên cho dịch vụ tempmail.plus với đuôi @mailto.plus"""
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = "mailto.plus"
    return username, domain, f"{username}@{domain}"

def fetch_otp_from_api(username, domain="mailto.plus", max_wait=40):
    """Lấy mã OTP 6 chữ số từ API tempmail.plus"""
    email = f"{username}@{domain}"
    print(f"[+] Đang chờ OTP gửi về: {email}...")
    
    inbox_url = f"https://tempmail.plus/api/mails?email={email}&limit=10"
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(inbox_url, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                data = response.json()
                mail_list = data.get("mail_list", [])
                
                if mail_list:
                    print(f"[+] Đã nhận được {len(mail_list)} thư mới!")
                    for mail in mail_list:
                        mail_id = mail.get("mail_id") or mail.get("id")
                        
                        detail_url = f"https://tempmail.plus/api/mails/{mail_id}?email={email}"
                        detail_res = requests.get(detail_url, headers=HEADERS, timeout=5)
                        
                        if detail_res.status_code == 200:
                            mail_data = detail_res.json()
                            body = mail_data.get("text", "") or mail_data.get("html", "")
                            
                            # Quét tìm mã 6 chữ số bằng Regex
                            match = re.search(r'\b\d{6}\b', body)
                            if match:
                                otp = match.group(0)
                                print(f"[+] Lấy thành công mã OTP: {otp}")
                                return otp
        except Exception as e:
            print(f"[-] Đang kết nối lại API TempMail: {e}")
            
        time.sleep(3)
        
    print("[-] Hết thời gian chờ nhưng không nhận được OTP.")
    return None

def get_2captcha_balance():
    """Kiểm tra số dư hiện tại trong tài khoản 2Captcha ($)"""
    url = f"http://2captcha.com/res.php?key={API_KEY_2CAPTCHA}&action=getbalance&json=1"
    try:
        res = requests.get(url, timeout=5).json()
        if res.get("status") == 1:
            return float(res.get("request"))
        else:
            print(f"[-] Lỗi check số dư 2Captcha: {res.get('request')}")
            return None
    except Exception as e:
        print(f"[-] Lỗi kết nối 2Captcha API: {e}")
        return None

def solve_cloudflare(page_url, site_key):
    """Giải Cloudflare Turnstile Captcha và kiểm tra an toàn số dư"""
    balance = get_2captcha_balance()
    if balance is not None:
        print(f"[💰] Số dư 2Captcha hiện tại: ${balance:.3f}")
        if balance < 0.003:
            raise Exception("⚠️ Tài khoản 2Captcha HẾT TIỀN (Số dư < $0.003). Vui lòng nạp thêm tiền!")

    url_in = "http://2captcha.com/in.php"
    payload = {
        'key': API_KEY_2CAPTCHA,
        'method': 'turnstile',
        'sitekey': site_key,
        'pageurl': page_url,
        'json': 1
    }
    try:
        res = requests.post(url_in, data=payload).json()
        if res.get("status") != 1:
            err_code = res.get("request")
            if err_code == "ERROR_ZERO_BALANCE":
                raise Exception("⚠️ Tài khoản 2Captcha HẾT TIỀN (ERROR_ZERO_BALANCE)!")
            elif err_code == "ERROR_KEY_DOES_NOT_EXIST":
                raise Exception("⚠️ API Key 2Captcha KHÔNG HỢP LỆ!")
            else:
                return None
        
        request_id = res["request"]
        url_out = f"http://2captcha.com/res.php?key={API_KEY_2CAPTCHA}&action=get&id={request_id}&json=1"
        
        for _ in range(30):
            time.sleep(4)
            res_code = requests.get(url_out).json()
            if res_code.get("status") == 1:
                return res_code.get("request")
            elif res_code.get("request") != "CAPCHA_NOT_READY":
                return None
    except Exception as e:
        raise e
    return None