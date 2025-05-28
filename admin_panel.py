
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="لوحة الإدارة", layout="wide")

st.title("🛠️ لوحة إدارة التطبيق")

ADMIN_PASSWORD = "admin123"

# تأمين الصفحة
password = st.text_input("🔐 أدخل كلمة مرور المسؤول", type="password")
if password != ADMIN_PASSWORD:
    st.warning("يرجى إدخال كلمة مرور صحيحة للوصول إلى لوحة الإدارة.")
    st.stop()

st.success("✅ تم الدخول كمسؤول")

# عرض المستخدمين الذين استخدموا التجربة المجانية
st.header("📊 مستخدمو النسخة التجريبية")
trial_file = "trial_users.txt"

if os.path.exists(trial_file):
    df = pd.read_csv(trial_file)
    st.dataframe(df)
    st.download_button("📥 تحميل ملف المستخدمين", data=df.to_csv(index=False), file_name="trial_users.csv")
else:
    st.info("لا يوجد أي مستخدمين مسجلين حتى الآن.")

# عرض الأكواد المتبقية
st.header("🔐 الأكواد المتاحة للتفعيل")
codes_file = "activation_codes.txt"

if os.path.exists(codes_file):
    with open(codes_file, "r", encoding="utf-8") as f:
        codes = f.read().splitlines()
    st.write(f"عدد الأكواد المتبقية: {len(codes)}")
    st.code("\n".join(codes), language="text")
    st.download_button("📥 تحميل الأكواد", data="\n".join(codes), file_name="activation_codes.txt")
else:
    st.info("لا يوجد ملف أكواد.")

# إضافة كود جديد
st.header("➕ إضافة أكواد تفعيل جديدة")
new_codes = st.text_area("أدخل الأكواد الجديدة (كل كود في سطر منفصل)")

if st.button("إضافة الأكواد"):
    new_list = [c.strip() for c in new_codes.splitlines() if c.strip()]
    if new_list:
        with open(codes_file, "a", encoding="utf-8") as f:
            for code in new_list:
                f.write(code + "\n")
        st.success(f"تمت إضافة {len(new_list)} كود جديد.")
        st.experimental_rerun()
    else:
        st.warning("لم يتم إدخال أي كود.")
