#!/usr/bin/env python3
"""
Dashboard Interactivo en Streamlit: Diagnóstico Digital y Análisis Estratégico (Entrega 1)
Materia: Tecnologías para la Gestión (FCE - UNLP)
Caso de Estudio: El Emporio del Terciado S.A.
"""

import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Entrega 1: Diagnóstico Digital - El Emporio del Terciado",
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Rutas dinámicas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_CATEGORIZADAS = os.path.join(BASE_DIR, "resenas_categorizadas.csv")
CSV_ORIGINAL = os.path.join(BASE_DIR, "resenas_emporio_terciado_3_o_menos.csv")

# Paleta accesible Okabe-Ito y jerarquía visual
COLOR_1_STAR = "#0072B2"  # Azul profundo
COLOR_2_STAR = "#E69F00"  # Ámbar / Naranja
COLOR_3_STAR = "#94A3B8"  # Gris azulado neutro

HIERARCHY_PALETTE = [
    "#0072B2",  # Top 1: Máximo contraste
    "#E69F00",  # Top 2: Contraste medio-alto
    "#009E73",  # Top 3: Verde azulado
    "#64748B",  # Top 4: Pizarra
    "#94A3B8",  # Top 5: Gris suave
    "#CBD5E1",  # Top 6: Muy suave
    "#E2E8F0"   # Top 7+: Neutro
]

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
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.1rem;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.82rem;
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
    .process-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border-left: 5px solid #0072B2;
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
    .badge-dato { background-color: #E6F4EA; color: #137333; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; border: 1px solid #CEEAD6; }
    .badge-supuesto { background-color: #FEF7E0; color: #B06000; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem; border: 1px solid #FEEFC3; }
    .callout-box {
        background-color: #F1F5F9;
        border-left: 4px solid #475569;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
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
    elif os.path.exists(os.path.join(BASE_DIR, "resenas_unificadas.csv")):
        df = pd.read_csv(os.path.join(BASE_DIR, "resenas_unificadas.csv"))
    elif os.path.exists(CSV_ORIGINAL):
        df = pd.read_csv(CSV_ORIGINAL)
    else:
        st.error("No se encontró el archivo de datos CSV.")
        return pd.DataFrame()
        
    if "anio_estimado" not in df.columns and "fecha" in df.columns:
        df["anio_estimado"] = df["fecha"].apply(parse_year)
    if "sucursal" not in df.columns:
        df["sucursal"] = "Casa Central (Calle 31)"
    return df


df = load_data()
if df.empty:
    st.stop()

min_year = int(df["anio_estimado"].min())
max_year = int(df["anio_estimado"].max())

# Sidebar - Menú Narrativo tipo Historia
st.sidebar.markdown("### 🎓 Tecnologías para la Gestión")
st.sidebar.caption("Trabajo Práctico Integrador — FCE UNLP")
st.sidebar.markdown("**Caso:** *El Emporio del Terciado S.A.*")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Estructura de la Entrega 1:",
    [
        "1. Presentación & Diagnóstico Digital",
        "2. Evidencia Empírica (Scraping)",
        "3. Mapeo de Procesos AS-IS",
        "4. Matriz FODA Estratégica",
        "5. Explorador de Reseñas (Voz del Cliente)",
        "6. Hoja de Ruta & Supuestos Base"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Filtros de Análisis")

# Filtro de Sucursal
sucursales_lista = ["Todas las sucursales"] + sorted(df["sucursal"].dropna().unique().tolist())
filtro_sucursal = st.sidebar.selectbox("Sucursal:", sucursales_lista)

rango_anios = st.sidebar.slider(
    "Período de análisis (Años):",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1
)

filtro_estrellas = st.sidebar.multiselect(
    "Calificación (Estrellas):",
    options=[1, 2, 3, 4, 5],
    default=[1, 2, 3, 4, 5],
    help="Universo completo (1 a 5 estrellas) seleccionado para alimentar FODA"
)

categorias_disponibles = sorted(df["categoria_principal"].dropna().unique())
filtro_categorias = st.sidebar.multiselect(
    "Categoría de Queja / Opinión:",
    options=categorias_disponibles,
    default=categorias_disponibles
)

filtro_respuesta = st.sidebar.selectbox(
    "Respuesta Institucional:",
    ["Todas", "Solo con respuesta", "Sin respuesta"]
)

# Filtro global
df_filtrado = df[
    (df["anio_estimado"] >= rango_anios[0]) &
    (df["anio_estimado"] <= rango_anios[1]) &
    (df["estrellas"].isin(filtro_estrellas))
]

if filtro_sucursal != "Todas las sucursales":
    df_filtrado = df_filtrado[df_filtrado["sucursal"] == filtro_sucursal]

if filtro_respuesta == "Solo con respuesta":
    df_filtrado = df_filtrado[df_filtrado["respuesta_dueno"].notna() & (df_filtrado["respuesta_dueno"].str.strip() != "")]
elif filtro_respuesta == "Sin respuesta":
    df_filtrado = df_filtrado[df_filtrado["respuesta_dueno"].isna() | (df_filtrado["respuesta_dueno"].str.strip() == "")]

if filtro_categorias:
    df_filtrado = df_filtrado[df_filtrado["categoria_principal"].isin(filtro_categorias) | df_filtrado["texto"].isna()]

df_filtrado_texto = df_filtrado[df_filtrado["texto"].notna() & (df_filtrado["texto"].str.strip() != "")]


# ==============================================================================
# 1. PRESENTACIÓN & DIAGNÓSTICO DIGITAL
# ==============================================================================
if menu == "1. Presentación & Diagnóstico Digital":
    st.markdown('<div class="main-header">Entrega 1: Diagnóstico Digital y Análisis Estratégico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Auditoría Integral de Sistemas de Información, Procesos de Negocio y Madurez Digital</div>', unsafe_allow_html=True)

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.markdown("**Organización Cliente:** El Emporio del Terciado S.A.")
        st.markdown("**Ubicación:** La Plata, Prov. de Buenos Aires")
    with col_meta2:
        st.markdown("**Fundación:** 1962 (64 años de trayectoria)")
        st.markdown("**Rubro:** Maderas, placas, herrajes y construcción en seco")
    with col_meta3:
        st.markdown("**Enfoque:** Consultoría en Transformación Digital")
        st.markdown("**Marco Metodológico:** Laudon & Laudon (16ª Ed.)")

    st.markdown("---")

    st.subheader("1. Perfil Corporativo y Modelo de Negocio")
    col_corp1, col_corp2 = st.columns([6, 4])
    with col_corp1:
        st.markdown("""
        **El Emporio del Terciado S.A.** es una empresa comercializadora y distribuidora de maderas, placas aglomeradas y MDF melamínicos, fenólicos, herrajes e insumos para la construcción en seco (Durlock/Knauf).
        
        Fundada en **1962** en la ciudad de La Plata, cuenta con más de seis décadas de liderazgo en el abastecimiento para carpintería, arquitectura y construcción.
        
        **Segmentos de Demanda Atendidos:**
        - **B2B (Mayorista e Industrial):** Constructoras, carpinterías y fabricantes de muebles con compras por volumen, cuentas corrientes y corte programado.
        - **B2C (Minorista y Particular):** Propietarios, instaladores independientes y público general (*Do It Yourself*).
        """)
    with col_corp2:
        st.markdown("""
        <div class="callout-box" style="margin-top: 0;">
            <b>Misión Organizacional:</b> Proveer a carpinteros, profesionales de la construcción y público en general una amplia variedad de maderas y placas de alta calidad, combinando asesoramiento técnico con servicios de corte computarizado de precisión.<br><br>
            <b>Visión Estratégica:</b> Consolidarse como el referente digital e industrial de la madera y la construcción en seco en la región, integrando canales de autogestión online con excelencia operativa y logística.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("2. Propuesta de Valor y Capacidades Operativas")
    st.markdown("""
    La principal ventaja competitiva de **El Emporio del Terciado S.A.** radica en la **integración vertical del servicio de dimensionado a medida**:
    
    * **Servicio Computarizado de Taller:** Maquinaria industrial de última generación para optimización de corte de placas, pegado de cantos en PVC/ABS, fresado y mecanizado.
    * **Catálogo Integral de Construcción en Seco:** Distribuidor líder en perfiles estructurales, placas de yeso y aislantes térmicos y acústicos bajo normas de calidad.
    * **Línea de Marca Propia (*Area Base*):** Desarrollo de productos propios para garantizar estándares de terminación y control directo de márgenes.
    * **Capacidad de Escala y Logística:** Depósito central y flota propia para abastecimiento mayorista a nivel regional y nacional.
    """)
    
    col_prop1, col_prop2 = st.columns([6, 4])
    with col_prop1:
        st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 1rem; border-radius: 8px;">
            <b style="color: #0F172A;">Cobertura y Horarios de Atención:</b><br>
            • Lunes a Viernes de 8:00 a 16:30 hs. | Sábados de 8:30 a 12:30 hs.<br>
            • <b>Red de Sucursales en La Plata:</b> Casa Central (Calle 31), EGGER HAUS (Av. 44) y Sucursal Centenario.
        </div>
        """, unsafe_allow_html=True)
    with col_prop2:
        st.markdown("""
        <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; padding: 1rem; border-radius: 8px;">
            <b style="color: #166534;">Diferencial de Servicio:</b><br>
            Corte computarizado con software optimizador para minimizar desperdicios de placa y entregar paquetes rotulados a medida.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("3. Diagnóstico de Madurez Digital Organizacional")
    st.markdown("""
    Evaluación integral del nivel de madurez tecnológica y operativa de **El Emporio del Terciado S.A.** aplicando un marco multidimensional de 6 ejes (Estrategia, Tecnología, Datos, Procesos, Personas/Cultura y Clientes/Canales), fundamentado en la metodología de *Laudon & Laudon* y respaldado por la auditoría de procesos y clientes.
    """)

    # --------------------------------------------------------------------------
    # OVERALL REVIEW / SÍNTESIS GLOBAL
    # --------------------------------------------------------------------------
    st.markdown("### 🌐 Overall Review: Diagnóstico y Dictamen Global")

    # Scorecard global con métricas clave
    col_ov1, col_ov2, col_ov3, col_ov4 = st.columns(4)
    with col_ov1:
        st.markdown("""
        <div class="metric-card" style="border-left: 4px solid #D55E00;">
            <div class="metric-value" style="color: #D55E00;">1.6 / 5.0</div>
            <div class="metric-label">Nivel de Madurez Global (AS-IS)</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;"><b>Estado:</b> Inicial / Reactivo</div>
        </div>
        """, unsafe_allow_html=True)
    with col_ov2:
        st.markdown("""
        <div class="metric-card" style="border-left: 4px solid #0072B2;">
            <div class="metric-value" style="color: #0072B2;">-2.4 pts</div>
            <div class="metric-label">Brecha vs. Benchmark Digital (4.0)</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">Sector retail / distribución moderno</div>
        </div>
        """, unsafe_allow_html=True)
    with col_ov3:
        st.markdown("""
        <div class="metric-card" style="border-left: 4px solid #E69F00;">
            <div class="metric-value" style="color: #E69F00;">Silos Aislados</div>
            <div class="metric-label">Arquitectura Predominante</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">On-premise sin integración API</div>
        </div>
        """, unsafe_allow_html=True)
    with col_ov4:
        st.markdown("""
        <div class="metric-card" style="border-left: 4px solid #009E73;">
            <div class="metric-value" style="color: #009E73;">4.1 / 5.0</div>
            <div class="metric-label">Meta de Transformación (TO-BE)</div>
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 4px;">Con ERP + CRM + Portal B2B + BI</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico Radar + Dictamen Ejecutivo
    col_rad1, col_rad2 = st.columns([5, 5])
    with col_rad1:
        st.markdown("##### 🕸️ Matriz Radar: Estado Actual (AS-IS) vs. Objetivo (TO-BE)")
        
        radar_categories = [
            "1. Estrategia Digital",
            "2. Tecnología & Infraestructura",
            "3. Datos & Analítica",
            "4. Procesos de Negocio",
            "5. Personas & Cultura",
            "6. Clientes & Canales"
        ]
        
        r_asis = [1.5, 1.8, 1.2, 1.5, 2.0, 1.6]
        r_tobe = [4.0, 4.0, 3.8, 4.2, 3.9, 4.5]
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=r_asis + [r_asis[0]],
            theta=radar_categories + [radar_categories[0]],
            fill='toself',
            name='Madurez Actual (AS-IS) [1.6/5.0]',
            line=dict(color='#0072B2', width=2.5),
            fillcolor='rgba(0, 114, 178, 0.25)',
            marker=dict(size=7, symbol='circle')
        ))
        
        fig_radar.add_trace(go.Scatterpolar(
            r=r_tobe + [r_tobe[0]],
            theta=radar_categories + [radar_categories[0]],
            fill='toself',
            name='Objetivo Estratégico (TO-BE) [4.1/5.0]',
            line=dict(color='#009E73', width=2, dash='dash'),
            fillcolor='rgba(0, 158, 115, 0.15)',
            marker=dict(size=6, symbol='diamond')
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickvals=[1, 2, 3, 4, 5],
                    ticktext=["1: Inicial", "2: Oportunista", "3: Definido", "4: Gestionado", "5: Optimizado"],
                    tickfont=dict(size=9, color="#64748B"),
                    gridcolor="#E2E8F0"
                ),
                angularaxis=dict(
                    tickfont=dict(size=10, color="#1E293B", family="sans-serif"),
                    rotation=90,
                    direction="clockwise"
                )
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(size=10)),
            height=370,
            margin=dict(l=30, r=30, t=20, b=50)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_rad2:
        st.markdown("##### 📋 Dictamen Ejecutivo y Arquetipo Organizacional")
        st.markdown("""
        <div style="background-color: #F8FAFC; border-left: 4px solid #0072B2; padding: 1rem 1.2rem; border-radius: 6px; font-size: 0.88rem; line-height: 1.5; color: #1E293B;">
            <b>Arquetipo:</b> <i>"Líder Productivo Tradicional con Asimetría Digital y Cuello de Botella Operativo"</i>.<br><br>
            • <b>La Paradoja de Automatización:</b> La empresa destaca por su maquinaria de corte computarizado de alta precisión y calidad de catálogo (fortaleza física), pero su <i>back-office</i> y canales de atención funcionan con métodos manuales (papel, planillas dispersas y POS local aislado).<br><br>
            • <b>El Núcleo del Problema:</b> Al no ofrecer canales de autogestión online (despieces, cotizaciones y pedidos web), toda la carga operativa recae sobre el salón de ventas y WhatsApp, generando el <b>circuito de 3 filas</b> y saturación del personal.<br><br>
            • <b>Impacto en la Reputación:</b> Esta desarticulación informática es la causa raíz del <b>56% de quejas por mala atención</b> y <b>17% por demoras</b> detectadas en Google Maps.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 0.8rem 1rem; margin-top: 0.6rem; font-size: 0.84rem; color: #92400E;">
            💡 <b>Veredicto de Consultoría:</b> La transformación no requiere cambiar el modelo de negocio ni el producto —ambos sumamente valorados— sino <b>orquestar un ecosistema digital integrado (ERP + CRM + Portal B2B de Despiece + BI)</b> que elimine la fricción en el cliente y libere al personal de tareas manuales.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3 Pilares del Diagnóstico Transversal
    st.markdown("##### 📌 Pilares Clave del Diagnóstico Transversal")
    pil1, pil2, pil3 = st.columns(3)
    with pil1:
        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #E69F00; height: 100%;">
            <b style="color: #B45309; font-size: 0.95rem;">1. Desconexión de Sistemas (Silos)</b>
            <p style="font-size: 0.84rem; color: #334155; margin-top: 0.5rem;">
            El software de optimización de cortes del taller no dialoga con el sistema de facturación ni con el inventario de salón. Esta fragmentación obliga a reingresar datos en papel, genera retrasos y quiebres de stock no alertados al cliente.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with pil2:
        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #D55E00; height: 100%;">
            <b style="color: #991B1B; font-size: 0.95rem;">2. Sobrecarga y Fricción Humana</b>
            <p style="font-size: 0.84rem; color: #334155; margin-top: 0.5rem;">
            Los vendedores atienden simultáneamente el mostrador presencial, teléfonos fijos y WhatsApp personal. La falta de automatización y CRM genera agotamiento en el equipo y un trato percibido como apurado o deficiente.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with pil3:
        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #009E73; height: 100%;">
            <b style="color: #166534; font-size: 0.95rem;">3. Potencial B2B Inexplorado</b>
            <p style="font-size: 0.84rem; color: #334155; margin-top: 0.5rem;">
            Los carpinteros y arquitectos (público B2B) demandan poder cotizar y mandar despieces desde su taller o smartphone 24/7. Digitalizar este flujo representaría un salto exponencial en fidelización y eficiencia de escala.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # DETALLE POR DIMENSIÓN
    # --------------------------------------------------------------------------
    st.markdown("### 📊 Evaluación Detallada por Dimensión (Modelo de 6 Ejes)")
    st.caption("Puntuación por eje basada en la escala de madurez Laudon (1: Inicial, 2: Oportunista, 3: Definido, 4: Gestionado, 5: Optimizado):")

    dim1, dim2, dim3 = st.columns(3)
    with dim1:
        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #0072B2;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #0072B2; margin:0;">1. Estrategia Digital</h4>
                <span style="background-color: #E0F2FE; color: #0369A1; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">1.5 / 5.0</span>
            </div>
            <p style="font-size: 0.85rem; color: #475569; margin: 4px 0 8px 0;"><b>Nivel: Inicial / Reactivo</b></p>
            <p style="font-size: 0.83rem; color: #334155; line-height: 1.4;">
            • Visión orientada al oficio y comercio tradicional sin plan director de TI.<br>
            • Inversiones en tecnología concentradas en maquinaria física sin hoja de ruta de software.<br>
            • Inexistencia de métricas (KPIs) para evaluar canales digitales o satisfacción.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #D55E00;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #D55E00; margin:0;">4. Procesos de Negocio</h4>
                <span style="background-color: #FFEDD5; color: #C2410C; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">1.5 / 5.0</span>
            </div>
            <p style="font-size: 0.85rem; color: #475569; margin: 4px 0 8px 0;"><b>Nivel: Manual / Fragmentado</b></p>
            <p style="font-size: 0.83rem; color: #334155; line-height: 1.4;">
            • Circuito presencial ineficiente de 3 filas sucesivas (mostrador ➔ caja ➔ entrega/taller).<br>
            • Dependencia crítica de soporte papel (remitos, planos a mano) para pasar pedidos a taller.<br>
            • Gestión reactiva de compras y stock sin automatización de puntos de reposición.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with dim2:
        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #E69F00;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #E69F00; margin:0;">2. Tecnología e Infra</h4>
                <span style="background-color: #FEF3C7; color: #B45309; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">1.8 / 5.0</span>
            </div>
            <p style="font-size: 0.85rem; color: #475569; margin: 4px 0 8px 0;"><b>Nivel: Silos Aislados / On-Premise</b></p>
            <p style="font-size: 0.83rem; color: #334155; line-height: 1.4;">
            • Facturación y POS monousuario local sin infraestructura Cloud ni redundancia.<br>
            • Falta de interoperabilidad entre software de corte, caja y depósito.<br>
            • Riesgo operativo por copias de seguridad locales y vulnerabilidades de continuidad.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #009E73;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #009E73; margin:0;">5. Personas y Cultura</h4>
                <span style="background-color: #DCFCE7; color: #15803D; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">2.0 / 5.0</span>
            </div>
            <p style="font-size: 0.85rem; color: #475569; margin: 4px 0 8px 0;"><b>Nivel: Tradicional / Sobrecargado</b></p>
            <p style="font-size: 0.83rem; color: #334155; line-height: 1.4;">
            • Alto conocimiento del oficio maderero pero cultura reacia o poco habituada a herramientas digitales.<br>
            • Personal sobreexigido por tareas administrativas manuales y atención multicanal no asistida.<br>
            • Necesidad prioritaria de capacitación en atención al cliente y uso de sistemas unificados.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with dim3:
        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #64748B;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #475569; margin:0;">3. Datos y Analítica</h4>
                <span style="background-color: #F1F5F9; color: #475569; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">1.2 / 5.0</span>
            </div>
            <p style="font-size: 0.85rem; color: #475569; margin: 4px 0 8px 0;"><b>Nivel: Básico / No Integrado</b></p>
            <p style="font-size: 0.83rem; color: #334155; line-height: 1.4;">
            • Decisiones de abastecimiento y precios basadas en intuición y planillas Excel dispersas.<br>
            • Datos no estructurados (reseñas de clientes, chats de WhatsApp) totalmente desaprovechados.<br>
            • El presente proyecto demuestra el alto valor oculto en los datos para la toma de decisiones.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="foda-card" style="border-top: 4px solid #CC79A7;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #CC79A7; margin:0;">6. Clientes y Canales</h4>
                <span style="background-color: #FCE7F3; color: #BE185D; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">1.6 / 5.0</span>
            </div>
            <p style="font-size: 0.85rem; color: #475569; margin: 4px 0 8px 0;"><b>Nivel: Multicanal Desarticulado</b></p>
            <p style="font-size: 0.83rem; color: #334155; line-height: 1.4;">
            • Canales remotos (WhatsApp y teléfono) sin CRM, chatbots ni trazabilidad de estados.<br>
            • Inexistencia de portal web transaccional o autogestión de despieces para clientes B2B.<br>
            • 68.3% de opiniones en Google Maps sin respuesta institucional ni escucha activa.
            </p>
        </div>
        """, unsafe_allow_html=True)




# ==============================================================================
# 2. EVIDENCIA EMPÍRICA (SCRAPING)
# ==============================================================================
elif menu == "2. Evidencia Empírica (Scraping)":
    # Dataset filtrado por período y sucursal para análisis de balance (FODA)
    df_periodo = df[
        (df["anio_estimado"] >= rango_anios[0]) &
        (df["anio_estimado"] <= rango_anios[1])
    ]
    if filtro_sucursal != "Todas las sucursales":
        df_periodo = df_periodo[df_periodo["sucursal"] == filtro_sucursal]

    total_periodo = len(df_periodo)
    df_pos_p = df_periodo[df_periodo["estrellas"] >= 4]
    df_neg_p = df_periodo[df_periodo["estrellas"] <= 3]
    
    n_pos = len(df_pos_p)
    n_neg = len(df_neg_p)
    pct_pos_p = (n_pos / total_periodo * 100) if total_periodo > 0 else 0
    pct_neg_p = (n_neg / total_periodo * 100) if total_periodo > 0 else 0

    st.markdown('<div class="main-header">Evidencia Empírica: Auditoría de Reseñas de Google Maps</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Período seleccionado: <b>{rango_anios[0]} - {rango_anios[1]}</b> | Sucursal: <b>{filtro_sucursal}</b> | Reseñas en período: <b>{total_periodo}</b> (Filtradas: <b>{len(df_filtrado)}</b>)</div>', unsafe_allow_html=True)

    # Indicadores Clave Dinámicos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_filtrado)}</div>
            <div class="metric-label">Reseñas en Filtro Actual</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        pct_texto = (len(df_filtrado_texto) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_filtrado_texto)} ({pct_texto:.1f}%)</div>
            <div class="metric-label">Opiniones con Comentario Escrito</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        promedio = df_filtrado['estrellas'].mean() if len(df_filtrado) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{promedio:.2f} / 5.0</div>
            <div class="metric-label">Calificación Promedio Filtrada</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        respondidas = df_filtrado['respuesta_dueno'].notna().sum()
        pct_resp = (respondidas / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{respondidas} ({pct_resp:.1f}%)</div>
            <div class="metric-label">Tasa de Respuesta del Comercio</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_foda_link, tab_nlp, tab_sucursales, tab_temporal = st.tabs([
        f"🎯 Evidencia para el FODA ({n_pos} Positivas vs {n_neg} Críticas)",
        "📊 Distribución Temática General (NLP)",
        "🏢 Comparativa Multi-Sucursal (3 Locales)",
        "📅 Evolución Temporal de Opiniones"
    ])

    with tab_foda_link:
        st.subheader(f"Base Empírica para la Matriz FODA ({rango_anios[0]} - {rango_anios[1]})")
        st.markdown(f"""
        Para el período **{rango_anios[0]} - {rango_anios[1]}** (con **{total_periodo} reseñas relevadas** en *{filtro_sucursal}*), la evidencia empírica respalda objetivamente la construcción de la matriz FODA:
        """)

        # Conteo dinámico de categorías en positivas y negativas con texto en el período
        df_pos_txt = df_pos_p[df_pos_p["texto"].notna() & (df_pos_p["texto"].str.strip() != "")]
        df_neg_txt = df_neg_p[df_neg_p["texto"].notna() & (df_neg_p["texto"].str.strip() != "")]
        
        pos_cat_counts = df_pos_txt["categoria_principal"].value_counts().to_dict() if len(df_pos_txt) > 0 else {}
        neg_cat_counts = df_neg_txt["categoria_principal"].value_counts().to_dict() if len(df_neg_txt) > 0 else {}
        
        c_pos_aten = pos_cat_counts.get("Atención y Trato del Personal", 0)
        c_pos_cortes = pos_cat_counts.get("Servicio de Cortes y Taller", 0)
        c_pos_precios = pos_cat_counts.get("Precios y Presupuestos", 0)
        
        c_neg_aten = neg_cat_counts.get("Atención y Trato del Personal", 0)
        c_neg_espera = neg_cat_counts.get("Tiempos de Espera y Demoras", 0)
        c_neg_canales = neg_cat_counts.get("Canales de Contacto (Teléfono / WhatsApp)", 0)
        c_neg_cortes = neg_cat_counts.get("Servicio de Cortes y Taller", 0)
        c_neg_stock = neg_cat_counts.get("Stock y Disponibilidad", 0)

        neg_sin_resp = (df_neg_p["respuesta_dueno"].isna().sum() / n_neg * 100) if n_neg > 0 else 0

        col_foda1, col_foda2 = st.columns(2)
        with col_foda1:
            st.markdown(f"""
            <div style="background-color: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 8px; padding: 1.2rem;">
                <h4 style="color: #166534; margin-top: 0;">🛡️ Sustento Empírico de FORTALEZAS ({n_pos} Reseñas ⭐4-5 | {pct_pos_p:.1f}%)</h4>
                <ul style="color: #14532D; font-size: 0.88rem; padding-left: 1.2rem;">
                    <li><b>F1. Precisión en Cortes y Taller:</b> <b>{c_pos_cortes}</b> menciones elogian la exactitud del corte computarizado y terminación de cantos en el período.</li>
                    <li><b>F2. Asesoramiento Profesional en Salón:</b> <b>{c_pos_aten}</b> comentarios destacan el buen trato y conocimiento técnico cuando la atención es personalizada.</li>
                    <li><b>F3. Variedad y Catálogo Integral:</b> Alta valoración de la disponibilidad de tableros melamínicos, fenólicos e insumos de construcción en seco.</li>
                    <li><b>F4. Precios y Escala Mayorista:</b> <b>{c_pos_precios}</b> opiniones destacan convenios comerciales, promociones y cuentas corrientes B2B.</li>
                    <li><b>F5. Trayectoria y Respaldo de Marca:</b> Consolidación histórica como el referente maderero en La Plata.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_foda2:
            st.markdown(f"""
            <div style="background-color: #FEF2F2; border: 1.5px solid #FCA5A5; border-radius: 8px; padding: 1.2rem;">
                <h4 style="color: #991B1B; margin-top: 0;">⚠️ Sustento Empírico de DEBILIDADES ({n_neg} Reseñas ⭐1-3 | {pct_neg_p:.1f}%)</h4>
                <ul style="color: #7F1D1D; font-size: 0.88rem; padding-left: 1.2rem;">
                    <li><b>D1. Circuito de 3 Filas y Colapso de Salón:</b> <b>{c_neg_aten}</b> quejas por fricción en mostrador/caja y <b>{c_neg_espera}</b> por demoras en horas pico.</li>
                    <li><b>D2. Incomunicación en Canales Remotos:</b> <b>{c_neg_canales}</b> quejas formales por llamadas desatendidas y demoras en WhatsApp.</li>
                    <li><b>D3. Inexistencia de Portal Web B2B:</b> Necesidad presencial obligatoria para pedir presupuestos y órdenes de despiece.</li>
                    <li><b>D4. Tiempos de Entrega de Taller:</b> <b>{c_neg_cortes}</b> reclamos por plazos extensos y <b>{c_neg_stock}</b> por quiebres de stock no avisados.</li>
                    <li><b>D5. Desatención de Reputación Online:</b> <b>{neg_sin_resp:.1f}%</b> de las opiniones negativas en este período no tienen respuesta oficial.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_sent1, col_sent2 = st.columns([6, 4])
        with col_sent1:
            df_sent = pd.DataFrame({
                "Sentimiento": ["Opiniones Positivas (Fortalezas ⭐4-5)", "Opiniones Críticas (Debilidades ⭐1-3)"],
                "Cantidad": [n_pos, n_neg],
                "Porcentaje": [round(pct_pos_p, 1), round(pct_neg_p, 1)]
            })
            fig_sent = px.bar(
                df_sent,
                x="Sentimiento",
                y="Cantidad",
                text=df_sent.apply(lambda r: f"{r['Cantidad']} ({r['Porcentaje']}%)", axis=1),
                color="Sentimiento",
                color_discrete_map={
                    "Opiniones Positivas (Fortalezas ⭐4-5)": "#009E73",
                    "Opiniones Críticas (Debilidades ⭐1-3)": "#0072B2"
                },
                title=f"Balance Empírico ({rango_anios[0]} - {rango_anios[1]} | {total_periodo} Reseñas)"
            )
            fig_sent.update_layout(height=340, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            fig_sent.update_traces(textposition="outside")
            st.plotly_chart(fig_sent, use_container_width=True)

        with col_sent2:
            st.markdown(f"""
            <div class="callout-box" style="margin-top: 1rem;">
                <b>Diagnóstico Estratégico del Período ({rango_anios[0]} - {rango_anios[1]}):</b><br><br>
                El <b>{pct_pos_p:.1f}% de satisfacción</b> demuestra la fortaleza en producto, variedad de stock y capacidad de taller.<br><br>
                El <b>{pct_neg_p:.1f}% de fricción</b> confirma la necesidad de implementar soluciones de <b>Transformación Digital</b> (ERP, CRM y Portal Web) para resolver cuellos de botella de mostrador y canales remotos.
            </div>
            """, unsafe_allow_html=True)

    with tab_nlp:
        col_chart1, col_chart2 = st.columns([6, 4])
        with col_chart1:
            st.subheader(f"Categorización Temática NLP ({rango_anios[0]} - {rango_anios[1]})")
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
                    xaxis_title="Cantidad de Menciones",
                    yaxis_title="",
                    showlegend=False,
                    height=380,
                    margin=dict(l=10, r=20, t=10, b=10)
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay comentarios de texto para los filtros seleccionados en este período.")

        with col_chart2:
            st.subheader(f"Distribución de Severidad ({rango_anios[0]} - {rango_anios[1]})")
            if len(df_filtrado) > 0:
                star_counts = df_filtrado["estrellas"].value_counts().sort_index().reset_index()
                star_counts.columns = ["Estrellas", "Cantidad"]
                star_counts["Etiqueta"] = star_counts["Estrellas"].apply(lambda s: f"{s} Estrella{'s' if s > 1 else ''}")
                
                star_palette = {1: "#0072B2", 2: "#E69F00", 3: "#94A3B8", 4: "#56B4E9", 5: "#009E73"}
                
                fig_pie = px.pie(
                    star_counts,
                    names="Etiqueta",
                    values="Cantidad",
                    hole=0.45,
                    color="Estrellas",
                    color_discrete_map=star_palette
                )
                fig_pie.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)

    with tab_sucursales:
        df_suc_periodo = df[
            (df["anio_estimado"] >= rango_anios[0]) &
            (df["anio_estimado"] <= rango_anios[1])
        ]
        st.subheader(f"Auditoría Consolidada por Sucursal ({rango_anios[0]} - {rango_anios[1]} | {len(df_suc_periodo)} Reseñas)")
        
        if len(df_suc_periodo) > 0:
            suc_resumen = df_suc_periodo.groupby("sucursal").agg(
                Total_Resenas=("id_resena", "count"),
                Promedio_Estrellas=("estrellas", "mean"),
                Resenas_Criticas=("estrellas", lambda x: (x <= 3).sum()),
                Pct_Criticas=("estrellas", lambda x: ((x <= 3).sum() / len(x) * 100).round(1)),
                Respondidas=("respuesta_dueno", lambda x: x.notna().sum())
            ).reset_index()
            suc_resumen.columns = ["Sucursal", "Total Reseñas", "Promedio ⭐", "Quejas (≤3 ⭐)", "% Quejas", "Respuestas"]
            suc_resumen["Promedio ⭐"] = suc_resumen["Promedio ⭐"].round(2)
            
            st.dataframe(suc_resumen, use_container_width=True, hide_index=True)
            
            col_sbar1, col_sbar2 = st.columns([6, 4])
            with col_sbar1:
                fig_suc = px.histogram(
                    df_suc_periodo,
                    x="sucursal",
                    color="estrellas",
                    barmode="group",
                    labels={"sucursal": "Sucursal", "count": "Cantidad", "estrellas": "Estrellas"},
                    color_discrete_map={1: "#0072B2", 2: "#E69F00", 3: "#94A3B8", 4: "#56B4E9", 5: "#009E73"},
                    title=f"Calificaciones por Sucursal ({rango_anios[0]} - {rango_anios[1]})"
                )
                fig_suc.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_suc, use_container_width=True)
                
            with col_sbar2:
                st.markdown(f"""
                <div class="callout-box" style="margin-top: 2rem;">
                    <b>Comportamiento en el período ({rango_anios[0]} - {rango_anios[1]}):</b><br><br>
                    • Se registraron <b>{len(df_suc_periodo)} reseñas</b> distribuidas en las sedes comerciales.<br>
                    • Permite evaluar si las iniciativas o problemas de atención se concentraron en una sucursal específica a lo largo del tiempo.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No se registran datos para las sucursales en el rango de años seleccionado.")

    with tab_temporal:
        st.subheader("Evolución Temporal de Opiniones por Año")
        anios_df = df_filtrado.groupby(["anio_estimado", "estrellas"]).size().reset_index(name="cantidad")
        anios_df["estrellas_str"] = anios_df["estrellas"].apply(lambda s: f"{s} Estrella{'s' if s > 1 else ''}")
        
        fig_evol = px.bar(
            anios_df,
            x="anio_estimado",
            y="cantidad",
            color="estrellas_str",
            labels={"anio_estimado": "Año", "cantidad": "Cantidad de Reseñas", "estrellas_str": "Calificación"},
            color_discrete_map={
                "1 Estrella": "#0072B2", "2 Estrellas": "#E69F00", "3 Estrellas": "#94A3B8",
                "4 Estrellas": "#56B4E9", "5 Estrellas": "#009E73"
            },
            barmode="stack"
        )
        fig_evol.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            height=380,
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_evol, use_container_width=True)


# ==============================================================================
# 3. MAPEO DE PROCESOS AS-IS
# ==============================================================================
elif menu == "3. Mapeo de Procesos AS-IS":
    st.markdown('<div class="main-header">Mapeo de Procesos AS-IS y Cuellos de Botella</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Relevamiento paso a paso de los circuitos operativos clave y su correlación con la evidencia empírica</div>', unsafe_allow_html=True)

    tab_proc1, tab_proc2 = st.tabs([
        "a) Venta, Corte y Entrega de Placas",
        "b) Gestión de Stock e Inventario"
    ])

    with tab_proc1:
        st.subheader("Circuito AS-IS: Proceso de Venta, Corte y Entrega de Placas")
        st.markdown("""
        Este proceso comprende desde el ingreso del cliente (presencial o remoto) hasta el retiro o flete del pedido fraccionado.
        """)

        col_p1, col_p2 = st.columns([6, 4])
        with col_p1:
            st.markdown("""
            <div class="process-card">
                <h4>Paso 1: Asesoramiento y Cotización en Mostrador</h4>
                <p><b>Entradas:</b> Solicitud del cliente, medidas preliminares o croquis en papel.<br>
                <b>Procesamiento:</b> El vendedor transcribe las medidas manualmente o en un software local. Si el cliente no es experto, el tiempo de asesoramiento se extiende.<br>
                <b>Salida:</b> Hoja de presupuesto impresa o cotización verbal.<br>
                <small style="color: #475569;">📌 <i>Hipótesis operativa:</i> El vendedor atiende llamadas telefónicas y mostrador en simultáneo, generando demoras en piso.</small></p>
            </div>
            
            <div class="process-card">
                <h4>Paso 2: Facturación y Cobro en Caja</h4>
                <p><b>Entradas:</b> Presupuesto en mano y medio de pago.<br>
                <b>Procesamiento:</b> El cliente hace una segunda fila obligatoria para abonar. La cajera vuelve a cargar los datos en el sistema POS.<br>
                <b>Salida:</b> Factura y remito de corte físico en 2 copias.<br>
                <small style="color: #0072B2;">📊 <i>Evidencia de campo:</i> El 56% de las quejas se concentran en la fricción de atención y lentitud en caja/mostrador.</small></p>
            </div>

            <div class="process-card">
                <h4>Paso 3: Taller de Corte y Optimización</h4>
                <p><b>Entradas:</b> Remito impreso derivado al taller.<br>
                <b>Procesamiento:</b> El operario carga el esquema en el optimizador computarizado. Si hay cola de trabajo acumulada, el plazo de entrega se estira de 2 a 3 semanas.<br>
                <b>Salida:</b> Placas cortadas, rotuladas y embaladas.</p>
            </div>

            <div class="process-card">
                <h4>Paso 4: Entrega o Flete</h4>
                <p><b>Entradas:</b> Comprobante de pago presentado en depósito.<br>
                <b>Procesamiento:</b> Tercera fila para control de mercadería y carga en vehículo particular o coordinación manual de flete.<br>
                <b>Salida:</b> Mercadería retirada y firma de conformidad.</p>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            st.markdown("""
            <div style="background-color: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 1.2rem;">
                <h4 style="color: #991B1B; margin-top: 0;">⚠️ Cuellos de Botella y Fricciones Detectadas</h4>
                <ul style="color: #7F1D1D; font-size: 0.9rem; padding-left: 1.2rem;">
                    <li><b>Triple Fila Obligatoria:</b> Venta &rarr; Caja &rarr; Depósito/Corte (genera el 17.3% de quejas por demoras).</li>
                    <li><b>Desconexión de Canales:</b> Teléfono y WhatsApp no cuentan con catálogo en tiempo real ni turnero.</li>
                    <li><b>Horarios rígidos de corte:</b> Rechazo de pedidos cerca del horario de cierre de taller.</li>
                    <li><b>Falta de autogestión web:</b> El carpintero no puede cargar su despiece desde su taller.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Testimonios del Proceso:**")
            st.markdown("""
            <div class="quote-box">
                "Fui a pedir un presupuesto... la señora me atendió bastante mal, se ponía a responder mensajes del celular... me mandó a la parte de atrás a ver los modelos y que saque conclusiones... y después de todo te dicen entrega en 2 a 3 semanas." — <b>Sergio M.</b>
            </div>
            """, unsafe_allow_html=True)

    with tab_proc2:
        st.subheader("Circuito AS-IS: Proceso de Gestión de Stock e Inventario")
        st.markdown("""
        Este proceso abarca la reposición, almacenamiento, control de inventario y disponibilidad comercial de materiales.
        """)

        col_s1, col_s2 = st.columns([6, 4])
        with col_s1:
            st.markdown("""
            <div class="process-card">
                <h4>Paso 1: Consulta de Disponibilidad Comercial</h4>
                <p><b>Entradas:</b> Consulta de cliente en mostrador o WhatsApp.<br>
                <b>Procesamiento:</b> El vendedor consulta una planilla o sistema local que no descuenta stock en tiempo real ni reserva placas en proceso de corte.<br>
                <b>Salida:</b> Confirmación de stock al cliente.</p>
            </div>

            <div class="process-card">
                <h4>Paso 2: Detección de Quiebre de Stock Físico</h4>
                <p><b>Entradas:</b> Remito emitido enviado a depósito.<br>
                <b>Procesamiento:</b> El operario de depósito advierte que la placa solicitada se agotó o está dañada, obligando a anular la venta o reemplazar el material.<br>
                <b>Salida:</b> Fricción comercial, devoluciones o retrasos.<br>
                <small style="color: #0072B2;">📊 <i>Evidencia de campo:</i> Clientes reportan confirmar stock por WhatsApp y al llegar al local no está disponible.</small></p>
            </div>

            <div class="process-card">
                <h4>Paso 3: Reabastecimiento a Proveedores</h4>
                <p><b>Entradas:</b> Conteo visual periódico o reclamo de faltante.<br>
                <b>Procesamiento:</b> Emisión manual de órdenes de compra a fabricantes líderes.<br>
                <b>Salida:</b> Recepción de camión y estiba en depósito.<br>
                <small style="color: #475569;">📌 <i>Hipótesis operativa:</i> No existe punto de pedido automático (ROP / EOQ) integrado al sistema de facturación.</small></p>
            </div>
            """, unsafe_allow_html=True)

        with col_s2:
            st.markdown("""
            <div style="background-color: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 1.2rem;">
                <h4 style="color: #991B1B; margin-top: 0;">⚠️ Ineficiencias de Inventario Detectadas</h4>
                <ul style="color: #7F1D1D; font-size: 0.9rem; padding-left: 1.2rem;">
                    <li><b>Asimetría de Información:</b> Desalineación entre lo que el vendedor ve en pantalla y las placas físicamente aptas en depósito.</li>
                    <li><b>Falta de Reserva Automática:</b> Las placas asignadas a un pedido de corte no se bloquean de inmediato, generando sobreventa.</li>
                    <li><b>Gestión Reactiva de Compras:</b> Reposición basada en urgencias en lugar de pronósticos de demanda impulsados por datos (BI).</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# 4. MATRIZ FODA ESTRATÉGICA
# ==============================================================================
elif menu == "4. Matriz FODA Estratégica":
    st.markdown('<div class="main-header">Matriz FODA Cruzada con Enfoque Tecnológico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Cruce estratégico validado con evidencia empírica de minería de opiniones (Google Maps)</div>', unsafe_allow_html=True)

    tab_foda, tab_cruces, tab_gap = st.tabs([
        "Matriz Cuadrante FODA",
        "Cruces Estratégicos (FO, DO, FA, DA)",
        "Diagnóstico de Brecha (Discurso vs. Realidad)"
    ])

    with tab_foda:
        c_izq, c_der = st.columns(2)
        with c_izq:
            st.markdown("""
            <div class="foda-card foda-f">
                <h4 style="color: #009E73; margin-top:0;">🛡️ FORTALEZAS (Internas)</h4>
                <ul>
                    <li><b>Taller Computarizado:</b> Maquinaria industrial de corte y pegado de cantos con optimizador digital de placas.</li>
                    <li><b>Trayectoria y Respaldo (+60 años):</b> Alianzas comerciales sólidas con fabricantes líderes de placas y perfiles de construcción en seco.</li>
                    <li><b>Variedad de Catálogo y Escala:</b> Capacidad de abastecer grandes obras y distribución mayorista en la región.</li>
                    <li><b>Desarrollo de Marca Propia:</b> Línea de productos <i>Area Base</i> para control de calidad y margen.</li>
                </ul>
            </div>

            <div class="foda-card foda-d">
                <h4 style="color: #D55E00; margin-top:0;">⚠️ DEBILIDADES (Internas)</h4>
                <ul>
                    <li><b>Circuito de Compra Fragmentado:</b> Triple fila obligatoria (Venta &rarr; Caja &rarr; Despacho) sin terminales mPOS ni turnero digital.</li>
                    <li><b>Canales Remotos Saturados:</b> WhatsApp y teléfono atendidos por personal de piso sin CRM ni chatbot de derivación.</li>
                    <li><b>Inexistencia de Portal Web de Autogestión:</b> El cliente profesional no puede despiezar, cotizar ni reservar turnos online.</li>
                    <li><b>Sistemas Desintegrados:</b> Desconexión entre stock de salón, taller de corte y facturación.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with c_der:
            st.markdown("""
            <div class="foda-card foda-o">
                <h4 style="color: #0072B2; margin-top:0;">🚀 OPORTUNIDADES (Externas)</h4>
                <ul>
                    <li><b>Portal Web B2B de Despiece 24/7:</b> Habilitar cotizador y optimizador online para carpinteros y profesionales.</li>
                    <li><b>CRM Conversacional y Automatización:</b> Respuestas instantáneas en WhatsApp para stock, horarios y seguimiento de pedidos.</li>
                    <li><b>Integración ERP End-to-End:</b> Trazabilidad de inventario en tiempo real entre salón, depósito y taller.</li>
                    <li><b>Reingeniería 'Smart Retail':</b> Turnero digital por QR y cobro unificado en punto de venta.</li>
                </ul>
            </div>

            <div class="foda-card foda-a">
                <h4 style="color: #E69F00; margin-top:0;">⚡ AMENAZAS (Externas)</h4>
                <ul>
                    <li><b>Competencia Nativa Digital:</b> Grandes superficies (Easy, Sodimac) y madereras con cotizadores web y checkout ágil.</li>
                    <li><b>Nuevas Generaciones de Clientes:</b> Profesionales y público DIY que exigen atención 100% digital e inmediata.</li>
                    <li><b>Deterioro de Reputación Online:</b> Impacto negativo de reseñas visibles en Google Maps sin gestión de respuesta sistemática.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with tab_cruces:
        st.subheader("Matriz de Cruces Estratégicos")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("""
            #### 🌟 Estrategias FO (Apalancamiento)
            * **Plataforma Web de Despiece 24/7:** Conectar el optimizador de cortes interno a una interfaz web para que carpinteros carguen planos y reserven turnos.
            * **Portal B2B de Construcción en Seco:** Aprovechar el liderazgo de catálogo para ofrecer a constructoras abastecimiento con seguimiento de entregas.
            
            #### 🛡️ Estrategias FA (Blindaje)
            * **Compatibilidad CAD/CAM:** Integración de software de diseño con el sistema de pedidos para crear barreras de salida frente a grandes cadenas.
            * **Garantía Digital de Calidad:** Certificación de tolerancias mínimas de corte y plazos garantizados para blindarse de competidores informales.
            """)
        with col_c2:
            st.markdown("""
            #### 🔄 Estrategias DO (Reingeniería Digital)
            * **CRM Omnicanal en WhatsApp:** Desacoplar la atención telefónica/WhatsApp de los vendedores de piso mediante chatbots y agentes dedicados.
            * **Reingeniería de Salón (Turnero + mPOS):** Eliminar la triple fila implementando turneros por código QR y cobro en mostrador.
            
            #### 🚨 Estrategias DA (Mitigación de Riesgos)
            * **Rediseño de Puestos y Descompresión Operativa:** Liberar a cajeras y vendedores de tareas manuales repetitivas para reducir el 56% de quejas por atención.
            * **Protocolo de Reputación Online:** Gestionar activamente las opiniones en Google Maps y capturar satisfacción en caja (CSAT/NPS).
            """)

    with tab_gap:
        st.subheader("Contraste: Discurso Institucional vs. Procesos Reales")
        gap_table = [
            {"Dimensión": "1. Circuito de Atención", "Declaración": "Búsqueda de la excelencia y máxima satisfacción.", "Realidad Operativa": "3 filas obligatorias, demoras y personal saturado.", "Impacto": "56% quejas de atención + 17% de demoras."},
            {"Dimensión": "2. Canales Remotos", "Declaración": "Asesoramiento y sinergia fluida con el cliente.", "Realidad Operativa": "Teléfonos que no atienden y WhatsApp sin CRM.", "Impacto": "8.7% quejas por incomunicación y llamadas cortadas."},
            {"Dimensión": "3. Taller y Cortes", "Declaración": "Sistema computarizado de optimización de vanguardia.", "Realidad Operativa": "Optimizador de uso interno cerrado a clientes.", "Impacto": "Demoras de 2 a 3 semanas y restricciones de horarios."},
            {"Dimensión": "4. Control de Stock", "Declaración": "Garantizar procesos confiables y seguros.", "Realidad Operativa": "Planillas desintegradas sin descuento en tiempo real.", "Impacto": "Quiebres de stock no avisados al cliente."},
            {"Dimensión": "5. Reputación Digital", "Declaración": "Calidad total y mejora continua permanente.", "Realidad Operativa": "68.3% de reseñas negativas sin respuesta.", "Impacto": "Erosión de imagen en Google Maps."}
        ]
        st.dataframe(pd.DataFrame(gap_table), use_container_width=True, hide_index=True)


# ==============================================================================
# 5. EXPLORADOR DE RESEÑAS
# ==============================================================================
elif menu == "5. Explorador de Reseñas (Voz del Cliente)":
    st.markdown('<div class="main-header">Explorador Interactivo de Reseñas</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Mostrando <b>{len(df_filtrado)}</b> reseñas filtradas ({rango_anios[0]} - {rango_anios[1]})</div>', unsafe_allow_html=True)

    busqueda = st.text_input("🔍 Buscar por palabras clave, autor o texto de respuesta:", "")

    df_display = df_filtrado.copy()
    if busqueda:
        mask = (
            df_display["texto"].fillna("").str.contains(busqueda, case=False, regex=False) |
            df_display["autor"].fillna("").str.contains(busqueda, case=False, regex=False) |
            df_display["respuesta_dueno"].fillna("").str.contains(busqueda, case=False, regex=False)
        )
        df_display = df_display[mask]
        st.caption(f"Coincidencias encontradas: {len(df_display)}")

    for idx, row in df_display.iterrows():
        stars_str = f"[{int(row['estrellas'])} ⭐]"
        suc_badge = f"`{row['sucursal']}`" if "sucursal" in row and pd.notna(row["sucursal"]) else ""
        cat_badge = f"`{row['categoria_principal']}`" if pd.notna(row.get("categoria_principal")) else "`Sin categoría`"
        year_badge = f"Año: {row['anio_estimado']}"
        
        with st.expander(f"{stars_str} {suc_badge} | **{row['autor']}** — {year_badge} — {cat_badge}", expanded=False):
            if pd.notna(row['texto']) and row['texto'].strip():
                st.markdown(f"**Opinión:** {row['texto']}")
            else:
                st.markdown("*El usuario dejó solo calificación sin texto.*")
                
            if pd.notna(row['respuesta_dueno']) and row['respuesta_dueno'].strip():
                st.markdown(f"""
                <div style="background-color: #F0FDF4; border-left: 4px solid #009E73; padding: 0.6rem 1rem; border-radius: 4px; margin-top: 0.5rem;">
                    <b>Respuesta oficial del comercio:</b><br>{row['respuesta_dueno']}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=df_display.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
        file_name=f"resenas_filtradas_{rango_anios[0]}_{rango_anios[1]}.csv",
        mime="text/csv"
    )


# ==============================================================================
# 6. HOJA DE RUTA & SUPUESTOS BASE
# ==============================================================================
elif menu == "6. Hoja de Ruta & Supuestos Base":
    st.markdown('<div class="main-header">Hoja de Ruta de Transformación Digital y Supuestos Base</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Recomendaciones estratégicas y registro de supuestos para garantizar consistencia en las Entregas 2 (ERP), 3 (CRM) y 4 (BI)</div>', unsafe_allow_html=True)

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        st.subheader("🎯 Hoja de Ruta de Iniciativas Tecnológicas")
        st.markdown("""
        1. **Fase 1 (Corto Plazo - CX Inmediato):**
           - Implementar **CRM Conversacional en WhatsApp** con chatbot de FAQs y derivación inteligente.
           - Protocolo de gestión de reputación online (respuesta en < 48hs en Google Maps).
           - Medición de satisfacción en caja vía QR / terminal táctil.
        
        2. **Fase 2 (Mediano Plazo - Reingeniería de Salón y ERP):**
           - Implementación de **ERP Integrado** para sincronizar mostrador, caja, depósito y cola de taller.
           - Reingeniería del circuito de tienda: **Turnero digital por QR** y cobro integrado en puesto de venta (eliminación de la triple fila).
        
        3. **Fase 3 (Largo Plazo - Ecosistema Digital B2B / BI):**
           - Lanzamiento de **Portal Web de Despiece y Cotización Online 24/7** para carpinteros y arquitectos.
           - Tableros de **Inteligencia de Negocios (BI)** para pronósticos de demanda y optimización de compras.
        """)

    with col_h2:
        st.subheader("📌 Hipótesis y Supuestos Base Consolidados")
        st.markdown("""
        Los siguientes supuestos operativos fundamentados regirán las siguientes fases del proyecto de consultoría (ERP, CRM y BI):
        
        * **[SB-01] Estructura Organizacional:** Asumimos una dotación de ~30 empleados (8 ventas/asesoramiento, 4 administración/cajas, 12 operarios de depósito/taller, 4 choferes y 2 directivos/gerencia), debido a la escala comercial y volumen de sucursales.
        * **[SB-02] Software Transaccional Actual:** Asumimos que opera con un software POS / facturación contable tradicional no basado en la nube, con bases de datos locales no integradas.
        * **[SB-03] Gestión de Stock:** Asumimos el uso de planillas Excel complementarias y conteos físicos periódicos, sin módulo de reaprovisionamiento automático (ROP/EOQ).
        * **[SB-04] Atención Remota:** Asumimos que WhatsApp Web y las líneas telefónicas son atendidas por los mismos vendedores de mostrador sin asignación de turnos ni tickets.
        * **[SB-05] Software de Taller:** Asumimos que cuentan con software optimizador de cortes de placa monousuario en PC de taller, sin conexión API con la web de la empresa.
        """)

