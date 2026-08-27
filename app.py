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

# Paleta Okabe-Ito con alto contraste de luminancia y diferenciación para deuteranopia/protanopia
COLOR_1_STAR = "#0072B2"  # Azul profundo
COLOR_2_STAR = "#E69F00"  # Naranja / Ámbar de alta luminancia
COLOR_3_STAR = "#009E73"  # Verde azulado

OKABE_ITO_PALETTE = [
    "#0072B2",  # Azul
    "#E69F00",  # Naranja
    "#009E73",  # Verde azulado
    "#CC79A7",  # Púrpura rojizo
    "#56B4E9",  # Celeste cielo
    "#D55E00",  # Bermellón
    "#718096"   # Gris neutro
]

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
            
            fig = px.bar(
                cat_data,
                x="Cantidad",
                y="Categoría",
                orientation="h",
                text=cat_data.apply(lambda r: f"{r['Cantidad']} ({r['Porcentaje']}%)", axis=1),
                color="Categoría",
                color_discrete_sequence=OKABE_ITO_PALETTE,
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
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
        
        fig_cat_time = px.line(
            cat_time,
            x="anio_estimado",
            y="quejas",
            color="categoria_principal",
            color_discrete_sequence=OKABE_ITO_PALETTE,
            markers=True,
            labels={"anio_estimado": "Año", "quejas": "Cantidad de Quejas", "categoria_principal": "Motivo"},
            title="Tendencia Anual por Categoría de Queja"
        )
        fig_cat_time.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            height=380,
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
# 5. RECOMENDACIONES DE GESTIÓN
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
