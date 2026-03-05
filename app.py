import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile
import platform
import io
from pathlib import Path

# --- УСТАНОВКА TYPST (ДЛЯ ОБЛАКА) ---
def install_typst():
    if platform.system() == "Windows":
        return "typst"
    
    bin_dir = os.path.abspath("typst_executable")
    bin_path = os.path.join(bin_dir, "typst")
    
    if not os.path.exists(bin_path):
        os.makedirs(bin_dir, exist_ok=True)
        url = "https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
        archive = "typst.tar.xz"
        try:
            urllib.request.urlretrieve(url, archive)
            with tarfile.open(archive, "r:xz") as tar:
                tar.extractall(path=bin_dir)
            for root, dirs, files in os.walk(bin_dir):
                if "typst" in files and root != bin_dir:
                    os.replace(os.path.join(root, "typst"), bin_path)
                    break
            os.chmod(bin_path, 0o775) 
            if os.path.exists(archive): os.remove(archive)
        except Exception as e:
            st.error(f"Failed to install Typst: {e}")
            return "typst"
    return bin_path

# --- ЛОГИКА ПРЕОБРАЗОВАНИЯ ДЛЯ ОБЛАКА (БЕЗ EXCEL) ---
def load_excel_data(uploaded_file):
    """
    Универсальная логика чтения: пробует XLSX, бинарный XLS и XML-XLS.
    Работает в Linux/Cloud без установленного Microsoft Office.
    """
    try:
        # 1. Пробуем стандартный pandas (xlsx или правильный xls)
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file, sheet_name=0)
    except Exception:
        try:
            # 2. Пробуем старый бинарный формат (xlrd)
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file, sheet_name=0, engine='xlrd')
        except Exception:
            try:
                # 3. Если это XML-XLS (тот самый заголовок <?xml), читаем как HTML/XML таблицу
                uploaded_file.seek(0)
                # Нужны библиотеки: lxml, beautifulsoup4
                tables = pd.read_html(uploaded_file, flavor='bs4')
                if tables:
                    return tables[0]
                else:
                    raise ValueError("Таблицы не найдены внутри XML")
            except Exception as e:
                st.error(f"Ошибка при чтении файла: {e}")
                return None

# --- ИНИЦИАЛИЗАЦИЯ ---
TYPST_PATH = install_typst()
FIXED_TEMPLATE = "template2.typ"

st.title("🍺 Beer Stat Generator (Cloud Version)")

uploaded_file = st.file_uploader("Выберите файл (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Используем нашу логику преобразования
    df = load_excel_data(uploaded_file)
    
    if df is not None:
        # Показываем превью того, что прочитали
        st.write("Превью данных из файла:")
        st.dataframe(df.head(3))

        if st.button("Сгенерировать PDF"):
            try:
                # Очистка и подготовка колонок
                # Если всё слиплось в одну колонку (бывает в CSV-подобных XLS)
                if df.shape[1] == 1:
                    df = df.iloc[:, 0].astype(str).str.split(';', expand=True)

                # Берем первые 3 колонки
                df = df.iloc[:, :3]
                df.columns = ["brand_name", "origin_country", "quantity"]

                # Финальная чистка данных
                df = df.dropna(subset=["brand_name"])
                df["quantity"] = pd.to_numeric(df["quantity"], errors='coerce').fillna(0).astype(int)
                df = df[df["quantity"] > 0]

                # Сохранение JSON для Typst
                os.makedirs('data', exist_ok=True)
                df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)

                # Компиляция PDF
                output_path = "output/beer_report.pdf"
                os.makedirs('output', exist_ok=True)
                
                command = [TYPST_PATH, "compile", "--root", ".", f"templates/{FIXED_TEMPLATE}", output_path]
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode != 0:
                    st.error(f"Typst Error: {result.stderr}")
                else:
                    st.success("PDF успешно создан!")
                    with open(output_path, "rb") as f:
                        st.download_button("📥 Скачать отчет", f, "beer_report.pdf", "application/pdf")
            
            except Exception as e:
                st.error(f"Ошибка обработки: {e}")