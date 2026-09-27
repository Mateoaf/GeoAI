"""Script para reparar y limpiar el notebook 03_variables_geologia_estructuras.ipynb.

Corrige:
1. Rutas absolutas de Windows con barras invertidas ("C:\\Users\\...") que causan
   'Parse error: Got unexpected unicode' por el escape '\\U' de Python.
2. Caracteres corruptos o con signos de interrogación en el texto en español (markdown).
3. Asegura codificación UTF-8 limpia sin caracteres invisibles o de control.
"""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "notebooks" / "03_variables_geologia_estructuras.ipynb"


def fix_notebook():
    print(f"Cargando {NB_PATH}...")
    with open(NB_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # 1. Corregir Cell 0 (Markdown con '?' por problemas de codificación previa)
    cell_0_fixed = [
        "# 03 · Geología y estructuras — fase D revisada\n",
        "\n",
        "`ensure_run` continúa una ejecución compatible. Si cambian código o configuración, "
        "crea otra y recupera únicamente bloques con funciones de cálculo, parámetros y fuentes "
        "equivalentes y hashes válidos. Se exporta `reuse_audit.json`. No ejecutar dos inicios "
        "ni mezclar rutas manualmente.\n",
        "\n",
        "Se conservan las unidades mixtas; las asociaciones explícitas se añaden al integrar en 06. "
        "Las densidades siguen siendo aproximaciones circulares sobre longitud por celda, "
        "con cobertura de levantamiento no acreditada.",
    ]
    nb["cells"][0]["source"] = cell_0_fixed

    # 2. Corregir Cell 2 (Markdown)
    cell_2_fixed = [
        "## Unidades y edades\n",
        "Intersecciones exactas con la parte terrestre de cada celda. Se disuelve por categoría; "
        "los solapes entre categorías y atributos ausentes se auditan. "
        "Revisar `dictionaries/litologia.csv` y `edades.csv`.",
    ]
    nb["cells"][2]["source"] = cell_2_fixed

    # 3. Limpiar Cell 4 (Código obsoleto comentado con rutas C:\\Users que provocan SyntaxError/UnicodeError)
    cell_4_fixed = [
        "# Inspección alternativa con pyarrow (opcional):\n",
        "# import pyarrow.parquet as pq\n",
        "# table = pq.read_table(RUN / 'blocks' / 'geology_quality.parquet')\n",
        "# df = table.to_pandas()\n",
        "# display(df.head())\n",
    ]
    nb["cells"][4]["source"] = cell_4_fixed

    # 4. Asegurar Cell 5 (Inspección limpia con pd.read_parquet)
    cell_5_fixed = [
        "# Para inspeccionar calidad del bloque geología (recién generado):\n",
        "df = pd.read_parquet(RUN / 'blocks' / 'geology_quality.parquet')\n",
        "display(df.columns)\n",
        "# Nota: structural_quality.parquet se genera tras ejecutar la siguiente celda (fd.lines)\n",
    ]
    nb["cells"][5]["source"] = cell_5_fixed

    # 5. Asegurar Cell 8 (Mensaje de cierre con acento limpio)
    cell_8_fixed = [
        "display(pd.read_csv(RUN / 'dictionaries/estructuras.csv'))\n",
        "print('Continuar con 04 usando esta ejecución:', RUN)\n",
    ]
    nb["cells"][8]["source"] = cell_8_fixed

    # Guardar en UTF-8 limpio
    with open(NB_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print("Notebook 03 reparado y guardado correctamente en UTF-8.")


if __name__ == "__main__":
    fix_notebook()
