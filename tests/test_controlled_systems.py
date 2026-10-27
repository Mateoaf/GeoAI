"""Leakage, conservative typing and mixture invariants for the NB27 experiment."""
from pathlib import Path
import sys
import unittest
import tempfile
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geoau.controlled_system_features import audit_systems, FoldPathfinders
from geoau.controlled_system_models import BackgroundCDF, blend, choose_weights, fit_nested, METHODS


class ControlledSystemTests(unittest.TestCase):
    def test_province_is_not_an_epithermal_label_and_unknowns_are_not_rock(self):
        records = pd.DataFrame({"cell_id": ["darro", "unknown", "cinto", "mixed", "mixed"],
            "tipo_au_revisado": ["aluvial", "desconocido", "roca", "roca", "aluvial"],
            "deposit_id": ["dep_california_granadina_darro", None, "dep_rodalquilar_cinto", None, None],
            "Provincia": ["GRANADA", "ALMERIA", "ALMERIA", "LEON", "LEON"]})
        positives = pd.DataFrame({"cell_id": ["darro", "unknown", "cinto", "mixed"], "peso_confianza": 1.})
        _, cells, _ = audit_systems(records, positives)
        cells = cells.set_index("cell_id")
        self.assertFalse(cells.loc["darro", "epitermal"])
        self.assertTrue(cells.loc["unknown", "no_resuelto"])
        self.assertFalse(cells.loc["unknown", "primario"])
        self.assertTrue(cells.loc["cinto", "epitermal"])
        self.assertFalse(cells.loc["cinto", "primario_otro"])
        self.assertTrue(cells.loc["mixed", "mixto"])

    def test_background_scale_is_independent_of_test_batch_and_preserves_tails(self):
        normalizer = BackgroundCDF().fit([.1, .2, .2, .4])
        first = normalizer.transform([.3])[0]
        self.assertEqual(first, normalizer.transform([.3, .99, .001])[0])
        self.assertTrue(np.all(np.diff(normalizer.transform([.41, .5, .9, .99])) > 0))
        self.assertTrue(np.isnan(normalizer.transform([np.nan])[0]))
        self.assertFalse(BackgroundCDF().fit([np.nan]).available_)

    def test_pathfinder_statistics_are_frozen_after_training(self):
        names = [f"geoq_{e}_representante_intervalo_log" for e in ["as", "sb", "bi", "w"]]
        train = pd.DataFrame({n: [1., 2., 3.] for n in names})
        transform = FoldPathfinders().fit(train)
        mean = transform.mean_.copy()
        test = pd.DataFrame({n: [1000., np.nan] for n in names})
        result = transform.transform(test)
        pd.testing.assert_series_equal(mean, transform.mean_)
        self.assertTrue(np.isnan(result.indice_pathfinders_oro.iloc[1]))
        self.assertGreater(result.indice_pathfinders_oro.iloc[0], 100)

    def test_missing_specialist_renormalizes_weights_without_erasing_global(self):
        matrix = np.array([[.2, np.nan, .8], [.3, .6, np.nan]])
        np.testing.assert_allclose(blend(matrix, [.2, .3, .5]), [(.04+.4)/.7, (.06+.18)/.5])
        w, search = choose_weights([0, 1, 0, 1], np.array([[.1, np.nan], [.9, .8], [.2, .3], [.8, np.nan]]), .5)
        self.assertGreaterEqual(w[0], .1)
        self.assertAlmostEqual(w.sum(), 1)
        self.assertEqual(search.selected.sum(), 1)

    def test_nested_fit_replays_and_never_trains_the_outer_evaluation_cells(self):
        ids = [f"c{i:03d}" for i in range(123)]
        rng = np.random.default_rng(17)
        names = [f"geoq_{e}_representante_intervalo_log" for e in ["as", "sb", "bi", "w"]]
        names += ["indice_pathfinders_oro", "trampa_valle_aluvial", "vector_epitermal_hidrotermal",
                  "volcanismo_neogeno", "ratio_alteracion_filica_swir", "ratio_gossan_oxidos_hierro",
                  "dist_falla_cartografiada_m"]
        names += [f"litologia_u{k:03d}_fraccion" for k in [8, 11, 14, 15, 16]]
        names += [f"extra{i}" for i in range(95-len(names))]
        X = pd.DataFrame(rng.uniform(.1, .9, (123, 95)), index=ids, columns=names)
        X["indice_pathfinders_oro"] = np.nan
        positives = pd.DataFrame({"cell_id": ids[:12], "peso_confianza": [.5, 1.]*6})
        data = SimpleNamespace(positives=positives, config={"geochemical_columns": []})
        systems = positives.copy()
        systems["primario"] = [True]*6+[False]*6
        systems["aluvial"] = ~systems.primario
        systems["epitermal"] = [True]*2+[False]*10
        systems["primario_otro"] = systems.primario & ~systems.epitermal
        pool = pd.DataFrame({"cell_id": ids[:120]})
        cfg = {"bags": 2, "minimum_specialist_P": 2, "prediction_batch_size": 50, "weight_step": .5,
            "classifier": {"n_estimators": 2, "max_depth": 2, "num_leaves": 3,
                           "min_child_samples": 1, "verbosity": -1, "n_jobs": 1},
            "epithermal_classifier": {}}
        def splits(outer_pool, seed):
            master = pd.DataFrame({"cell_id": ids[:48], "label": [1]*12+[0]*36})
            roles, parts = [], []
            for fold in range(3):
                test = master.loc[np.arange(48)%3 == fold]
                allowed = outer_pool.loc[np.arange(len(outer_pool))%3 != fold]
                parts.append((fold, allowed, test))
                roles.append(pd.DataFrame({"cell_id": test.cell_id, "fold": fold, "role": "validation"}))
            return master, roles, parts
        temp_root = Path(__file__).resolve().parents[1] / "tmp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            folder = Path(directory).resolve()
            self.assertTrue(folder.is_relative_to(temp_root.resolve()))
            model, predictions = fit_nested(data, X, systems, pool, ids[:12], ids[120:],
                cfg, 42, folder, "cv", 0, splits, lambda message: None)
            raw, _ = model.predict_raw(X.loc[ids[120:]])
            replay, _ = model.combine(raw, X.loc[ids[120:]])
            for method in METHODS:
                np.testing.assert_allclose(replay[method], predictions[method])
            for file in folder.glob("training_*.parquet"):
                training = pd.read_parquet(file)
                self.assertFalse(set(training.cell_id) & set(ids[120:]))


if __name__ == "__main__":
    unittest.main()
