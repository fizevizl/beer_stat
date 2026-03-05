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

# --- ЛОГИКА ПРЕОБРАЗОВАНИЯ ДЛЯ ОБЛАКА ---
def load_excel_data(uploaded_file):
    try:
        # 1. Пробуем стандартный pandas (xlsx или честный бинарный xls)
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file, sheet_name=0)
    except Exception:
        try:
            # 2. Пробуем старый бинарный формат (xlrd)
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file, sheet_name=0, engine='xlrd')
        except Exception:
            try:
                # 3. ПОСЛЕДНИЙ ШАНС: Читаем как Microsoft XML Spreadsheet 2003
                uploaded_file.seek(0)
                # Парсим XML напрямую через read_xml с учетом пространств имен Microsoft
                df_xml = pd.read_xml(
                    uploaded_file, 
                    xpath=".//ss:Row", 
                    namespaces={"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
                )
                
                # Очищаем названия колонок от префиксов {urn:...}
                df_xml.columns = [c.split('}')[-1] for c in df_xml.columns]
                
                # Если вместо данных в колонках мы получили список "Data", 
                # значит XML слишком сложный. Пробуем прочитать через BeautifulSoup более агрессивно.
                if "Data" in df_xml.columns or df_xml.empty:
                    uploaded_file.seek(0)
                    # Используем flavor 'bs4' для парсинга "грязного" XML как HTML
                    tables = pd.read_html(uploaded_file, flavor='bs4')
                    return tables[0]
                
                return df_xml
            except Exception as e:
                st.error(f"Не удалось разобрать XML структуру: {e}")
                return None
            
# --- ИНИЦИАЛИЗАЦИЯ ---
TYPST_PATH = install_typst()
FIXED_TEMPLATE = "template2.typ"

st.title("🍺 Beer Stat Generator (Cloud Version)")

uploaded_file = st.file_uploader("Выберите файл (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Используем нашу логику преобразования
    df = load_excel_data(uploaded_file)
    
    if st.button("Сгенерировать PDF"):
            try:
                # 1. Проверяем, не слиплись ли данные в одну колонку
                if df.shape[1] == 1:
                    # Пробуем разделить по распространенным разделителям
                    for sep in [';', '\t', '|']:
                        temp_df = df.iloc[:, 0].astype(str).str.split(sep, expand=True)
                        if temp_df.shape[1] >= 2:
                            df = temp_df
                            break
                
                # 2. Динамически назначаем имена колонок
                # Вычисляем, сколько у нас колонок на самом деле
                real_cols_count = df.shape[1]
                target_names = ["brand_name", "origin_country", "quantity"]
                
                # Назначаем имена только для тех колонок, которые существуют
                new_columns = {}
                for i in range(real_cols_count):
                    if i < len(target_names):
                        new_columns[df.columns[i]] = target_names[i]
                
                df = df.rename(columns=new_columns)

                # 3. Добавляем недостающие колонки, если файл слишком узкий
                for name in target_names:
                    if name not in df.columns:
                        df[name] = "—" # Заполняем прочерком

                # 4. Очистка данных
                df = df.dropna(subset=["brand_name"])
                
                # Превращаем количество в число (извлекаем цифры, если там "10 шт")
                if "quantity" in df.columns:
                    df["quantity"] = df["quantity"].astype(str).str.extract(r'(\d+)')[0]
                    df["quantity"] = pd.to_numeric(df["quantity"], errors='coerce').fillna(0).astype(int)

                # Удаляем пустые строки
                df = df[df["brand_name"].astype(str).str.strip() != ""]

                # Проверка на пустоту
                if df.empty:
                    st.error("После обработки данных таблица оказалась пустой. Проверьте формат файла.")
                    st.stop()

                # --- Далее стандартный запуск Typst ---
                os.makedirs('data', exist_ok=True)
                df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)
                
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
                st.error(f"Ошибка при подготовке данных: {e}")