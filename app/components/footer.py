import streamlit as st

def render_footer():
    members = [
        "23120283 · Phạm Quốc Khánh",
        "23120301 · Phạm Thành Nam",
        "23120318 · Trương Quang Phát",
        "23120329 · Châu Huỳnh Phúc",
        "23120334 · Huỳnh Tấn Phước",
    ]
    chips = "".join([f'<span class="az-footer-chip">{m}</span>' for m in members])

    footer_html = """
        <div class="az-footer-wrap">
            <div class="az-footer-left">
                Trường Đại Học Khoa Học Tự Nhiên · Khoa CNTT · Trực Quan Hóa Dữ Liệu
            </div>
            <div class="az-footer-marquee">
                <div class="az-footer-track">
                    __CHIPS____CHIPS__
                </div>
            </div>
    </div>
    """

    st.markdown(footer_html.replace("__CHIPS__", chips), unsafe_allow_html=True)
