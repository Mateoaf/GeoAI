"""Genera y ejecuta el notebook 18 del sistema GeoAI de 64 predictores."""
from actualizar_notebooks_geoquimica import update_notebooks


def build_and_run_notebook():
    update_notebooks([18], execute=True)


if __name__ == "__main__":
    build_and_run_notebook()
