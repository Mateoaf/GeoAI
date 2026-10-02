"""
scripts/ejecutar_secciones_nuevas_notebooks.py
Ejecuta las celdas de código añadidas en los cuadernos 01, 08, 12, 13 y 17
y guarda las salidas renderizadas (HTML, texto y gráficos base64) dentro
de los archivos .ipynb para que se visualicen inmediatamente sin necesidad
de reejecutar todo el cuaderno.
"""

import sys
import io
from pathlib import Path
import nbformat
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import base64

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = ROOT / "notebooks"

def execute_and_capture(code: str, local_vars: dict) -> list:
    """Ejecuta un bloque de código y captura salidas para nbformat."""
    outputs = []
    
    # Custom display function
    def custom_display(obj):
        if isinstance(obj, pd.DataFrame):
            html = obj.to_html(classes="dataframe", border=1, justify="right")
            outputs.append(nbformat.v4.new_output(
                output_type="display_data",
                data={
                    "text/html": html,
                    "text/plain": repr(obj)
                }
            ))
        elif hasattr(obj, "_repr_html_"):
            outputs.append(nbformat.v4.new_output(
                output_type="display_data",
                data={
                    "text/html": obj._repr_html_(),
                    "text/plain": repr(obj)
                }
            ))
        else:
            outputs.append(nbformat.v4.new_output(
                output_type="display_data",
                data={"text/plain": repr(obj)}
            ))

    local_vars["display"] = custom_display

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(code, globals(), local_vars)
        stdout_text = sys.stdout.getvalue()
        if stdout_text:
            outputs.append(nbformat.v4.new_output(
                output_type="stream",
                name="stdout",
                text=stdout_text
            ))

        # Check if matplotlib has an open figure
        if plt.get_fignums():
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight", dpi=120)
            plt.close("all")
            buf.seek(0)
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            outputs.append(nbformat.v4.new_output(
                output_type="display_data",
                data={
                    "image/png": img_b64,
                    "text/plain": "<Figure size ...>"
                }
            ))
    except Exception as e:
        outputs.append(nbformat.v4.new_output(
            output_type="error",
            ename=type(e).__name__,
            evalue=str(e),
            traceback=[str(e)]
        ))
    finally:
        sys.stdout = old_stdout

    return outputs

def process_notebook(nb_name: str, marker: str):
    nb_path = NOTEBOOKS_DIR / nb_name
    print(f"Renderizando salidas en {nb_name}...")
    nb = nbformat.read(nb_path, as_version=4)

    found_marker = False
    for i, cell in enumerate(nb.cells):
        source_text = "".join(cell.source) if isinstance(cell.source, list) else cell.source
        if cell.cell_type == "markdown" and marker in source_text:
            found_marker = True
            continue
        
        if found_marker and cell.cell_type == "code":
            # Ejecutar esta celda de código
            code_str = "".join(cell.source) if isinstance(cell.source, list) else cell.source
            local_vars = {"ROOT": ROOT}
            outputs = execute_and_capture(code_str, local_vars)
            cell.outputs = outputs
            cell.execution_count = 1

    nbformat.write(nb, nb_path)
    print(f"  [OK] {nb_name} renderizado con éxito.")

if __name__ == "__main__":
    process_notebook("01_indicios_limpieza_etiquetas.ipynb", "Extensión Experimental")
    process_notebook("08_muestreo_presencia_fondo.ipynb", "Extensión Experimental")
    process_notebook("12_random_forest_espacial.ipynb", "Extensión Experimental")
    process_notebook("13_comparacion_modelos.ipynb", "Extensión Experimental")
    process_notebook("17_fase_h_mapa_interpretabilidad.ipynb", "Extensión Experimental")
    print("¡Todas las salidas renderizadas e inyectadas correctamente en los notebooks!")
