import typst
import pandas as pd

df = pd.read_excel('data/beer_stat.xlsx', sheet_name=1)
df = df.dropna(how='all').dropna(axis=1, how='all')
print(df.head())
df.to_json('data/pivo.json', orient='records', force_ascii=False, indent=2)
print("Файл pivo.json готов для Typst!")

