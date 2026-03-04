import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile
import platform

# --- ИСПРАВЛЕННЫЙ БЛОК УСТАНОВКИ ---
def install_typst():
    # 1. Проверка для Windows
    if platform.system() == "Windows":
        return "typst" # Используем системную команду
    
    # 2. Логика для Linux (Streamlit Cloud)
    bin_path = "typst_bin/typst"
    if not os.path.exists(bin_path):
        os.makedirs("typst_bin", exist_ok=True)
        url = "https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
        archive = "typst.tar.xz"
        try:
            urllib.request.urlretrieve(url, archive)
            with tarfile.open(archive, "r:xz") as tar:
                tar.extractall(path="typst_bin")
            # Поиск исполняемого файла в распакованной папке
            for root, dirs, files in os.walk("typst_bin"):
                if "typst" in files and root != "typst_bin":
                    os.rename(os.path.join(root, "typst"), bin_path)
                    break
            os.chmod(bin_path, 0o755)
            if os.path.exists(archive): os.remove(archive)
        except Exception as e:
            st.error(f"Failed to install Typst: {e}")
            return "typst" # Пробуем упасть на системную команду

    return "./" + bin_path

# ВЫЗЫВАЕМ ОДИН РАЗ
TYPST_PATH = install_typst()# Получаем правильный путь в зависимости от системы
install_typst()
FIXED_TEMPLATE = "template2.typ" # Шаблон зафиксирован

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
languages = {
    "en": {
        "title": "🍺 Beer Stat Generator",
        "description": "Upload an Excel file to generate a PDF report. The data for the transfer must be on the first sheet",
        "lang_label": "Select Language:",
        "file_label": "Choose Excel file (.xlsx)",
        "button": "Generate PDF",
        "success": "PDF created successfully!",
        "download": "📥 Download Report (PDF)",
        "error": "An error occurred:",
        "lang": "English"
    },
    "🇨🇿": {
        "title": "🍺 Generátor pivních statistik",
        "description": "Nahrajte soubor Excel pro vytvoření PDF reportu. Údaje pro převod musí být na prvním listu",
        "lang_label": "Vyberte jazyk:",
        "file_label": "Vyberte soubor Excel (.xlsx)",
        "button": "Generovat PDF",
        "success": "PDF bylo úspěšně vytvořeno!",
        "download": "📥 Stáhnout report (PDF)",
        "error": "Došlo k chybě:",
        "lang": "cheština"
    }
}

# 1. Выбор языка теперь первым элементом в центре
# Этот код нужно вставить ПЕРЕД отрисовкой selectbox
st.markdown("""
    <style>
    /* Находим контейнер выбора языка и выравниваем его содержимое вправо */
    div[data-testid="stSelectbox"] {
        margin-left: auto;
        width: 80px !important;
        padding: 0px;
        min-height: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
temp_lang_list = list(languages.keys())
lang_choice = st.selectbox("", temp_lang_list, index=0)
t = languages[lang_choice]

# 2. Основной контент
st.title(t["title"])
# st.info(f"Using template: {FIXED_TEMPLATE}") # Просто уведомление, какой шаблон используется
st.write(t["description"])

# 3. Загрузка файла
uploaded_file = st.file_uploader(t["file_label"], type="xlsx")

if uploaded_file is not None:
    if st.button(t["button"]):
        try:
            df = pd.read_excel(uploaded_file, sheet_name=1)
            
            rename_map = {
                "Značka piva": "brand_name",
                "Země původu": "origin_country",
                "Počet": "quantity"
            }
            df = df.rename(columns=rename_map)
            
            os.makedirs('data', exist_ok=True)
            df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)

            output_path = "output/beer_report.pdf"
            os.makedirs('output', exist_ok=True)
            
            # Используем FIXED_TEMPLATE
            command = [
                TYPST_PATH, "compile", 
                "--root", ".", 
                f"templates/{FIXED_TEMPLATE}", 
                output_path
            ]

            subprocess.run(command, check=True)
            st.success(t["success"])
            with open(output_path, "rb") as f:
                st.download_button(
                    label=t["download"],
                    data=f,
                    file_name="beer_report.pdf",
                    mime="application/pdf"
                )
            
        except Exception as e:
            st.error(f"{t['error']} {e}")