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

            last_seen_article = None  # لحفظ آخر مادة تم العثور عليها
            for para in doc.paragraphs:
                txt = para.text.strip()
                for kw in kw_list:
                    if kw in txt and txt not in seen:
                        seen.add(txt)
                        match = re.search(r"مادة\s*\(?\s*(\d+)", txt)
                        if match:
                            last_seen_article = match.group(1)
                        results.append({
                            "law": law_name,
                            "text": txt,
                            "uid": str(uuid.uuid4()),
                            "num": last_seen_article if last_seen_article else "غير معروفة"
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

        unique_laws = sorted(set(r["law"] for r in results))
        selected_law_filter = st.selectbox("استعرض النتائج حسب القانون", ["الكل"] + unique_laws, key="law_filter")

        filtered_results = results if selected_law_filter == "الكل" else [
            r for r in results if r["law"] == selected_law_filter
        ]

        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]

        for r in filtered_results:
            highlighted = highlight_keywords(r["text"], kw_list)
            st.markdown(f"""
            <div style='background-color:#f1f8e9;padding:15px;margin-bottom:15px;border-radius:10px;
                        border:1px solid #c5e1a5;direction:rtl;text-align:right'>
                <p id='{r["uid"]}' style='font-size:17px;line-height:1.8;margin-top:0px'>{highlighted}</p>
                <button onclick="navigator.clipboard.writeText(document.getElementById('{r["uid"]}').innerText);
                                 const note = document.getElementById('note_{r["uid"]}');
                                 note.style.display = 'inline';
                                 setTimeout(() => note.style.display = 'none', 1500);"
                        style='margin-top:10px;padding:6px 16px;border:none;border-radius:25px;
                               background-color:#81c784;font-weight:bold;font-size:16px;color:white;cursor:pointer'>
                    {r["law"]}
                </button>
                <span id='note_{r["uid"]}' style='display:none; color:green; margin-right:10px;'>✅ تم النسخ</span>
            </div>
            """, unsafe_allow_html=True)

        
        if st.button("📄 تحميل النتائج كملف Word"):
            docx_out = DocxDocument()
            style = docx_out.styles['Normal']
            font = style.font
            font.name = 'Arial'
            font.size = Pt(14)

            for r in filtered_results:
                # العنوان: اسم القانون + المادة
                p = docx_out.add_paragraph()
                run = p.add_run(f"{r['law']} - المادة {r['num']}")
                run.bold = True
                run.font.size = Pt(16)
                p.paragraph_format.alignment = 2  # يمين

                # الفقرة: نص المادة
                p2 = docx_out.add_paragraph()
                p2.paragraph_format.alignment = 2  # يمين
                words = re.split(r'(\s+)', r["text"])
                for w in words:
                    run = p2.add_run(w)
                    if any(kw.lower() in w.lower() for kw in kw_list):
                        run.font.highlight_color = 3  # أصفر
                    run.font.size = Pt(14)

                docx_out.add_paragraph("")  # فاصل

            buffer = BytesIO()
            docx_out.save(buffer)
            st.download_button("⬇️ تحميل ملف Word", buffer.getvalue(), file_name="نتائج_القوانين.docx")


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
