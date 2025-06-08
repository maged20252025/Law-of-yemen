import streamlit as st
import streamlit.components.v1 as components
from docx import Document
from docx.shared import Pt
import re
import uuid
import os
import time
from io import BytesIO
from docx import Document as DocxDocument

st.set_page_config(page_title="القوانين اليمنية بآخر تعديلاتها حتى عام 2025م", layout="wide")
st.markdown("<h1 style='text-align: center;'>مرحبًا بك في تطبيق القوانين اليمنية بآخر تعديلاتها حتى عام 2025م</h1>", unsafe_allow_html=True)

ACTIVATION_FILE = "activation_codes.txt"
ACTIVATION_STATE = "activated.txt"

def is_activated():
    return os.path.exists(ACTIVATION_STATE)

def activate_app(code):
    if not os.path.exists(ACTIVATION_FILE):
        return False
    with open(ACTIVATION_FILE, "r") as f:
        codes = [line.strip() for line in f.readlines()]
    if code in codes:
        codes.remove(code)
        with open(ACTIVATION_FILE, "w") as f:
            for c in codes:
                f.write(c + "\n")
        with open(ACTIVATION_STATE, "w") as f:
            f.write("activated")
        return True
    return False

def highlight_keywords(text, keywords):
    for kw in keywords:
        text = re.sub(f"({re.escape(kw)})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)
    return text

def run_main_app():
    components.html("""
    <style>
    .scroll-btn {
        position: fixed;
        left: 10px;
        padding: 12px;
        font-size: 24px;
        border-radius: 50%;
        background-color: #c5e1a5;
        color: black;
        cursor: pointer;
        z-index: 9999;
        border: none;
        box-shadow: 1px 1px 5px #888;
    }
    #scroll-top-btn { bottom: 80px; }
    #scroll-bottom-btn { bottom: 20px; }
    </style>
    
            </div>
            """, unsafe_allow_html=True)
            all_combined_text += f"{r['law']} - المادة {r['num']}\n{r['text']}\n\n"

        st.download_button("📋 نسخ جميع النتائج", all_combined_text, file_name="نتائج_القوانين.txt")

def main():
    if not is_activated():
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔐 لدي كود تفعيل"):
                code = st.text_input("أدخل كود التفعيل هنا")
                if code:
                    if activate_app(code.strip()):
                        st.success("✅ تم التفعيل بنجاح! أعد تشغيل التطبيق.")
                    else:
                        st.error("❌ الكود غير صالح أو تم استخدامه من قبل.")
        with col2:
            if "trial_start" not in st.session_state:
                if st.button("🕒 تجربة مجانية"):
                    st.session_state.trial_start = time.time()
                    run_main_app()
            elif time.time() - st.session_state.trial_start < 300:
                st.info("✅ أنت تستخدم النسخة التجريبية.")
                run_main_app()
            else:
                st.error("❌ انتهت مدة التجربة المجانية. يرجى التفعيل لمواصلة الاستخدام.")
    else:
        run_main_app()

main()
