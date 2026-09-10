"""Auditoría independiente de claves, separación y muestras de la ejecución E."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from geoau import evaluation as ev


def main():
    out = ev.current_run(ROOT)
    cfg, grid, relations, spec, _ = ev.context(ROOT, out)
    ev.verify(out, ev.read_json(out/'outputs_manifest.json'))
    units = pd.read_parquet(out/'design/spatial_units.parquet').set_index('cell_id')
    selected, _ = ev.choose_labels(grid, relations, cfg)
    positive_ids = set(selected.cell_id)
    holdout = set(units.index[units.holdout])
    eligible = set(grid.loc[grid.eligible, 'cell_id'])
    coords = grid.set_index('cell_id')[['x_center', 'y_center']]
    summary = pd.read_csv(out/'sample_summary.csv')
    checked = 0
    for item in ev.read_json(out/'split_plan.json')['splits']:
        split_id = item['split_id']
        membership = pd.read_parquet(out/f'memberships/{split_id}.parquet')
        assert membership.cell_id.is_unique and membership.cell_id.equals(grid.cell_id)
        train = set(membership.loc[membership.role.eq('train'), 'cell_id'])
        test = set(membership.loc[membership.role.eq('test'), 'cell_id'])
        assert train and test and train <= eligible and test <= eligible
        assert not train & test and not (train | test) & holdout
        assert not set(units.loc[list(train), 'unit_id']) & set(units.loc[list(test), 'unit_id'])
        # Independiente del EDT del módulo: árbol de centros y cota de huellas.
        reference = test | holdout
        distance = cKDTree(coords.loc[sorted(reference)]).query(coords.loc[sorted(train)])[0]
        assert (distance - np.sqrt(2)*spec['resolution_m']).min() >= cfg['spatial_gap_m'] - 1e-7
        if item['level'] == 'inner':
            parent = pd.read_parquet(out/f"memberships/outer_{item['outer_fold']:02d}.parquet")
            assert train | test <= set(parent.loc[parent.role.eq('train'), 'cell_id'])
        train_p = train & positive_ids
        tree = cKDTree(coords.loc[sorted(train_p)])
        for row in summary[summary.split_id.eq(split_id)].itertuples(index=False):
            sample = pd.read_parquet(out/f'samples/{row.sample_id}.parquet')
            assert sample.cell_id.is_unique and set(sample.cell_id) <= train
            p = sample[sample.sample_class.eq(1)]
            u = sample[sample.sample_class.eq(0)]
            assert len(p) == row.n_P and len(u) == row.n_U
            assert set(p.cell_id) == train_p and not set(u.cell_id) & train_p
            assert u.sample_role.eq('U_unlabelled').all()
            assert p.sample_role.eq('P_candidate_proxy' if cfg['mode'] == 'diagnostic' else 'P_reviewed').all()
            assert sample.inclusion_probability.between(0, 1, inclusive='right').all()
            np.testing.assert_allclose(sample.inverse_inclusion_weight, 1/sample.inclusion_probability)
            np.testing.assert_allclose(u.area_weight_m2, u.land_area_m2/u.inclusion_probability)
            lower = np.maximum(0, tree.query(coords.loc[u.cell_id])[0] - np.sqrt(2)*spec['resolution_m'])
            assert lower.min() >= cfg['background_buffer_m'] - 1e-7
            if cfg['mode'] == 'diagnostic': assert not sample.training_allowed.any()
            checked += 1
        print('Verificado:', split_id, flush=True)
    print(f'OK: {checked} muestras; hashes, anidamiento, reserva, distancias, etiquetas y pesos.')


if __name__ == '__main__': main()
