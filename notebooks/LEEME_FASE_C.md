# Ejecutar 02_rejilla_armonizacion_cobertura

Abre `02_rejilla_armonizacion_cobertura.ipynb`, selecciona
`.venv-fase-a/Scripts/python.exe` y ejecuta todas las celdas en orden.
Utiliza las mismas dependencias de A y B; no necesita instalar paquetes nuevos.

Desde la raíz del proyecto:

```powershell
.\.venv-fase-a\Scripts\python.exe scripts/ejecutar_notebook_02.py
.\.venv-fase-a\Scripts\python.exe -m unittest discover -s tests -v
```

El ejecutor guarda las salidas del notebook solo si termina correctamente. Los
productos se escriben en `reports/fase_c/<fecha-hora-UTC>/`; un directorio incompleto
mantiene `estado_ejecucion=en_curso` y no sirve de entrada aceptada para otra fase.
Procesar las ocho familias vectoriales completas puede tardar varios minutos y
escribe varios GB. Cada ejecución crea un directorio nuevo y conserva los anteriores.

La configuración está en `config/grid.yaml`. El código reutilizable está en
`src/geoau/territory.py`. `scripts/crear_notebook_02.py` es el generador del cuaderno:
**no hace falta ejecutarlo para usar el notebook** y sobrescribe sus celdas/salidas.

## Entradas y continuidad

Se fija la ejecución B `20260906T172408_668076Z`, que a su vez referencia la ejecución
A `20260906T142956_752136Z`. Para usar una revisión posterior, cambia `phase_b_run`.
No depende de variables del kernel, ni modifica `labels.py`, ni los notebooks 00/01.

Se verifican al inicio y al final los hashes de las fuentes inventariadas por A.
Se congelan además los productos de B utilizados, la nueva máscara, configuración
y código. B no selló sus productos mediante un manifiesto de hashes: el sello de C
acredita su estado al iniciar C, no retrospectivamente el momento en que B los creó.

Se incorporó una fuente independiente de límites:
`data/raw/territorio/ES-region-01m-4326-2024.geojson`, con URL, consulta, hash y
condiciones en `provenance.json`. El notebook usa esa copia local, sin descargas
implícitas al volver a ejecutarlo. Es GISCO Countries 2024, escala 1:1.000.000,
**máscara regional candidata**, pendiente de contraste con límites más detallados.

© EuroGeographics para los límites administrativos. Las
[condiciones específicas de GISCO](https://ec.europa.eu/eurostat/web/gisco/geodata/administrative-units)
exigen atribución y contemplan uso no comercial. No se acredita autorización comercial
de esta máscara ni de sus derivados. Se puede sustituir por otra fuente, adaptando
el cargador y la procedencia; un cambio territorial exige revisar la versión de rejilla.

## Correspondencia con el plan

| Paso | Implementación |
|---|---|
| 13 | Máscara continental independiente; inventario de componentes fuera del ámbito; rejilla de 1 km, IDs estables, área terrestre y política costera |
| 14 | Diccionario de soporte común para P/U/inferencia, NoData y estado de cada variable |
| 15 | Ocho familias separadas en UTM30; lotes por FID e índice espacial, margen 20 km, conversión 2D, reparación y registro de cambios |
| 16 | Diez rásteres: coincidencia exacta de soporte 500 m, agregación a 1 km, clases enteras/moda/proporciones y elevación media |
| 17 | `coverage.gpkg`, diagnóstico por familia y bloques de 50 km, decisiones, mapa, correspondencia Au–celda y revisión puntual de huecos |

## Productos principales

| Archivo dentro de cada ejecución | Uso |
|---|---|
| `grid_1km.csv.gz` y `grid_spec.json` | Rejilla reconstruible; fila, columna, centro, área y versión |
| `feature_dictionary.csv` | Soporte de extracción; distingue armonización de predictores pendientes |
| `vectors/*.gpkg` | Capas geométricamente saneadas, con atributos y FID de origen |
| `vectors/*_geometry_changes.csv` | Reparaciones, cambios de tipo y cuarentenas; consultar original por FID |
| `vector_harmonization.csv` | Recuentos, CRS, advertencias, paginación y cobertura estimada/solapes |
| `rasters/*_1km.tif` | Rásteres alineados, fracción válida y representaciones de clase |
| `raster_alignment.csv` | Métodos, coincidencia de píxel y áreas válidas |
| `coverage.gpkg` | Máscara peninsular, componentes españolas y polígonos de estados |
| `coverage_by_cell.csv.gz` | Disponibilidad por celda, decisión y recuentos de candidatos/revisados |
| `coverage_by_scope_family.csv` | Área válida/huecos por familia, península y bloques diagnósticos |
| `coverage_decisions.csv` | Superficie y registros en cada estado |
| `indicios_celda_cobertura.csv` | Relación registro–celda sin uniones que multipliquen filas |
| `revision_au_sin_geoquimica.csv` | Casos sin geoquímica puntual, estado celular y decisión conservadora |
| `contraste_cobertura_puntual_B_C.csv` | Contraste reproducible con el muestreo de fase B |
| `distorsion_crs.csv` | Sensibilidad métrica UTM30 en una muestra espacial y extremos |
| `mapa_cobertura.png` | Cobertura candidata; no favorabilidad |
| `control_cierre.json`, `outputs_manifest.json` | Estado técnico/científico y sello SHA-256 de productos |

## Interpretación y límites

Todas las celdas con tierra se conservan. La elegibilidad costera inicial exige 50 %
terrestre. La disponibilidad por familia exige 95 % del área terrestre con dato.
Ambos umbrales se fijan en configuración antes de modelizar; no se ajustan para
rescatar positivos o mejorar métricas. Una celda con varios indicios sigue siendo
una fila. El centro de extracción es el mismo en P/U/inferencia.

El área terrestre es la intersección exacta con la máscara candidata en UTM30.
La cobertura de polígonos geológicos es una **estimación por centros de 500 m**:
no tiene la misma precisión que un overlay poligonal exacto. Los solapes y huecos
necesitan revisión por hoja y dominio. En líneas, tener o no una traza no acredita
si se ha cartografiado el entorno; su cobertura de levantamiento queda desconocida.

La conversión de curvas tiene tolerancia angular explícita y contraste muestral
1°/0,5°. No equivale a garantizar un error métrico global. Z/M se descartan para el
uso 2D y los originales se preservan. La clasificación de fallas/contactos/bordes,
la deduplicación GEODE–MAGNA y las equivalencias geológicas son trabajo de D.

La geoquímica conserva clase 0 válida y no interpola códigos. Moda y proporciones
son alternativas de representación; las concentraciones representativas no pasan
a ser mediciones continuas. La elevación se agrega desde banda 1; no se reutilizan
como definitivos pendiente/TPI/TRI antiguos. Los huecos puntuales Au no se rellenan
con cero ni se borran los indicios por carecer de dato.

`fase_c_cientifica_cerrada=false` y `prediction_allowed=false` conservan pendientes
reales: máscara candidata, cobertura de levantamiento, revisión geométrica/semántica
y etiquetas sin revisión geológica. No hay modelo ni predicciones. Islas y enclaves
quedan fuera de esta rejilla; se inventarían sin atribuirles cobertura peninsular.
