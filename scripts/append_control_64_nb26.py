"""Append and execute only the new 64/95 factorial control, preserving old NB26."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from geoau.base_decoupling_control import DEFAULT_OUTPUT, NOTEBOOK, prefix_hash
from geoau.geochemical_experiment import sha256, write_json

TAG = "geoai_control_64_95_nb26"


def build_addition(output=DEFAULT_OUTPUT):
    cells = []
    def md(text):
        cells.append(nbf.v4.new_markdown_cell(text.strip(), metadata={TAG: True}))
    def code(text):
        cells.append(nbf.v4.new_code_cell(text.strip(), metadata={TAG: True}))
    md("""# 11. Control añadido: desacoplamiento desde la base original de 64 variables

Esta ampliación conserva las celdas 1–18 anteriores y sus resultados históricos. **Las celdas nuevas se ejecutan en un kernel independiente**; no dependen de objetos ni de etiquetas heurísticas calculados arriba. Se conserva una copia byte a byte del notebook anterior en la nueva carpeta de resultados.

Pregunta: ¿el desacoplamiento aporta valor por sí mismo, o la diferencia depende de las variables añadidas después de NB19? Se ajustan cuatro opciones:

| Variables | Global | Desacoplado por sistemas |
| --- | --- | --- |
| 64 originales | global64 | max3_64 |
| 95 corregidas | global95 | max3_95 |

No se presupone que 64 variables sean más sólidas: se comprueba. El endpoint principal se fija antes de esta ejecución: depósitos recuperados al priorizar el5% de las celdas reservadas; contraste max3_64 menos global64. Los territorios ya se han explorado en otros experimentos, por lo que esta comparación es exploratoria.

El desacoplado conserva un componente global con todas las P (también las de sistema no resuelto) y especialistas primario no epitermal, aluvial y epitermal. Se usa el máximo de sus percentiles frente al fondo U. Las etiquetas se auditan y las CDF se aprenden mediante tres pliegues espaciales internos, únicamente dentro del entrenamiento. No se repite el min–max sobre la reserva ni la asignación epitermal por provincia de la sección histórica.""")
    code(f"""from pathlib import Path
import sys
import json
import pandas as pd
from IPython.display import display, Markdown, Image

ROOT_CONTROL = Path.cwd().resolve()
if ROOT_CONTROL.name == 'notebooks':
    ROOT_CONTROL = ROOT_CONTROL.parent
sys.path.insert(0, str(ROOT_CONTROL / 'src'))
from geoau.base_decoupling_control import BaseDecouplingControl

control64 = BaseDecouplingControl(ROOT_CONTROL, output={output!r})
display(pd.Series(control64.cfg).to_frame('diseño_fijado'))
display(pd.read_csv(control64.output / 'resumen_tipologias.csv'))
""")
    md("""## 11.1. Matrices y condiciones comunes

La matriz64 se carga directamente de las56 variables físicas aprobadas y las ocho clases geoquímicas originales. Se comprueba que sea idéntica a las primeras64 de la matriz95 corregida de NB27. No recibe índices nuevos ni cálculos auxiliares de las31 variables adicionales.

Se conserva la receta nacional original: ocho LightGBM,150 árboles, profundidad5,24 hojas, learning_rate0.04 y colsample_bytree1.0; ocho miembros tanto para global como para cada especialista disponible. El epitermal mantiene80 árboles/profundidad3/8 hojas por sus escasas P. Por componente y miembro,64 y95 reciben exactamente las mismas filas, su orden, pesos y semillas. U:P=3:1 sin reemplazo; las P de otro sistema tampoco se convierten en U.

En cada miembro, imputación, escalado y codificación se ajustan con su entrenamiento. Solo95 calcula el índice de pathfinders con estadísticas del entrenamiento. Se conserva el tratamiento categórico de las ocho clases del atlas en ambas matrices.""")
    code("""display(control64.prepare_features())
display(pd.read_csv(control64.output / 'contrato_variables_64_95.csv').groupby('matrix').size().rename('variables_de_entrada'))
""")
    md("""## 11.2. Evaluación mediante CV espacial

