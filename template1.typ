#set page(
  paper: "a4",
  margin: (x: 1cm, y: 1.5cm),
  header: align(right)[Beer Statistics Report],
  // Добавляем ключевое слово context перед счетчиком
  footer: context align(center)[
    Page #counter(page).display()
  ],
)

// Используем шрифт с поддержкой спецсимволов
#set text(font: "Arial", lang: "en")

#let beer-data = json("data/pivo.json")

#table(
  columns: (1fr, 1fr, 50pt), 
  fill: (x, y) => if y == 0 { gray.lighten(80%) },
  stroke: 0.5pt + gray,
  inset: 7pt,
  
  // Вместо header-rows: 1 используем это:
  table.header(
    [*Značka piva*], [*Země původu*], [*Počet*],
  ),

  ..beer-data.map(item => (
    item.at("brand_name", default: "-"), 
    item.at("origin_country", default: "-"), 
    str(item.at("quantity", default: 0)),    
  )).flatten()
)