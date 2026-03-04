import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile

# --- ФУНКЦИЯ УСТАНОВКИ TYPST ---
def install_typst():
    if not os.path.exists("typst_bin/typst"):
        with st.spinner("Установка Typst..."):
            os.makedirs("typst_bin", exist_ok=True)
            # Ссылка на версию для Linux x64
            url = "https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
            archive = "typst.tar.xz"
            urllib.request.urlretrieve(url, archive)
            
            # Распаковка
            with tarfile.open(archive, "r:xz") as tar:
                tar.extractall(path="typst_bin")
            
            # Находим сам файл (он распаковывается в подпапку)
            for root, dirs, files in os.walk("typst_bin"):
                if "typst" in files:
                    os.rename(os.path.join(root, "typst"), "typst_bin/typst")
                    break
            
            os.chmod("typst_bin/typst", 0o755) # Даем права на запуск
            os.remove(archive)

# Запускаем установку
install_typst()
TYPST_PATH = "./typst_bin/typst"

localisation = {
    "en": {
        "load-file": "Upload Excel file (.xlsx)",
        "generate-pdf": "Generate PDF",
    },
    "cz": {
        "load-file": "Upload Excel file (.xlsx)",
        "generate-pdf": "Generate PDF",
    },
    "ru": {
        "load-file": "Загрузите Excel-файл (.xlsx), чтобы получить PDF-отчет по шаблону.",
        "generate-pdf": "Сгенерировать PDF",
    }
}


# --- ДАЛЕЕ ВАШ ОСНОВНОЙ КОД ---
# ... (title, file_uploader и т.д.)
st.set_page_config(page_title="Beer Stat PDF Generator", page_icon="🍺")

# 1. Выбор языка
langs_options = ["en", "cz", "ru"]
# selected_lang = st.selectbox("", langs_options)

cur_lang = "en"
# if selected_lang:
#     cur_lang = selected_lang
cur_locale = localisation[cur_lang]


st.title("🍺 Beer Stat Generator")

selected_template = "template2.typ"

# 2. Загрузка файла
uploaded_file = st.file_uploader(cur_locale["load-file"], type="xlsx")

if uploaded_file is not None:
    if st.button(cur_locale["generate-pdf"]):
        try:
            # Читаем данные напрямую из загруженного файла
            df = pd.read_excel(uploaded_file, sheet_name=1)

            # Ваша логика переименования
            rename_map = {
                "Značka piva": "brand_name",
                "Země původu": "origin_country",
                "Počet": "quantity"
            }
            df = df.rename(columns=rename_map)

            # Сохраняем временный JSON (Typst берет данные отсюда)
            os.makedirs('data', exist_ok=True)
            df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)

            # Подготовка путей
            output_path = "output/beer_report.pdf"
            os.makedirs('output', exist_ok=True)

            # Команда для Typst
           # Исправленная команда
            command = [
            TYPST_PATH, "compile",  # Используем путь к скачанному бинарнику
            "--root", ".", 
            f"templates/{selected_template}", 
            output_path
            ]
            # Запуск компиляции
            subprocess.run(command, check=True)
            
            st.success("PDF успешно создан!")

            # Кнопка для скачивания готового файла
            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 Скачать отчет (PDF)",
                    data=f,
                    file_name="beer_report.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")