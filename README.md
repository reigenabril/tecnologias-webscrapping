# Analisis de Puntos de Dolor y Experiencia del Cliente

Este proyecto fue desarrollado para la materia **Tecnologias para la Gestion**. El objetivo es analizar la experiencia de usuario y detectar los principales puntos de dolor (pain points) operativos y de atencion en una empresa comercial del sector minorista de materiales y construccion, a partir de sus resenas publicas de baja calificacion (1 a 3 estrellas) en Google Maps.

Por motivos de privacidad y confidencialidad academica, la identidad comercial de la empresa se mantiene bajo reserva.

## Aplicacion Desplegada

El dashboard interactivo se encuentra disponible publicamente en:
- **Enlace de la aplicacion:** [https://tecnologias-webscrapping.streamlit.app](https://tecnologias-webscrapping.streamlit.app)

## Estructura del Proyecto

- `app.py`: Dashboard interactivo desarrollado en Streamlit con filtros temporales, indicadores de gestion, visualizaciones y explorador de resenas.
- `analisis_quejas.py`: Script de procesamiento de lenguaje natural y categorizacion tematica de motivos de queja.
- `scrape_reviews.py`: Script de extraccion automatizada de resenas publicas utilizando Playwright.
- `resenas_categorizadas.csv`: Dataset procesado con clasificacion tematica y año estimado.
- `grafico_top_quejas.png`: Grafico de distribucion de las principales categorias de reclamos.

## Requisitos e Instalacion Local

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/reigenabril/tecnologias-webscrapping.git
   cd tecnologias-webscrapping
   ```

2. Crear y activar un entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecucion Local del Dashboard

Para iniciar la aplicacion de forma local:

```bash
streamlit run app.py
```

La aplicacion estara disponible en `http://localhost:8501`.
