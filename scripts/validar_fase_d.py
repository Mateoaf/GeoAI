"""Comprueba productos completos sin recalcular geoprocesamiento."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from geoau import features as fd

run=fd.current_run(ROOT)
fd.verify_records(run,fd.read_json(run/'outputs_manifest.json'))
control=fd.read_json(run/'control_cierre.json')
assert control['estado_ejecucion']=='completada'
x=pd.read_parquet(run/'Grid_Master_Au.parquet')
q=pd.read_parquet(run/'calidad_y_soporte.parquet')
y=pd.read_parquet(run/'etiquetas_por_celda.parquet')
links=pd.read_parquet(run/'relacion_indicios_celda.parquet')
assert x.cell_id.is_unique and x.cell_id.equals(q.cell_id) and x.cell_id.equals(y.cell_id)
allow=fd.read_json(run/'feature_allowlist.json')
assert set(x.columns)=={'cell_id',*allow['candidate_columns']}
assert not allow['approved_training_columns'] and not control['prediction_allowed']
assert y.n_candidatos.sum()==links.cell_id.notna().sum()
assert not np.isinf(x.select_dtypes(include='number')).any().any()
for col in x:
    v=x[col].dropna()
    if col.endswith('_fraccion') or '_proporcion_clase_' in col:
        assert v.between(0,1+1e-6).all(),col
    if col.startswith('dist_') or col.startswith('dens_aprox_'):
        assert (v>=0).all(),col
assert x.pendiente_grados.dropna().between(0,90).all()
for element in fd.local_palettes(ROOT):
    props=x.filter(regex=f'^{element.lower()}_proporcion_clase_')
    present=props.notna().all(axis=1)
    assert np.allclose(props.loc[present].sum(axis=1),1,atol=1e-6),element
    assert (props.notna().any(axis=1)==present).all(),element
print('Verificación satisfactoria:',run)
print(control)
