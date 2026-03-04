#set page(
  paper: "a4",
  flipped: true,
  margin: (x: 1cm, y: 1.5cm),
  header: align(right)[Beer List],
  footer: context align(center)[Page #counter(page).display()],
)

#set text(font: "Arial", lang: "en", size: 9pt) // Уменьшим шрифт, чтобы влезало больше

#let beer-data = json("../data/pivo.json")

#let total-quantity = beer-data.map(item => {
  let val = item.at("quantity", default: 0)
  // На случай, если в JSON число пришло как строка, переводим в int
  if type(val) == str { int(val) } else { val }
}).sum()

// 1. Сортировка по алфавиту по ключу "brand_name" (или "Značka piva")
#let sorted-data = beer-data.sorted(key: it => it.at("brand_name", default: ""))


// 2. Включаем режим двух колонок на странице
#show: rest => columns(2, gutter: 15pt, rest)

#table(
  columns: (1fr, 100pt, 40pt), 
  stroke: none,         
  row-gutter: 4pt,
  // Заливка строк теперь делается через этот аргумент в самой таблице:
  fill: (x, y) => if y > 0 and calc.even(y) { luma(245) }, 
  
  // Правильный способ оформления заголовка в Typst 0.13:
  table.header(
    table.cell(fill: silver)[*Značka piva*],
    table.cell(fill: silver)[*Země původu*],
    table.cell(fill: silver)[*Počet*],
  ),

  ..sorted-data.map(item => (
    item.at("brand_name", default: "-"),
    item.at("origin_country", default: "-"),
    align(right, str(item.at("quantity", default: 0))),
  )).flatten()  
)
#align(right)[*Celkem:* #total-quantity] 