"""Build and execute NB27 using this Python environment and a workspace kernel."""
from pathlib import Path
import argparse
import json
import os
import sys
import traceback

import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
NAME = "27_auditoria_sistemas_y_comparacion_controlada.ipynb"


def build(output):
    cells = []
    def md(text):
        cells.append(nbf.v4.new_markdown_cell(text))
    def code(text):
        cells.append(nbf.v4.new_code_cell(text))

    md("""# Notebook 27 · Auditoría de sistemas minerales y comparación controlada

Este cuaderno ejecuta los **puntos 1 a 4 de la revisión del NB26** y reentrena los modelos nacionales. Conserva las entradas y resultados anteriores.

1. Revisar las tipologías: sin provincia como sustituto de sistema mineral, sin asignar los desconocidos a roca y conservando casos mixtos.
2. Auditar la geoquímica: distinguir representantes de intervalos de mediciones analíticas; conservar ausentes y ajustar las estadísticas aprendidas solo dentro de entrenamiento.
3. Revisar la mezcla: normalización de fondo aprendida dentro de entrenamiento y pesos elegidos mediante CV interna; sin factor 0,7 ni mínimos/máximos del test.
4. Comparar global93/global95, dos y tres especialistas, máximo/fusión aprendida, una regla geológica predefinida y selección aleatoria. Reentrenar y guardar todos los modelos y sus mapas.

**Diseño exploratorio interno:** se reutilizan territorios ya examinados en NB19–26. Aunque cada ajuste excluye su evaluación, esta ejecución no constituye una campaña externa nueva ni acredita probabilidades físicas de encontrar oro. No se añaden las nuevas fuentes o el piloto de los puntos 5–6.

Implementación reproducible: `src/geoau/controlled_system_features.py`, `controlled_system_models.py` y `controlled_system_experiment.py`. Las celdas siguientes ejecutan sus etapas y muestran los datos, métricas y visualizaciones obtenidos realmente.""")
    code(f"""from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown

ROOT = Path.cwd().resolve()
if not (ROOT / 'src').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / 'src'))
from geoau.controlled_system_experiment import ControlledExperiment
from geoau.controlled_system_models import BackgroundCDF, FAMILIES, METHODS

exp = ControlledExperiment(ROOT, output={output!r})
print('Python:', sys.executable)
print('Repositorio:', ROOT)
print('Resultados:', exp.output)
print('Dominio:', len(exp.data.grid), '| P:', len(exp.data.positives))
""")
    md("""## 1. Revisión operativa de tipologías

Se utiliza `tipo_au_revisado` y la identificación documentada de los depósitos de Rodalquilar. **Primario no significa exclusivamente orogénico**: incluye contextos de roca no separados con suficiente evidencia. La regla epitermal se limita a `dep_rodalquilar_cinto` y `dep_rodalquilar_santa_josefa`, con la documentación ya contenida en el inventario. Esto no sustituye una nueva certificación geológica.

Los pendientes conservan su peso 0,5 y las confirmadas peso 1. Las P de sistema desconocido se conservan en los modelos globales y en el componente global de las fusiones, sin imputarles una génesis. Una celda de 1 km puede conservar varias tipologías documentadas. Las tablas por registro incluyen evidencia, motivo y regla aplicada.""")
    code("""tipologias = exp.audit_labels()
display(tipologias)
auditoria_registros = pd.read_csv(exp.output / 'auditoria_sistemas_por_registro.csv')
display(auditoria_registros.loc[auditoria_registros.epitermal,
    ['Nombre_mina', 'deposit_id', 'tipo_au_revisado', 'regla_sistema', 'evidencia']])
display(exp.systems.loc[exp.systems.mixto | exp.systems.no_resuelto].head(12))
""")
    md("""## 2. Auditoría de geoquímica y construcción de covariables

Se inspecciona la banda 2, sus valores distintos y su relación con las clases. **Un representante numérico por intervalo no es una concentración analítica continua original.** Promediar 2 × 2 píxeles y aplicar log1p no crea mediciones nuevas. Se conserva esta representación con nombres y limitaciones explícitos.

La matriz tiene 95 variables; la versión de 93 excluye únicamente `trampa_valle_aluvial` y `vector_epitermal_hidrotermal`. Ambas comparten las correcciones. `grado_metamorfico` y `afinidad_esquistos_verdes` se documentan como proxies heurísticos litológicos, no como mediciones de facies metamórfica.

Se reconstruyen los cuatro indicadores MODIS desde las teselas ya descargadas para retirar el relleno por mediana nacional anterior. No se adquiere otro sensor ni se aplica una nueva máscara QA. Los residuos de ventana fija son covariables cartográficas sin etiquetas. Las medianas, escalado, categorías y estadísticas empíricas globales del índice pathfinder se aprenden **por miembro, solo con sus filas de entrenamiento**.

Para obtener analítica continua real hace falta una fuente con mediciones o valores originales; el cuaderno no la inventa a partir de las clases.""")
    code("""auditoria_geoquimica = exp.prepare_features()
display(auditoria_geoquimica)
display(pd.read_csv(exp.output / 'representantes_clases_geoquimicas.csv').head(16))
contrato = pd.read_csv(exp.output / 'contrato_variables.csv')
print('Variables global93:', int(contrato.incluida_93.sum()), '| global95:', len(contrato))
display(exp.X[['trampa_valle_aluvial', 'vector_epitermal_hidrotermal']].describe())
print('Ausentes retenidos en representantes geoquímicos:')
display(exp.X.filter(like='representante_intervalo').isna().sum().to_frame('celdas_sin_dato'))
""")
    md("""## 3. Mezcla ajustada dentro del entrenamiento

Cada componente utiliza ocho LightGBM con muestreo U independiente **sin reemplazo** y tres U por P. El muestreo parte del territorio autorizado, tanto para entrenamiento interno y externo como para el mapa final. Global93 y global95 comparten exactamente P, U, pesos, semillas e hiperparámetros; los componentes comunes de las arquitecturas se reutilizan.

En cada entrenamiento externo:

1. Se construyen tres pliegues espaciales internos por bloques de 50 km y buffer de 15 km.
2. Se generan predicciones internas OOF de cada componente.
3. Se ajustan referencias de fondo con las predicciones U internas. La normalización usa rangos medios interpolados y anclas fijas 0/1; no depende de qué otras celdas se puntúen después.
4. Con referencias de fondo cruzadas entre los pliegues internos se eligen pesos no negativos que maximizan AP interna. El componente global conserva peso mínimo 0,1. Los pesos y las referencias se fijan antes de predecir el territorio externo.

`max_2`/`fusion_2`: global95 + primario + aluvial. `max_3`/`fusion_3`: global95 + primario_otro + aluvial + epitermal. Máximo y fusión usan **exactamente los mismos componentes**. La diferencia es el operador de agregación. Si hay menos de dos P de un especialista se marca no disponible; no se fabrica un modelo ni se sustituye por una regla adaptada al test.

El especialista epitermal tiene una capacidad reducida predeclarada por su escasez. Las comparaciones de los componentes comunes conservan su configuración. Los scores normalizados expresan rareza frente al fondo, **no probabilidades de depósito**.""")
    code("""display(pd.Series(exp.cfg, name='Diseño fijado antes de evaluar').to_frame())
display(pd.DataFrame([{'metodo': k, 'componentes': ' + '.join(v)} for k,v in FAMILIES.items()]))

# Demostración de invariancia: añadir otra celda al lote no cambia el score de la primera.
cdf = BackgroundCDF().fit(np.array([0.1, 0.2, 0.3, 0.4]))
assert cdf.transform([0.25])[0] == cdf.transform([0.25, 0.99])[0]
print('Normalización independiente del lote de predicción: verificada')
""")
    md("""## 4. Comparación controlada y reentrenamiento

Las métricas se generan desde predicciones y CSV, sin escribir manualmente los resultados de la tabla. Se reutilizan las cinco particiones espaciales originales para métricas P/U y las siete reservas distritales para recuperación de depósitos. Bloques de 50 km, buffer de 15 km y presupuestos exactos con desempate por cell_id.

El contraste global93/global95 aísla los dos descriptores nuevos bajo un procedimiento común corregido. Las comparaciones 2/3 expertos estudian la partición de tipologías y arquitectura. Máximo/fusión compara la agregación de los mismos modelos. El resultado histórico del NB26 tiene otra preparación y mezcla: se conserva como antecedente, no como control causal equivalente.

**Las medias OOF globales no son una media simple de las métricas por pliegue.** Brier se calcula frente a P/U y, para scores de rareza, es solo un diagnóstico numérico; no acredita calibración ni sirve para comparar probabilidades físicas.""")
    code("""metricas_cv = exp.evaluate_cv()
display(metricas_cv)
display(pd.read_csv(exp.output / 'cv_fold_metrics.csv'))
""")
    md("""### 4.1. Recuperación territorial y referencias

Se puntúan todas las celdas de cada reserva y se cuenta una vez cada depósito representado en la selección. La referencia aleatoria utiliza la probabilidad exacta de seleccionar al menos una de las celdas de cada depósito con el mismo presupuesto; no supone que un depósito ocupe una sola celda. La regla geológica es una referencia física simple predefinida, sin ajuste al test.""")
    code("""metricas_rotaciones = exp.evaluate_rotations()
display(metricas_rotaciones[['method', 'n_deposits', 'captured_01', 'captured_05', 'captured_10', 'captured_20']])
display(pd.read_csv(exp.output / 'random_summary.csv'))
display(pd.read_csv(exp.output / 'rotation_metrics.csv'))
""")
    md("""### 4.2. Ajuste nacional de todos los procedimientos

Se reajustan componentes y referencias internas usando las 664 P elegibles. Se guardan todos los procedimientos, sus miembros y sus mapas. `fusion_3` es la cartografía experimental principal **predeclarada**, no un ganador elegido mirando los resultados externos. Los pesos pueden reducir la contribución de un especialista cuando no aporta señal en entrenamiento.

La recuperación nacional de los depósitos utilizados para entrenar es descriptiva in-sample. No sustituye las rotaciones ni una campaña independiente.""")
    code("""metricas_nacionales_descriptivas = exp.fit_national()
display(metricas_nacionales_descriptivas)
pesos_nacionales = json.loads((exp.output / 'partitions/national_0/weights.json').read_text())
display(pd.DataFrame(pesos_nacionales).fillna(0))
""")
    md("""### 4.3. Validación independiente de artefactos

Se recalculan métricas, presupuestos, ausencia de fuga de celdas, separación de bloques, buffers internos/externos, tipos de los especialistas, ratios U:P, muestras sin reemplazo, pesos documentales, estadísticas aprendidas por miembro y referencias de fondo. Se reproducen predicciones desde los modelos guardados y se verifica que NB26 y los resultados anteriores siguen intactos.""")
    code("""validacion = exp.validate()
display(pd.Series(validacion).to_frame('validacion'))
""")
    md("""### 4.4. Comparación visual y artefactos finales

Las figuras y tablas proceden de esta ejecución. Las diferencias deben leerse junto con la distribución por territorio y las referencias. La mejora de una métrica interna no acredita una mejora universal ni utilidad prospectiva externa. Los siete territorios se han reutilizado durante el desarrollo; se conserva expresamente esa limitación.""")
    code("""figuras = exp.make_figures()
for figura in figuras:
    display(Image(filename=str(figura)))
informe = exp.write_report()
exp.seal(informe)
display(Markdown(informe.read_text(encoding='utf-8').split('## Validación y reproducibilidad')[0].split('### Cartografía y ajuste final')[0]))
print('Informe:', informe)
print('Modelo nacional:', exp.output / 'partitions/national_0/model.joblib')
print('Mapa experimental:', exp.output / 'maps/NB27_fusion3_score.tif')
""")
    nb = nbf.v4.new_notebook(cells=cells)
    nb.metadata.update({"kernelspec": {"display_name": "Python (GeoAI)", "language": "python", "name": "python3"},
                        "language_info": {"name": "python", "version": sys.version.split()[0]}})
    return nb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/nb27_comparacion_controlada_20261022")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    path = ROOT / "notebooks" / NAME
    nb = build(args.output)
    nbf.validate(nb)
    nbf.write(nb, path)
    print(f"Notebook construido: {path}", flush=True)
    if args.build_only:
        return
    runtime = ROOT / "reports" / "nb27_runtime_20261022"
    kernel_dir = runtime / "kernels" / "geoai_nb27"
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-X", "utf8", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "GeoAI NB27 workspace", "language": "python",
        "env": {"PYTHONPATH": str(ROOT / "src"), "MPLCONFIGDIR": str(runtime / "matplotlib"),
                "JUPYTER_RUNTIME_DIR": str(runtime), "PYTHONIOENCODING": "utf-8"}}), encoding="utf-8")
    manager = AsyncKernelManager(kernel_name="geoai_nb27", connection_file=str(runtime / "connection.json"),
        kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(runtime / "kernels")]))
    def checkpoint(**kwargs):
        nbf.write(nb, path)
        print(f"Celda {kwargs.get('cell_index', '?')} ejecutada", flush=True)
    client = NotebookClient(nb, km=manager, timeout=7200, resources={"metadata": {"path": str(ROOT)}},
                            on_cell_executed=checkpoint)
    try:
        client.execute()
    except BaseException:
        nbf.write(nb, path)
        print("Ejecución interrumpida; notebook y entrenamientos completados conservados.", flush=True)
        raise
    nbf.write(nb, path)
    sys.path.insert(0, str(ROOT / "src"))
    from geoau.geochemical_experiment import sha256, write_json
    code = [c for c in nb.cells if c.cell_type == "code"]
    errors = [o for c in code for o in c.get("outputs", []) if o.output_type == "error"]
    if errors or any(c.execution_count is None for c in code):
        raise AssertionError("No todas las celdas se han ejecutado correctamente.")
    write_json(ROOT / args.output / "notebook_execution.json", {"notebook": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path), "code_cells_executed": len(code), "errors": len(errors), "python": sys.executable})
    print(f"NB27 ejecutado y guardado: {len(code)} celdas de código, sin errores", flush=True)


if __name__ == "__main__":
    main()
