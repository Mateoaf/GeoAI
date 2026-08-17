# 📋 Registro de Decisiones Metodológicas y de Arquitectura (Decision Log)

**Proyecto:** GeoAI - Mineral Prospectivity Mapping (MPM)  
**Repositorio:** `https://github.com/Mateoaf/GeoAI.git`  

---

## DECISIÓN 01: Eliminación Total de Proxies Sintéticos y Heurísticas Ocultas
* **Fecha:** 2026-08-17
* **Contexto:** Las variables geoquímicas ($As, Sb, Cu, Pb, Zn$) y espectrales ($Gossan, Sericita$) del prototipo inicial se calcularon condicionadas por el commodity minero (target leakage).
* **Decisión:** Purgar completamente estas columnas del dataset de entrenamiento v2. Ninguna variable sintética o inferida por reglas fijas formará parte de los modelos finales.
* **Impacto:** Las métricas de entrenamiento reflejan el rendimiento real de las variables observadas (litología, estructuras tectónicas reales, altimetría/geomorfología DEM), eliminando el sobreajuste artificial.

---

## DECISIÓN 02: Geometría Vectorial de Fallas y Contactos IGME
* **Fecha:** 2026-08-17
* **Contexto:** La función de inferencia anterior construía el árbol espacial KDTree usando las coordenadas de las minas conocidas, provocando fuga de proximidad minera.
* **Decisión:** Descargar y cachear las geometrías lineales oficiales del IGME (Capa 2 del Mapa Geológico 1M: Fallas, Cabalgamientos y Contactos). El cálculo de `dist_fault_m` y `fault_density` se realiza calculando la distancia euclidiana y densidad espacial respecto a las líneas estructurales reales del IGME en EPSG:25830.
* **Impacto:** Inferencia estructural geológicamente real y libre de leakage con respecto a los yacimientos conocidos.

---

## DECISIÓN 03: Desacoplamiento de Targets: Mineralización Moderna vs. Explotación Romana
* **Fecha:** 2026-08-17
* **Contexto:** OxREP documenta exclusivamente la minería histórica romana, la cual presenta sesgos tecnológicos, arqueológicos y de accesibilidad antiguos.
* **Decisión:** Definir dos targets independientes:
  1. `Y_modern_deposit`: Ground truth geológico de depósitos e indicios minerales inventariados en bases modernas (IGME BDMIN / EuroGeoSurveys). Target principal para MPM greenfield.
  2. `Y_roman_exploitation`: Evidencia arqueometalúrgica histórica de OxREP v3.0, utilizada para estudiar patrones arqueológicos y como conjunto de validación externa.
* **Impacto:** Claridad conceptual rigurosa que no confunde historia humana con geología del subsuelo.

---

## DECISIÓN 04: Estrategia de Validación Espacial (Spatial Block CV & LODO)
* **Fecha:** 2026-08-17
* **Contexto:** La validación cruzada aleatoria estándar (Random K-Fold) produce fuga de autocorrelación espacial cuando muestras del mismo distrito minero caen en train y test.
* **Decisión:** 
  1. **Spatial Block Cross-Validation (5 Bloques Geográficos)** asegurando que cada fold contenga suficientes positivos y negativos para calcular ROC-AUC y PR-AUC.
  2. **Leave-One-District-Out (LODO):** Excluir distritos completos (ej. Noroeste Aurífero, Faja Pirítica, Sierra Morena) durante el entrenamiento para verificar si el modelo transfiere firmas geológicas a regiones no vistas.
  3. **Ablation Test de Coordenadas:** Entrenar modelos con y sin `Coord_X`/`Coord_Y` para cuantificar la dependencia de la posición geográfica absoluta.
* **Impacto:** Métricas de rendimiento honestas y capacidad de generalización territorial demostrable.

---

## DECISIÓN 05: Unificación Arquitectónica (Single-Pipeline Architecture)
* **Fecha:** 2026-08-17
* **Contexto:** Existía divergencia entre cómo se generaban las variables en los scripts de preprocesamiento y cómo se evaluaban en la inferencia web.
* **Decisión:** Crear el módulo `src/geoai_roman_spain/features/extractor.py`. La misma función `extract_features_for_point(lat, lon)` es utilizada para construir el dataset de entrenamiento y para servir inferencias en tiempo real.
* **Impacto:** Cero discrepancia training-serving y reproducibilidad total.

---

## DECISIÓN 06: Terminología y Salidas Probabilísticas
* **Fecha:** 2026-08-17
* **Contexto:** Las salidas del modelo se comunicaban como "probabilidad de que exista una mina".
* **Decisión:** Reformular las salidas como **Prospectivity Score / Favorabilidad Geológica Relativa** en escala 0.0 a 1.0, acompañada del nivel de confianza geológica e índices de incertidumbre espacial.
* **Impacto:** Precisión estadística y prevención de interpretaciones erróneas en exploración mineral.
