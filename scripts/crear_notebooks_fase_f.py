"""Crea 10–14 sin sobrescribir cuadernos existentes."""
from pathlib import Path
import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]
SETUP = '''from pathlib import Path
import sys, importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'src/geoau/training.py').is_file())
if str(ROOT/'src') not in sys.path: sys.path.insert(0, str(ROOT/'src'))
from geoau import training as tr
from geoau import evaluation as ev
importlib.reload(tr)
'''

BOOKS = {
 '10_pipelines_y_contrato_entrenamiento': [
  ('m', '# 10 · Pipelines y contrato de entrenamiento\n\nFase F, paso 31. Consulte [LEEME_FASE_F.md](LEEME_FASE_F.md). Se verifica la ejecución E y se congelan configuración, familias, candidatos, predictores y evaluación. **Modo diagnóstico:** los ajustes ensayan el código con candidatos; no autorizan producción ni validan las etiquetas.'),
  ('c', SETUP + '\nRUN = tr.ensure_run(ROOT)\ndisplay(ev.read_json(RUN/"control_cierre.json"))\ndisplay(ev.read_json(RUN/"config_snapshot.json"))'),
  ('m', '## Columnas y transformaciones\nSolo entran predictores de la lista D. Se excluyen coordenadas, IDs, etiquetas, grupos y pesos. Las categorías y clases geoquímicas se codifican como categorías, con estados explícitos para ausente/desconocido. La mediana, categorías y escalado de regresión logística se aprenden en cada entrenamiento interno. El boosting desactiva la validación aleatoria implícita de early stopping.'),
  ('c', '''schema = ev.read_json(RUN/'feature_schema.json')
display(pd.DataFrame([{'set': name, 'predictors': len(v['columns']), 'categorical': len(v['categorical'])}
                      for name, v in schema.items()]))
display(ev.read_json(RUN/'candidates.json'))'''),
  ('m', '## Protocolo predefinido\nSelección por recuperación de candidatos al priorizar el 5 % del área en validación interna. En modo validado se cuenta una vez cada depósito. Empates por hash de celda independiente de las etiquetas. AP y ROC-AUC P/U se calculan en una muestra fija de evaluación y no miden descubrimiento real. No se generan predicciones de la reserva.\n\nEl piloto usa tres candidatos por familia y ratios 3/1/10. La referencia de Random Forest tiene 500 árboles, hoja mínima 5 y `max_features="sqrt"`. La configuración permite ampliar la búsqueda en una nueva ejecución.')],
 '11_referencias_y_regresion_logistica': [
  ('m', '# 11 · Referencias y regresión logística\n\nPaso 32. Ranking constante, aleatorio reproducible y regla ilustrativa geológica fijada antes de ver resultados. La regla combina proximidad a fallas y fracción de unidades explícitamente granitoides; requiere revisión geológica y no pretende describir todos los tipos de oro.'),
  ('c', SETUP + '\nRUN = tr.current_run(ROOT)\nreferences = tr.fit_references(ROOT, RUN)\ndisplay(references)'),
  ('m', '## Regresión logística anidada\nCada candidato se ajusta de nuevo en cada train interno. Tras seleccionar regularización y ratio por resultados internos, se ajusta en train externo y se predice todo su territorio test elegible. No se usa accuracy para seleccionar.'),
  ('c', 'logistic = tr.fit_family(ROOT, RUN, "logistic")\ndisplay(logistic)')],
 '12_random_forest_espacial': [
  ('m', '# 12 · Random Forest con evaluación espacial\n\nPaso 33. Usa las particiones E, búsqueda interna y predicciones fuera de entrenamiento. No usa OOB como estimación de transferencia espacial. Se guardan pipeline, parámetros, ratio, variables, tiempos, RSS después del ajuste y hash de cada muestra.'),
  ('c', SETUP + '\nRUN = tr.current_run(ROOT)\nrf = tr.fit_family(ROOT, RUN, "random_forest")\ndisplay(rf)'),
  ('m', 'La ponderación inicial es la del diseño P/U sin pesos adicionales. No se acumula una compensación automática mediante `class_weight`. El peso de inclusión de U permanece disponible; `normalized_design_u` permite estudiarlo en una ejecución separada conservando el peso total de U. Ninguna alternativa calibra una probabilidad física de presencia.'),
  ('c', 'display(pd.DataFrame(ev.read_json(RUN/"random_forest_selections.json")))')],
 '13_comparacion_modelos': [
  ('m', '# 13 · ExtraTrees y boosting\n\nPaso 34. Ambas familias utilizan el mismo territorio, muestras, métrica interna y número de candidatos que RF/logística. Esto iguala el número de evaluaciones; no garantiza el mismo coste computacional. El boosting emplea codificación one-hot y un número de iteraciones prefijado, sin early stopping aleatorio.'),
  ('c', SETUP + '\nRUN = tr.current_run(ROOT)\nextra = tr.fit_family(ROOT, RUN, "extra_trees")\ndisplay(extra)'),
  ('c', 'boost = tr.fit_family(ROOT, RUN, "hist_boosting")\ndisplay(boost)'),
  ('m', '## Comparación externa descriptiva\nLos resultados externos describen transferencia entre los bloques diagnósticos. El procedimiento final selecciona familia por resultados internos de cada fold. No se proclama un ganador global a partir de esta tabla.'),
  ('c', '''families = ev.read_json(RUN/'config_snapshot.json')['families']
comparison = pd.concat([pd.read_csv(RUN/f'{f}_outer_metrics.csv') for f in families])
display(comparison.groupby('family')[['recovery_at_05','average_precision_PU','roc_auc_PU']].agg(['mean','std']))''')],
 '14_ablaciones_PU_y_cierre': [
  ('m', '# 14 · Ablaciones, bagging de U y cierre\n\nPaso 35. Se comparan conjuntos incrementales de geología, relieve, elementos guía, Au, hidrología y proporciones geoquímicas con RF de parámetros fijos. Usan exactamente los mismos folds, soporte y muestra por fold. Son contrastes exploratorios; no se selecciona una variante por su test externo.'),
  ('c', SETUP + '\nRUN = tr.current_run(ROOT)\nsensitivity = tr.run_sensitivity(ROOT, RUN)\ndisplay(sensitivity)'),
  ('m', '## Variación de fondo\nEl bagging promedia tres RF ajustados con las realizaciones U de E. Conserva P, los parámetros seleccionados internamente y el territorio test. La dispersión incluye variación de fondo y semilla del estimador; no es un intervalo de confianza de la mineralización. No se calibra contra U como si fueran ausencias verificadas.'),
  ('c', '''control = tr.finish_run(ROOT, RUN)
display(control)
display(pd.read_csv(RUN/'nested_procedure_metrics.csv'))
display(ev.read_json(RUN/'pending_experiments.json'))'''),
  ('c', '''import matplotlib.pyplot as plt
table = pd.read_csv(RUN/'comparison_by_fold.csv')
fig, ax = plt.subplots(figsize=(10, 5))
for name, part in table.groupby('family'):
    ax.plot(part.split_id, part.recovery_at_05, marker='o', label=name)
ax.set(ylabel='Fracción de celdas candidatas recuperadas al 5 % del área',
       xlabel='Fold externo', title='Ensayo diagnóstico · sin interpretación probabilística')
ax.legend(bbox_to_anchor=(1.02, 1)); fig.tight_layout(); plt.show()
ev.verify(RUN, ev.read_json(RUN/'outputs_manifest.json'))'''),
  ('m', '## Continuación\nLa resolución de 500 m, cambios de buffers/etiquetas y geofísica requieren nuevas entradas verificadas y nuevas ejecuciones anteriores. No se simulan capas ausentes. El cierre técnico de F no aprueba científicamente B/D/E ni sustituye la evaluación G. La reserva sigue cerrada.')]
}

if __name__ == '__main__':
    for name, cells in BOOKS.items():
        path = ROOT/'notebooks'/(name+'.ipynb')
        if path.exists():
            print('Conservado:', path.name); continue
        book = nb.v4.new_notebook(cells=[nb.v4.new_markdown_cell(s) if k == 'm' else nb.v4.new_code_cell(s) for k, s in cells])
        book.metadata.kernelspec = dict(name='geoau-fase-a', display_name='GeoAu fase A', language='python')
        nb.validate(book); nb.write(book, path)
        print('Creado:', path.name)
