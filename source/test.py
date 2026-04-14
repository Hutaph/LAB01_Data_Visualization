import streamlit as st

st.title("Hello world 👋")
st.write("Đây là app đầu tiên của tôi")

name = st.text_input("Nhập tên bạn:")

if name:
    st.write(f"Hello {name} 😎")