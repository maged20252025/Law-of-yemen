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

# التغيير هنا: مدة التجربة 3 دقائق (180 ثانية)
TRIAL_DURATION = 180  # 3 دقائق بالثواني
TRIAL_USERS_FILE = "trial_users.txt"
DEVICE_ID_FILE = "device_id.txt" # تعريف اسم الملف هنا لسهولة الوصول إليه
ACTIVATED_FILE = "activated.txt" # تعريف اسم ملف التفعيل
ACTIVATION_CODES_FILE = "activation_codes.txt" # تعريف اسم ملف أكواد التفعيل

def get_device_id():
    # استخدام المتغير المعرف بدلاً من تكرار السلسلة
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
    # التأكد من أن الملف موجود لضمان عدم وجود خطأ عند أول تسجيل
    if not os.path.exists(TRIAL_USERS_FILE):
        with open(TRIAL_USERS_FILE, "w", newline='') as f: # استخدام newline='' لمنع الأسطر الفارغة
            pass # إنشاء الملف إذا لم يكن موجودًا
    with open(TRIAL_USERS_FILE, "a", newline='') as f: # استخدام newline='' هنا أيضًا
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
        # استخدام re.escape للتأكد من أن الكلمات المفتاحية التي تحتوي على أحرف خاصة لا تسبب مشاكل في regex
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

    if st.button("🔍 بدء البحث") and keywords:
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        results = []
        search_files = files if selected_file == "الكل" else [selected_file]

        # عرض رسالة تحميل
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
                    # نمط محسن لـ "مادة (رقم)" أو "مادة رقم"
                    match = re.match(r"مادة\s*[\(]?\s*(\d+)[\)]?", txt)
                    if match:
                        if current_article:
                            full_text = "\n".join(current_article)
                            # تحقق من وجود أي كلمة مفتاحية قبل التظليل
                            # تحويل الكلمات إلى أحرف صغيرة للمقارنة لتجاهل حالة الأحرف
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

                # إضافة المقالة الأخيرة بعد انتهاء حلقة الفقرات
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


    if st.session_state.search_done and st.session_state.results:
        results = st.session_state.results
        unique_laws = sorted(set(r["law"] for r in results))
        st.success(f"تم العثور على {len(results)} نتيجة في {len(unique_laws)} قانون/ملف.")
        selected_law = st.selectbox("فلترة حسب القانون", ["الكل"] + unique_laws)
        filtered = results if selected_law == "الكل" else [r for r in results if r["law"] == selected_law]

        for i, r in enumerate(filtered):
            # استخدام st.expander لتحسين تنظيم عرض النتائج
            with st.expander(f"🔷 {r['law']} - المادة {r['num']}", expanded=True if i < 3 else False): # افتراضيا افتح أول 3 نتائج
                st.markdown(f'''
<div style="background-color:#f1f8e9;padding:15px;margin-bottom:5px;border-radius:10px;
            border:1px solid #c5e1a5;direction:rtl;text-align:right">
    <p style="font-size:17px;line-height:1.8;margin-top:0px">
        {r["text"]}
    </p>
</div>
''', unsafe_allow_html=True)
                # استخدام key فريد لـ text_area لتجنب الأخطاء عند وجود نتائج متعددة
                st.text_area(f"📋 المادة كاملة (اضغط لتحديدها ونسخها):", value=r["plain"], height=200, key=f"plain_text_{r['law']}_{r['num']}_{i}")

def main():
    # التحقق من حالة التفعيل مرة واحدة في بداية main
    if is_activated():
        run_main_app()
        return # إنهاء الدالة بعد تشغيل التطبيق الرئيسي إذا كان مفعلًا

    # إذا لم يكن مفعلًا، نعرض خيارات التفعيل/التجربة
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("تفعيل التطبيق")
        code = st.text_input("أدخل كود التفعيل هنا", key="activation_code_input")
        if st.button("🔐 تفعيل", key="activate_button"):
            if code and activate_app(code.strip()):
                st.success("✅ تم التفعيل بنجاح! يرجى إعادة تشغيل التطبيق لتطبيق التغييرات.")
                # st.experimental_rerun() # لا حاجة لإعادة التشغيل هنا، st.stop() أو يغادر التطبيق أفضل
                st.stop() # إيقاف التطبيق مؤقتًا لفرض إعادة التشغيل من قبل المستخدم
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
                st.experimental_rerun() # إعادة تشغيل التطبيق لعرض العداد
        else:
            elapsed_time = time.time() - trial_start
            remaining_time = TRIAL_DURATION - elapsed_time

            if remaining_time > 0:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                # عرض العداد بوضوح
                st.info(f"⏳ النسخة التجريبية لا تزال نشطة. الوقت المتبقي: {minutes:02d}:{seconds:02d}")
                # التأكد من أن التطبيق يعمل في وضع Streamlit Cloud أو بيئة يتم فيها إعادة تحميل الصفحة
                # لا يمكن لـ st.experimental_rerun() أن تكون داخل loop بلا نهاية في Streamlit Cloud
                # الحل هو تحديث العداد بطريقة مختلفة أو السماح لـ Streamlit بإعادة التشغيل
                # تلقائياً في دورته العادية (وهو ما سيحدث عند تفاعل المستخدم)
                
                # إزالة time.sleep(1) و st.experimental_rerun() من هذا المكان
                # لأن Streamlit يقوم بإعادة تشغيل الكود بأكمله عند كل تفاعل أو كل ثانية
                # عندما يكون هناك عنصر تفاعلي. الأفضل هو ترك العداد يظهر فقط.

                # إذا أردت تحديثًا مستمرًا بدون تفاعل، ستحتاج إلى ميزة تحديث تلقائي خارجية
                # أو استخدام st.empty() مع تحديث مستمر (لكنه سيظل يستهلك موارد).
                # بالنسبة للسياق الحالي، الأفضل هو عرضه فقط والسماح للمستخدم بالتفاعل.
                run_main_app() # تشغيل التطبيق الرئيسي طالما التجربة نشطة

            else:
                st.error("❌ انتهت مدة التجربة المجانية لهذا الجهاز. يرجى تفعيل التطبيق.")
                # لا يوجد حاجة لزر "تفعيل التطبيق الآن" منفصل هنا،
                # لأن حقول التفعيل موجودة بالفعل في العمود الأول.


main()
