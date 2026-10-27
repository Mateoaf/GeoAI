"""Independent safeguards for NB29 semantics, null model, pairing and saved fits."""
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geoau.prospective_features import add_descriptors, match_pilot, ALLUVIAL, SPECTRAL
from geoau.prospective_experiment import random_capture_counts
from geoau.prospective_models import nested29, NEW_METHODS29
from geoau.controlled_system_models import fit_components


class ProspectiveTests(unittest.TestCase):
    def test_aluvial_uses_documented_unit_not_u000_and_preserves_missingness(self):
        x = pd.DataFrame({"litologia_u000_fraccion": [0., 1., 0., 0.],
            "litologia_u012_fraccion": [.8, .8, 0., np.nan], "dist_cauce_m": 100.,
            "pendiente_grados": 2., "tpi_1000m_m": -10., "ratio_alteracion_filica_swir": 1.5,
            "ratio_gossan_oxidos_hierro": 2., "ndvi_cobertura_vegetal": .2})
        out = add_descriptors(x)
        self.assertEqual(out.loc[0, ALLUVIAL], out.loc[1, ALLUVIAL])
        self.assertGreater(out.loc[0, ALLUVIAL], out.loc[2, ALLUVIAL])
        self.assertTrue(np.isnan(out.loc[3, ALLUVIAL]))
        pd.testing.assert_frame_equal(out[x.columns], x)

    def test_spectral_proxy_attenuates_vegetation_without_global_fitted_statistics(self):
        x = pd.DataFrame({"litologia_u012_fraccion": .5, "dist_cauce_m": 100., "pendiente_grados": 1.,
            "tpi_1000m_m": 0., "ratio_alteracion_filica_swir": 2., "ratio_gossan_oxidos_hierro": 2.,
            "ndvi_cobertura_vegetal": [0., .5, 1., np.nan]})
        values = add_descriptors(x)[SPECTRAL]
        self.assertGreater(values.iloc[0], values.iloc[1])
        self.assertEqual(values.iloc[2], 0.)
        self.assertTrue(np.isnan(values.iloc[3]))
        self.assertEqual(add_descriptors(x.iloc[:1])[SPECTRAL].iloc[0], values.iloc[0])

    def test_random_reference_preserves_multicell_and_overlapping_deposits(self):
        rel = pd.DataFrame({"cell_id": ["c0", "c1", "c1"], "deposit_id": ["a", "a", "b"]})
        result = random_capture_counts(rel, 3, 1, 30000, 42)
        self.assertLess(abs(result.mean()-1.), .025)
        for count in [0, 1, 2]:
            self.assertLess(abs((result == count).mean()-1/3), .02)
        self.assertTrue((random_capture_counts(rel, 3, 3, 100, 42) == 2).all())
        self.assertTrue((random_capture_counts(rel, 3, 0, 100, 42) == 0).all())

    def test_pilot_triplets_are_complete_and_separated_and_constraints_not_relaxed(self):
        xy = [(10000, 10000), (25000, 10000), (40000, 10000), (60000, 60000), (75000, 60000), (90000, 60000)]
        x = pd.DataFrame({"cell_id": [f"c{i}" for i in range(6)], "x_center": [v[0] for v in xy],
            "y_center": [v[1] for v in xy], "substrate": "u012", "percentile": [.999, .825, .225, .998, .825, .225],
            "score": [.99, .7, .2, .98, .7, .2], "block_id": ["0_0"]*3+["1_1"]*3})
        out, rejected = match_pilot(x, target_pairs=3)
        self.assertEqual(len(out), 6)
        self.assertTrue(out.groupby("triplet_id").size().eq(3).all())
        self.assertTrue(out.cell_id.is_unique)
        # Removing low controls leaves no valid triplets; there is no fallback.
        out, rejected = match_pilot(x.loc[x.percentile.gt(.3)], target_pairs=3)
        self.assertTrue(out.empty)
        self.assertGreater(len(rejected), 0)

    def test_actual_fits_pair_with_nb27_and_saved_bundle_replays(self):
        rng = np.random.default_rng(123)
        ids = [f"c{i:03d}" for i in range(123)]
        cols = [f"geoq_{e}_representante_intervalo_log" for e in ["as", "sb", "bi", "w"]]
        cols += ["indice_pathfinders_oro", "litologia_u012_fraccion", "dist_cauce_m", "pendiente_grados",
            "tpi_1000m_m", "ratio_alteracion_filica_swir", "ratio_gossan_oxidos_hierro", "ndvi_cobertura_vegetal"]
        cols += [f"extra{i}" for i in range(95-len(cols))]
        base = pd.DataFrame(rng.uniform(.1, 2., (123, 95)), index=pd.Index(ids, name="cell_id"), columns=cols)
        base.indice_pathfinders_oro = np.nan
        X = add_descriptors(base)
        positives = pd.DataFrame({"cell_id": ids[:12], "peso_confianza": [.5, 1.]*6})
        data = SimpleNamespace(positives=positives, config={"geochemical_columns": []})
        systems = positives.copy()
        systems["primario"] = [True]*6+[False]*6
        systems["aluvial"] = ~systems.primario
        systems["epitermal"] = [True]*2+[False]*10
        systems["primario_otro"] = systems.primario & ~systems.epitermal
        pool = pd.DataFrame({"cell_id": ids[:120]})
        cfg = {"bags": 2, "minimum_specialist_P": 2, "prediction_batch_size": 100, "weight_step": .5,
            "classifier": {"n_estimators": 2, "max_depth": 2, "num_leaves": 3, "min_child_samples": 1,
                "verbosity": -1, "n_jobs": 1}, "epithermal_classifier": {}}
        def splits(pool, seed):
            master = pd.DataFrame({"cell_id": ids[:48], "label": [1]*12+[0]*36})
            memberships, parts = [], []
            for fold in range(3):
                test = master.loc[np.arange(48)%3 == fold]
                allowed = pool.loc[np.arange(len(pool))%3 != fold]
                parts.append((fold, allowed, test))
                memberships.append(pd.DataFrame({"cell_id": test.cell_id, "fold": fold, "role": "validation"}))
            return master, memberships, parts
        temp_root = Path(__file__).resolve().parents[1] / "tmp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as name:
            folder = Path(name).resolve()
            self.assertTrue(folder.is_relative_to(temp_root.resolve()))
            exp = SimpleNamespace(data=data, X=X, systems=systems, cfg=cfg, inner_splits=splits, log=lambda text: None)
            predictions = nested29(exp, pool, positives.cell_id, ids[120:], 42, folder, "cv", 0).set_index("cell_id")
            bundle = joblib.load(folder / "model.joblib")
            raw, _ = bundle.predict_components(X.loc[ids[120:]])
            replay, _ = bundle.combine(raw)
            for method in NEW_METHODS29:
                np.testing.assert_allclose(replay[method], predictions[method])
            self.assertAlmostEqual(bundle.predict(X.loc[ids[120:121]])[0], replay.max3_97.iloc[0], places=12)
            control_dir = folder / "control"
            fit_components(data, base, systems, pool, positives.cell_id, ids[120:], cfg, 42, control_dir, "cv", 0, "outer", lambda text: None)
            control = pd.read_parquet(control_dir / "training_outer.parquet")
            new = pd.read_parquet(folder / "training_outer.parquet")
            for member in range(2):
                expected = control.loc[control.component.eq("mono95") & control.member.eq(member), "cell_id"].tolist()
                for c in ["mono96_aluvial", "mono96_espectral", "mono97"]:
                    actual = new.loc[new.component.eq(c) & new.member.eq(member), "cell_id"].tolist()
                    self.assertEqual(actual, expected)
            for file in folder.glob("training_*.parquet"):
                frame = pd.read_parquet(file)
                self.assertFalse(set(frame.cell_id) & set(ids[120:]))


if __name__ == "__main__":
    unittest.main()
