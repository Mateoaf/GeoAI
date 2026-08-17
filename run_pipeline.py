"""
GeoAI Hispania v2.0 - Master Pipeline CLI
Ejecución integral y reproducible del pipeline científico de prospectividad mineral.
"""
import sys
import argparse
import subprocess
import logging
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_pipeline")

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable

def run_step(description: str, cmd_args: list):
    """Ejecuta un paso del pipeline verificando código de salida."""
    print("\n" + "=" * 80, flush=True)
    print(f"🚀 {description}", flush=True)
    print("=" * 80, flush=True)
    
    result = subprocess.run([PYTHON_EXE] + cmd_args, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        logger.error(f"Error en paso: {description} (código {result.returncode})")
        sys.exit(result.returncode)
    else:
        logger.info(f"Paso completado con éxito: {description}")

def main():
    parser = argparse.ArgumentParser(
        description="GeoAI Hispania v2.0: Pipeline Científico de Prospectividad Mineral (MPM)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--all", action="store_true", help="Ejecuta el pipeline completo (Dataset + Modelos + Mapas + Tests)")
    parser.add_argument("--dataset", action="store_true", help="Genera el dataset maestro v2 con geodatos 100% observados")
    parser.add_argument("--train", action="store_true", help="Ejecuta Spatial CV, Ablation, LODO, Calibración y Modelado")
    parser.add_argument("--map", action="store_true", help="Genera los visores cartográficos interactivos HTML v2")
    parser.add_argument("--tests", action="store_true", help="Ejecuta la suite de 20 tests unitarios y de integración")
    
    args = parser.parse_args()
    
    if not any([args.all, args.dataset, args.train, args.map, args.tests]):
        parser.print_help()
        sys.exit(0)
        
    if args.all or args.dataset:
        run_step("1/4. Generación de Dataset Maestro v2 (IGME + Copernicus DEM)", ["src/build_ml_dataset_v2.py"])
        
    if args.all or args.train:
        run_step("2/4. Validación Espacial, Calibración, LODO y Modelado v2", ["src/run_spatial_experiments_v2.py"])
        
    if args.all or args.map:
        run_step("3/4. Generación de Visores Cartográficos Interactivos v2", ["src/build_interactive_map_v2.py"])
        
    if args.all or args.tests:
        run_step("4/4. Ejecución de Tests Automatizados de Robustez GeoAI v2", ["-m", "unittest", "tests/test_geoai_hardened_suite.py"])
        
    print("\n" + "=" * 80)
    print("🎉 ¡PIPELINE GeoAI Hispania v2.0 EJECUTADO Y COMPLETADO SATISFACTORIAMENTE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
