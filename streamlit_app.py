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
                match_article = re.search(r"مادة\s*\(?\s*(\d+)", txt)
                if match_article:
                    last_article = match_article.group(1)
                for kw in kw_list:
                    if kw in txt and txt not in seen:
                        seen.add(txt)
                        before = paragraphs[i - 1].text.strip() if i > 0 else ""
                        after = paragraphs[i + 1].text.strip() if i + 1 < len(paragraphs) else ""
                        results.append({
                            "law": law_name,
                            "text": txt,
                            "uid": str(uuid.uuid4()),
                            "num": last_article,
                            "before": before,
                            "after": after
                        })
                        break

        st.session_state.results = results
        st.session_state.search_done = True

    if st.session_state.search_done and st.session_state.results:
        results = st.session_state.results
        unique_laws = sorted(set(r["law"] for r in results))
        file_count = len(unique_laws)
        file_list_str = "، ".join(unique_laws)
        st.success(f"تم العثور على {len(results)} نتيجة في {file_count} ملف: {file_list_str}")

        selected_law_filter = st.selectbox("استعرض النتائج حسب القانون", ["الكل"] + unique_laws, key="law_filter")
        filtered_results = results if selected_law_filter == "الكل" else [r for r in results if r["law"] == selected_law_filter]
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]

        all_combined_text = ""

        for r in filtered_results:
            highlighted = highlight_keywords(r["text"], kw_list)
            st.markdown(f"""
            <div style='background-color:#f1f8e9;padding:15px;margin-bottom:15px;border-radius:10px;
                        border:1px solid #c5e1a5;direction:rtl;text-align:right'>
                <p style='font-weight:bold;font-size:18px;margin:0'>🔷 {r["law"]} - المادة {r["num"]}</p>
                <p id='{r["uid"]}' style='font-size:17px;line-height:1.8;margin-top:10px'>
                    {highlight_keywords(r["before"], kw_list)}<br>
                    {highlighted}<br>
                    {highlight_keywords(r["after"], kw_list)}
                </p>
                <button onclick="navigator.clipboard.writeText('{r["law"]} - المادة {r["num"]}\n{r["text"]}');
                                 const note = document.getElementById('note_{r["uid"]}');
                                 note.style.display = 'inline';
                                 setTimeout(() => note.style.display = 'none', 1500);"
                        style='margin-top:10px;padding:6px 16px;border:none;border-radius:25px;
                               background-color:#81c784;font-weight:bold;font-size:16px;color:white;cursor:pointer'>
                    📋 نسخ المادة
                </button>
                <span id='note_{r["uid"]}' style='display:none; color:green; margin-right:10px;'>✅ تم النسخ</span>
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
