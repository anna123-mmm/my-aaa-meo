import os
import streamlit as st

# ==========================================
# THÔNG TIN TÀI KHOẢN & MẬT KHẨU
# ==========================================
USER_CREDENTIALS = {
    "xuongcongnhanmeo": "meomeolumbeui"
}

def load_css(file_name="style.css"):
    """Đọc file CSS bên ngoài và nhúng vào Streamlit"""
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def check_login():
    """Hàm kiểm tra đăng nhập - luôn bắt đăng nhập khi mở tab mới"""
    # 1. Tải giao diện CSS màu hồng
    load_css()

    # 2. Reset đăng nhập nếu mở tab/cửa sổ mới
    if "_has_run" not in st.session_state:
        st.session_state._has_run = True
        st.session_state.logged_in = False

    # 3. Nếu đã đăng nhập thành công thì trả về True để vào app.py
    if st.session_state.get("logged_in", False):
        return True

    # 4. Vẽ giao diện Form Đăng Nhập
    _, col2, _ = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>ĐĂNG NHẬP</h2>", unsafe_allow_html=True)
        st.caption("<p style='text-align: center; color: #FF6B8B;'>Chỉ người dễ thương mới được vào thui ak</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", placeholder="").strip()
            password = st.text_input("Mật khẩu", type="password", placeholder="").strip()
            submit_btn = st.form_submit_button("Đăng nhập", use_container_width=True, type="secondary")

            if submit_btn:
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Nhập sai tên hoặc mật khẩu rùi")

    return False