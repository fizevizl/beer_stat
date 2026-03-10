import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile
import platform
import json
import warnings
from pathlib import Path
from datetime import datetime
from bs4 import XMLParsedAsHTMLWarning

# Отключаем специфическое предупреждение парсера BS4, чтобы не засорять консоль
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

st.set_page_config(page_title='Beer Stat', page_icon='🍺')

# --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ И ПУТИ ---
TYPST_VERSION_URL = "https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
DATA_DIR = Path("data")              # Папка для промежуточных JSON данных
OUTPUT_DIR = Path("output")          # Папка для готовых PDF отчетов
TEMP_DIR = Path("typst_executable")  # Папка для исполняемого файла Typst
TEMPLATE_PATH = Path("templates/template2.typ") # Путь к шаблону отчета

# --- АВТОМАТИЧЕСКАЯ УСТАНОВКА TYPST ---
@st.cache_resource
def get_typst_path():
    """
    Проверяет наличие Typst. Если его нет — скачивает и распаковывает.
    Работает как для Windows (ожидает в системе), так и для Linux (Streamlit Cloud).
    """
    if platform.system() == "Windows":
        return "typst"  # Предполагаем, что в Windows Typst добавлен в PATH
    
    bin_path = TEMP_DIR / "typst"
    if not bin_path.exists():
        TEMP_DIR.mkdir(exist_ok=True)
        archive = "typst.tar.xz"
        try:
            # Скачиваем свежий релиз Typst для Linux
            urllib.request.urlretrieve(TYPST_VERSION_URL, archive)
            with tarfile.open(archive, "r:xz") as tar:
                tar.extractall(path=TEMP_DIR)
            
            # Находим бинарный файл во вложенных папках и переносим в корень TEMP_DIR
            for p in TEMP_DIR.rglob("typst"):
                if p.is_file():
                    p.replace(bin_path)
                    break
            
            # Даем права на выполнение файла
            bin_path.chmod(0o775)
            if Path(archive).exists():
                os.remove(archive)
        except Exception as e:
            st.error(f"Typst install failed: {e}")
            return "typst"
    return str(bin_path)

# --- МОДУЛЬ ЧТЕНИЯ ДАННЫХ ---
def try_read_excel(file) -> pd.DataFrame:
    """
    Универсальный «комбайн» для чтения таблиц. 
    """
    
    # 1. Пробуем стандартные движки Pandas (XLSX, XLS)
    for engine in [None, 'xlrd', 'openpyxl']:
        try:
            file.seek(0)
            return pd.read_excel(file, engine=engine)
        except Exception:
            continue

    # 2. Ручной разбор XML Spreadsheet 2003
    try:
        file.seek(0)
        import xml.etree.ElementTree as ET
        tree = ET.parse(file)
        root = tree.getroot()
        
        # Пространство имен Excel XML
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows_data = []
        
        # Итерируемся по строкам и ячейкам
        for row in root.findall('.//ss:Row', ns):
            cells = [cell.find('ss:Data', ns).text if cell.find('ss:Data', ns) is not None else "" 
                     for cell in row.findall('ss:Cell', ns)]
            if any(cells): # Игнорируем абсолютно пустые строки
                rows_data.append(cells)
        
        if rows_data:
            return pd.DataFrame(rows_data)
    except Exception as e:
        pass

    # Если ничего не помогло — выбрасываем исключение
    raise ValueError("The file format was not recognized. Please ensure it is a valid Excel or XML file.")

