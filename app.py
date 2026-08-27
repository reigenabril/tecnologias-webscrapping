#!/usr/bin/env python3
"""
Dashboard Interactivo en Streamlit: Análisis de Puntos de Dolor y Experiencia del Cliente
Materia: Tecnologías para la Gestión
"""

import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Análisis de Puntos de Dolor - Tecnologías para la Gestión",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Rutas dinámicas compatibles con ejecución local y despliegue en Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_CATEGORIZADAS = os.path.join(BASE_DIR, "resenas_categorizadas.csv")
CSV_ORIGINAL = os.path.join(BASE_DIR, "resenas_emporio_terciado_3_o_menos.csv")

# Paleta con jerarquía de contraste visual (alto contraste para lo crítico, bajo contraste para lo secundario)
COLOR_1_STAR = "#0072B2"  # Alto contraste (Azul profundo dominante)
COLOR_2_STAR = "#E69F00"  # Contraste medio (Ámbar / Naranja cálido)
COLOR_3_STAR = "#94A3B8"  # Bajo contraste (Gris azulado suave / neutro)

# Jerarquía para barras de categorías: Top destacados vs secundarios atenuados
HIERARCHY_PALETTE = [
    "#0072B2",  # Top 1: Máximo contraste / impacto visual
    "#E69F00",  # Top 2: Contraste medio-alto
    "#009E73",  # Top 3: Contraste medio
    "#64748B",  # Top 4: Contraste medio-bajo
    "#94A3B8",  # Top 5: Bajo contraste
    "#CBD5E1",  # Top 6: Muy bajo contraste
    "#E2E8F0"   # Top 7+: Atenuado
]

