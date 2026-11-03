# Diagnóstico Digital — El Emporio del Terciado

Dashboard web para el análisis de experiencia del cliente y el diagnóstico digital de **El Emporio del Terciado S.A.**, a partir de **1.075 reseñas públicas de Google Maps**.

Materia: **Tecnologías para la Gestión** (FCE – UNLP).

## Demo

Sitio publicado con GitHub Pages:

**https://reigenabril.github.io/tecnologias-webscrapping/**

## Stack

- HTML, CSS y JavaScript, sin build ni framework.
- [Plotly.js](https://plotly.com/javascript/) (vendorizado) para los gráficos.
- pandas para generar el JSON de datos desde el CSV.

## Estructura

```
docs/                     # sitio publicado por GitHub Pages
├── index.html            # las 6 secciones del dashboard
├── assets/
│   ├── styles.css        # diseño responsive e impresión
│   ├── metrics.js        # filtros y agregaciones (sin DOM)
│   ├── app.js            # router, controles y gráficos
│   ├── favicon.svg
│   └── vendor/           # Plotly.js y su licencia
├── data/resenas.json     # dataset generado desde el CSV
└── Entrega_1_...pdf      # informe de la entrega
data/                     # dataset fuente (CSV)
scripts/                  # scraping, análisis y build del JSON
tests/                    # tests de paridad numérica
```

## Desarrollo local

```bash
python3 -m http.server 8000 --directory docs
# abrir http://localhost:8000
```

No abras `docs/index.html` con `file://`: el navegador bloquea el `fetch` del JSON.

## Datos

`data/resenas_categorizadas.csv` es la fuente de verdad (1.075 filas × 17 columnas).

Para regenerar el JSON que consume el sitio:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/build_site_data.py
```

El script valida el esquema, normaliza los valores faltantes e imprime los conteos de control.

## Tests

```bash
node --test tests/metrics.test.js
```

Verifican la paridad numérica del dashboard (totales, promedios, filtros, FODA y export CSV).

## Scraping y análisis (opcional)

```bash
pip install -r requirements-dev.txt
python3 scripts/scrape_reviews.py
python3 scripts/analisis_quejas.py
```

## Deploy

GitHub Pages: **Settings → Pages → Deploy from a branch → Branch `main` / carpeta `/docs`**.

Alternativa Vercel: importar el repositorio, configurar **Root Directory** en `docs`, framework “Other” y sin build.

## Créditos

Trabajo Práctico Integrador — Tecnologías para la Gestión, FCE UNLP.

Caso de estudio: El Emporio del Terciado S.A. (La Plata).
