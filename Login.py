import streamlit as st
import os
from datetime import datetime

USER_CREDENTIALS = {
    "username": "password",
}


# 登录函数
def login():
    username = st.session_state['username']
    password = st.session_state['password']
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Logged in as {username}\n".encode())
        st.session_state['username_logged'] = username
        st.session_state['logged_in'] = True
        os.write(1, f"{'-'*80} \n".encode())
    else:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Failed to log in as {username}\n".encode())
        st.error("Incorrect username or password. Please try again.")


def show_login_page():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Logging in...\n".encode())
    with st.container(border=True):
        st.title("Login")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        c1, c2 = st.columns([8, 1])
        c1.empty()
        c2.button("Login", on_click=login, use_container_width=True)


if __name__ == "__main__":
    show_login_page()
