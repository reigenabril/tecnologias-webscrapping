#!/usr/bin/env python3
"""
Dashboard Interactivo en Streamlit: Analisis de Puntos de Dolor y Experiencia del Cliente
Materia: Tecnologias para la Gestion
"""

import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Analisis de Puntos de Dolor - Tecnologias para la Gestion",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSV_CATEGORIZADAS = "/Users/abril/tecnologias/resenas_categorizadas.csv"
CSV_ORIGINAL = "/Users/abril/tecnologias/resenas_emporio_terciado_3_o_menos.csv"

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
        background-color: #FEF2F2;
        border-left: 4px solid #EF4444;
        padding: 0.8rem 1.2rem;
        margin: 0.8rem 0;
        border-radius: 4px;
        font-style: italic;
        color: #7F1D1D;
    }
</style>
""", unsafe_allow_html=True)


def parse_year(fecha_str: str, current_year: int = 2026) -> int:
    """Convierte strings de fecha relativa a anio estimado."""
    if not isinstance(fecha_str, str):
        return current_year
    f = fecha_str.lower()
    if any(w in f for w in ['mes', 'semana', 'dia', 'hora']):
        return current_year
    if 'un anio' in f or 'un año' in f or '1 anio' in f or '1 año' in f:
        return current_year - 1
    m = re.search(r'(\d+)\s+a[nñ]o', f)
    if m:
        return current_year - int(m.group(1))
    return current_year


@st.cache_data
def load_data():
    if os.path.exists(CSV_CATEGORIZADAS):
        df = pd.read_csv(CSV_CATEGORIZADAS)
    else:
        df = pd.read_csv(CSV_ORIGINAL)
    if "anio_estimado" not in df.columns:
        df["anio_estimado"] = df["fecha"].apply(parse_year)
    return df


df = load_data()
min_year = int(df["anio_estimado"].min())
max_year = int(df["anio_estimado"].max())

# Sidebar - Filtros Globales
st.sidebar.title("Tecnologias para la Gestion")
st.sidebar.caption("Analisis de Puntos de Dolor en Comercio Minorista")

menu = st.sidebar.radio(
    "Navegacion:",
    [
        "Resumen Ejecutivo",
        "Evolucion Temporal",
        "Top Motivos de Queja",
        "Explorador de Resenas",
        "Recomendaciones de Gestion"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtro por Anio")

# Filtro de rango de anios
rango_anios = st.sidebar.slider(
    "Selecciona el rango temporal:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Adicionales")

filtro_estrellas = st.sidebar.multiselect(
    "Calificacion (Estrellas):",
    options=[1, 2, 3],
    default=[1, 2, 3]
)

categorias_disponibles = sorted(df["categoria_principal"].dropna().unique())
filtro_categorias = st.sidebar.multiselect(
    "Categoria de Queja:",
    options=categorias_disponibles,
    default=categorias_disponibles
)

filtro_respuesta = st.sidebar.selectbox(
    "Respuesta de la Empresa:",
    ["Todas", "Solo con respuesta", "Sin respuesta"]
)

# Aplicar filtros
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
    st.markdown('<div class="main-header">Auditoria de Experiencia del Cliente y Puntos de Dolor</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Estudio de Caso: Empresa de Materiales y Maderas | Periodo: <b>{rango_anios[0]} - {rango_anios[1]}</b></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_filtrado)}</div>
            <div class="metric-label">Resenas Bajas (1 a 3 Estrellas)</div>
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
            <div class="metric-label">Promedio de Calificacion</div>
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
        st.subheader("Top Motivos de Queja en el Periodo")
        if len(df_filtrado_texto) > 0:
            cat_data = df_filtrado_texto["categoria_principal"].value_counts().reset_index()
            cat_data.columns = ["Categoria", "Cantidad"]
            cat_data["Porcentaje"] = (cat_data["Cantidad"] / len(df_filtrado_texto) * 100).round(1)
            
            fig = px.bar(
                cat_data,
                x="Cantidad",
                y="Categoria",
                orientation="h",
                text=cat_data.apply(lambda r: f"{r['Cantidad']} ({r['Porcentaje']}%)", axis=1),
                color="Cantidad",
                color_continuous_scale=["#3B82F6", "#EF4444"],
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                xaxis_title="Cantidad de Resenas",
                yaxis_title="",
                coloraxis_showscale=False,
                height=380,
                margin=dict(l=10, r=20, t=10, b=10)
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay resenas con texto para los filtros seleccionados.")

    with col_chart2:
        st.subheader("Distribucion por Calificacion")
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
                color_discrete_map={1: "#EF4444", 2: "#F97316", 3: "#FBBF24"}
            )
            fig_pie.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("Diagnostico Principal")
    st.info("""
    El 82.0% de las quejas se concentran en 3 areas criticas de gestion:
    1. Atencion y Trato del Personal (56.0%): Friccion recurrente en linea de cajas y mostrador de ventas.
    2. Tiempos de Espera (17.3%): Demoras en la atencion y retiro de mercaderia.
    3. Canales Remotos (8.7%): Dificultades de comunicacion telefonica y retrasos en atencion por WhatsApp.
    """)


# ==========================================
# 2. EVOLUCION TEMPORAL POR ANIOS
# ==========================================
elif menu == "Evolucion Temporal":
    st.markdown('<div class="main-header">Evolucion Historica de Quejas por Anio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tendencia temporal de resenas de baja calificacion</div>', unsafe_allow_html=True)

    anios_df = df_filtrado.groupby(["anio_estimado", "estrellas"]).size().reset_index(name="cantidad")
    anios_df["estrellas_str"] = anios_df["estrellas"].apply(lambda s: f"{s} Estrella{'s' if s > 1 else ''}")
    
    fig_evol = px.bar(
        anios_df,
        x="anio_estimado",
        y="cantidad",
        color="estrellas_str",
        title=f"Volumen Anual de Resenas ({rango_anios[0]} - {rango_anios[1]})",
        labels={"anio_estimado": "Anio", "cantidad": "Cantidad de Resenas", "estrellas_str": "Calificacion"},
        color_discrete_map={"1 Estrella": "#EF4444", "2 Estrellas": "#F97316", "3 Estrellas": "#FBBF24"},
        barmode="stack"
    )
    fig_evol.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        height=420,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_evol, use_container_width=True)

    st.subheader("Evolucion de los Principales Motivos de Queja a lo largo del tiempo")
    if len(df_filtrado_texto) > 0:
        top_cats = df_filtrado_texto["categoria_principal"].value_counts().head(4).index
        sub_time = df_filtrado_texto[df_filtrado_texto["categoria_principal"].isin(top_cats)]
        cat_time = sub_time.groupby(["anio_estimado", "categoria_principal"]).size().reset_index(name="quejas")
        
        fig_cat_time = px.line(
            cat_time,
            x="anio_estimado",
            y="quejas",
            color="categoria_principal",
            markers=True,
            labels={"anio_estimado": "Anio", "quejas": "Cantidad de Quejas", "categoria_principal": "Motivo"},
            title="Tendencia Anual por Categoria de Queja"
        )
        fig_cat_time.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            height=380,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_cat_time, use_container_width=True)


# ==========================================
# 3. TOP MOTIVOS DE QUEJA
# ==========================================
elif menu == "Top Motivos de Queja":
    st.markdown('<div class="main-header">Diagnostico del Top 3 Problemas de Gestion</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Causas raiz, metricas e impacto en el cliente ({rango_anios[0]} - {rango_anios[1]})</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. Atencion y Trato (56%)",
        "2. Tiempos de Espera (17%)",
        "3. Canales Remotos (8.7%)",
        "Matriz Comparativa"
    ])

    with tab1:
        st.error("### Problema 1: Atencion y Trato del Personal")
        col_t1, col_t2 = st.columns([7, 3])
        with col_t1:
            st.write("""
            **Diagnostico:** Principal punto de friccion de la empresa. La mayoria de los clientes insatisfechos relatan destrato en la linea de caja y mostrador de ventas, senalando falta de predisposicion para asesorar y atencion deficiente.
            """)
            st.markdown("**Citas textuales representativas:**")
            st.markdown('<div class="quote-box">"Varios empleados tras mostrador, hablando entre ellos sin atender. Cuando finalmente te llaman atienden de mala manera como si el cliente estuviera molestando o pidiera algo gratis." — Cliente (1 Estrella)</div>', unsafe_allow_html=True)
            st.markdown('<div class="quote-box">"El lugar tiene de todo, pero pesima atencion de los empleados, sobre todo la caja 2. Cero asesoramiento." — Cliente (1 Estrella)</div>', unsafe_allow_html=True)
        with col_t2:
            sub_c = df_filtrado_texto[df_filtrado_texto["categoria_principal"] == "Atención y Trato del Personal"]
            st.metric("Total Quejas en Periodo", len(sub_c))
            pct_c = (len(sub_c) / len(df_filtrado_texto) * 100) if len(df_filtrado_texto) > 0 else 0
            st.metric("% de quejas escritas", f"{pct_c:.1f}%")
            resp_c = (sub_c["respuesta_dueno"].notna().sum() / len(sub_c) * 100) if len(sub_c) > 0 else 0
            st.metric("Tasa de Respuesta", f"{resp_c:.1f}%")

    with tab2:
        st.warning("### Problema 2: Tiempos de Espera y Demoras")
        col_t1, col_t2 = st.columns([7, 3])
        with col_t1:
            st.write("""
            **Diagnostico:** El circuito de compra presenta cuellos de botella: el cliente realiza filas sucesivas para presupuestar, pagar en caja y retirar mercaderia o cortes en deposito.
            """)
            st.markdown("**Citas textuales representativas:**")
            st.markdown('<div class="quote-box">"...la mujer de la caja no solo que no estaba sino que tardo 5 minutos en aparecer (eramos 2 personas y no tenia cola), luego de pagar fui a buscar los herrajes y el chico aparecio 3 minutos despues." — Cliente (1 Estrella)</div>', unsafe_allow_html=True)
            st.markdown('<div class="quote-box">"Mala atencion. La mujer de la caja siempre te hace esperar, pareciera que lo hace intencionalmente." — Cliente (1 Estrella)</div>', unsafe_allow_html=True)
        with col_t2:
            sub_c = df_filtrado_texto[df_filtrado_texto["categoria_principal"] == "Tiempos de Espera y Demoras"]
            st.metric("Total Quejas en Periodo", len(sub_c))
            pct_c = (len(sub_c) / len(df_filtrado_texto) * 100) if len(df_filtrado_texto) > 0 else 0
            st.metric("% de quejas escritas", f"{pct_c:.1f}%")
            resp_c = (sub_c["respuesta_dueno"].notna().sum() / len(sub_c) * 100) if len(sub_c) > 0 else 0
            st.metric("Tasa de Respuesta", f"{resp_c:.1f}%")

    with tab3:
        st.warning("### Problema 3: Canales de Contacto Remoto (Telefono / WhatsApp)")
        col_t1, col_t2 = st.columns([7, 3])
        with col_t1:
            st.write("""
            **Diagnostico:** Categoria con la calificacion mas baja (promedio 1.15 estrellas). Genera frustracion previa a la visita fisica, provocando desercion de clientes potenciales.
            """)
            st.markdown("**Citas textuales representativas:**")
            st.markdown('<div class="quote-box">"Llamas por telefono y suena durante mas de 3 minutos y cuando atienden te cortan. Impresentables." — Cliente (1 Estrella)</div>', unsafe_allow_html=True)
            st.markdown('<div class="quote-box">"Envio un WhatsApp con los detalles del presupuesto... pasan dos horas y no soy atendido. Llamo y me dicen de mala manera que los presupuestos van por WhatsApp." — Cliente (1 Estrella)</div>', unsafe_allow_html=True)
        with col_t2:
            sub_c = df_filtrado_texto[df_filtrado_texto["categoria_principal"] == "Canales de Contacto (Teléfono / WhatsApp)"]
            st.metric("Total Quejas en Periodo", len(sub_c))
            pct_c = (len(sub_c) / len(df_filtrado_texto) * 100) if len(df_filtrado_texto) > 0 else 0
            st.metric("% de quejas escritas", f"{pct_c:.1f}%")
            resp_c = (sub_c["respuesta_dueno"].notna().sum() / len(sub_c) * 100) if len(sub_c) > 0 else 0
            st.metric("Tasa de Respuesta", f"{resp_c:.1f}%")

    with tab4:
        st.subheader("Matriz Comparativa de Problemas en el Periodo")
        if len(df_filtrado_texto) > 0:
            resumen_df = []
            for cat in categorias_disponibles:
                sub = df_filtrado_texto[df_filtrado_texto["categoria_principal"] == cat]
                if len(sub) > 0:
                    resumen_df.append({
                        "Categoria": cat,
                        "Quejas": len(sub),
                        "% del Total": f"{len(sub)/len(df_filtrado_texto)*100:.1f}%",
                        "Promedio Estrellas": round(sub["estrellas"].mean(), 2),
                        "% Respondidas": f"{sub['respuesta_dueno'].notna().sum()/len(sub)*100:.1f}%"
                    })
            st.dataframe(pd.DataFrame(resumen_df), use_container_width=True, hide_index=True)


# ==========================================
# 4. EXPLORADOR DE RESENAS
# ==========================================
elif menu == "Explorador de Resenas":
    st.markdown('<div class="main-header">Explorador Interactivo de Resenas</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Mostrando <b>{len(df_filtrado)}</b> de {len(df)} resenas ({rango_anios[0]} - {rango_anios[1]})</div>', unsafe_allow_html=True)

    busqueda = st.text_input("Buscar palabras clave en resenas o respuestas:", "")

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
        cat_badge = f"`{row['categoria_principal']}`" if pd.notna(row.get("categoria_principal")) else "`Sin categoria`"
        year_badge = f"Anio: {row['anio_estimado']} ({row['fecha']})"
        
        with st.expander(f"{stars_str} | **{row['autor']}** — {year_badge} — {cat_badge}", expanded=False):
            if pd.notna(row['texto']) and row['texto'].strip():
                st.markdown(f"**Opinion:** {row['texto']}")
            else:
                st.markdown("*El usuario dejo solo calificacion sin comentario de texto.*")
                
            if pd.notna(row['respuesta_dueno']) and row['respuesta_dueno'].strip():
                st.markdown(f"""
                <div style="background-color: #F0FDF4; border-left: 4px solid #22C55E; padding: 0.6rem 1rem; border-radius: 4px; margin-top: 0.5rem;">
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
# 5. RECOMENDACIONES DE GESTION
# ==========================================
elif menu == "Recomendaciones de CX":
    st.markdown('<div class="main-header">Propuestas de Mejora y Accion de Gestion</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Estrategias operativas para optimizar la satisfaccion del cliente</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        ### 1. Reestructuracion del Circuito en Cajas y Mostrador
        * **Problema:** 56% de quejas por atencion y predisposicion deficiente.
        * **Propuesta de Mejora:**
          - Capacitacion en servicio al cliente y resolucion de objeciones.
          - Monitoreo continuo de satisfaccion en el punto de cobro.
          - Reemplazo y refuerzo en cajas durante horarios de mayor concurrencia.
        """)
        
        st.markdown("""
        ### 2. Optimizacion de Flujos y Tiempos de Espera
        * **Problema:** Multiples filas sucesivas (Asesoramiento -> Caja -> Despacho).
        * **Propuesta de Mejora:**
          - Implementar cobro integrado o turnero digital para retiro de mercaderia y corte de placas.
          - Sistema de aviso de despacho preparado.
        """)

    with c2:
        st.markdown("""
        ### 3. Automatizacion y Soporte en Canales Remotos
        * **Problema:** Congestion telefonica y demoras en WhatsApp.
        * **Propuesta de Mejora:**
          - Configuracion de chatbot para consultas frecuentes (catalogo, horarios, estado de corte).
          - Asignacion de rol dedicado a cotizaciones remotas para no desatender el salon.
        """)

        st.markdown("""
        ### 4. Protocolo de Gestion de Reputacion Online
        * **Problema:** Respuestas ocasionalmente tardias o defensivas.
        * **Propuesta de Mejora:**
          - Estandarizar protocolo de respuesta constructiva y empatica en menos de 48 horas.
          - Canal de contacto directo con gestion comercial para resolver inconvenientes.
        """)
