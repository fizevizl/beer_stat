import streamlit as st
import pandas as pd
import subprocess
import os

st.set_page_config(page_title="Beer Stat PDF Generator", page_icon="🍺")

st.title("🍺 Beer Stat Generator")
st.write("Загрузите Excel-файл, чтобы получить PDF-отчет по шаблону.")

# 1. Выбор шаблона
template_options = ["template1.typ", "template2.typ"]
selected_template = st.selectbox("Выберите шаблон:", template_options)

# 2. Загрузка файла
uploaded_file = st.file_uploader("Выберите Excel файл (.xlsx)", type="xlsx")

if uploaded_file is not None:
    if st.button("Сгенерировать PDF"):
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
            command = [
                "typst", "compile", 
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