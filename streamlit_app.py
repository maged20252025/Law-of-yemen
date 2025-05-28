
import streamlit as st
from docx import Document
import re
import uuid
import os

st.set_page_config(page_title="القوانين اليمنية", layout="wide")
st.title("القوانين اليمنية")

laws_dir = "laws"

if not os.path.exists(laws_dir):
    st.error("⚠️ مجلد 'laws/' غير موجود في المشروع.")
else:
    available_files = [f for f in os.listdir(laws_dir) if f.endswith(".docx")]

    if not available_files:
        st.warning("📂 لا توجد ملفات قوانين داخل مجلد 'laws/'.")
    else:
        selected_file_name = st.selectbox("اختر قانونًا للبحث داخله أو اختر 'الكل' للبحث في جميع الملفات", ["الكل"] + available_files)
        keywords = st.text_area("الكلمات المفتاحية (افصل كل كلمة بفاصلة)", "")

        search_button = st.button("🔍 بدء البحث")

        if search_button and keywords:
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
            results = []
            seen_paragraphs = set()

            files_to_search = available_files if selected_file_name == "الكل" else [selected_file_name]

            for filename in files_to_search:
                filepath = os.path.join(laws_dir, filename)
                doc = Document(filepath)
                current_law = filename.replace(".docx", "")

                for para in doc.paragraphs:
                    paragraph_text = para.text.strip()

                    for keyword in keyword_list:
                        if keyword in paragraph_text and paragraph_text not in seen_paragraphs:
                            seen_paragraphs.add(paragraph_text)
                            results.append({
                                "القانون": current_law,
                                "نص المادة": paragraph_text,
                                "uid": str(uuid.uuid4()),
                                "رقم المادة": re.search(r"مادة\s*\(?\s*(\d+)", paragraph_text).group(1)
                                    if re.search(r"مادة\s*\(?\s*(\d+)", paragraph_text) else "غير معروفة"
                            })
                            break

            if results:
                st.success(f"تم العثور على {len(results)} نتيجة")

                for res in results:
                    uid = res["uid"]
                    article_num = res["رقم المادة"]
                    law_name = res["القانون"]
                    st.markdown(f"""
                    <div style='background-color:#f1f8e9;padding:15px;margin-bottom:15px;border-radius:10px;
                                border:1px solid #c5e1a5;direction:rtl;text-align:right'>
                        <p id="{uid}" style='font-size:17px;line-height:1.8;margin-top:0px'>{res["نص المادة"]}</p>
                        <button onclick="navigator.clipboard.writeText(document.getElementById('{uid}').innerText);
                                         const note = document.getElementById('note_{uid}');
                                         note.style.display = 'inline';
                                         setTimeout(() => note.style.display = 'none', 1500);"
                                style='margin-top:10px;padding:6px 10px;border:none;border-radius:5px;
                                       background-color:#aed581;cursor:pointer'>
                            📋 نسخ المادة رقم {article_num} - {law_name}
                        </button>
                        <span id="note_{uid}" style="display:none; color:green; margin-right:10px;'>✅ تم النسخ</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("لم يتم العثور على أي نتائج.")