Se utilizan las mismas cinco particiones congeladas, bloques de50km y buffer de15km. El global64 debe reproducir las predicciones de la evaluación de la receta nacional anterior. Se evalúan ROC-AUC, Average Precision, área PR trapezoidal, Brier P/U y recuperación de P al1/5/10%.

Las CDF internas convierten los scores de los componentes en percentiles frente a U de entrenamiento; no son probabilidades calibradas. Se exporta un diagnóstico del global normalizado porque la normalización por pliegue puede cambiar métricas agrupadas entre pliegues, aunque preserve el orden dentro de cada uno.""")
    code("""cv_control64 = control64.evaluate_cv()
display(cv_control64)
display(pd.read_csv(control64.output / 'cv_cdf_diagnostic.csv'))
""")
    md("""## 11.3. Rotaciones de distritos y atribución de diferencias

Los distritos son las agrupaciones de indicios y depósitos del inventario empleadas para representar zonas mineralizadas. Se reservan siete grupos, sus bloques completos y15km de entorno, y se puntúan todas las celdas reservadas. Cada uno de los45 depósitos se cuenta una sola vez, con presupuestos exactos del1/5/10/20% y desempate por cell_id.

Los cuatro contrastes separan el efecto de desacoplar a64 o95 variables y el de añadir31 variables en global o desacoplado. Se muestran intervalos exploratorios con10000 remuestreos pareados de los siete grupos, junto con la esperanza aleatoria que considera huellas multicelda. No se usan las reservas externas para ajustar modelos, normalización, pesos ni hiperparámetros.""")
    code("""rotaciones_control64 = control64.evaluate_rotations()
display(rotaciones_control64[['method','n_deposits','captured_01','captured_05','captured_10','captured_20']])
display(pd.read_csv(control64.output / 'random_summary.csv'))
contrastes_control64 = pd.read_csv(control64.output / 'factorial_contrasts.csv')
display(contrastes_control64.loc[contrastes_control64.budget_percent.eq(5)])
""")
    md("""## 11.4. Reentrenamiento nacional real

Se reajustan los ocho miembros de cada componente64/95 con todas las664 P elegibles y U admisibles nacionales. Se guardan pipelines, CDF internas, scores, dispersión de miembros, importancias y cuatro GeoTIFF. El bundle conserva el contrato de variables para reproducir la inferencia.

`max3_64` es el mapa experimental fijado para estudiar la base simplificada. Los otros tres se conservan para comparación. Las métricas sobre presencias del mapa nacional son descriptivas in-sample; no sustituyen las rotaciones o CV. Esta sección no cambia el modelo servido por la aplicación.""")
    code("""nacional_control64 = control64.fit_national()
display(nacional_control64[['method','n_deposits','captured_deposits_at_01','captured_deposits_at_05','captured_deposits_at_10','captured_deposits_at_20']])
print('Bundle nacional:', control64.output / 'partitions/national_0/model.joblib')
print('Mapa experimental64:', control64.output / 'maps/NB26_control_max3_64_score.tif')
""")
    md("""## 11.5. Verificaciones, resultados y reproducción

Se verifican las celdas históricas, fuentes, contratos de64/95 variables, muestras P/U pareadas, pesos, buffers, CDF internas y predicciones de los trece bundles serializados. El global64 debe coincidir con la receta nacional anterior en CV y las siete rotaciones. Los resultados y la conclusión se generan con los archivos de esta ejecución.

Para ejecutar únicamente esta ampliación: `.venv-fase-a/Scripts/python.exe scripts/append_control_64_nb26.py`. No es necesario volver a ejecutar las celdas históricas del comienzo. La copia original permite comprobar su hash anterior, conservado en los manifiestos históricos de NB27/NB29.""")
    code("""validacion_control64 = control64.validate()
