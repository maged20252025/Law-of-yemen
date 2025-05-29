
import streamlit as st
import streamlit.components.v1 as components
from docx import Document
import re
import uuid
import os
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="القوانين اليمنية", layout="wide")

# رسالة ترحيب
if "welcomed" not in st.session_state:
    st.session_state.welcomed = True
    st.success("مرحباً بك في تطبيق القوانين اليمنية بآخر تعديلاتها حتى عام 2025م")

# ملفات التفعيل والتجربة
ACTIVATION_FILE = "activation_codes.json"
TRIAL_FILE = "trial_users.json"

# تحميل بيانات التفعيل
def load_json(file):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f)

activation_codes = load_json(ACTIVATION_FILE)
trial_users = load_json(TRIAL_FILE)

# معرف الجهاز (بسيط)
device_id = str(uuid.uuid4())[:8]
st.session_state["device_id"] = device_id

# التحقق من التفعيل
if "activated" not in st.session_state:
    st.session_state.activated = False

if not st.session_state.activated:
    st.markdown("### يرجى اختيار طريقة الوصول إلى التطبيق:")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔑 لدي كود تفعيل"):
            code = st.text_input("أدخل كود التفعيل هنا:")
            if code and code in activation_codes and not activation_codes[code]["used"]:
                activation_codes[code]["used"] = True
                activation_codes[code]["device"] = device_id
                save_json(ACTIVATION_FILE, activation_codes)
                st.session_state.activated = True
                st.success("تم تفعيل النسخة بنجاح.")
            elif code:
                st.error("❌ كود غير صالح أو مستخدم من قبل.")

    with col2:
        if st.button("🧪 تجربة مجانية لمدة 5 دقائق"):
            if device_id not in trial_users:
                trial_users[device_id] = {"start_time": datetime.now().isoformat()}
                save_json(TRIAL_FILE, trial_users)
                st.session_state.activated = True
                st.success("تم بدء التجربة المجانية.")
            else:
                start = datetime.fromisoformat(trial_users[device_id]["start_time"])
                if datetime.now() - start < timedelta(minutes=5):
                    st.session_state.activated = True
                    st.success("أهلاً بك مجدداً، التجربة لا تزال فعالة.")
                else:
                    st.error("انتهت مدة التجربة المجانية.")

if not st.session_state.activated:
    st.stop()

# أسهم عائمة للتنقل
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
#scroll-top-btn {
    bottom: 80px;
}
#scroll-bottom-btn {
    bottom: 20px;
}
</style>
<button class="scroll-btn" id="scroll-top-btn" onclick="window.scrollTo({top: 0, behavior: 'smooth'});">⬆️</button>
<button class="scroll-btn" id="scroll-bottom-btn" onclick="window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});">⬇️</button>
""", height=1)

# بحث القوانين
laws_dir = "laws"
if not os.path.exists(laws_dir):
    st.error("⚠️ مجلد 'laws/' غير موجود.")
else:
    files = [f for f in os.listdir(laws_dir) if f.endswith(".docx")]
    if not files:
        st.warning("لا توجد ملفات داخل مجلد القوانين.")
    else:
        selected = st.selectbox("اختر قانونًا أو الكل", ["الكل"] + files)
        keywords = st.text_area("الكلمات المفتاحية (افصل بفاصلة)")

        if st.button("🔍 بدء البحث") and keywords:
            kws = [k.strip() for k in keywords.split(",") if k.strip()]
            results = []
            seen = set()
            files_to_search = files if selected == "الكل" else [selected]

            for file in files_to_search:
                doc = Document(os.path.join(laws_dir, file))
                law_title = file.replace(".docx", "")
                for para in doc.paragraphs:
                    text = para.text.strip()
                    for kw in kws:
                        if kw in text and text not in seen:
                            seen.add(text)
                            num_match = re.search(r"مادة\s*\(?\s*(\d+)", text)
                            article_num = num_match.group(1) if num_match else "غير معروفة"
                            uid = str(uuid.uuid4())
                            results.append({
                                "law": law_title,
                                "text": text,
                                "num": article_num,
                                "uid": uid
                            })
                            break
            if results:
                st.success(f"تم العثور على {len(results)} نتيجة")
                for r in results:
                    st.markdown(f"""
                    <div style='background-color:#f1f8e9;padding:15px;margin-bottom:15px;border-radius:10px;
                                border:1px solid #c5e1a5;direction:rtl;text-align:right'>
                        <p id="{r["uid"]}" style='font-size:17px;line-height:1.8;margin-top:0px'>{r["text"]}</p>
                        <button onclick="navigator.clipboard.writeText(document.getElementById('{r["uid"]}').innerText);
                                         const note = document.getElementById('note_{r["uid"]}');
                                         note.style.display = 'inline';
                                         setTimeout(() => note.style.display = 'none', 1500);"
                                style='margin-top:10px;padding:6px 10px;border:none;border-radius:5px;
                                       background-color:#aed581;cursor:pointer'>
                            📋 نسخ المادة رقم {r["num"]} - {r["law"]}
                        </button>
                        <span id="note_{r["uid"]}" style="display:none; color:green; margin-right:10px;'>✅ تم النسخ</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("لم يتم العثور على أي نتائج.")
