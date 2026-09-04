#!/usr/bin/env python3
"""
Scraper de Reseñas de Google Maps para "El Emporio del Terciado S.A."
Extrae el 100% de las reseñas (1 a 5 estrellas) utilizando Playwright con Google Chrome.
"""

import os
import re
import csv
import time
import argparse
import subprocess
from typing import Dict, List
from playwright.sync_api import sync_playwright

MAPS_URL = "https://www.google.com/maps/place/El+Emporio+del+Terciado+S.A./@-34.9105382,-57.9682882,17z/data=!4m8!3m7!1s0x95a2e7b4461a4efb:0x7afddf40c8abb97a!8m2!3d-34.9105382!4d-57.9657079!9m1!1b1!16s%2Fg%2F1tm2bvyw?hl=es"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT_CSV = os.path.join(PROJECT_ROOT, "data", "raw", "resenas_emporio_terciado_todas.csv")
PROFILE_DIR = os.path.expanduser("~/.gmaps_chrome_session")


def extract_stars(aria_text: str) -> int:
    if not aria_text:
        return 0
    m = re.search(r"(\d+)", aria_text)
    return int(m.group(1)) if m else 0


def expand_all_more(page):
    """Expande todos los botones 'Más' en las reseñas visibles."""
    for btn in page.query_selector_all("button.w8nwRe, button[aria-label='Ver más'], button[aria-label='Más']"):
        try:
            if btn.is_visible():
                btn.click(timeout=200)
        except Exception:
            pass


def extract_cards_from_dom(
    page,
    extracted_dict: Dict[str, Dict[str, str]],
    fallback_star: int = 0,
    min_stars: int = 1,
    max_stars: int = 5
):
    """Extrae las tarjetas del DOM actual y las agrega al diccionario deduplicado."""
    expand_all_more(page)
    cards = page.query_selector_all("div.jftiEf, div[data-review-id]")
    for card in cards:
        review_id = card.get_attribute("data-review-id") or ""
        
        # Autor
        auth_el = card.query_selector("div.d4r55") or card.query_selector(".TSUbDb")
        author = auth_el.inner_text().strip() if auth_el else "Anónimo"
        
        # Calificación
        rating_el = card.query_selector("span.kvMYJc") or card.query_selector("span[aria-label*='estrella' i]")
        rating_aria = rating_el.get_attribute("aria-label") if rating_el else ""
        stars = extract_stars(rating_aria)
        if stars == 0 and fallback_star > 0:
            stars = fallback_star
            
        # Fecha
        date_el = card.query_selector("span.rsqaWe")
        date_text = date_el.inner_text().strip() if date_el else ""
        
        # Texto
        text_el = card.query_selector("span.wiI7pd")
        review_text = text_el.inner_text().strip() if text_el else ""
        
        # Respuesta del dueño
        resp_el = card.query_selector("div.CDe7pd")
        resp_text = ""
        if resp_el:
            resp_body = resp_el.query_selector("div.wiI7pd") or resp_el
            resp_text = resp_body.inner_text().strip()
            
        key = review_id if review_id else f"{author}_{date_text}_{stars}"
        
        if key not in extracted_dict and min_stars <= stars <= max_stars:
            extracted_dict[key] = {
                "id_resena": key,
                "autor": author,
                "estrellas": str(stars),
                "fecha": date_text,
                "texto": review_text,
                "respuesta_dueno": resp_text
            }


def scroll_current_view(page, max_scrolls: int = 50):
    """Scrollea el contenedor de reseñas."""
    prev_cnt = 0
    stagnant = 0
    for s in range(1, max_scrolls + 1):
        expand_all_more(page)
        cards = page.locator("div.jftiEf, div[data-review-id]")
        cnt = cards.count()
        if cnt > 0:
            try:
                cards.last.scroll_into_view_if_needed(timeout=800)
            except Exception:
                pass
                
        page.evaluate("""
            const containers = Array.from(document.querySelectorAll('div.m6QErb'));
            for (const c of containers) {
                if (c.scrollHeight > c.clientHeight && c.querySelectorAll('div.jftiEf').length > 0) {
                    c.scrollTop = c.scrollHeight;
                }
            }
        """)
        page.wait_for_timeout(1500)
        
        if cnt == prev_cnt and cnt > 0:
            stagnant += 1
            if stagnant >= 4:
                break
        else:
            stagnant = 0
            prev_cnt = cnt


def select_sort_option(page, keyword: str) -> bool:
    """Abre el menú de ordenamiento y selecciona la opción deseada."""
    sort_btn = page.locator("button[aria-label='Ordenar reseñas'], button[aria-label='Ordenar opiniones']").first
    if sort_btn.is_visible():
        try:
            sort_btn.click()
            page.wait_for_timeout(1200)
            opt = page.locator(f"div[role='menuitemradio']:has-text('{keyword}'), div[role='menuitem']:has-text('{keyword}')").first
            if opt.is_visible():
                opt.click()
                page.wait_for_timeout(3000)
                return True
        except Exception as e:
            print(f"[!] Aviso al ordenar por '{keyword}': {e}")
    return False