# Símbolos y estilos de línea accesibles para doble codificación (redundant encoding)
ACCESSIBLE_SYMBOLS = ["circle", "square", "triangle-up", "diamond", "cross", "x"]
ACCESSIBLE_DASHES = ["solid", "dash", "dot", "dashdot", "longdash"]

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 500;
    }
    .quote-box {
        background-color: #F8FAFC;
        border-left: 4px solid #0072B2;
        padding: 0.8rem 1.2rem;
        margin: 0.8rem 0;
        border-radius: 4px;
        font-style: italic;
        color: #1E293B;
    }
    .foda-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .foda-f { border-top: 4px solid #009E73; }
    .foda-o { border-top: 4px solid #0072B2; }
    .foda-d { border-top: 4px solid #D55E00; }
    .foda-a { border-top: 4px solid #E69F00; }
    .foda-badge-f { background-color: #E6F4EA; color: #137333; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .foda-badge-o { background-color: #E8F0FE; color: #1A73E8; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .foda-badge-d { background-color: #FCE8E6; color: #C5221F; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .foda-badge-a { background-color: #FEF7E0; color: #B06000; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)


def parse_year(fecha_str: str, current_year: int = 2026) -> int:
    """Convierte strings de fecha relativa a año estimado."""
    if not isinstance(fecha_str, str):
        return current_year
    f = fecha_str.lower()
    if any(w in f for w in ['mes', 'semana', 'día', 'dia', 'hora']):
        return current_year
    if 'un año' in f or 'un anio' in f or '1 año' in f or '1 anio' in f:
        return current_year - 1
    m = re.search(r'(\d+)\s+a[nñ]o', f)
    if m:
        return current_year - int(m.group(1))
    return current_year


@st.cache_data
def load_data():
    if os.path.exists(CSV_CATEGORIZADAS):
        df = pd.read_csv(CSV_CATEGORIZADAS)
    elif os.path.exists(CSV_ORIGINAL):
        df = pd.read_csv(CSV_ORIGINAL)
    else:
        st.error("No se encontró el archivo de datos CSV.")
        return pd.DataFrame()
        
    if "anio_estimado" not in df.columns:
        df["anio_estimado"] = df["fecha"].apply(parse_year)
    return df


df = load_data()
if df.empty:
    st.stop()

min_year = int(df["anio_estimado"].min())
max_year = int(df["anio_estimado"].max())

# Sidebar - Filtros Globales
st.sidebar.title("Tecnologías para la Gestión")
st.sidebar.caption("Análisis de Puntos de Dolor en Comercio Minorista")

menu = st.sidebar.radio(
    "Navegación:",
    [
        "Resumen Ejecutivo",
        "Evolución Temporal",
        "Top Motivos de Queja",
        "Explorador de Reseñas",
        "Matriz FODA",
        "Recomendaciones de Gestión"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtro por Años")

rango_anios = st.sidebar.slider(
    "Selecciona el rango de años:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Adicionales")

filtro_estrellas = st.sidebar.multiselect(
    "Calificación (Estrellas):",
    options=[1, 2, 3],
    default=[1, 2, 3]
)

categorias_disponibles = sorted(df["categoria_principal"].dropna().unique())
filtro_categorias = st.sidebar.multiselect(
    "Categoría de Queja:",
    options=categorias_disponibles,
    default=categorias_disponibles
)

filtro_respuesta = st.sidebar.selectbox(
    "Respuesta de la Empresa:",
    ["Todas", "Solo con respuesta", "Sin respuesta"]
)

# Aplicar filtros a nivel global
df_filtrado = df[
    (df["anio_estimado"] >= rango_anios[0]) &
    (df["anio_estimado"] <= rango_anios[1]) &
    (df["estrellas"].isin(filtro_estrellas))
]

if filtro_respuesta == "Solo con respuesta":
    df_filtrado = df_filtrado[df_filtrado["respuesta_dueno"].notna() & (df_filtrado["respuesta_dueno"].str.strip() != "")]
elif filtro_respuesta == "Sin respuesta":
    df_filtrado = df_filtrado[df_filtrado["respuesta_dueno"].isna() | (df_filtrado["respuesta_dueno"].str.strip() == "")]

if filtro_categorias:
    df_filtrado = df_filtrado[df_filtrado["categoria_principal"].isin(filtro_categorias) | df_filtrado["texto"].isna()]

df_filtrado_texto = df_filtrado[df_filtrado["texto"].notna() & (df_filtrado["texto"].str.strip() != "")]


# ==========================================
# 1. RESUMEN EJECUTIVO
# ==========================================
if menu == "Resumen Ejecutivo":
    st.markdown('<div class="main-header">Auditoría de Experiencia del Cliente y Puntos de Dolor</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Estudio de Caso: Empresa de Materiales y Maderas | Período: <b>{rango_anios[0]} - {rango_anios[1]}</b></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_filtrado)}</div>
            <div class="metric-label">Reseñas Bajas ({rango_anios[0]}-{rango_anios[1]})</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        pct_texto = (len(df_filtrado_texto) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_filtrado_texto)} ({pct_texto:.1f}%)</div>
            <div class="metric-label">Quejas con Detalle Escrito</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        promedio = df_filtrado['estrellas'].mean() if len(df_filtrado) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{promedio:.2f} / 5.0</div>
            <div class="metric-label">Promedio de Calificación</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        respondidas = df_filtrado['respuesta_dueno'].notna().sum()
        pct_resp = (respondidas / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{respondidas} ({pct_resp:.1f}%)</div>
            <div class="metric-label">Tasa de Respuesta Institucional</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns([6, 4])
    
    with col_chart1:
        st.subheader("Top Motivos de Queja en el Período")
        if len(df_filtrado_texto) > 0:
            cat_data = df_filtrado_texto["categoria_principal"].value_counts().reset_index()
            cat_data.columns = ["Categoría", "Cantidad"]
            cat_data["Porcentaje"] = (cat_data["Cantidad"] / len(df_filtrado_texto) * 100).round(1)
            
            bar_colors = [HIERARCHY_PALETTE[min(i, len(HIERARCHY_PALETTE)-1)] for i in range(len(cat_data))]
            
            fig = px.bar(
                cat_data,
                x="Cantidad",
                y="Categoría",
                orientation="h",
                text=cat_data.apply(lambda r: f"{r['Cantidad']} ({r['Porcentaje']}%)", axis=1),
                color="Categoría",
                color_discrete_sequence=bar_colors,
            )
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="Cantidad de Reseñas",
                yaxis_title="",
                showlegend=False,
                height=380,
                margin=dict(l=10, r=20, t=10, b=10)
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay reseñas con texto para los filtros seleccionados.")

    with col_chart2:
        st.subheader("Distribución por Calificación")
        if len(df_filtrado) > 0:
            star_counts = df_filtrado["estrellas"].value_counts().sort_index().reset_index()
            star_counts.columns = ["Estrellas", "Cantidad"]
            star_counts["Etiqueta"] = star_counts["Estrellas"].apply(lambda s: f"{s} Estrella{'s' if s > 1 else ''}")
            
            fig_pie = px.pie(
                star_counts,
                names="Etiqueta",
                values="Cantidad",
                hole=0.45,
                color="Estrellas",
                color_discrete_map={1: COLOR_1_STAR, 2: COLOR_2_STAR, 3: COLOR_3_STAR}
            )
            fig_pie.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader(f"Diagnóstico Dinámico ({rango_anios[0]} - {rango_anios[1]})")
    if len(df_filtrado_texto) > 0:
        top_cats_summary = df_filtrado_texto["categoria_principal"].value_counts().head(3)
        top_text_lines = []
        for i, (cat_name, count) in enumerate(top_cats_summary.items(), 1):
            pct = (count / len(df_filtrado_texto)) * 100
            top_text_lines.append(f"{i}. **{cat_name}** ({pct:.1f}% - {count} quejas)")
        
        sum_pct = (top_cats_summary.sum() / len(df_filtrado_texto)) * 100
        st.info(f"""
        Para el período seleccionado (**{rango_anios[0]} - {rango_anios[1]}**), los principales motivos representan el **{sum_pct:.1f}%** de las quejas:
        \n""" + "\n".join([f"- {line}" for line in top_text_lines]))
    else:
        st.info("No se encontraron suficientes datos para generar el diagnóstico en este rango de años.")


# ==========================================
# 2. EVOLUCIÓN TEMPORAL POR AÑOS
# ==========================================
elif menu == "Evolución Temporal":
    st.markdown('<div class="main-header">Evolución Histórica de Quejas por Año</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tendencia temporal de reseñas de baja calificación</div>', unsafe_allow_html=True)

    anios_df = df_filtrado.groupby(["anio_estimado", "estrellas"]).size().reset_index(name="cantidad")
    anios_df["estrellas_str"] = anios_df["estrellas"].apply(lambda s: f"{s} Estrella{'s' if s > 1 else ''}")
    
    fig_evol = px.bar(
        anios_df,
        x="anio_estimado",
        y="cantidad",
        color="estrellas_str",
        title=f"Volumen Anual de Reseñas ({rango_anios[0]} - {rango_anios[1]})",
        labels={"anio_estimado": "Año", "cantidad": "Cantidad de Reseñas", "estrellas_str": "Calificación"},
        color_discrete_map={"1 Estrella": COLOR_1_STAR, "2 Estrellas": COLOR_2_STAR, "3 Estrellas": COLOR_3_STAR},
        barmode="stack"
    )
    fig_evol.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        height=420,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_evol, use_container_width=True)

    st.subheader("Evolución de los Principales Motivos de Queja a lo largo del tiempo")
    if len(df_filtrado_texto) > 0:
        top_cats = df_filtrado_texto["categoria_principal"].value_counts().head(4).index
        sub_time = df_filtrado_texto[df_filtrado_texto["categoria_principal"].isin(top_cats)]
        cat_time = sub_time.groupby(["anio_estimado", "categoria_principal"]).size().reset_index(name="quejas")
        
        # Doble codificación accesible: Color + Forma de marcador (círculo, cuadrado, triángulo, rombo) + Estilo de línea (sólida, guiones, puntos)
        fig_cat_time = px.line(
            cat_time,
            x="anio_estimado",
            y="quejas",
            color="categoria_principal",
            symbol="categoria_principal",
            line_dash="categoria_principal",
            color_discrete_sequence=HIERARCHY_PALETTE,
            symbol_sequence=ACCESSIBLE_SYMBOLS,
            line_dash_sequence=ACCESSIBLE_DASHES,
            labels={"anio_estimado": "Año", "quejas": "Cantidad de Quejas", "categoria_principal": "Motivo"},
            title="Tendencia Anual por Categoría de Queja"
        )
        fig_cat_time.update_traces(
            marker=dict(size=9, line=dict(width=1, color="#FFFFFF")),
            line=dict(width=2.5)
        )
        fig_cat_time.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            height=400,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_cat_time, use_container_width=True)


# ==========================================
# 3. TOP MOTIVOS DE QUEJA (DINÁMICO SEGÚN AÑOS)
# ==========================================
elif menu == "Top Motivos de Queja":
    st.markdown('<div class="main-header">Diagnóstico Dinámico del Top de Problemas</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Análisis actualizado para el período seleccionado: <b>{rango_anios[0]} - {rango_anios[1]}</b> ({len(df_filtrado_texto)} quejas con texto)</div>', unsafe_allow_html=True)

    if len(df_filtrado_texto) == 0:
        st.warning("No hay suficientes reseñas con texto en el rango de años seleccionado para elaborar el diagnóstico.")
    else:
        top_series = df_filtrado_texto["categoria_principal"].value_counts()
        top_categories = list(top_series.index[:3])
        total_periodo_texto = len(df_filtrado_texto)

        tab_names = []
        for i, cat in enumerate(top_categories, 1):
            cnt = top_series[cat]
            pct = (cnt / total_periodo_texto) * 100
            tab_names.append(f"#{i} {cat} ({pct:.1f}%)")
        tab_names.append("Matriz Comparativa")

        tabs = st.tabs(tab_names)

        for i, cat in enumerate(top_categories):
            with tabs[i]:
                cnt = top_series[cat]
                pct = (cnt / total_periodo_texto) * 100
                sub_df = df_filtrado_texto[df_filtrado_texto["categoria_principal"] == cat]
                avg_stars = sub_df["estrellas"].mean()
                resp_rate = (sub_df["respuesta_dueno"].notna().sum() / len(sub_df)) * 100

                st.subheader(f"Problema #{i+1}: {cat}")
                
                col_t1, col_t2 = st.columns([7, 3])
                with col_t1:
                    if "Atención" in cat or "Trato" in cat:
                        diag_text = "Principal foco de insatisfacción en el período seleccionado. Se concentran reclamos sobre la predisposición en cajas y mostrador de ventas, falta de asesoramiento y actitudes percibidas como distantes o poco colaborativas."
                    elif "Espera" in cat or "Demora" in cat:
                        diag_text = "Fricción operativa en los tiempos del proceso de compra: esperas consecutivas para atención, caja y despacho de mercadería o cortes."
                    elif "Teléfono" in cat or "WhatsApp" in cat or "Canales" in cat:
                        diag_text = "Canal con la calificación más baja. Clientes experimentan llamadas sin respuesta o demoras prolongadas en presupuestos por mensajería antes de visitar el local."
                    elif "Precios" in cat or "Presupuesto" in cat:
                        diag_text = "Percepción de precios elevados respecto al mercado o discrepancias entre cotizaciones previas y valores finales facturados."
                    elif "Cortes" in cat or "Taller" in cat:
                        diag_text = "Inconvenientes con el servicio de dimensionado de placas, restricciones en horarios de corte o demoras en la preparación."
                    elif "Stock" in cat:
                        diag_text = "Disconformidad por falta de mercadería informada previamente como disponible."
                    else:
                        diag_text = "Reclamos variados sobre la operatoria general del comercio en el período seleccionado."

                    st.markdown(f"**Diagnóstico del período ({rango_anios[0]}-{rango_anios[1]}):**")
                    st.write(diag_text)

                    st.markdown("**Citas textuales de clientes en este período:**")
                    sample_reviews = sub_df[sub_df["texto"].str.len() > 30].head(3)
                    if len(sample_reviews) > 0:
                        for _, r in sample_reviews.iterrows():
                            quote_txt = r['texto'].replace('\n', ' ')
                            st.markdown(f'<div class="quote-box">"{quote_txt}" — <b>{r["autor"]}</b> ({int(r["estrellas"])} Estrellas, {r["anio_estimado"]})</div>', unsafe_allow_html=True)
                    else:
                        for _, r in sub_df.head(2).iterrows():
                            st.markdown(f'<div class="quote-box">"{r["texto"]}" — <b>{r["autor"]}</b> ({int(r["estrellas"])} Estrellas)</div>', unsafe_allow_html=True)

                with col_t2:
                    st.metric(f"Quejas ({rango_anios[0]}-{rango_anios[1]})", f"{cnt}")
                    st.metric("% del Total en Período", f"{pct:.1f}%")
                    st.metric("Promedio de Estrellas", f"{avg_stars:.2f} / 5.0")
                    st.metric("Tasa de Respuesta", f"{resp_rate:.1f}%")

        with tabs[-1]:
            st.subheader(f"Matriz Comparativa de Categorías ({rango_anios[0]} - {rango_anios[1]})")
            resumen_df = []
            for cat in categorias_disponibles:
                sub = df_filtrado_texto[df_filtrado_texto["categoria_principal"] == cat]
                if len(sub) > 0:
                    resumen_df.append({
                        "Categoría": cat,
                        "Quejas": len(sub),
                        "% del Total": f"{len(sub)/len(df_filtrado_texto)*100:.1f}%",
                        "Promedio Estrellas": round(sub["estrellas"].mean(), 2),
                        "% Respondidas": f"{sub['respuesta_dueno'].notna().sum()/len(sub)*100:.1f}%"
                    })
            if resumen_df:
                st.dataframe(pd.DataFrame(resumen_df), use_container_width=True, hide_index=True)
            else:
                st.info("No hay datos para la matriz en este rango de años.")


# ==========================================
# 4. EXPLORADOR DE RESEÑAS
# ==========================================
elif menu == "Explorador de Reseñas":
    st.markdown('<div class="main-header">Explorador Interactivo de Reseñas</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Mostrando <b>{len(df_filtrado)}</b> de {len(df)} reseñas ({rango_anios[0]} - {rango_anios[1]})</div>', unsafe_allow_html=True)

    busqueda = st.text_input("Buscar palabras clave en reseñas o respuestas:", "")

    df_display = df_filtrado.copy()
    if busqueda:
        mask = (
            df_display["texto"].fillna("").str.contains(busqueda, case=False, regex=False) |
            df_display["autor"].fillna("").str.contains(busqueda, case=False, regex=False) |
            df_display["respuesta_dueno"].fillna("").str.contains(busqueda, case=False, regex=False)
        )
        df_display = df_display[mask]
        st.caption(f"Coincidencias encontradas con '{busqueda}': {len(df_display)}")

    for idx, row in df_display.iterrows():
        stars_str = f"[{int(row['estrellas'])} Estrellas]"
        cat_badge = f"`{row['categoria_principal']}`" if pd.notna(row.get("categoria_principal")) else "`Sin categoría`"
        year_badge = f"Año: {row['anio_estimado']} ({row['fecha']})"
        
        with st.expander(f"{stars_str} | **{row['autor']}** — {year_badge} — {cat_badge}", expanded=False):
            if pd.notna(row['texto']) and row['texto'].strip():
                st.markdown(f"**Opinión:** {row['texto']}")
            else:
                st.markdown("*El usuario dejó solo calificación sin comentario de texto.*")
                
            if pd.notna(row['respuesta_dueno']) and row['respuesta_dueno'].strip():
                st.markdown(f"""
                <div style="background-color: #F0FDF4; border-left: 4px solid #009E73; padding: 0.6rem 1rem; border-radius: 4px; margin-top: 0.5rem;">
                    <b>Respuesta oficial:</b><br>{row['respuesta_dueno']}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.download_button(
        label="Descargar datos filtrados en CSV",
        data=df_display.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=f"resenas_filtradas_{rango_anios[0]}_{rango_anios[1]}.csv",
        mime="text/csv"
    )


# ==========================================
# 5. MATRIZ FODA ESTRATÉGICA
# ==========================================
elif menu == "Matriz FODA":
    st.markdown('<div class="main-header">Matriz FODA y Diagnóstico Estratégico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Cruce analítico entre la <b>identidad institucional declarada</b> y los <b>puntos de dolor empíricos</b> de los clientes</div>', unsafe_allow_html=True)

    # Métricas destacadas del cruce
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">1962</div>
            <div class="metric-label">Fundación (+60 Años de Trayectoria)</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">+20 Años</div>
            <div class="metric-label">Liderazgo en Construcción en Seco</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="color: #D55E00;">56.0%</div>
            <div class="metric-label">Quejas por Trato y Atención</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value" style="color: #0072B2;">26.0%</div>
            <div class="metric-label">Fricción en Esperas y Canales</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_foda, tab_cruces, tab_gap = st.tabs([
        "Matriz Cuadrante FODA",
        "Estrategias y Cruces (FO, DO, FA, DA)",
        "Diagnóstico de Brecha (Discurso vs. Realidad)"
    ])

    with tab_foda:
        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown("""
            <div class="foda-card foda-f">
                <div class="foda-title" style="color: #009E73;">
                    <span>🛡️ FORTALEZAS (Internas)</span>
                    <span class="foda-badge-f">Capacidades Clave</span>
                </div>
                <ul>
                    <li><b>Trayectoria y liderazgo consolidado:</b> Más de 60 años en el mercado (fundada en 1962), referente indiscutido en La Plata y alcance de distribución nacional.</li>
                    <li><b>Amplitud de catálogo y primeras marcas:</b> Especialización en placas aglomeradas, MDF melamínicos, terciados y más de 20 años liderando distribución de construcción en seco bajo norma.</li>
                    <li><b>Tecnología y servicios de valor agregado:</b> Sistema computarizado con optimizador de corte, pegado de cantos, fresados y mecanizados a medida.</li>
                    <li><b>Línea de productos propia:</b> Impulso de su marca <i>Area Base</i>.</li>
                    <li><b>Políticas formales de calidad:</b> Compromiso explícito de la dirección con sistemas de calidad total, reinversión de ganancias y relación sólida con proveedores.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="foda-card foda-d">
                <div class="foda-title" style="color: #D55E00;">
                    <span>⚠️ DEBILIDADES (Internas)</span>
                    <span class="foda-badge-d">Puntos Críticos Detectados</span>
                </div>
                <ul>
                    <li><b>Grave brecha en atención al cliente (56.0% de quejas):</b> Destrato, falta de predisposición y desidia en cajas y mostrador de ventas (inconsistencia con su política de "desarrollo humano").</li>
                    <li><b>Cuellos de botella y demoras operativas (17.3% de quejas):</b> Circuitos burocráticos con filas sucesivas (mostrador &rarr; caja &rarr; despacho / taller).</li>
                    <li><b>Colapso de canales remotos (8.7% de quejas):</b> Teléfonos sin respuesta, llamadas cortadas y demoras prolongadas para cotizaciones por WhatsApp.</li>
                    <li><b>Fricciones en el servicio de taller:</b> Horarios acotados de corte, desajustes en plazos de entrega y errores dimensionales.</li>
                    <li><b>Gestión reactiva de reputación digital:</b> Casi el 70% de las reseñas de 1 a 3 estrellas carecen de respuesta institucional o seguimiento.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_der:
            st.markdown("""
            <div class="foda-card foda-o">
                <div class="foda-title" style="color: #0072B2;">
                    <span>🚀 OPORTUNIDADES (Externas)</span>
                    <span class="foda-badge-o">Potencial de Crecimiento</span>
                </div>
                <ul>
                    <li><b>Auge del diseño de interiores y construcción en seco:</b> Creciente demanda de arquitectos, carpinteros, diseñadores y público <i>Do-It-Yourself</i>.</li>
                    <li><b>Digitalización y autogestión:</b> Incorporación de cotizadores online de placas y cortes con stock en tiempo real, agilizando el flujo previo al local.</li>
                    <li><b>Fidelización B2B especializada:</b> Creación de canales preferenciales y programas de beneficios para gremios, instaladores y constructoras.</li>
                    <li><b>Automatización omnicanal:</b> Implementación de chatbots en WhatsApp para consultas de catálogo, horarios y estado de pedidos.</li>
                    <li><b>Capacitación técnica abierta:</b> Posicionamiento como polo formador en sistemas constructivos modernos en la región.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="foda-card foda-a">
                <div class="foda-title" style="color: #E69F00;">
                    <span>⚡ AMENAZAS (Externas)</span>
                    <span class="foda-badge-a">Riesgos del Entorno</span>
                </div>
                <ul>
                    <li><b>Fuga de clientes a competidores ágiles:</b> Madereras locales y grandes cadenas (Easy, Sodimac) con procesos de cobro y despacho más dinámicos.</li>
                    <li><b>Deterioro de reputación de marca:</b> Reseñas públicas negativas en Google Maps y redes sociales que disuaden a potenciales compradores.</li>
                    <li><b>Volatilidad macroeconómica y de precios:</b> Inflación y disparidad de precios que generan fricción al cotizar o facturar.</li>
                    <li><b>Creciente exigencia de inmediatez:</b> Clientes que penalizan la espera física y la falta de respuesta inmediata en canales digitales.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with tab_cruces:
        st.subheader("Matriz de Cruces Estratégicos")
        c_fo, c_do = st.columns(2)
        with c_fo:
            st.markdown("""
            #### 🌟 Estrategias FO (Maxi - Maxi)
            *Apalancar Fortalezas para capturar Oportunidades:*
            * **Plataforma Integral de Servicios Digitales:** Utilizar el optimizador de corte computarizado y el amplio catálogo para lanzar un cotizador web con turnero para carpinteros y arquitectos.
            * **Alianzas B2B con Constructoras:** Aprovechar los 20 años de liderazgo en construcción en seco para ofrecer paquetes integrales de abastecimiento y capacitación técnica.
            """)

            st.markdown("""
            #### 🛡️ Estrategias FA (Maxi - Mini)
            *Apalancar Fortalezas para mitigar Amenazas:*
            * **Fidelización y Blindaje de Cartera:** Respaldarse en los más de 60 años de trayectoria y relación con proveedores de primeras marcas para garantizar precios competitivos y disponibilidad frente a grandes cadenas.
            * **Diferenciación por Asesoramiento Especializado:** Ofrecer servicio técnico de vanguardia en taller y mecanizados que los competidores genéricos no pueden igualar.
            """)

        with c_do:
            st.markdown("""
            #### 🔄 Estrategias DO (Mini - Maxi)
            *Superar Debilidades aprovechando Oportunidades:*
            * **Automatización y Canal WhatsApp Inteligente:** Integrar un chatbot para cotizaciones frecuentes y consultas de stock, liberando a los vendedores para que atiendan con calidez en el salón.
            * **Reingeniería de Procesos de Compra:** Unificar asesoramiento, cobro y despacho mediante turnero digital para eliminar filas y demoras.
            """)

            st.markdown("""
            #### 🚨 Estrategias DA (Mini - Mini)
            *Minimizar Debilidades y neutralizar Amenazas:*
            * **Plan de Choque en Cultura de Servicio:** Capacitación obligatoria al personal de cajas y ventas en habilidades blandas, empatía y resolución de objeciones para frenar la pérdida de clientes.
            * **Protocolo de Reputación Online:** Responder al 100% de las quejas en Google Maps en menos de 48 hs con soluciones concretas y contacto directo de gerencia.
            """)

    with tab_gap:
        st.subheader("Diagnóstico de la Brecha: Discurso Institucional vs. Experiencia Real")
        st.markdown("Comparativa entre los compromisos formalmente declarados por la empresa y la evidencia empírica relevada en la auditoría de clientes:")

        gap_data = [
            {
                "Pilar Evaluado": "1. Factor Humano y Trato al Cliente",
                "Postura Institucional Declarada": "Desarrollo permanente del factor humano, capacitación constante, búsqueda de la excelencia y satisfacción total.",
                "Realidad Empírica (Reseñas)": "56.0% de quejas por maltrato, desidia, mala predisposición en cajas y atención de mala gana.",
                "Nivel de Brecha": "🔴 Crítica (Urgente)"
            },
            {
                "Pilar Evaluado": "2. Eficiencia y Tiempos de Espera",
                "Postura Institucional Declarada": "Optimización continua de procesos, sistemas ágiles y servicio integral oportuno.",
                "Realidad Empírica (Reseñas)": "17.3% de quejas por demoras excesivas, circuitos burocráticos con 3 filas consecutivas para una sola compra.",
                "Nivel de Brecha": "🟠 Alta (Prioritaria)"
            },
            {
                "Pilar Evaluado": "3. Canales de Contacto Remoto",
                "Postura Institucional Declarada": "Interacción fluida con clientes y soluciones integrales de asesoramiento.",
                "Realidad Empírica (Reseñas)": "8.7% de quejas por teléfonos desatendidos, llamadas colgadas y presupuestos de WhatsApp demorados por días.",
                "Nivel de Brecha": "🟠 Alta (Prioritaria)"
            },
            {
                "Pilar Evaluado": "4. Taller de Cortes y Dimensionado",
                "Postura Institucional Declarada": "Sistema computarizado de optimización de cortes, mecanizado de vanguardia y máxima precisión.",
                "Realidad Empírica (Reseñas)": "Reclamos puntuales por horarios restrictivos para cortar y demoras en la preparación de pedidos.",
                "Nivel de Brecha": "🟡 Media (Mejora Continua)"
            },
            {
                "Pilar Evaluado": "5. Gestión de Calidad y Reputación",
                "Postura Institucional Declarada": "Sistema de gestión de calidad total, indicadores a procesos críticos y fidelización activa.",
                "Realidad Empírica (Reseñas)": "Casi 70% de las quejas públicas no tienen respuesta oficial, evidenciando gestión reactiva.",
                "Nivel de Brecha": "🟠 Alta (Prioritaria)"
            }
        ]

        st.dataframe(pd.DataFrame(gap_data), use_container_width=True, hide_index=True)


# ==========================================
# 6. RECOMENDACIONES DE GESTIÓN
# ==========================================
elif menu == "Recomendaciones de Gestión":
    st.markdown('<div class="main-header">Propuestas de Mejora y Acción de Gestión</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Estrategias operativas para optimizar la satisfacción del cliente</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        ### 1. Reestructuración del Circuito en Cajas y Mostrador
        * **Problema:** Fricción recurrente por atención y predisposición en el punto de cobro.
        * **Propuesta de Mejora:**
          - Capacitación en servicio al cliente y resolución de objeciones.
          - Monitoreo continuo de satisfacción en el punto de cobro.
          - Reemplazo y refuerzo en cajas durante horarios de mayor concurrencia.
        """)
        
        st.markdown("""
        ### 2. Optimización de Flujos y Tiempos de Espera
        * **Problema:** Múltiples filas sucesivas (Asesoramiento -> Caja -> Despacho).
        * **Propuesta de Mejora:**
          - Implementar cobro integrado o turnero digital para retiro de mercadería y corte de placas.
          - Sistema de aviso de despacho preparado.
        """)

    with c2:
        st.markdown("""
        ### 3. Automatización y Soporte en Canales Remotos
        * **Problema:** Congestión telefónica y demoras en WhatsApp.
        * **Propuesta de Mejora:**
          - Configuración de chatbot para consultas frecuentes (catálogo, horarios, estado de corte).
          - Asignación de rol dedicado a cotizaciones remotas para no desatender el salón.
        """)

        st.markdown("""
        ### 4. Protocolo de Gestión de Reputación Online
        * **Problema:** Respuestas ocasionalmente tardías o defensivas.
        * **Propuesta de Mejora:**
          - Estandarizar protocolo de respuesta constructiva y empática en menos de 48 horas.
          - Canal de contacto directo con gestión comercial para resolver inconvenientes.
        """)
