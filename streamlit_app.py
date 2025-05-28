
import streamlit as st
from docx import Document
import re
import uuid

st.set_page_config(page_title="القوانين اليمنية", layout="wide")

st.title("القوانين اليمنية")

uploaded_files = st.file_uploader("ارفع ملف أو عدة ملفات Word (docx)", type="docx", accept_multiple_files=True)

keywords = st.text_area("الكلمات المفتاحية (افصل كل كلمة بفاصلة)", "")

selected_file_name = None
if uploaded_files:
    filenames = [f.name for f in uploaded_files]
    selected_file_name = st.selectbox("اختر ملفًا للبحث داخله أو اختر 'الكل' للبحث في جميع الملفات", ["الكل"] + filenames)

search_button = st.button("🔍 بدء البحث")

if uploaded_files and search_button:
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    results = []
    seen_paragraphs = set()

    files_to_search = uploaded_files if selected_file_name == "الكل" else [f for f in uploaded_files if f.name == selected_file_name]

    for uploaded_file in files_to_search:
        doc = Document(uploaded_file)
        current_law = "قانون غير معروف"

        for para in doc.paragraphs:
            paragraph_text = para.text.strip()

            if "قانون" in paragraph_text and len(paragraph_text) < 100:
                current_law = paragraph_text

            for keyword in keyword_list:
                if keyword in paragraph_text and paragraph_text not in seen_paragraphs:
                    seen_paragraphs.add(paragraph_text)
                    results.append({
                        "القانون": current_law,
                        "نص المادة": paragraph_text,
                        "uid": str(uuid.uuid4())
                    })
                    break

    if results:
        st.success(f"تم العثور على {len(results)} نتيجة")

        for res in results:
            uid = res["uid"]
            st.markdown(f"""
            <div style='background-color:#f1f8e9;padding:15px;margin-bottom:15px;border-radius:10px;border:1px solid #c5e1a5;direction:rtl;text-align:right'>
                <p id="{uid}" style='font-size:17px;line-height:1.8;margin-top:0px'>{res["نص المادة"]}</p>
                <button onclick="navigator.clipboard.writeText(document.getElementById('{uid}').innerText);
                                 const note = document.getElementById('note_{uid}');
                                 note.style.display = 'inline';
                                 setTimeout(() => note.style.display = 'none', 2000);"
                        style='margin-top:10px;padding:6px 10px;border:none;border-radius:5px;background-color:#aed581;cursor:pointer'>
                    📋 نسخ المادة
                </button>
                <span id="note_{uid}" style="display:none; color:green; margin-right:10px;'>✅ تم النسخ</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("لم يتم العثور على أي نتائج.")