# --- МОДУЛЬ ОЧИСТКИ ДАННЫХ ---
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Приводит таблицу к единому стандарту:
    - Разделяет слипшиеся колонки (CSV-style).
    - Выбирает первые 3 колонки.
    - Удаляет пустые строки и преобразует числа.
    """
    # Если данные загрузились одной строкой текста — пробуем разделить по разделителям
    if df.shape[1] == 1:
        for sep in [';', '\t', ',']:
            temp_df = df.iloc[:, 0].astype(str).str.split(sep, expand=True)
            if temp_df.shape[1] >= 2:
                df = temp_df
                break
    
    # Оставляем только три важных столбца и даем им понятные имена
    df = df.iloc[:, :3]
    df.columns = ["brand_name", "origin_country", "quantity"]
    
    # Удаляем строки без названия бренда
    df = df.dropna(subset=["brand_name"])
    
    # Конвертируем количество в целое число (ошибки станут нулями)
    df["quantity"] = pd.to_numeric(df["quantity"], errors='coerce').fillna(0).astype(int)
    
    # Возвращаем только те позиции, где количество больше нуля
    return df[df["quantity"] > 0]

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
def load_language():
    """Загружает переводы из внешнего JSON файла."""
    try:
        with open("language.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        # Если файл потерян — возвращаем минимальный английский интерфейс
        return {
            "en": {"title": "Error", "description": f"Could not load language.json: {e}", 
                   "button": "Error", "success": "Error", "download": "Error"}
        }

# Подготовка словаря языков
# Кастомный CSS для компактного выбора языка в углу
# st.markdown("""
#     <style>
#     div[data-testid="stSelectbox"] {
#         margin-left: auto;
#         width: 80px !important;
#     }
#     </style>
#     """, unsafe_allow_html=True)

# # Выбор языка (лейбл скрыт для красоты)
# temp_lang_list = list(languages.keys())
# lang_choice = st.selectbox(
#     "Language Selection", 
#     options=temp_lang_list, 
#     index=0, 
#     label_visibility="collapsed"
# )
# lang = languages[lang_choice]

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
languages = load_language()
# Устанавливаем английский по умолчанию без отрисовки интерфейса выбора
lang_choice = "en" 
# Если в будущем захотите вернуть выбор, 
# вы сможете снова добавить st.selectbox, использующий keys из languages
lang = languages.get(lang_choice, languages[list(languages.keys())[0]])

st.title(lang["title"])
st.info(lang["description"])

# Поле загрузки файла
uploaded_file = st.file_uploader("Excel file", type=["xlsx", "xls", "xml"])

def report_generator(btn_start_caption, template_name, base_name):
    # Генерируем текущую дату в формате ГГГГ-ММ-ДД
    current_date = datetime.now().strftime("%d-%m-%y")
    
    # Формируем новое имя файла: "beer_statistics_2026-03-10.pdf"
    # base_name здесь — это префикс (например, "beer_statistics")
    file_name = f"{base_name}_{current_date}.pdf"
    
    if st.button(btn_start_caption):
        with st.spinner('Generating report...'):
            # Передаем file_name в функцию генерации
            res, path = generate_pdf(template_name, file_name)
            
            if res.returncode == 0:
                st.success(f"Report ready!")
                with open(path, "rb") as f:
                    st.download_button(
                        label='Download PDF', 
                        data=f, 
                        file_name=file_name, # Это имя увидит пользователь при сохранении
                        mime="application/pdf"
                    )
            else:
                st.error(f"Error: {res.stderr}")

if uploaded_file:
    try:
        # ЭТАП 1: Чтение
        raw_df = try_read_excel(uploaded_file)
        
        # ЭТАП 2: Очистка
        df = clean_data(raw_df)
        
        if df.empty:
            st.warning("No data found after cleaning.")
            st.stop()

        # ЭТАП 3: Сохранение данных для Typst
        DATA_DIR.mkdir(exist_ok=True)
        df.to_json(DATA_DIR / 'pivo.json', orient='records', force_ascii=False, indent=2)

        st.subheader("Generate Reports")
        
        # Создаем 3 колонки для кнопок
        col1, col2, col3 = st.columns(3)
        
        typst_bin = get_typst_path()
        OUTPUT_DIR.mkdir(exist_ok=True)

        # Функция для генерации PDF (чтобы не дублировать код)
        def generate_pdf(template_name, output_name):
            t_path = Path("templates") / template_name
            p_path = OUTPUT_DIR / output_name
            cmd = [typst_bin, "compile", "--root", ".", str(t_path), str(p_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result, p_path

        with col1:
            report_generator("🍺 Full Beer List", "template2.typ", "beer_full_stat")            
        with col2:
            report_generator("🍻 Beer in Contry Stat", "template1.typ", "beer_country_stat")
        with col3:
            report_generator("🌍 Country Stats", "template3.typ", "country_stat")

        
    except Exception as e:
        st.error(f"Error: {e}")