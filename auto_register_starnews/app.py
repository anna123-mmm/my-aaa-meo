import os
import re
import time
import random
import pandas as pd
import streamlit as st
from main import run_registration
from email_captcha_api import get_2captcha_balance
from auth import check_login

st.set_page_config(page_title="Ráng tạo meo nha", layout="wide")

if not check_login():
    st.stop()
CSV_FILE = "accounts.csv"

# Khởi tạo cờ dừng tiến trình trong session_state
if "stop_processing" not in st.session_state:
    st.session_state.stop_processing = False

# Khởi tạo file CSV nếu chưa tồn tại
if not os.path.exists(CSV_FILE):
    df_init = pd.DataFrame(columns=["STT", "Email", "Password", "Thời gian tạo", "Trạng thái"])
    df_init.to_csv(CSV_FILE, index=False)

def load_accounts():
    return pd.read_csv(CSV_FILE)

def save_account(email, password, status="Thành công"):
    df = load_accounts()
    new_id = len(df) + 1
    new_row = {
        "STT": new_id,
        "Email": email,
        "Password": password,
        "Thời gian tạo": time.strftime("%Y-%m-%d %H:%M:%S"),
        "Trạng thái": status
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

# ==========================================
# THANH SIDEBAR: CHECK 2CAPTCHA
# ==========================================
with st.sidebar:
    st.title("⚙️ Cấu Hình Hệ Thống")
    if st.button("Check Số Dư 2Captcha", width="stretch"):
        bal = get_2captcha_balance()
        if bal is not None:
            st.success(f"Số dư 2Captcha: **${bal:.3f}**")
        else:
            st.error("Không lấy được số dư. Kiểm tra lại API Key!")

# ==========================================
# CHIA GIAO DIỆN THÀNH 2 NỬA
# ==========================================
col_left, col_right = st.columns([1, 1], gap="large")

# ------------------------------------------
# NỬA PHẢI: BẢNG DỮ LIỆU & NÚT BẤM
# ------------------------------------------
with col_right:
    st.header("Sheet meo AAA")
    
    table_placeholder = st.empty()

    def update_table_view():
        """Hàm chỉ cập nhật hiển thị của bảng dữ liệu"""
        df_accounts = load_accounts()
        table_placeholder.dataframe(
            df_accounts, 
            width="stretch", 
            height=450,
            hide_index=True
        )

    # Hiển thị bảng lần đầu
    update_table_view()

    # Tạo dữ liệu xuất CSV
    df_current = load_accounts()
    df_export = df_current[["Email", "Password"]] if not df_current.empty else pd.DataFrame(columns=["Email", "Password"])
    csv_data = df_export.to_csv(index=False).encode('utf-8')

    btn_col1, btn_col2 = st.columns([2, 1])
    
    with btn_col1:
        st.download_button(
            label="Tải xuống CSV (Chỉ Email & Password)",
            data=csv_data,
            file_name="starnews_accounts.csv",
            mime="text/csv",
            key="static_download_btn",
            width="stretch"
        )
        
    with btn_col2:
        if st.button("Xóa bảng", type="primary", key="static_reset_btn", width="stretch"):
            df_empty = pd.DataFrame(columns=["STT", "Email", "Password", "Thời gian tạo", "Trạng thái"])
            df_empty.to_csv(CSV_FILE, index=False)
            st.toast("Đã làm sạch dữ liệu cũ!")
            time.sleep(0.3)
            st.rerun()

# ------------------------------------------
# NỬA TRÁI: CHATBOT ĐIỀU KHUYỂN
# ------------------------------------------
with col_left:
    st.header("Tool tạo meo AAA")
    st.caption("Cú pháp ví dụ: 'tạo 5 tài khoản với mật khẩu Eomland113'")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Nhập: 'tạo [số lượng] tài khoản với mật khẩu Eomland113' để bắt đầu."}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("Nhập.."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        match_count = re.search(r'(\d+)\s*tài khoản', user_input, re.IGNORECASE)
        match_pass = re.search(r'mật khẩu\s+([^\s]+)', user_input, re.IGNORECASE)

        if match_count and match_pass:
            count = int(match_count.group(1))
            password = match_pass.group(1)

            # Reset cờ dừng về False mỗi khi chạy lượt mới
            st.session_state.stop_processing = False

            response_msg = f"Bắt đầu tiến trình tạo **{count}** tài khoản..."
            st.session_state.messages.append({"role": "assistant", "content": response_msg})
            with st.chat_message("assistant"):
                st.write(response_msg)

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Đặt nút Ngừng tiến trình ngay dưới thanh tiến trình
            stop_btn_placeholder = st.empty()
            if stop_btn_placeholder.button("Ngừng Tiến Trình", key="stop_btn", type="secondary", width="stretch"):
                st.session_state.stop_processing = True

            completed_count = 0
            for i in range(count):
                # Kiểm tra xem người dùng có bấm nút Ngừng không
                if st.session_state.stop_processing:
                    st.warning("Tiến trình đã dừng lại!")
                    break

                status_text.text(f"Đang tạo tài khoản {i+1}/{count}...")
                
                try:
                    created_email = run_registration(custom_password=password)
                    if created_email:
                        save_account(created_email, password, "Thành công")
                        update_table_view()
                except Exception as e:
                    save_account("Lỗi tạo acc", password, f"Lỗi: {e}")
                    update_table_view()
                    if "HẾT TIỀN" in str(e) or "2Captcha" in str(e):
                        st.error(f"Dừng luồng tạo do lỗi: {e}")
                        break

                completed_count = i + 1
                progress_bar.progress(completed_count / count)
                
                # Kiểm tra lại lần nữa trước khi nghỉ delay
                if st.session_state.stop_processing:
                    st.warning("Tiến trình đã dừng lại!")
                    break

                if i < count - 1:
                    sleep_time = random.randint(2, 5)
                    for remaining in range(sleep_time, 0, -1):
                        if st.session_state.stop_processing:
                            break
                        status_text.text(f"Tạm nghỉ {remaining} giây trước khi tạo tài khoản tiếp theo...")
                        time.sleep(1)

            # Xóa nút dừng sau khi xong hoặc đã dừng
            stop_btn_placeholder.empty()

            if st.session_state.stop_processing:
                final_msg = f"Đã dừng tiến trình. Đã tạo được {completed_count}/{count} tài khoản."
            else:
                final_msg = f"Đã hoàn tất đợt tạo {count} tài khoản!"

            st.session_state.messages.append({"role": "assistant", "content": final_msg})
            status_text.text(final_msg)
            st.rerun()

        else:
            err_msg = "Cú pháp chưa đúng. Dạng chuẩn: **'tạo [số lượng] tài khoản với mật khẩu [mật khẩu]'**"
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
            with st.chat_message("assistant"):
                st.write(err_msg)