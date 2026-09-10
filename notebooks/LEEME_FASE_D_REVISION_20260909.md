# Fase D revisada · 9 de septiembre de 2026

Esta es la guía vigente para los cuadernos 03–06 y la construcción de
`Grid_Master_Au`. La revisión parte de la ejecución incompleta
`20260909T085704_618911Z` y del plan, pasos 18–26. Las ejecuciones anteriores se
conservan; la ruta vigente se consulta en `reports/fase_d/current_run.json`.

## Problemas corregidos

1. El 03 tenía dos celdas de inicio que creaban ejecuciones diferentes. Ahora hay
   una y usa `ensure_run`: continúa una ejecución compatible o inicia otra si
   cambia el código/configuración.
2. La ejecución abierta no contenía el bloque de geología. Se añadió recuperación
   auditada desde otras ejecuciones con funciones de cálculo, parámetros, fuentes
   y rejilla equivalentes. No se copian Parquet sin verificar sus manifiestos.
3. La reutilización de geología estaba desactivada en el código. Se restauró.
4. El 06 mostraba una ejecución antigua. Se limpiaron salidas obsoletas y se
   ejecuta de nuevo sobre la misma ruta que 03–05.
5. Una celda exploratoria del 04 descartaba clases cero. Ahora filtra con
   `notna()`: cero es una clase válida, no una ausencia de dato.
6. El control RGB exacto rechazaba diferencias mínimas de exportación. Ahora se
   exige distancia máxima 2 y margen mínimo 10 frente al segundo color de clase.
   Las discrepancias de 8 niveles de Zn/W siguen excluidas y cuantificadas.
7. El reparto de longitud sobre bordes compartidos reducía también a la mitad
   las trazas del borde exterior. Se distingue el contorno exterior de la rejilla
   de los bordes entre celdas/teselas. Se elimina además ruido FFT inferior a
   `1e-7` metros de longitud; no se transforma NoData en cero.
8. El maestro inicial contenía solo X y no estaba particionado. Ahora se exportan
   maestro completo, X independiente y dataset Parquet particionado.

Las copias de los cuadernos anteriores a esta revisión están en
`reports/revision_fase_d_20260909/antes/`. Se conservaron las celdas exploratorias
añadidas por el usuario; la celda que eliminaba clase cero fue corregida.

## Ejecutar

Seleccionar `.venv-fase-a` en VS Code. Desde **Proyecto Con Luis**, PowerShell:

```powershell
& '.\.venv-fase-a\Scripts\python.exe' -m pip install -r requirements-fase-d.txt
& '.\.venv-fase-a\Scripts\python.exe' scripts/ejecutar_notebooks_fase_d.py
```

Orden: 03 geología/estructuras → 04 geoquímica → 05 relieve/hidrografía → 06 matriz.
No es necesario repetir A–C. Cada cuaderno imprime su ejecución. Para continuar:

```powershell
& '.\.venv-fase-a\Scripts\python.exe' scripts/ejecutar_notebooks_fase_d.py --desde 4
```

Si cambian parámetros o código, comenzar por 03. `reuse_audit.json` explica qué
bloques se recuperaron y su procedencia. El código utilizado en la ejecución
original de cada bloque recuperado se conserva también en el nuevo directorio.
Las entradas modificadas se rechazan; no se actualizan sus hashes para aceptarlas.

## Métodos y alcance

**Geología:** intersecciones exactas con la parte terrestre de cada celda, unión
por categoría, control de solapes entre categorías y de atributos vacíos. Fracción
respecto a tierra, no respecto al área cartografiada. Soporte mínimo 95 %;
solapes tolerados hasta `max(1 m², área terrestre × 1e-6)`. Las unidades mixtas se
conservan. En 06 se añaden asociaciones explícitas para granitoides, unidades
mixtas con granitoides, volcanitas, básicas/ultrabásicas, gneisses y unidades con
gravas/arenas/limos. El diccionario documenta la correspondencia por descripción,
no por códigos numéricos arbitrarios. Son superficies de unidades, no porcentajes
internos de roca; tampoco identifican automáticamente terrazas ni metasedimentos.

**Estructuras:** GEODE como única fuente de trazas de V1; no suma MAGNA duplicado.
Diccionario textual de fallas/cizallas, cabalgamientos y contactos intrusivos,
cartografiados o supuestos. «Cartografiado» no certifica observación de campo.
Distancias del centro a trazas dentro de 10 km; sin coincidencia, NaN y bandera.
La ausencia de traza no acredita cobertura de levantamiento.

Las densidades a 1/5/10 km siguen siendo **aproximadas**: longitud por celda de
1 km, nodada/disuelta para no sumar coincidencias exactas, agregada mediante pesos
círculo/celda y dividida por área terrestre del mismo soporte. Se supone reparto
uniforme subcelda. No son intersecciones exactas con cada círculo. Conservar ese
carácter experimental, especialmente en radio 1 km.

