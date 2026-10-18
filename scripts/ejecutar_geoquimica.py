"""Ejecuta el flujo GeoAI de 64 predictores, con ocho variables geoquímicas."""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from geoau.geochemical_experiment import run_experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--stage", choices=["all", "audit", "benchmark", "diagnostics", "rotations", "maps", "fusion", "report"], default="all")
    args = parser.parse_args()
    data = run_experiment(ROOT, args.config, args.stage)
    print(f"Completado {args.stage}: {data.output}", flush=True)


if __name__ == "__main__":
    main()
