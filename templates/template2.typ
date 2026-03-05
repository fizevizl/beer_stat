#set page(
  paper: "a4",
  // flipped: true,
  margin: (x: 1cm, y: 1.5cm),
  header: align(right)[Beer List],
  footer: context align(center)[Page #counter(page).display()],
)

#set text(font: "Libertinus Serif", lang: "en", size: 8pt) // Уменьшим шрифт, чтобы влезало больше

#let beer-data = json("../data/pivo.json")

#let total_quantity = beer-data.map(item => {
  let val = item.at("quantity", default: 0)
  // Убеждаемся, что значение — это число
  if type(val) == str { int(val) } else { val }
}).sum(default: 0) // Добавили default: 0 на случай пустого списка

// 1. Сортировка по алфавиту по ключу "brand_name" (или "Značka piva")
#let sorted-data = beer-data.sorted(key: it => it.at("brand_name", default: ""))


// 2. Включаем режим двух колонок на странице
#show: rest => columns(2, gutter: 0pt, rest)

#table(
  columns: (1fr, 80pt, 35pt),
  stroke: 0.5pt + luma(100),
  row-gutter: 0pt,
  inset: 3pt,

  fill: (x, y) => if y == 0 {
    rgb("#F8CBAD")
  } else if x == 0 {
    rgb("#B4C6E7")
  } else if x == 1 {
    rgb("#C6E0B4")
  } else if x == 2 {
    rgb("#FFD966")
  },

  table.header([*Značka piva*], [*Země původu*], [*Počet*]),

  ..sorted-data
    .map(item => (
      item.at("brand_name", default: "-"),
      table.cell(
        align: center + horizon,
        item.at("origin_country", default: "-"),
      ),
      table.cell(
        align: center + horizon,
        str(item.at("quantity", default: 0)),
      ),
    ))
    .flatten(),
)
#align(right)[*Celkem:* #total_quantity]
