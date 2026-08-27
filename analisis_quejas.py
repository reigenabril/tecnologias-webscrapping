#!/usr/bin/env python3
"""
Analisis y Categorizacion de Motivos de Queja
Materia: Tecnologias para la Gestion
"""

import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_INPUT = os.path.join(BASE_DIR, "resenas_emporio_terciado_3_o_menos.csv")
CSV_OUTPUT = os.path.join(BASE_DIR, "resenas_categorizadas.csv")
IMG_OUTPUT = os.path.join(BASE_DIR, "grafico_top_quejas.png")

CATEGORIAS = {
    "Atención y Trato del Personal": [
        r"\batenci[oó]n\b", r"\btrato\b", r"\bcajera\b", r"\bcaja\b", r"\bcajero\b",
        r"\bemplead[oa]s?\b", r"\bvendedor(es)?\b", r"\bmala\s+gana\b", r"\bmal\s+educad[oa]s?\b",
        r"\bdestrato\b", r"\bsoberbi[ao]\b", r"\bdesidia\b", r"\bdesagradable\b",
        r"\batender\b", r"\batienden\b", r"\batendi[oó]\b", r"\batendieron\b",
        r"\bp[eé]sima\b", r"\bordinari[ao]\b", r"\bgana\b", r"\bactitud\b"
    ],
    "Canales de Contacto (Teléfono / WhatsApp)": [
        r"\btel[eé]fono\b", r"\btelef[oó]nic[ao]\b", r"\btel\b", r"\bwhats?app\b", r"\bwsp\b",
        r"\bllamar\b", r"\bllamada\b", r"\bllamo\b", r"\bllam[eé]\b", r"\bcortan\b",
        r"\bcortar\b", r"\bcortaron\b", r"\bno\s+contestan\b", r"\bno\s+atienden\b",
        r"\bmensaje\b", r"\bmensajes\b", r"\bl[ií]nea\b", r"\bcomunicar\b", r"\bcontestador\b"
    ],
    "Tiempos de Espera y Demoras": [
        r"\bespera\b", r"\besperar\b", r"\besperando\b", r"\besper[eé]\b", r"\btardan\b",
        r"\btardaron\b", r"\btard[oó]\b", r"\bdemora\b", r"\bdemoran\b", r"\bdemoras\b",
        r"\bcola\b", r"\bfilas?\b", r"\bhoras?\b", r"\bminutos?\b", r"\blent[oa]s?\b",
        r"\blentitud\b", r"\beterno\b", r"\btiempo\b"
    ],
    "Precios y Presupuestos": [
        r"\bprecios?\b", r"\bcar[oa]s?\b", r"\bcar[ií]sim[oa]s?\b", r"\bpresupuestos?\b",
        r"\bcobran\b", r"\bcobrar\b", r"\bcobraron\b", r"\bplata\b", r"\bcompetencia\b",
        r"\bpesos\b", r"\bsobreprecio\b", r"\bfactura\b", r"\bcara\b"
    ],
    "Stock y Disponibilidad": [
        r"\bstock\b", r"\bno\s+tienen\b", r"\bno\s+hay\b", r"\bfalta\b", r"\bfaltante\b",
        r"\bcat[aá]logo\b", r"\bmercader[ií]a\b", r"\bmercanc[ií]a\b", r"\bdisponib(le|ilidad)\b"
    ],
    "Servicio de Cortes y Taller": [
        r"\bcortes?\b", r"\bcortan\b", r"\bcortar\b", r"\bplacas?\b", r"\bmedidas?\b",
        r"\btaller\b", r"\bhorario\s+de\s+corte\b", r"\bterciado\b", r"\bmelamina\b", r"\bmaderas?\b"
    ],
    "Calidad, Entregas y Flete": [
        r"\benv[ií]os?\b", r"\bflete\b", r"\bentrega(ron)?\b", r"\broto\b", r"\brota\b",
        r"\bcalidad\b", r"\bdefectuos[oa]\b", r"\bda[ñn]ad[oa]\b", r"\broturas?\b", r"\brayad[oa]\b"
    ]
}


def parse_year(fecha_str: str, current_year: int = 2026) -> int:
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


def categorizar_texto(texto: str):
    if not isinstance(texto, str) or not texto.strip():
        return [], "Solo Calificacion (Sin Comentario)"
        
    texto_norm = texto.lower()
    scores = {}
    
    for cat, regexes in CATEGORIAS.items():
        count = 0
        for r in regexes:
            if re.search(r, texto_norm):
                count += 1
        if count > 0:
            scores[cat] = count
            
    if not scores:
        return ["Otras Quejas Generales"], "Otras Quejas Generales"
        
    categoria_principal = max(scores, key=scores.get)
    return list(scores.keys()), categoria_principal


def main():
    print("=" * 70)
    print("  ANALISIS DE MOTIVOS DE QUEJA")
    print("=" * 70)
    
    df = pd.read_csv(CSV_INPUT)
    print(f"[*] Total de resenas cargadas: {len(df)}")
    
    categorias_activas = []
    categorias_principales = []
    
    for _, row in df.iterrows():
        cats, main_cat = categorizar_texto(row["texto"])
        categorias_activas.append(cats)
        categorias_principales.append(main_cat)
        
    df["categorias"] = [", ".join(c) for c in categorias_activas]
    df["categoria_principal"] = categorias_principales
    df["anio_estimado"] = df["fecha"].apply(parse_year)
    
    for cat in CATEGORIAS.keys():
        df[f"cat_{cat}"] = df["texto"].fillna("").apply(
            lambda t: any(re.search(r, t.lower()) for r in CATEGORIAS[cat])
        )
        
    df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"[+] Dataset categorizado exportado a: {CSV_OUTPUT}")
    
    df_texto = df[df["texto"].notna() & (df["texto"].str.strip() != "")]
    total_con_texto = len(df_texto)
    
    cat_counts = df_texto["categoria_principal"].value_counts()
    
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6))
    
    # Paleta Okabe-Ito de alto contraste
    colors = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#718096"]
    
    y_data = cat_counts.index
    x_data = cat_counts.values
    
    bars = ax.barh(y_data, x_data, color=colors[:len(y_data)], edgecolor="none", height=0.65)
    ax.invert_yaxis()
    
    for bar in bars:
        width = bar.get_width()
        pct = (width / total_con_texto) * 100
        ax.text(
            width + 1.2,
            bar.get_y() + bar.get_height() / 2,
            f"{int(width)} ({pct:.1f}%)",
            va="center",
            ha="left",
            fontsize=11,
            fontweight="bold",
            color="#333333"
        )
        
    ax.set_title("Distribucion de Puntos de Dolor en Resenas Negativas (1 a 3 Estrellas)", fontsize=13, fontweight="bold", pad=20)
    ax.set_xlabel("Cantidad de Resenas", fontsize=11, labelpad=10)
    ax.set_xlim(0, max(x_data) + 12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(IMG_OUTPUT, dpi=300)
    plt.close()
    
    print(f"[+] Grafico guardado en: {IMG_OUTPUT}")


if __name__ == "__main__":
    main()
