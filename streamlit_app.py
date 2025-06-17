import streamlit as st
import streamlit.components.v1 as components
from docx import Document
from docx.shared import Inches
import re
import uuid
import os
import time
import html
import csv

st.set_page_config(page_title="القوانين اليمنية بآخر تعديلاتها حتى عام 2025م", layout="wide")
st.markdown("<h1 style='text-align: center;'>مرحبًا بك في تطبيق القوانين اليمنية بآخر تعديلاتها حتى عام 2025م</h1>", unsafe_allow_html=True)

TRIAL_DURATION = 180  # 3 دقائق بالثواني
TRIAL_USERS_FILE = "trial_users.txt"
DEVICE_ID_FILE = "device_id.txt"
ACTIVATED_FILE = "activated.txt"
ACTIVATION_CODES_FILE = "activation_codes.txt"

def get_device_id():
    if os.path.exists(DEVICE_ID_FILE):
        with open(DEVICE_ID_FILE, "r") as f:
            return f.read().strip()
    new_id = str(uuid.uuid4())
    with open(DEVICE_ID_FILE, "w") as f:
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
    if not os.path.exists(TRIAL_USERS_FILE):
        with open(TRIAL_USERS_FILE, "w", newline='') as f:
            pass
    with open(TRIAL_USERS_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([device_id, time.time()])

def is_activated():
    return os.path.exists(ACTIVATED_FILE)

def activate_app(code):
    if not os.path.exists(ACTIVATION_CODES_FILE):
        return False
    with open(ACTIVATION_CODES_FILE, "r") as f:
        codes = [line.strip() for line in f.readlines()]
    if code in codes:
        codes.remove(code)
        with open(ACTIVATION_CODES_FILE, "w") as f:
            for c in codes:
                f.write(c + "\n")
        with open(ACTIVATED_FILE, "w") as f:
            f.write("activated")
        return True
    return False

def highlight_keywords(text, keywords):
    for kw in keywords:
        text = re.sub(f"({re.escape(kw)})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)
    return text

# دالة جديدة لتصدير النتائج إلى ملف Word
def export_results_to_word(results, filename="نتائج_البحث.docx"):
    document = Document()
    document.add_heading('نتائج البحث في القوانين اليمنية', level=1)
    
    if not results:
        document.add_paragraph("لم يتم العثور على نتائج للكلمات المفتاحية المحددة.")
    else:
        for i, r in enumerate(results):
            document.add_heading(f"القانون: {r['law']} - المادة: {r['num']}", level=2)
            # إضافة المحتوى كنص عادي (بدون تمييز HTML)
            document.add_paragraph(r['plain'])
            document.add_page_break() # إضافة فاصل صفحات بين كل نتيجة

    # حفظ المستند في ذاكرة مؤقتة (BytesIO)
    from io import BytesIO
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


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
        st.error("⚠️ مجلد 'laws/' غير موجود. يرجى التأكد من وجود ملفات القوانين.")
        return

    files = [f for f in os.listdir(laws_dir) if f.endswith(".docx")]
    if not files:
        st.warning("📂 لا توجد ملفات قوانين في مجلد 'laws/'.")
        return

    selected_file = st.selectbox("اختر قانونًا أو 'الكل' للبحث في الجميع", ["الكل"] + files)
    keywords = st.text_area("الكلمات المفتاحية (افصل بفاصلة)", "")

    if "results" not in st.session_state:
        st.session_state.results = []
    if "search_done" not in st.session_state:
        st.session_state.search_done = False

    # استخدام st.columns لوضع الأزرار جنبًا إلى جنب
    col_search_btn, col_export_btn = st.columns([0.2, 0.8]) # تحديد عرض الأعمدة

    with col_search_btn:
        if st.button("🔍 بدء البحث") and keywords:
            kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
            results = []
            search_files = files if selected_file == "الكل" else [selected_file]

            with st.spinner("جاري البحث في القوانين... قد يستغرق الأمر بعض الوقت."):
                for file in search_files:
                    try:
                        doc = Document(os.path.join(laws_dir, file))
                    except Exception as e:
                        st.warning(f"⚠️ تعذر قراءة الملف {file}: {e}. يرجى التأكد من أنه ملف DOCX صالح.")
                        continue

                    law_name = file.replace(".docx", "")
                    last_article = "غير معروفة"
                    current_article = []
                    for para in doc.paragraphs:
                        txt = para.text.strip()
                        if not txt:
                            continue
                        match = re.match(r"مادة\s*[\(]?\s*(\d+)[\)]?", txt)
                        if match:
                            if current_article:
                                full_text = "\n".join(current_article)
                                if any(kw.lower() in full_text.lower() for kw in kw_list):
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
                        if any(kw.lower() in full_text.lower() for kw in kw_list):
                            highlighted = highlight_keywords(full_text, kw_list)
                            results.append({
                                "law": law_name,
                                "num": last_article,
                                "text": highlighted,
                                "plain": full_text
                            })

            st.session_state.results = results
            st.session_state.search_done = True
            if not results:
                st.info("لم يتم العثور على نتائج للكلمات المفتاحية المحددة.")
    
    with col_export_btn:
        # زر التصدير يظهر فقط إذا كانت هناك نتائج للبحث
        if st.session_state.search_done and st.session_state.results:
            export_data = export_results_to_word(st.session_state.results)
            st.download_button(
                label="⬇️ تصدير النتائج إلى Word",
                data=export_data,
                file_name="نتائج_البحث_القوانين_اليمنية.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_button_word"
            )
        elif st.session_state.search_done and not st.session_state.results:
             st.info("لا توجد نتائج لتصديرها.")


    if st.session_state.search_done and st.session_state.results:
        results = st.session_state.results
        unique_laws = sorted(set(r["law"] for r in results))
        st.success(f"تم العثور على {len(results)} نتيجة في {len(unique_laws)} قانون/ملف.")
        selected_law = st.selectbox("فلترة حسب القانون", ["الكل"] + unique_laws)
        filtered = results if selected_law == "الكل" else [r for r in results if r["law"] == selected_law]

        for i, r in enumerate(filtered):
            with st.expander(f"🔷 {r['law']} - المادة {r['num']}", expanded=True if i < 3 else False):
                st.markdown(f'''
<div style="background-color:#f1f8e9;padding:15px;margin-bottom:5px;border-radius:10px;
            border:1px solid #c5e1a5;direction:rtl;text-align:right">
    <p style="font-size:17px;line-height:1.8;margin-top:0px">
        {r["text"]}
    </p>
</div>
''', unsafe_allow_html=True)
                st.text_area(f"📋 المادة كاملة (اضغط لتحديدها ونسخها):", value=r["plain"], height=200, key=f"plain_text_{r['law']}_{r['num']}_{i}")

def main():
    if is_activated():
        run_main_app()
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("تفعيل التطبيق")
        code = st.text_input("أدخل كود التفعيل هنا", key="activation_code_input")
        if st.button("🔐 تفعيل", key="activate_button"):
            if code and activate_app(code.strip()):
                st.success("✅ تم التفعيل بنجاح! يرجى إعادة تشغيل التطبيق لتطبيق التغييرات.")
                st.stop()
            else:
                st.error("❌ كود التفعيل غير صحيح أو انتهت صلاحيته.")
    with col2:
        st.subheader("النسخة التجريبية")
        device_id = get_device_id()
        trial_start = get_trial_start(device_id)

        if trial_start is None:
            if st.button("🕒 بدء التجربة المجانية", key="start_trial_button"):
                register_trial(device_id)
                st.success("✅ بدأت النسخة التجريبية الآن. لديك 3 دقائق.")
                st.session_state.trial_started_this_session = True # علم لبدء العرض
        
        if "trial_started_this_session" in st.session_state and st.session_state.trial_started_this_session:
             trial_start = get_trial_start(device_id) # أعد قراءة القيمة لتحديثها بعد التسجيل
             st.session_state.trial_started_this_session = False # أعد تعيينها لتجنب إعادة القراءة المستمرة

        if trial_start is not None:
            elapsed_time = time.time() - trial_start
            remaining_time = TRIAL_DURATION - elapsed_time

            if remaining_time > 0:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                st.info(f"⏳ النسخة التجريبية لا تزال نشطة. الوقت المتبقي: {minutes:02d}:{seconds:02d}")
                run_main_app()
            else:
                st.error("❌ انتهت مدة التجربة المجانية لهذا الجهاز. يرجى تفعيل التطبيق.")

main()
