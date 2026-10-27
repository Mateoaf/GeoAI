"""The 64-variable control must reproduce the original fit without extra features."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geoau.base_decoupling_models import fit_paired, BaseDecouplingBundle, COMPONENTS
from geoau.controlled_system_models import BackgroundCDF
from geoau.geochemical_experiment import select_sample, make_model, predict


class BaseControlTests(unittest.TestCase):
    def test_original_fit_exact_reproduction_and_paired_specialist_inference(self):
        ids = [f"c{i:03d}" for i in range(180)]
        rng = np.random.default_rng(17)
        original = pd.DataFrame(rng.normal(size=(180, 64)), index=ids, columns=[f"x{i}" for i in range(64)])
        original.index.name = "cell_id"
        extended = original.copy()
        for element in ["as", "sb", "bi", "w"]:
            extended[f"geoq_{element}_representante_intervalo_log"] = rng.normal(size=180)
        extended["indice_pathfinders_oro"] = np.nan
        for i in range(26):
            extended[f"additional{i}"] = rng.normal(size=180)
        grid = pd.DataFrame({"cell_id": ids, "block_id": np.arange(180)//10,
            "x_center": np.arange(180)*1000, "y_center": 0})
        positives = pd.DataFrame({"cell_id": ids[:12], "peso_confianza": [.5, 1.]*6})
        systems = positives.copy()
        systems["primario_otro"] = [False]*2+[True]*4+[False]*6
        systems["aluvial"] = [False]*6+[True]*4+[False]*2
        systems["epitermal"] = [False]*10+[True]*2
        data = SimpleNamespace(positives=positives, grid=grid, config={"u_per_p": 3,
            "geochemical_columns": [], "lightgbm_trees": 150, "n_jobs": 1})
        parameters = make_model(original.columns, [], "lightgbm", data.config, 42).named_steps["model"].get_params()
        parameters.pop("random_state")
        cfg = {"bags": 2, "minimum_specialist_P": 2, "classifier": parameters,
            "epithermal_classifier": {}, "prediction_batch_size": 30}
        pool = grid.iloc[:160]
        matrices = {64: original, 95: extended}
        tmp = Path(__file__).resolve().parents[1] / "tmp"
        tmp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp) as directory:
            folder = Path(directory)
            models, raw = fit_paired(data, matrices, systems, pool, ids[:12], ids[160:], cfg,
                42, folder, "cv", 0, "outer", lambda message: None)
            exact = []
            for member in range(2):
                sample = select_sample(data, pool.cell_id, 42+5000+101*member)
                model = make_model(original.columns, [], "lightgbm", data.config, 42+member)
                model.fit(original.loc[sample.cell_id], sample.label, model__sample_weight=sample.peso_confianza)
                exact.append(predict(model, original.loc[ids[160:]]))
            np.testing.assert_array_equal(raw.global64, np.column_stack(exact).mean(axis=1))
            for model in models["global64"]:
                self.assertNotIn("pathfinders_training_only", model.named_steps)
                self.assertEqual(list(model.named_steps["preprocess"].feature_names_in_), list(original))
            for model in models["global95"]:
                self.assertIn("pathfinders_training_only", model.named_steps)
            runs = pd.read_csv(folder / "fits_outer.csv")
            self.assertTrue(runs.groupby(["component", "member"]).ordered_sample_hash.nunique().eq(1).all())
            train = pd.read_parquet(folder / "training_outer.parquet")
            self.assertFalse(set(train.loc[train.label.eq(0), "cell_id"]) & set(positives.cell_id))
            for member in range(2):
                p = train.loc[train.component.eq("global") & train.member.eq(member) & train.label.eq(1), "cell_id"]
                self.assertEqual(set(p), set(positives.cell_id))  # unresolved P remain in global
            normalizers = {f"{c}{n}": BackgroundCDF().fit([.05, .2, .4, .8]) for n in [64,95] for c in COMPONENTS}
            bundle = BaseDecouplingBundle(models, normalizers, {n: X.columns for n, X in matrices.items()})
            joblib.dump(bundle, folder / "bundle.joblib")
            loaded = joblib.load(folder / "bundle.joblib")
            test = {n: X.loc[ids[160:]] for n, X in matrices.items()}
            expected = bundle.combine(raw.set_index("cell_id"))
            replay = loaded.combine(loaded.raw_predictions(test))
            for m in ["global64", "max3_64", "global95", "max3_95"]:
                np.testing.assert_array_equal(expected[m], replay[m])
            np.testing.assert_array_equal(loaded.predict({n: X.iloc[:1] for n, X in test.items()}), replay.max3_64.iloc[:1])


if __name__ == "__main__":
    unittest.main()
