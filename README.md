# Analisis de Puntos de Dolor y Experiencia del Cliente

Este proyecto fue desarrollado para la materia **Tecnologias para la Gestion**. El objetivo es analizar la experiencia de usuario y detectar los principales puntos de dolor (pain points) operativos y de atencion en una empresa comercial del sector minorista de materiales y construccion, a partir de sus resenas publicas de baja calificacion (1 a 3 estrellas) en Google Maps.

Por motivos de privacidad y confidencialidad academica, la identidad comercial de la empresa se mantiene bajo reserva.

## Aplicacion Desplegada

El dashboard interactivo se encuentra disponible publicamente en:
- **Enlace de la aplicacion:** [https://tecnologias-webscrapping.streamlit.app](https://tecnologias-webscrapping.streamlit.app)

## Estructura del Proyecto

- `app.py`: Dashboard interactivo principal en Streamlit con filtros temporales, diagnóstico de madurez digital, análisis FODA y explorador de reseñas.
- `data/`:
  - `resenas_categorizadas.csv`: Dataset principal consolidado y procesado con clasificación temática, sucursal y año estimado (1.332 reseñas).
  - `raw/`: Datasets crudos originales extraídos por sucursal (Casa Central, Egger Haus, Centenario).
- `docs/`:
  - `Entrega_1_Diagnostico_Digital_El_Emporio_del_Terciado.pdf`: Informe académico completo de la Entrega 1.
- `scripts/`:
  - `analisis_quejas.py`: Script de procesamiento y categorización temática de quejas.
  - `scrape_reviews.py`: Script de extracción automatizada de reseñas utilizando Playwright.
- `requirements.txt`: Dependencias esenciales para el despliegue del dashboard en Streamlit Cloud.
- `requirements-dev.txt`: Dependencias adicionales para tareas de scraping y desarrollo local.

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
