"""
scripts/ajustar_mapa_nb17.py
Ajusta la celda final del cuaderno 17 eliminando el plt.title redundante
y re-ejecuta el renderizado de la imagen.
"""
import sys
from pathlib import Path
import nbformat
import shutil

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def main():
    # 1. Asegurar que la imagen limpia esté generada y copiada
    from scripts.comparar_mapas_v1_vs_exp import main as generar_mapa
    generar_mapa()

    # 2. Modificar el notebook 17
    nb_path = ROOT / "notebooks/17_fase_h_mapa_interpretabilidad.ipynb"
    nb = nbformat.read(nb_path, as_version=4)

    # Buscar la celda que muestra la imagen
    for cell in nb.cells:
        if cell.cell_type == "code" and "comparativa_mapa_v1_vs_experimental.png" in "".join(cell.source):
            lines = cell.source if isinstance(cell.source, list) else cell.source.splitlines(keepends=True)
            new_lines = []
            for line in lines:
                if "plt.title(" in line:
                    new_lines.append("    plt.tight_layout()\n")
                elif "plt.figure(" in line:
                    new_lines.append("    plt.figure(figsize=(16, 8.5), dpi=150)\n")
                else:
                    new_lines.append(line)
            cell.source = "".join(new_lines)
            print("  [OK] Celda de imagen en Notebook 17 modificada.")

    nbformat.write(nb, nb_path)

    # 3. Re-renderizar las salidas del cuaderno 17
    from scripts.ejecutar_secciones_nuevas_notebooks import process_notebook
    process_notebook("17_fase_h_mapa_interpretabilidad.ipynb", "Extensión Experimental")
    print("  [OK] Notebook 17 re-renderizado con la imagen ajustada.")

if __name__ == "__main__":
    main()