def run_scraper(url: str = MAPS_URL, output_file: str = DEFAULT_OUTPUT_CSV, min_stars: int = 1, max_stars: int = 5):
    # Asegurar idioma español en Maps
    if "hl=es" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}hl=es"

    print("=" * 75)
    print("  SCRAPER DE RESEÑAS DE GOOGLE MAPS")
    print("=" * 75)
    print(f"[-] URL: {url}")
    print(f"[-] Rango de calificación: {min_stars} a {max_stars} estrella(s)")
    print(f"[-] Archivo de salida: {output_file}")
    print(f"[-] Perfil de navegador: {PROFILE_DIR}\n")
    
    os.makedirs(PROFILE_DIR, exist_ok=True)
    
    # Iniciar instancia de Chrome con puerto de depuración
    cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    proc = subprocess.Popen(cmd)
    time.sleep(3)
    
    all_reviews: Dict[str, Dict[str, str]] = {}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            
            print("[*] Cargando ubicación en Google Maps...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)
            
            # Pestaña Reseñas
            for tab in page.query_selector_all("button[role='tab']"):
                txt = tab.inner_text().strip()
                if "Reseñas" in txt or "Opiniones" in txt:
                    tab.click()
                    page.wait_for_timeout(3000)
                    break
                    
            # Paso 1: Ordenar por más recientes
            print("[+] Paso 1: Ordenando por 'Más recientes'...")
            select_sort_option(page, "más recientes")
            scroll_current_view(page, max_scrolls=70)
            extract_cards_from_dom(page, all_reviews, min_stars=min_stars, max_stars=max_stars)
            print(f"[+] Reseñas acumuladas tras Paso 1: {len(all_reviews)}")

            # Paso 2: Ordenar por valoración más alta
            print("[+] Paso 2: Ordenando por 'Valoración más alta'...")
            select_sort_option(page, "más alta")
            scroll_current_view(page, max_scrolls=70)
            extract_cards_from_dom(page, all_reviews, min_stars=min_stars, max_stars=max_stars)
            print(f"[+] Reseñas acumuladas tras Paso 2: {len(all_reviews)}")

            # Paso 3: Ordenar por valoración más baja
            print("[+] Paso 3: Ordenando por 'Valoración más baja'...")
            select_sort_option(page, "más baja")
            scroll_current_view(page, max_scrolls=70)
            extract_cards_from_dom(page, all_reviews, min_stars=min_stars, max_stars=max_stars)
            print(f"[+] Reseñas acumuladas tras Paso 3: {len(all_reviews)}")

            # Paso 4: Filtro por barras de histograma (1 a 5 estrellas)
            for star in range(min_stars, max_stars + 1):
                print(f"[+] Paso 4.{star}: Filtrando por {star} estrella(s)...")
                row = page.locator(f"tr[aria-label*='{star} estrellas'], tr[aria-label*='{star} estrella']").first
                if row.is_visible():
                    row.click()
                    page.wait_for_timeout(3000)
                    scroll_current_view(page, max_scrolls=50)
                    extract_cards_from_dom(page, all_reviews, fallback_star=star, min_stars=min_stars, max_stars=max_stars)
                    print(f"[+] Reseñas acumuladas tras filtro de {star} estrella(s): {len(all_reviews)}")
                    
            browser.close()
    finally:
        proc.terminate()
        
    filtered = [r for r in all_reviews.values() if min_stars <= int(r["estrellas"]) <= max_stars]
    filtered.sort(key=lambda x: (int(x["estrellas"]), x["fecha"]))
    
    fields = ["id_resena", "autor", "estrellas", "fecha", "texto", "respuesta_dueno"]
    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(filtered)
        
    print("\n" + "=" * 75)
    print(f" RESUMEN FINAL:")
    print(f" [+] Archivo CSV guardado en: {output_file}")
    print(f" [+] Total de reseñas extraídas ({min_stars} a {max_stars} estrellas): {len(filtered)}")
    
    dist = {}
    with_resp = 0
    with_txt = 0
    for r in filtered:
        s = r["estrellas"]
        dist[s] = dist.get(s, 0) + 1
        if r["respuesta_dueno"]:
            with_resp += 1
        if r["texto"]:
            with_txt += 1
            
    for s in range(min_stars, max_stars + 1):
        print(f" [+] {s} estrella(s): {dist.get(str(s), 0)}")
    print(f" [+] Reseñas con texto escrito: {with_txt}")
    print(f" [+] Reseñas con respuesta del comercio: {with_resp}")
    print("=" * 75)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de reseñas de Google Maps")
    parser.add_argument("--url", type=str, default=MAPS_URL, help="URL de la sucursal en Google Maps")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_CSV, help="Ruta del archivo CSV de salida")
    parser.add_argument("--min-stars", type=int, default=1, help="Calificación mínima a extraer (default: 1)")
    parser.add_argument("--max-stars", type=int, default=5, help="Calificación máxima a extraer (default: 5)")
    args = parser.parse_args()
    
    run_scraper(url=args.url, output_file=args.output, min_stars=args.min_stars, max_stars=args.max_stars)