display(pd.Series(validacion_control64).to_frame('validacion'))
display(Image(filename=str(control64.make_figures())))
informe_control64 = control64.write_report()
control64.seal(informe_control64)
display(Markdown(informe_control64.read_text(encoding='utf-8').split('## Qué se compara')[0]))
print('Informe:', informe_control64)
""")
    return nbf.v4.new_notebook(cells=cells)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    path, output = ROOT / NOTEBOOK, ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    book = nbf.read(path, as_version=4)
    indices = [i for i, c in enumerate(book.cells) if c.metadata.get(TAG)]
    first = min(indices) if indices else len(book.cells)
    if indices and indices != list(range(first, len(book.cells))):
        raise ValueError("Hay celdas ajenas después del control; se conservan sin sobrescribir. Revisar ubicación.")
    historical = copy.deepcopy(book.cells[:first])
    history_path = output / "historical_notebook.json"
    if not history_path.exists():
        if indices:
            raise ValueError("Falta la copia previa necesaria para reconstruir este control.")
        (output / "notebook26_original.ipynb").write_bytes(path.read_bytes())
        write_json(history_path, {"historical_cell_count": first, "original_notebook_sha256": sha256(path),
            "prefix_sha256": prefix_hash(historical), "original_notebook": NOTEBOOK,
            "original_metadata": dict(book.metadata)})
    history = json.loads(history_path.read_text(encoding="utf-8"))
    if first != history["historical_cell_count"] or prefix_hash(historical) != history["prefix_sha256"]:
        raise ValueError("Las celdas históricas no coinciden con la copia preservada.")
    if sha256(output / "notebook26_original.ipynb") != history["original_notebook_sha256"]:
        raise ValueError("La copia original del notebook ha cambiado.")
    addition = build_addition(args.output)
    def checkpoint(**kwargs):
        book.cells = historical + addition.cells
        nbf.validate(book)
        nbf.write(book, path)
        if "cell_index" in kwargs:
            print(f"Celda nueva {kwargs['cell_index']} ejecutada", flush=True)
    checkpoint()
    print(f"NB26: {first} celdas históricas conservadas; {len(addition.cells)} nuevas", flush=True)
    if args.build_only:
        return
    runtime = output / "runtime"
    kernel_dir = runtime / "kernels/geoai_control64"
    kernel_dir.mkdir(parents=True, exist_ok=True)
    env = {"PYTHONPATH": str(ROOT / "src"), "MPLCONFIGDIR": str(runtime / "matplotlib"),
        "JUPYTER_RUNTIME_DIR": str(runtime), "IPYTHONDIR": str(runtime / "ipython"), "PYTHONIOENCODING": "utf-8"}
    (kernel_dir / "kernel.json").write_text(json.dumps({"argv": [sys.executable, "-X", "utf8", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "GeoAI control64 NB26", "language": "python", "env": env}), encoding="utf-8")
    manager = AsyncKernelManager(kernel_name="geoai_control64", connection_file=str(runtime / "connection.json"),
        kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(runtime / "kernels")]))
    client = NotebookClient(addition, km=manager, timeout=7200, resources={"metadata": {"path": str(ROOT)}},
        on_cell_executed=checkpoint)
    try:
        client.execute(cleanup_kc=True)
    except BaseException:
        checkpoint()
        print("Checkpoints de notebook y particiones completadas conservados.", flush=True)
        raise
    checkpoint()
    codes = [c for c in addition.cells if c.cell_type == "code"]
    errors = [o for c in codes for o in c.outputs if o.output_type == "error"]
    if errors or any(c.execution_count is None for c in codes):
        raise AssertionError("Control incompleto o con errores.")
    if prefix_hash(nbf.read(path, as_version=4).cells[:first]) != history["prefix_sha256"]:
        raise AssertionError("Han cambiado las celdas históricas.")
    write_json(output / "notebook_execution.json", {"notebook": NOTEBOOK, "sha256": sha256(path),
        "code_cells_executed": len(codes), "errors": len(errors), "historical_cells_preserved": first,
        "historical_prefix_sha256": history["prefix_sha256"], "python": sys.executable})
    print(f"Control NB26 ejecutado: {len(codes)} celdas de código, sin errores; historial conservado", flush=True)


if __name__ == "__main__":
    main()
