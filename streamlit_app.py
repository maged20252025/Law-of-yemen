import streamlit as st import streamlit.components.v1 as components from docx import Document from docx.shared import Pt import re import uuid import os import time from io import BytesIO from docx import Document as DocxDocument

st.set_page_config(page_title="القوانين اليمنية بآخر تعديلاتها حتى عام 2025م", layout="wide") st.markdown("<h1 style='text-align: center;'>مرحبًا بك في تطبيق القوانين اليمنية بآخر تعديلاتها حتى عام 2025م</h1>", unsafe_allow_html=True)

ACTIVATION_FILE = "activation_codes.txt" ACTIVATION_STATE = "activated.txt"

def is_activated(): return os.path.exists(ACTIVATION_STATE)

def activate_app(code): if not os.path.exists(ACTIVATION_FILE): return False with open(ACTIVATION_FILE, "r") as f: codes = [line.strip() for line in f.readlines()] if code in codes: codes.remove(code) with open(ACTIVATION_FILE, "w") as f: for c in codes: f.write(c + "\n") with open(ACTIVATION_STATE, "w") as f: f.write("activated") return True return False

def highlight_keywords(text, keywords): for kw in keywords: text = re.sub(f"({re.escape(kw)})", r"<mark>\1</mark>", text, flags=re.IGNORECASE) return text

def run_main_app(): components.html(""" <style> .scroll-btn { position: fixed; left: 10px; padding: 12px; font-size: 24px; border-radius: 50%; background-color: #c5e1a5; color: black; cursor: pointer; z-index: 9999; border: none; box-shadow: 1px 1px 5px #888; } #scroll-top-btn { bottom: 80px; } #scroll-bottom-btn { bottom: 20px; } </style> <button class='scroll-btn' id='scroll-top-btn' onclick='window.scrollTo({top: 0, behavior: "smooth"});'>⬆️</button> <button class='scroll-btn' id='scroll-bottom-btn' onclick='window.scrollTo({top: document.body.scrollHeight, behavior: "smooth"});'>⬇️</button> """, height=1)

laws_dir = "laws"
if not os.path.exists(laws_dir):
    st.error("⚠️ مجلد 'laws/' غير موجود.")
    return

files = [f for f in os.listdir(laws_dir) if f.endswith(".docx")]
if not files:
    st.warning("📂 لا توجد ملفات قوانين.")
    return

selected_file = st.selectbox("اختر قانونًا أو 'الكل' للبحث في الجميع", ["الكل"] + files)
keywords = st.text_area("الكلمات المفتاحية (افصل بفاصلة)", "")

if "results" not in st.session_state:
    st.session_state.results = []
if "search_done" not in st.session_state:
    st.session_state.search_done = False

if st.button("🔍 بدء البحث") and keywords:
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    seen = set()
    results = []
    search_files = files if selected_file == "الكل" else [selected_file]

    for file in search_files:
        doc = Document(os.path.join(laws_dir, file))
        law_name = file.replace(".docx", "")
        last_article = "غير معروفة"
        paragraphs = doc.paragraphs
        for i, para in enumerate(paragraphs):
            txt = para.text.strip()
            if not txt:
                continue
            match_article = re.search(r"مادة\s*

