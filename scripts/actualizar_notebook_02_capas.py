"""Extiende el notebook sin eliminar celdas exploratorias añadidas por el usuario."""
from pathlib import Path
import nbformat


def extend_notebook(nb):
    marker = '## 7b. Capas recuperadas'
    if any(c.cell_type == 'markdown' and marker in c.source for c in nb.cells):
        return nb
    for cell in nb.cells:
        if cell.cell_type == 'markdown':
            cell.source = cell.source.replace('ocho familias vectoriales saneadas',
                'ocho familias vectoriales base y ocho capas recuperadas saneadas')
    position = next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and
                    'fracciones_vector, control_vectores = harmonize_vectors' in c.source) + 1
    extra = [nbformat.v4.new_markdown_cell('''## 7b. Capas recuperadas — pasos 14–17

La fase A del 8/9/2026 ya inventaría estas ocho capas con datos. Se usan las copias
del proyecto, comprobadas por SHA-256; no se mezclan con los GPKG vacíos anteriores.
La caché base solo se reutiliza si sus ocho fuentes, algoritmo, máscara y parámetros
geométricos coinciden. Un cambio de etiquetas o la adición de otras familias no
invalida por sí solo esas geometrías. Cada producto reutilizado se verifica por hash.

| Capa | Contenido observado | Tratamiento en C |
|---|---|---|
| Magnetometría/radiometría | 3.811 líneas de vuelo | Conservar trazas y campaña; `VALU_LINE` no se interpreta como anomalía |
| Magnetotelúrica | 73 sitios, perfiles y archivos EDI | Presencia de sitios; sin inferir resistividad ni profundidad |
| Petrofísica | 2.780 localizaciones con referencias | Sin inferir propiedades físicas ausentes en los atributos |
| Gravimetría | 241.355 puntos y `VALU_BOU267` | Conservar valores y diagnóstico; unidades, correcciones y centinelas pendientes |
| Buzamientos | 225.450 puntos Z y simbología | Pasar a 2D conservando Z original; no equiparar ROTATION a dirección sin leyenda |
| Medidas estructurales | 251.654 líneas con DIRECCION/BUZAMIENTO | Conservar geometría y ángulos; revisar rangos; no usar longitud del símbolo como falla |
| Cuaternario | 44.464 polígonos | Huella temática; auxiliares no equivalen automáticamente a terrazas |
| Zonas GEODE | 28 polígonos con códigos/nombres | Ámbitos cartográficos; no son distritos metalogenéticos validados |

Se leen todas las filas en lotes y se distinguen geometrías inválidas de geometrías
fuera del ámbito más margen. Las extensiones insulares se registran fuera del ámbito
peninsular, sin reasignar CRS por conjetura. Los campos angulares y físicos se conservan;
los controles de rango son diagnósticos, no correcciones automáticas.

**La ocupación de una celda por un punto o una traza no es cobertura del levantamiento.**
La huella de cuaternario tampoco permite etiquetar su exterior como ausencia de ese
material. Se generan diagnósticos separados y no se convierten estas ocho capas en
requisitos del conjunto básico ni se interpolan superficies geofísicas.
'''), nbformat.v4.new_code_cell('''from geoau.additional_layers import harmonize_additional
control_adicionales = harmonize_additional(ROOT, FUENTES, mascara, area_terrestre_500m, SPEC, RUN_DIR)
display(control_adicionales[["familia", "source_features", "kept_with_margin", "invalid_before",
                              "quarantine_count", "outside_scope_margin", "support_role"]])
display(pd.read_csv(RUN_DIR / "additional_attribute_qc.csv"))
''')]
    nb.cells[position:position]=extra
    position = next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and
                    'grid_cobertura, cobertura_ambitos, decisiones, indicios_celda, estados = coverage_products' in c.source)+1
    nb.cells[position:position]=[nbformat.v4.new_markdown_cell('''### Cobertura complementaria y relación espacial

`additional_support_by_scope.csv` resume presencia/huella por península y bloque de
50 km. En puntos y líneas no se informa un área válida inventada. Los campos se añaden
a `coverage_by_cell.csv.gz` como `entity_present_*` o `footprint_*`, separados de `valid_*`.
`indicios_zonas_cuaternario.csv` contiene intersecciones exactas entre puntos Au y
polígonos, incluyendo solapes y falta de intersección sin convertirla en ausencia.
`coverage.gpkg` añade `huella_zonasgeode` y `huella_cuaternariorecintos`.
'''), nbformat.v4.new_code_cell('''soporte_adicional = pd.read_csv(RUN_DIR / "additional_support_by_scope.csv")
display(soporte_adicional[soporte_adicional.ambito.eq("peninsula")])
relaciones = pd.read_csv(RUN_DIR / "indicios_zonas_cuaternario.csv")
display(relaciones.groupby(["familia","estado"]).record_id.nunique().to_frame("registros_distintos"))
''')]
    position = next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and 'control = finish_run(' in c.source)
    nb.cells[position].source='assert control_adicionales.pagination_complete.all()\n'+nb.cells[position].source
    return nb


if __name__=='__main__':
    path=Path(__file__).resolve().parents[1]/'notebooks/02_rejilla_armonizacion_cobertura.ipynb'
    nb=extend_notebook(nbformat.read(path,4))
    nbformat.validate(nb)
    nbformat.write(nb,path)
