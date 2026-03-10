#import "@preview/shadowed:0.3.0": shadow

#let today = datetime.today().display("[day].[month].[year]")

#set page(
  paper: "a4",
  margin: (x: 1cm, y: 1.5cm),
  header: align(right)[Beer List by Country (#today)],
  footer: context align(center)[Page #counter(page).display()],
)

#set text(font: "Libertinus Serif", size: 8pt)

// 1. Загрузка данных (исправляем имя переменной на beer_data)
#let beer_data = json("../data/pivo.json")

// 2. Логика группировки данных по странам
#let countries = beer_data.map(item => item.at("origin_country", default: "Unknown")).dedup().sorted()

#columns(2, gutter: 15pt)[
  #for country in countries {
    // Фильтруем пиво только для текущей страны
    let beers = beer_data.filter(item => item.at("origin_country", default: "Unknown") == country)

    // Считаем общий итог по стране
    let total = beers
      .map(b => {
        let val = b.at("quantity", default: 0)
        if type(val) == str { int(val) } else { val }
      })
      .sum()

    // Заголовок страны
    // heading(level: 2, outlined: false,)[#country]

    table(
      columns: (1fr, 30pt),
      fill: (x, y) => if y == 0 {
        rgb("#F8CBAD")
      } else if x == 0 {
        rgb("#C6E0B4")
      } else if x == 1 {
        rgb("#FFD966")
      },
      stroke: 0.5pt + gray,
      inset: 3pt,
      table.header([*Značka piva* *(#country)*], [*Počet*]),

      ..beers
        .map(item => (
          item.at("brand_name", default: "-"),
          align(center)[#str(item.at("quantity", default: 0))],
        ))
        .flatten(),
    )

    align(right)[
      #shadow(
      blur: 4pt,
      )[
      #block(
        width: 20%,
        // stroke: 0.5pt + gray,
        inset: 5pt,
        radius: 0pt,
        fill: rgb("#F8CBAD"),
      )[
        #set text(size: 6pt)
        #grid(
          columns: 1fr,
          align: right,
          [*Celkem:* #total],
        )]
      ]]
  }
]

