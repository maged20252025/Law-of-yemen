
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
                                "uid": str(uuid.uuid4())
                            })
                            break

            if results:
                st.success(f"تم العثور على {len(results)} نتيجة")

                for res in results:
                    with st.container():
                        st.markdown(
                            f"<div style='background-color:#f1f8e9;padding:15px;margin-bottom:15px;border-radius:10px;"
                            f"border:1px solid #c5e1a5;direction:rtl;text-align:right'><p style='font-size:17px;"
                            f"line-height:1.8;margin-top:0px'>{res['نص المادة']}</p></div>",
                            unsafe_allow_html=True
                        )
                        st.code(res["نص المادة"], language="text")
            else:
                st.warning("لم يتم العثور على أي نتائج.")
