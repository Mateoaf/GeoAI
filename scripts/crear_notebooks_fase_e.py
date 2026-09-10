"""Crea exclusivamente cuadernos E ausentes; nunca sobrescribe trabajo existente."""
from pathlib import Path
import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]
SETUP = '''from pathlib import Path
import sys
import importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'src/geoau/evaluation.py').is_file())
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))
from geoau import evaluation as ev
importlib.reload(ev)
'''

books = {
 '07_particiones_espaciales': [
  ('m', '# 07 · Particiones espaciales y reserva\n\nFase E, pasos 27–28. Lee la ejecución D fijada en `config/evaluation.yaml`, verifica sus hashes y congela el protocolo. Consulte [LEEME_FASE_E.md](LEEME_FASE_E.md).\n\n**El modo diagnóstico usa candidatos, no positivos confirmados.** Los bloques de 50 km y la separación de 5 km son hipótesis iniciales pendientes de revisión geológica.'),
  ('c', SETUP + '\nRUN = ev.ensure_run(ROOT)\ndisplay(ev.read_json(RUN / "readiness.json"))'),
  ('m', '## Unidades completas y anidamiento\nLos bloques conectados por un mismo depósito/distrito se unen transitivamente. En diagnóstico se añade el grupo de proximidad de 500 m, sin equipararlo a un depósito. La reserva geográfica se elige por semilla antes del ajuste. Las particiones internas solo acceden al entrenamiento externo.'),
  ('c', 'summary = ev.build_splits(ROOT, RUN)\ndisplay(summary)\ndisplay(pd.read_csv(RUN / "block_sensitivity.csv"))\ndisplay(ev.read_json(RUN / "split_plan.json"))'),
  ('m', 'La tabla 25/50/100 km describe agrupación y disponibilidad de unidades. **No mide autocorrelación ni demuestra que 50 km sea óptimo.** La reducción de folds comprueba factibilidad; no maximiza una métrica de rendimiento.'),
  ('c', '''import matplotlib.pyplot as plt
territory = pd.read_parquet(RUN / 'territory.parquet')
units = pd.read_parquet(RUN / 'design/spatial_units.parquet')
view = territory.merge(units, on='cell_id', validate='one_to_one')
fig, ax = plt.subplots(figsize=(10, 8))
development = view[~view.holdout]
plot = ax.scatter(development.x_center, development.y_center,
                  c=development.outer_fold, cmap='tab10', s=.2, rasterized=True)
reserve = view[view.holdout]
ax.scatter(reserve.x_center, reserve.y_center, color='black', s=.2, label='Reserva')
ax.set(aspect='equal', xlabel='ETRS89 / UTM 30N · metros', ylabel='Metros',
       title='Asignación territorial diagnóstica; consultar máscaras para buffers y soporte')
ax.legend(); fig.colorbar(plot, ax=ax, label='Fold externo'); plt.show()''')],
 '08_muestreo_presencia_fondo': [
  ('m', '# 08 · Muestreo presencia–fondo\n\nPaso 29 y preparación del paso 30. U significa **no etiquetado**, nunca ausencia confirmada. Las realizaciones se generan únicamente dentro de cada entrenamiento externo/interno. Los positivos retenidos no intervienen en la exclusión del fondo.'),
  ('c', SETUP + '\nRUN = ev.current_run(ROOT)\nsamples = ev.build_samples(ROOT, RUN)\ndisplay(samples)'),
  ('m', '## Ratios y probabilidades de inclusión\nSe ensayan 1/3/10 U por P y tres realizaciones. El buffer de 250 m se aplica conservadoramente entre huellas de celdas de 1 km: no representa una precisión demostrada de las coordenadas. Es distinto de los 5 km entre entrenamiento y prueba.\n\nEl muestreo por bloques guarda probabilidades de inclusión, pesos inversos y pesos de área. Cuando hay menos muestras que bloques se seleccionan primero bloques al azar. Estos pesos no son `class_weight` ni estimaciones de prevalencia.'),
  ('c', '''display(samples.groupby(['level', 'ratio_requested']).agg(
    designs=('sample_id','size'), min_P=('n_P','min'), max_P=('n_P','max'),
    min_U=('n_U','min'), capped=('pool_capped','sum')))
example = samples.sample_id.iloc[0]
display(pd.read_parquet(RUN / f'samples/{example}.parquet').head())
display(pd.read_parquet(RUN / f'samples/{example}_allocation.parquet').head())'''),
  ('m', 'La evaluación usa todas las celdas elegibles `role=test` de la misma membresía, con independencia del ratio y de la realización. No se ha inventado una capa de esfuerzo de observación: esa alternativa exige información verificable.')],
 '09_protocolo_PU_y_control': [
  ('m', '# 09 · Contrato de aprendizaje y cierre técnico\n\nPaso 30. La referencia utiliza una realización U; la alternativa PU agregará scores de varias realizaciones manteniendo P y evaluación. Los modelos se ajustarán en fase F. Un score P/U no es una probabilidad absoluta de encontrar oro.'),
  ('c', SETUP + '\nRUN = ev.current_run(ROOT)\ncontrol = ev.finish_run(ROOT, RUN)\ndisplay(control)\ndisplay(ev.read_json(RUN / "learning_contract.json"))'),
  ('m', '## Condiciones para entrenar\nLa selección de variables, algoritmo, ratio e hiperparámetros pertenece al bucle interno. El externo evalúa ese procedimiento completo. La reserva solo se abre una vez fijadas las decisiones. Seleccionar modelos repetidamente por la reserva invalida su papel de prueba final.'),
  ('c', '''ev.verify(RUN, ev.read_json(RUN / 'outputs_manifest.json'))
try:
    ev.assert_ready_for_training(ROOT, RUN)
    print('Protocolo aprobado para fase F.')
except ValueError as error:
    if control.get('training_allowed'): raise
    print(str(error))
    display(control['reasons_not_ready'])
print('Ejecución:', RUN)'''),
  ('m', 'Para abandonar el modo diagnóstico hacen falta etiquetas revisadas, depósitos y distritos identificados, cartografía territorial de distritos, predictores aprobados en D y revisión del protocolo. Para el objetivo aluvial se requieren además cuencas. Cambiar únicamente `mode` no supera estos controles.')]
}

if __name__ == '__main__':
    for name, cells in books.items():
        path = ROOT / 'notebooks' / (name + '.ipynb')
        if path.exists():
            print('Conservado:', path.name)
            continue
        book = nb.v4.new_notebook(cells=[nb.v4.new_markdown_cell(s) if k == 'm' else nb.v4.new_code_cell(s) for k, s in cells])
        book.metadata.kernelspec = dict(name='geoau-fase-a', display_name='GeoAu fase A', language='python')
        nb.validate(book); nb.write(book, path)
        print('Creado:', path.name)
