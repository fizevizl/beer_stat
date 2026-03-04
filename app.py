import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile
import platform

# --- ИСПРАВЛЕННЫЙ БЛОК УСТАНОВКИ ---
def install_typst():
    if platform.system() == "Windows":
        return "typst"
    
    bin_path = "typst_bin/typst"
    if not os.path.exists(bin_path):
        os.makedirs("typst_bin", exist_ok=True)
        url = "https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
        archive = "typst.tar.xz"
        try:
            urllib.request.urlretrieve(url, archive)
            with tarfile.open(archive, "r:xz") as tar:
                tar.extractall(path="typst_bin")
            for root, dirs, files in os.walk("typst_bin"):
                if "typst" in files and root != "typst_bin":
                    os.rename(os.path.join(root, "typst"), bin_path)
                    break
            os.chmod(bin_path, 0o755)
            if os.path.exists(archive): os.remove(archive)
        except Exception as e:
            st.error(f"Failed to install Typst: {e}")
            return "typst"
    return "./" + bin_path

TYPST_PATH = install_typst()
FIXED_TEMPLATE = "template2.typ"

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
languages = {
    "en": {
        "title": "🍺 Beer Stat Generator",
        "description": "Upload an Excel file to generate a PDF report. The data for the transfer must be on the second sheet.",
        "file_label": "Choose Excel file (.xlsx)",
        "button": "Generate PDF",
        "success": "PDF created successfully!",
        "download": "📥 Download Report (PDF)",
        "error": "An error occurred:",
    },
    "🇨🇿": {
        "title": "🍺 Generátor pivních statistik",
        "description": "Nahrajte soubor Excel pro vytvoření PDF reportu. Údaje pro převod musí být на druhém listu.",
        "file_label": "Vyberte soubor Excel (.xlsx)",
        "button": "Generovat PDF",
        "success": "PDF bylo úspěšně vytvořeno!",
        "download": "📥 Stáhnout report (PDF)",
        "error": "Došlo k chybě:",
    }
}

# --- ИНТЕРФЕЙС ---
st.markdown("""
    <style>
    div[data-testid="stSelectbox"] {
        margin-left: auto;
        width: 100px !important;
    }
    </style>
    """, unsafe_allow_html=True)

temp_lang_list = list(languages.keys())
lang_choice = st.selectbox("", temp_lang_list, index=0)
t = languages[lang_choice]

st.title(t["title"])
st.write(t["description"])

# 3. Загрузка файла
uploaded_file = st.file_uploader(t["file_label"], type="xlsx")

if uploaded_file is not None:
    # Определяем параметры листов
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    sheet_num = 2  # Индекс 1 — это второй лист в Excel
    
    # Кнопка генерации (теперь она ОДНА)
    if st.button(t["button"]):
        try:
            # Читаем только первые 3 колонки (индексы 0, 1, 2)
            df = pd.read_excel(uploaded_file, sheet_name=sheet_num, usecols=[0, 1, 2])

            df = df.dropna(subset=[df.columns[0]])
            
            # Переименовываем колонки по индексам для надежности
            rename_map = {
                df.columns[0]: "brand_name",
                df.columns[1]: "origin_country",
                df.columns[2]: "quantity"
            }
            df = df.rename(columns=rename_map)
            
            # Сохраняем данные для Typst
            os.makedirs('data', exist_ok=True)
            df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)

            # Путь к результату
            output_path = "output/beer_report.pdf"
            os.makedirs('output', exist_ok=True)
            
            # Запуск компиляции
            command = [
                TYPST_PATH, "compile", 
                "--root", ".", 
                f"templates/{FIXED_TEMPLATE}", 
                output_path
            ]

            # Замените subprocess.run(command, check=True) на этот блок:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                st.error(f"Typst Error: {result.stderr}") # Это покажет реальную причину
                st.stop()
            
            st.success(t["success"])
            
            # Кнопка скачивания
            with open(output_path, "rb") as f:
                st.download_button(
                    label=t["download"],
                    data=f,
                    file_name="beer_report.pdf",
                    mime="application/pdf"
                )
            
        except Exception as e:
            st.error(f"{t['error']} {e}")