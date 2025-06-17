import io

import streamlit as st
import streamlit.components.v1 as components
from docx import Document
import re
import uuid
import os
import time
import html
import csv

st.set_page_config(page_title="القوانين اليمنية بآخر تعديلاتها حتى عام 2025م", layout="wide")
st.markdown("<h1 style='text-align: center;'>مرحبًا بك في تطبيق القوانين اليمنية بآخر تعديلاتها حتى عام 2025م</h1>", unsafe_allow_html=True)

TRIAL_DURATION = 300  # ساعة واحدة بالثواني
TRIAL_USERS_FILE = "trial_users.txt"

def get_device_id():
    device_id_file = "device_id.txt"
    if os.path.exists(device_id_file):
        with open(device_id_file, "r") as f:
            return f.read().strip()
    new_id = str(uuid.uuid4())
    with open(device_id_file, "w") as f:
        f.write(new_id)
    return new_id

def get_trial_start(device_id):
    if not os.path.exists(TRIAL_USERS_FILE):
        return None
    with open(TRIAL_USERS_FILE, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0] == device_id:
                return float(row[1])
    return None

def register_trial(device_id):
    with open(TRIAL_USERS_FILE, "a") as f:
        writer = csv.writer(f)
        writer.writerow([device_id, time.time()])

def is_activated():
    return os.path.exists("activated.txt")

def activate_app(code):
    if not os.path.exists("activation_codes.txt"):
        return False
    with open("activation_codes.txt", "r") as f:
        codes = [line.strip() for line in f.readlines()]
    if code in codes:
        codes.remove(code)
        with open("activation_codes.txt", "w") as f:
            for c in codes:
                f.write(c + "\n")
        with open("activated.txt", "w") as f:
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
    <button class='scroll-btn' id='scroll-top-btn' onclick='window.scrollTo({top: 0, behavior: "smooth"});'>⬆️</button>
    <button class='scroll-btn' id='scroll-bottom-btn' onclick='window.scrollTo({top: document.body.scrollHeight, behavior: "smooth"});'>⬇️</button>
    """, height=1)

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

    
    col_search, col_export = st.columns([1, 1])
    with col_search:
        search_clicked = st.button("🔍 بدء البحث")
    with col_export:
        export_clicked = st.button("📤 تصدير النتائج إلى Word")

    if search_clicked and keywords:

        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        results = []
        search_files = files if selected_file == "الكل" else [selected_file]

        for file in search_files:
            doc = Document(os.path.join(laws_dir, file))
            law_name = file.replace(".docx", "")
            last_article = "غير معروفة"
            current_article = []
            for para in doc.paragraphs:
                txt = para.text.strip()
                if not txt:
                    continue
                match = re.match(r"مادة\s*\(?\s*(\d+)\)?", txt)
                if match:
                    if current_article:
                        full_text = "\n".join(current_article)
                        if any(kw in full_text for kw in kw_list):
                            highlighted = highlight_keywords(full_text, kw_list)
                            results.append({
                                "law": law_name,
                                "num": last_article,
                                "text": highlighted,
                                "plain": full_text
                            })
                        current_article = []
                    last_article = match.group(1)
                current_article.append(txt)

            if current_article:
                full_text = "\n".join(current_article)
                if any(kw in full_text for kw in kw_list):
                    highlighted = highlight_keywords(full_text, kw_list)
                    results.append({
                        "law": law_name,
                        "num": last_article,
                        "text": highlighted,
                        "plain": full_text
                    })

        st.session_state.results = results
        st.session_state.search_done = True

    if st.session_state.search_done and st.session_state.results:
        results = st.session_state.results
        unique_laws = sorted(set(r["law"] for r in results))
        st.success(f"تم العثور على {len(results)} نتيجة في {len(unique_laws)} قانون/ملف.")
        selected_law = st.selectbox("فلترة حسب القانون", ["الكل"] + unique_laws)
        filtered = results if selected_law == "الكل" else [r for r in results if r["law"] == selected_law]

        for r in filtered:
        if filtered:
            if export_clicked:
                doc = Document()
                doc.add_heading("نتائج البحث", 0)
                for r in filtered:
                    doc.add_heading(f"{r['law']} - المادة {r['num']}", level=1)
                    doc.add_paragraph(r['plain'])
                buffer = io.BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button("⬇️ تحميل الملف", data=buffer, file_name="نتائج البحث.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            st.markdown(f'''
<div style="background-color:#f1f8e9;padding:15px;margin-bottom:15px;border-radius:10px;
            border:1px solid #c5e1a5;direction:rtl;text-align:right">
    <p style="font-weight:bold;font-size:18px;margin:0">🔷 {r["law"]} - المادة {r["num"]}</p>
    <p style="font-size:17px;line-height:1.8;margin-top:10px">
        {r["text"]}
    </p>
</div>
''', unsafe_allow_html=True)

            st.text_area("📋 المادة كاملة (اضغط لتحديدها ونسخها):", value=r["plain"], height=200)

def main():
    if not is_activated():
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔐 لدي كود تفعيل"):
                code = st.text_input("أدخل كود التفعيل هنا")
                if code and activate_app(code.strip()):
                    st.success("✅ تم التفعيل! أعد تشغيل التطبيق.")
        with col2:
            device_id = get_device_id()
            trial_start = get_trial_start(device_id)
            if trial_start is None:
                if st.button("🕒 تجربة مجانية"):
                    register_trial(device_id)
                    st.success("✅ بدأت النسخة التجريبية.")
                    run_main_app()
            elif time.time() - trial_start < TRIAL_DURATION:
                remaining = int(TRIAL_DURATION - (time.time() - trial_start))
    mins, secs = divmod(remaining, 60)
    st.info(f"✅ النسخة التجريبية لا تزال نشطة. الوقت المتبقي: {mins:02d}:{secs:02d}")
                run_main_app()
            else:
                st.error("❌ انتهت مدة التجربة المجانية لهذا الجهاز.")
    else:
        run_main_app()

main()
