import typst
import pandas as pd

df = pd.read_excel('data/beer_stat.xlsx', sheet_name=1)
rename_map = {
    "Značka piva": "brand_name",
    "Země původu": "origin_country",
    "Počet": "quantity"
}
df = df.rename(columns=rename_map)
df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)
print("Файл pivo.json готов для Typst!")

