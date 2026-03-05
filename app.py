import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile
import platform
import io  # Добавлено для конвертации в памяти

# --- БЛОК УСТАНОВКИ ---
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
            if os.path.exists(archive): 
                os.remove(archive)
        except Exception as e:
            st.error(f"Failed to install Typst: {e}")
            return "typst"
            
    return bin_path

TYPST_PATH = install_typst()
FIXED_TEMPLATE = "template2.typ"

# --- СЛОВАРЬ ПЕРЕВОДОВ ---
languages = {
    "en": {
        "title": "🍺 Beer Stat Generator",
        "description": "Upload an Excel file to generate a PDF report. The data for the transfer must be on the first sheet.",
        "file_label": "Choose Excel file (.xlsx, .xls)",
        "button": "Generate PDF",
        "success": "PDF created successfully!",
        "download": "📥 Download Report (PDF)",
        "error": "An error occurred:",
    },
    "🇨🇿": {
        "title": "🍺 Generátor pivních statistik",
        "description": "Nahrajte soubor Excel pro vytvoření PDF reportu. Údaje pro převod musí být na prvním listu.",
        "file_label": "Vyberte soubor Excel (.xlsx, .xls)",
        "button": "Generovat PDF",
        "success": "PDF было успешно vytvořeno!",
        "download": "📥 Stáhnout report (PDF)",
        "error": "Došlo k chybě:",
    }
}

# --- ИНТЕРФЕЙС ---
st.markdown("""
    <style>
    div[data-testid="stSelectbox"] {
        margin-left: auto;
        width: 80px !important;
    }
    </style>
    """, unsafe_allow_html=True)

temp_lang_list = list(languages.keys())
lang_choice = st.selectbox("", temp_lang_list, index=0)
t = languages[lang_choice]

st.title(t["title"])
st.write(t["description"])

# Загрузка файла (теперь принимает и xls)
uploaded_file = st.file_uploader(t["file_label"], type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # --- УЛУЧШЕННЫЙ БЛОК ЧТЕНИЯ (Поддержка XML-XLS) ---
        df_dict = None
        
        try:
            # 1. Пробуем прочитать как стандартный Excel (xlsx или честный xls)
            df_dict = pd.read_excel(uploaded_file, sheet_name=None)
        except Exception:
            try:
                # 2. Если упало, пробуем движок xlrd (старый бинарный xls)
                uploaded_file.seek(0)
                df_dict = pd.read_excel(uploaded_file, sheet_name=None, engine='xlrd')
            except Exception:
                # 3. Если всё еще ошибка "Expected BOF record", значит это XML-таблица
                uploaded_file.seek(0)
                # Читаем HTML-таблицу внутри XML
                tables = pd.read_html(uploaded_file)
                if tables:
                    # Имитируем словарь листов для совместимости с остальным кодом
                    df_dict = {"Sheet1": tables[0]}
                else:
                    raise ValueError("Could not find any tables in the file.")

        # Конвертируем всё в XLSX в памяти для унификации
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, df_sheet in df_dict.items():
                df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
        output.seek(0)
        processed_file = output

        # Определяем параметры листов
        xls_tool = pd.ExcelFile(processed_file)
        sheet_names = xls_tool.sheet_names
        sheet_num = 0  # Первый лист

        if st.button(t["button"]):
            # Читаем только первые 3 колонки
            df = pd.read_excel(processed_file, sheet_name=sheet_num, usecols=[0, 1, 2])
            
            # Очистка пустых строк
            df = df.dropna(subset=[df.columns[0]])
            
            # Переименование колонок
            rename_map = {
                df.columns[0]: "brand_name",
                df.columns[1]: "origin_country",
                df.columns[2]: "quantity"
            }
            df = df.rename(columns=rename_map)
            
            # Сохраняем JSON
            os.makedirs('data', exist_ok=True)
            df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)

            # Путь к PDF
            output_path = "output/beer_report.pdf"
            os.makedirs('output', exist_ok=True)
            
            command = [
                TYPST_PATH, "compile", 
                "--root", ".", 
                f"templates/{FIXED_TEMPLATE}", 
                output_path
            ]

            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                st.error(f"Typst Error: {result.stderr}")
                st.stop()
            
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