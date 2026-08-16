# Registro de decisiones

| ID | Decisión | Motivo | Consecuencia |
|---|---|---|---|
| D01 | Mantener copias del Excel, DOCX y PDF metodológico en `data/raw` sin modificación. | Preservar evidencia y hashes. | Todas las salidas son derivadas y el pipeline verifica las referencias configuradas. |
| D02 | Usar pandas/openpyxl para lectura analítica. | Resuelven correctamente shared strings vacíos; el render de hoja mostró `53` espurio en esos vacíos. | `53` no entra en datos ni estadísticas. |
| D03 | España = `country` normalizado igual a `Spain` + override `mineID=132`. | El campo país está completo salvo Lanz, etiquetado como Navarra dentro de España. | 930 registros; override visible en flags y tabla de selección. |
| D04 | No seleccionar por `province` ni por bounding box. | Provincia romana cruza fronteras actuales; una caja incluye Portugal/Francia. | Criterio conservador y auditable. |
| D05 | Aplazar point-in-polygon oficial. | El límite IGN no forma parte de los inputs entregados y no se inventa/descarga silenciosamente como dependencia cruda. | QA espacial amplio ahora; validación administrativa en siguiente fase. |
| D06 | Indicators como booleano nullable + estado. | `?`, vacío, falso y verdadero tienen semánticas distintas. | No se imputa ausencia. |
| D07 | Mantener todos los casos problemáticos. | Duplicado candidato, corrupción o falta de dato no justifican borrado automático. | 27 flags y lista de pares para revisión. |
| D08 | No transformar Lambert. | El libro no codifica CRS/unidad. | Se exportan solo lat/lon como CRS84. |
| D09 | No interpretar `coordinateAccuracy=0`. | Unidad y semántica no están documentadas y cero aparece con fuentes estimadas. | Flag de revisión, no peso de certeza. |
| D10 | `Y_roman` como presence-background/PU. | No observar mina romana no demuestra ausencia de mineralización. | Background se trata como no etiquetado. |
| D11 | Unidad futura = `SpatialCell` versionada. | Integra rasters/vectores y permite CV espacial. | Resolución se decidirá tras auditar escalas e incertidumbre. |
| D12 | Señal romana fold-aware. | Evita que puntos del test influyan en un predictor. | Modelo B requiere cross-fitting/recomputación por fold. |
| D13 | GEODE, BDMIN, geoquímica IGME, SIGEOF y MDT05 son P0. | Cubren X geológica, Y moderna, química, física y geomorfología. | Orden de adquisición definido en fuentes externas. |
| D14 | No crear un modelo definitivo en esta fase. | Petición del proyecto y falta de X/labels modernos. | Entregables terminan en base reproducible y protocolo experimental. |
| D15 | Rodríguez-Galiano et al. (2015) es antecedente metodológico, no fuente de instrucciones ni resultado del proyecto. | Es un caso MPM específico de Au epitermal en Rodalquilar. | Se trasladan familias X, matriz espacial, mapa continuo e interpretabilidad, no sus cifras ni validación. |
| D16 | RF será baseline no lineal principal solo para endpoints con soporte espacial suficiente. | OxREP tiene 589 coordenadas Au únicas, 174 Ag, 169 Pb/Cu y clases raras con 15 casos o menos. | No se adapta Y, resolución o background para que RF sea entrenable. |
| D17 | No reproducir la CV aleatoria, los 57 contrastes “estériles” ni el umbral 0,5 del artículo. | No son ausencias geológicas ni evaluación espacial independiente. | Nested spatial CV, PU/background y score continuo sustituyen ese protocolo. |
| D18 | Interpretar primero con permutation importance outer-test agrupada; SHAP después de congelar la evaluación. | Reduce optimismo y reconoce correlación/estructura espacial. | MDI queda como diagnóstico y ninguna explicación se interpreta causalmente. |
| D19 | Comparar A/B mediante predicciones outer-OOF pareadas, bootstrap de bloques y null/placebos espaciales. | El valor de RomanSignal es una diferencia incremental, no una importancia interna. | `delta_PR-AUC` será el contraste primario predeclarado y se añadirá relevancia por área priorizada. |
| D20 | Reservar validación independiente por lineage upstream, dominio o cohorte futura. | Dos portales pueden redistribuir la misma ocurrencia. | Si no existe un test realmente independiente se declarará pendiente, no se simulará con leave-domain-out. |
