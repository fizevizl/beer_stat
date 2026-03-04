import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile

# --- УСТАНОВКА TYPST (как делали раньше) ---
def install_typst():
    if not os.path.exists("typst_bin/typst"):
        os.makedirs("typst_bin", exist_ok=True)
        url = "https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
        archive = "typst.tar.xz"
        urllib.request.urlretrieve(url, archive)
        with tarfile.open(archive, "r:xz") as tar:
            tar.extractall(path="typst_bin")
        for root, dirs, files in os.walk("typst_bin"):
            if "typst" in files:
                os.rename(os.path.join(root, "typst"), "typst_bin/typst")
                break
        os.chmod("typst_bin/typst", 0o755)
        if os.path.exists(archive): os.remove(archive)

install_typst()
TYPST_PATH = "./typst_bin/typst"

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
languages = {
    "English": {
        "title": "🍺 Beer Stat Generator",
        "description": "Upload an Excel file to generate a PDF report.",
        "template_label": "Select Template:",
        "file_label": "Choose Excel file (.xlsx)",
        "button": "Generate PDF",
        "success": "PDF created successfully!",
        "download": "📥 Download Report (PDF)",
        "error": "An error occurred:"
    },
    "Čeština 🇨🇿": {
        "title": "🍺 Generátor pivních statistik",
        "description": "Nahrajte soubor Excel pro vytvoření PDF reportu.",
        "template_label": "Vyberte šablonu:",
        "file_label": "Vyberte soubor Excel (.xlsx)",
        "button": "Generovat PDF",
        "success": "PDF bylo úspěšně vytvořeno!",
        "download": "📥 Stáhnout report (PDF)",
        "error": "Došlo k chybě:"
    },
    "Русский": {
        "title": "🍺 Генератор статистики пива",
        "description": "Загрузите Excel-файл для создания PDF-отчета.",
        "template_label": "Выберите шаблон:",
        "file_label": "Выберите Excel файл (.xlsx)",
        "button": "Сгенерировать PDF",
        "success": "PDF успешно создан!",
        "download": "📥 Скачать отчет (PDF)",
        "error": "Произошла ошибка:"
    }
}

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---

# Панель выбора языка в сайдбаре (сбоку)
st.sidebar.title("Settings / Настройки")
lang_choice = st.sidebar.selectbox("Language / Язык", list(languages.keys()), index=0) # Index 0 = English
t = languages[lang_choice] # Переменная t теперь содержит все тексты на выбранном языке

st.title(t["title"])
st.write(t["description"])

# Выбор шаблона
template_options = ["template1.typ", "template2.typ"]
selected_template = st.selectbox(t["template_label"], template_options)

# Загрузка файла
uploaded_file = st.file_uploader(t["file_label"], type="xlsx")

if uploaded_file is not None:
    if st.button(t["button"]):
        try:
            df = pd.read_excel(uploaded_file, sheet_name=1)
            
            # Логика обработки данных
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

            command = [
                TYPST_PATH, "compile", 
                "--root", ".", 
                f"templates/{selected_template}", 
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