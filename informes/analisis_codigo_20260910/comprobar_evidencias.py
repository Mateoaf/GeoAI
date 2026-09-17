"""Comprobaciones de lectura para el informe; no ejecuta ni modifica notebooks."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import pandas as pd
import shapely
from geoau import features as fd, evaluation as ev, training as tr


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def main():
    inventory = []
    for p in sorted((ROOT / 'notebooks').glob('[0-9][0-9]_*.ipynb')):
        n = json.loads(p.read_text(encoding='utf-8'))
        for i, c in enumerate(n['cells']):
            if c['cell_type'] != 'code':
                continue
            source = ''.join(c['source'])
            tree = ast.parse(source)
            inventory.append(dict(notebook=p.name, cell_index_0=i, cell_position_1=i+1,
                execution_count=c.get('execution_count'), lines=len(source.splitlines()),
                executable_statements=len(tree.body), sha256=hashlib.sha256(source.encode()).hexdigest(),
                stored_errors=[o for o in c.get('outputs', []) if o.get('output_type') == 'error']))
    pd.DataFrame(inventory).to_csv(OUT/'inventario_celdas.csv', index=False, encoding='utf-8-sig')
    source_paths = [*sorted((ROOT/'src/geoau').glob('*.py')), *sorted((ROOT/'notebooks').glob('[0-9][0-9]_*.ipynb')),
                    *sorted((ROOT/'config').glob('*.yaml')), ROOT/'informes/PLAN_PROSPECTIVIDAD_AURIFERA_ESPANA.md']
    write('fuentes_analizadas_sha256.json', ev.records(ROOT, source_paths))
    f = ROOT/'reports/fase_f/20260909T184735_016759Z'
    e = ROOT/'reports/fase_e/20260909T124128_606717Z'
    d = ROOT/'reports/fase_d/20260909T104712_606095Z'
    comparison = pd.read_csv(f/'comparison_by_fold.csv')
    comparison.groupby('family')[['recovery_at_01','recovery_at_05','recovery_at_10','average_precision_PU','roc_auc_PU']].agg(['mean','std']).to_csv(OUT/'metricas_diagnosticas.csv')
    sensitivity = pd.read_csv(f/'sensitivity_metrics.csv')
    sensitivity.groupby('experiment')[['recovery_at_05','average_precision_PU']].mean().to_csv(OUT/'ablaciones_diagnosticas.csv')
    grid = pd.read_parquet(e/'territory.parquet')
    units = pd.read_parquet(e/'design/spatial_units.parquet')
    hold = grid.merge(units, on='cell_id', validate='one_to_one')
    positives = pd.read_parquet(e/'design/selected_positive_records.parquet')
    obs = set(positives.cell_id)
    frames = [pd.read_parquet(f/f'evaluation/outer_{i:02d}.parquet') for i in range(5)]
    frame = pd.concat(frames, ignore_index=True)
    evidence = dict(notebooks=15, code_cells=len(inventory),
        executable_code_cells=sum(x['executable_statements'] > 0 for x in inventory),
        total_code_lines=sum(x['lines'] for x in inventory),
        eligible_cells=int(grid.eligible.sum()), holdout_eligible_cells=int((hold.holdout & hold.eligible).sum()),
        holdout_positive_cells=int((hold.holdout & hold.cell_id.isin(obs)).sum()),
        holdout_fraction_units=float(hold.groupby('unit_id').holdout.first().mean()),
        holdout_fraction_eligible_area=float(hold.loc[hold.holdout & hold.eligible,'land_area_m2'].sum()/hold.loc[hold.eligible,'land_area_m2'].sum()),
        oof_unique_cells=frame.cell_id.nunique(), oof_candidate_cells=int(frame.observed_P.sum()),
        models=len(list((f/'models').glob('*.joblib'))), predictions=len(list((f/'predictions').glob('*.parquet'))),
        sklearn_version=__import__('sklearn').__version__,
        optional_renderers={n:importlib.util.find_spec(n) is not None for n in ['markdown','markdown_it','docx']})
    meta = ev.read_json(next((f/'models').glob('*.json')))
    evidence['historical_sample_path'] = meta['sample_path']
    evidence['historical_sample_path_exists'] = Path(meta['sample_path']).exists()
    # Reproducción mínima del efecto real de la celda 11 de NB01 sobre la celda 10.
    import geopandas as gpd
    raw = gpd.read_file(ROOT/'IndiciosII.gpkg')
    from geoau.labels import normalize_indicios
    cfg = __import__('yaml').safe_load((ROOT/'config/labels.yaml').read_text(encoding='utf-8'))
    cfg['source_sha256'] = 'diagnostico_sin_exportacion'
    normalized = normalize_indicios(raw, cfg)
    normalized['conflicto_au'] = False
    evidence['conflict_column_before_nb01_cell11'] = 'conflicto_au' in normalized
    normalized = normalize_indicios(raw, cfg)
    evidence['conflict_column_after_nb01_cell11'] = 'conflicto_au' in normalized
    # Caso geométrico límite: solo una celda terrestre conserva el borde de costa.
    cell = np.array([shapely.box(10,10,20,20)], dtype=object)
    line = np.array([shapely.LineString([(10,10),(10,20)])], dtype=object)
    outer = shapely.box(0,0,100,100).boundary
    evidence['coastal_edge_synthetic'] = dict(real_length=10,computed_length=float(fd.line_lengths(line, cell, outer)[0]),
        scope='caso sintético de borde coincidente; no cuantifica el efecto en España')
    # En el modo validado actual, el pool U no excluye candidatos aún sin revisar.
    gg = pd.DataFrame({'cell_id':['reviewed','pending','far'],'x_center':[0,5000,10000],'y_center':[0,0,0]})
    membership = gg[['cell_id']].assign(role='train')
    _, pool = ev.background_pool(gg, membership, {'reviewed'}, 250, 1000)
    evidence['unreviewed_candidate_can_enter_validated_U'] = 'pending' in set(pool.cell_id)
    write('evidencias.json', evidence)
    outcomes=[]
    for phase in 'def':
        began=time.perf_counter()
        process=subprocess.run([sys.executable, str(ROOT/f'scripts/validar_fase_{phase}.py')], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace', timeout=300)
        (OUT/f'validacion_fase_{phase}.txt').write_text(process.stdout, encoding='utf-8')
        outcome=dict(phase=phase,exit_code=process.returncode,seconds=time.perf_counter()-began,
                     last_lines=process.stdout.splitlines()[-8:])
        outcomes.append(outcome); print(json.dumps(outcome,ensure_ascii=False),flush=True)
        write('resultado_validadores.json',outcomes)
    print(json.dumps(evidence,ensure_ascii=False,indent=2),flush=True)


if __name__ == '__main__':
    main()
