import pandas as pd
import subprocess
import os


TEMPLATE = "template2.typ"

# 1. Загрузка и обработка данных
df = pd.read_excel('data/beer_stat.xlsx', sheet_name=1)

# Переименовываем столбцы для Typst
rename_map = {
    "Značka piva": "brand_name",
    "Země původu": "origin_country",
    "Počet": "quantity"
}
df = df.rename(columns=rename_map)

# Сохраняем JSON в папку data
os.makedirs('data', exist_ok=True)
df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)
print("JSON обновлен!")

# 2. Создаем папку output, если её нет
os.makedirs('output', exist_ok=True)

# 3. Запуск компиляции Typst
# Мы используем список аргументов, это надежнее
try:
    command = [
        "typst", "compile", 
        "--root", ".", 
        f"templates/{TEMPLATE}", 
        "output/beer_report.pdf"
    ]
    
    subprocess.run(command, check=True)
    print("PDF успешно создан в папке output/beer_report.pdf!")
    
except FileNotFoundError:
    print("Ошибка: Typst не установлен или не найден в PATH.")
except subprocess.CalledProcessError as e:
    print(f"Ошибка Typst при компиляции: {e}")