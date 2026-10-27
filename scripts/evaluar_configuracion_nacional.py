"""Evalúa la receta nacional con los pliegues y territorios originales, sin modificar mapas."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geoau.geochemical_experiment import load_data, sha256
from geoau.national_evaluation import run_evaluation, validate_evaluation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/evaluacion_configuracion_nacional_20261021"))
    parser.add_argument("--report", type=Path, default=Path("informes/evaluacion_configuracion_nacional_20261021/INFORME_EVALUACION_CONFIGURACION_NACIONAL.md"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    report = (ROOT / args.report).resolve()
    if args.validate_only:
        manifest = json.loads((output / "outputs_manifest.json").read_text(encoding="utf-8"))
        for name, expected in manifest.items():
            if sha256(output / name) != expected:
                raise AssertionError(f"Artefacto modificado: {name}")
        for name, expected in json.loads((output / "code_manifest.json").read_text(encoding="utf-8")).items():
            if sha256(ROOT / name) != expected:
                raise AssertionError(f"Código modificado: {name}")
        result = validate_evaluation(load_data(ROOT), output)
        print(f"Validación correcta: {result['n_checks']} comprobaciones, {result['models_replayed']} modelos reproducidos")
    else:
        run_evaluation(ROOT, output, report)


if __name__ == "__main__":
    main()