**Geoquímica:** paletas leídas de constantes locales mediante AST, sin ejecutar
scripts históricos. El umbral RGB 2 admite diferencias de un nivel en dos canales;
el margen 10 rechaza colores ambiguos. Se cuantifican coincidencias exactas y
tolerancias 2/8 sobre tierra. No se amplía el umbral a 8 para recuperar todos los
píxeles sin revisar la discrepancia. Au/As/Sb/Bi se conservan; Hg/Cu/Pb recuperan
las pequeñas diferencias de exportación. Zn/W mantienen huecos. Esto no valida
leyendas oficiales, medio de muestreo, extracción ni concentraciones. Las columnas
son clases modales o proporciones alternativas; no ratios ni logaritmos químicos.

**Relieve:** banda 1 de elevación a 500 m; pendiente por diferencias centrales,
TPI z−media circular incluyendo el centro, desviación estándar poblacional local
(no TRI), radios 1/5 km. Vecindarios válidos al 95 %, sin rellenar huecos con cero
ni reflejar terreno en bordes. Se agregan después a 1 km por área terrestre válida.

**Hidrografía:** distancia y densidad de red regional con las mismas limitaciones
de soporte lineal. No equivale a un modelo aluvial detallado.

**Extensiones:** el plan presenta intersecciones/orientación, geoquímica analítica,
geofísica y análisis aluvial detallado como ampliaciones condicionadas. Se conservan
en `pending_extensions.json`: no se fabrican anomalías desde líneas de vuelo,
propiedades desde localizaciones ni terrazas desde recintos cuaternarios genéricos.

## Grid_Master_Au y tablas auxiliares

- `Grid_Master_Au.parquet`: una fila por celda, con predictores, rejilla, cobertura,
  calidad y etiquetas. **No usar todas sus columnas como X.**
- `Grid_Master_Au/`: los mismos registros en dataset particionado por
  `partition_id = row // 100`. Son bandas de almacenamiento, no folds espaciales.
- `grid_spec.json`: CRS, resolución, origen y ámbito heredados de C para
  reconstruir la geometría de las celdas fuera del proyecto original.
- `X_features.parquet`: `cell_id` y únicamente predictores candidatos.
- `calidad_y_soporte.parquet`: coordenadas, soporte D, coberturas C con prefijo
  `fase_c_`, elegibilidad y controles; no predictores por defecto.
- `etiquetas_por_celda.parquet`: recuentos y estados P revisado/candidato/U.
- `relacion_indicios_celda.parquet`: todos los indicios de C y los atributos de B
  necesarios para tipo de Au, depósito, distrito y grupos de proximidad. Incluye
  los registros fuera de máscara con `cell_id` vacío.
- `relacion_deposit_id_celda.parquet`, `relacion_district_id_celda.parquet`,
  `relacion_proximity_group_500m_celda.parquet`: relaciones sin duplicados. Los
  grupos de proximidad no se convierten automáticamente en depósitos.
- `column_roles.csv`: clave, predictor candidato, etiqueta o auxiliar.
- `feature_allowlist.json`: candidatos explícitos; aprobados para entrenar aún
  vacíos mientras falten revisión semántica y etiquetas validadas.
- `feature_sets.json`: base, geoquímica modal 4/9 y proporciones alternativas;
  identifica variables constantes o completamente ausentes para revisión.
- `variables_qc.csv`, `soporte_modelos.csv`, diccionarios, manifiestos y control final.

La elegibilidad `eligible_geology_terrain` exige costa admitida, litología y edad
válidas y elevación/pendiente disponibles. `eligible_geo4` y `eligible_geo9` añaden
las clases modales de esos elementos. No se exige que toda distancia sea finita:
NaN puede indicar ausencia de traza en el radio, no un fallo de extracción.
Estos criterios describen soporte, no autorización científica de predicción.

Ejemplo de lectura:

```python
from pathlib import Path
import json
import pandas as pd
ROOT = Path.cwd()  # raíz Proyecto Con Luis; adaptar si se abre desde notebooks
RUN = ROOT / json.loads((ROOT / 'reports/fase_d/current_run.json').read_text())['run']
X = pd.read_parquet(RUN / 'X_features.parquet')
master_part = pd.read_parquet(RUN / 'Grid_Master_Au', filters=[('partition_id', '==', 0)])
roles = pd.read_csv(RUN / 'column_roles.csv')
```

No se imputan valores, no se generan negativos ni particiones de evaluación, ni
se entrena RF. Eso corresponde a E/F. La fase puede estar técnicamente completada
y conservar `fase_d_cientifica_cerrada=false` y `prediction_allowed=false`.

## Verificación

```powershell
& '.\.venv-fase-a\Scripts\python.exe' -m unittest discover -s tests -p test_features.py -v
& '.\.venv-fase-a\Scripts\python.exe' scripts/validar_fase_d.py
```

Pruebas: geometría y solapes, bordes compartidos/exteriores, distancias truncadas,
plano/huecos topográficos, clase cero, tolerancia RGB y ambigüedad, integridad de
hashes, cambio de funciones de cálculo, proporciones inválidas, agregación de
varios indicios y separación X/etiquetas. El validador revisa productos reales y
equivalencia de claves entre maestro único, particionado y X.
