import streamlit as st
import pandas as pd
import subprocess
import os
import urllib.request
import tarfile
import platform
from pathlib import Path
import warnings
from bs4 import XMLParsedAsHTMLWarning


warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# --- КОНСТАНТЫ ---
TYPST_VERSION_URL = "https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz"
DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
TEMP_DIR = Path("typst_executable")
TEMPLATE_PATH = Path("templates/template2.typ")

# --- ЛОГИКА УСТАНОВКИ ---
@st.cache_resource
def get_typst_path():
    """Устанавливает Typst и возвращает путь к исполняемому файлу."""
    if platform.system() == "Windows":
        return "typst"
    
    bin_path = TEMP_DIR / "typst"
    if not bin_path.exists():
        TEMP_DIR.mkdir(exist_ok=True)
        archive = "typst.tar.xz"
        try:
            urllib.request.urlretrieve(TYPST_VERSION_URL, archive)
            with tarfile.open(archive, "r:xz") as tar:
                tar.extractall(path=TEMP_DIR)
            
            # Поиск бинарника во вложенных папках архива
            for p in TEMP_DIR.rglob("typst"):
                if p.is_file():
                    p.replace(bin_path)
                    break
            
            bin_path.chmod(0o775)
            if Path(archive).exists():
                os.remove(archive)
        except Exception as e:
            st.error(f"Typst install failed: {e}")
            return "typst"
    return str(bin_path)

# --- ЛОГИКА ОБРАБОТКИ ДАННЫХ ---
def try_read_excel(file) -> pd.DataFrame:
    """Пытается прочитать файл разными методами (XLSX, XLS, XML, HTML)."""
    
    # 1. Стандартные движки (XLSX / Бинарный XLS)
    for engine in [None, 'xlrd', 'openpyxl']:
        try:
            file.seek(0)
            return pd.read_excel(file, engine=engine)
        except Exception:
            continue

   # 2 Прямое извлечение данных из тегов <Data>
    try:
        file.seek(0)
        import xml.etree.ElementTree as ET
        tree = ET.parse(file)
        root = tree.getroot()
        
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows_data = []
        
        for row in root.findall('.//ss:Row', ns):
            cells = [cell.find('ss:Data', ns).text if cell.find('ss:Data', ns) is not None else "" 
                     for cell in row.findall('ss:Cell', ns)]
            if any(cells): # Пропускаем совсем пустые строки
                rows_data.append(cells)
        
        if rows_data:
            return pd.DataFrame(rows_data)
    except Exception as e:
        st.error(f"Error reading XML: {e}")


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Очистка и нормализация данных."""
    # Если данные слиплись в одну колонку
    if df.shape[1] == 1:
        for sep in [';', '\t', ',']:
            temp_df = df.iloc[:, 0].astype(str).str.split(sep, expand=True)
            if temp_df.shape[1] >= 2:
                df = temp_df
                break
    
    df = df.iloc[:, :3]
    df.columns = ["brand_name", "origin_country", "quantity"]
    
    df = df.dropna(subset=["brand_name"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors='coerce').fillna(0).astype(int)
    return df[df["quantity"] > 0]

# --- ИНТЕРФЕЙС ---
languages = {
    "en": {
        "title": "🍺 Beer Stat Generator",
        "description": "Upload Excel (XLSX, XLS, XML) The data for the transfer must be on the first sheet.",
        "button": "Generate PDF",
        "success": "PDF created!",
        "download": "📥 Download PDF"
    },
    "🇨🇿": {
        "title": "🍺 Generátor pivních statistik",
        "description": "Nahrajte Excel (XLSX, XLS, XML) Údaje pro převod musí být na prvním listu.",
        "button": "Generovat PDF",
        "success": "PDF vytvořeno!",
        "download": "📥 Stáhnout PDF"
    }
}
st.markdown("""
    <style>
    div[data-testid="stSelectbox"] {
        margin-left: auto;
        width: 80px !important;
    }
    </style>
    """, unsafe_allow_html=True)

temp_lang_list = list(languages.keys())
lang_choice = st.selectbox(
    "Language Selection",        # Текст метки (теперь он обязателен)
    options=temp_lang_list, 
    index=0, 
    label_visibility="collapsed" # Скрывает метку, сохраняя ваш дизайн
)
t = languages[lang_choice]

st.title(t["title"])
st.info(t["description"])

uploaded_file = st.file_uploader("Excel file", type=["xlsx", "xls", "xml"])

if uploaded_file:
    if st.button(t["button"]):
        try:
            # 1. Загрузка
            raw_df = try_read_excel(uploaded_file)
            
            # 2. Очистка
            df = clean_data(raw_df)
            
            if df.empty:
                st.warning("No data found after cleaning.")
                st.stop()

            # 3. Сохранение промежуточных данных
            DATA_DIR.mkdir(exist_ok=True)
            df.to_json(DATA_DIR / 'pivo.json', orient='records', force_ascii=False, indent=2)

            # 4. Компиляция PDF
            OUTPUT_DIR.mkdir(exist_ok=True)
            pdf_path = OUTPUT_DIR / "beer_report.pdf"
            
            typst_bin = get_typst_path()
            cmd = [typst_bin, "compile", "--root", ".", str(TEMPLATE_PATH), str(pdf_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                st.success(t["success"])
                with open(pdf_path, "rb") as f:
                    st.download_button(t["download"], f, "beer_report.pdf", "application/pdf")
            else:
                st.error(f"Typst Error: {result.stderr}")

        except Exception as e:
            st.error(f"Error: {e}")