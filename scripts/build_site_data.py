#!/usr/bin/env python3
"""
Genera el JSON que consume el sitio estatico (docs/data/resenas.json)
a partir de data/resenas_categorizadas.csv.

Uso:
    python3 scripts/build_site_data.py

El CSV sigue siendo la fuente de verdad. Si cambia el CSV, volver a correr
este script y commitear el JSON actualizado.
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_INPUT = ROOT / "data" / "resenas_categorizadas.csv"
JSON_OUTPUT = ROOT / "docs" / "data" / "resenas.json"

REQUIRED_COLUMNS = [
    "id_resena",
    "sucursal",
    "autor",
    "estrellas",
    "fecha",
    "texto",
    "respuesta_dueno",
    "categorias",
    "categoria_principal",
    "anio_estimado",
]

INT_COLUMNS = {"estrellas", "anio_estimado"}


def clean_value(column: str, value):
    """Convierte valores de pandas a tipos JSON estables."""
    if pd.isna(value):
        return None
    if column.startswith("cat_"):
        return bool(value)
    if column in INT_COLUMNS:
        return int(value)
    return str(value)


def main() -> int:
    if not CSV_INPUT.exists():
        print(f"ERROR: no existe {CSV_INPUT}", file=sys.stderr)
        return 1

    df = pd.read_csv(CSV_INPUT, encoding="utf-8-sig")
    columns = list(df.columns)

    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        print(f"ERROR: faltan columnas requeridas: {missing}", file=sys.stderr)
        return 1

    if len(columns) != 17:
        print(
            f"ERROR: se esperaban 17 columnas y hay {len(columns)}",
            file=sys.stderr,
        )
        return 1

    rows = [
        {col: clean_value(col, row[col]) for col in columns}
        for row in df.to_dict(orient="records")
    ]

    payload = {
        "meta": {
            "count": len(rows),
            "source": "data/resenas_categorizadas.csv",
        },
        "columns": columns,
        "rows": rows,
    }

    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    pos = sum(1 for r in rows if r["estrellas"] >= 4)
    neg = sum(1 for r in rows if r["estrellas"] <= 3)
    con_texto = sum(1 for r in rows if r["texto"] not in (None, ""))
    con_respuesta = sum(
        1 for r in rows if r["respuesta_dueno"] not in (None, "")
    )

    print(
        f"OK -> {JSON_OUTPUT.relative_to(ROOT)} | "
        f"total={len(rows)} pos={pos} neg={neg} "
        f"con_texto={con_texto} con_respuesta={con_respuesta}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
