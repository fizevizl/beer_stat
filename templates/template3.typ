#set page(
  paper: "a4",
  margin: (x: 1cm, y: 1cm), // Уменьшили отступы, чтобы влезло больше
  header: align(right)[Spotřeba piva podle země],
  footer: context align(center)[Page #counter(page).display()],
)

#set text(font: "Libertinus Serif", size: 8pt) // Чуть меньше шрифт для компактности

// 1. Загрузка данных
#let beer_data = json("../data/pivo.json")

// 2. Группировка данных по странам
#let country_list = beer_data.map(item => item.at("origin_country", default: "Unknown")).dedup()

#let stats = country_list.map(c => {
  let entries = beer_data.filter(item => item.at("origin_country", default: "Unknown") == c)
  let sum_qty = entries.map(item => {
    let val = item.at("quantity", default: 0)
    if type(val) == str { int(val) } else { val }
  }).sum()
  (name: c, count: sum_qty)
}).sorted(key: it => it.count).rev()

// --- ТАБЛИЦА В 2 КОЛОНКИ ---
#show: rest => columns(2, gutter: 20pt, rest)

#table(
  columns: (1fr, 40pt), // Узкая колонка для цифр
  stroke: 0.5pt + luma(180),
  inset: 4pt,
  fill: (x, y) => if y == 0 {
    rgb("#F8CBAD")
  } else if x == 0 {
    rgb("#C6E0B4")
  } else if x == 1 {
    rgb("#FFD966")
  },
  align: horizon + center,
  
  table.header(
    [*Země původu*], 
    [*Počet*]
  ),

  ..stats.map(item => (
    item.name,
    align(center)[#item.count]
  )).flatten()
)