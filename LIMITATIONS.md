# Declaración de Limitaciones Científicas y Metodológicas: GeoAI-Au v1.0

## 1. Introducción y Marco de Honestidad Intelectual

El proyecto **GeoAI-Au v1.0** se ha desarrollado bajo los principios de máxima transparencia metodológica, auditabilidad y reproducibilidad. En el ámbito del Mapeo de Prospectividad Mineral (MPM) mediante Aprendizaje Automático, el rigor científico exige explicitar detalladamente las restricciones estructurales, estadísticas y geológicas del sistema para evitar interpretaciones erróneas o sobreestimaciones de su capacidad predictiva.

---

## 2. Limitaciones Estadísticas y de Tamaño Muestral

### 2.1. Tamaño Muestral del Inventario Auditado ($N=45$ Depósitos Modelables)
- **Restricción**: A diferencia de aplicaciones de Machine Learning en dominios de datos masivos (visión por computador o procesamiento de lenguaje), la geología económica en España peninsular cuenta con un número finito y físicamente limitado de yacimientos auríferos documentados.
- **Impacto**: Tras la rigurosa auditoría de Fase B y el filtrado por máscara de soporte de Fase D, existen exactamente **45 depósitos independientes modelables** distribuidos en 32 distritos metalogenéticos.
- **Consecuencia**: Ajustar un modelo sobre 37 depósitos de desarrollo y evaluar sobre 8 depósitos de holdout introduce una alta varianza intrínseca en cualquier estimador estadístico.

### 2.2. Potencia Estadística en la Evaluación Ciega ($N=8$ Depósitos de Test)
- **Granularidad Discreta**: Con solo 8 depósitos en la reserva ciega de Fase G, cada depósito individual acertado o fallado representa un escalón discreto de **12,50%** en la tasa de recuperación (`deposit_recovery`).
- **Incertidumbre Bootstrap**: Los intervalos de confianza bootstrap del 95% calculados sobre los 8 depósitos de test son amplios:
  - `deposit_recovery@1%`: $[0,00\%, 25,00\%]$ (media empírica: 12,50%).
  - `deposit_recovery@5%`: $[0,00\%, 37,50\%]$ (media empírica: 12,50%).
  - `deposit_recovery@10%`: $[0,00\%, 50,00\%]$ (media empírica: 25,00%).
- **Interpretación**: Las métricas de test ciego deben entenderse como una estimación puntual acotada por una banda de dispersión considerable debido al reducido número de grados de libertad.

---

## 3. Limitaciones Metalogenéticas y Geológicas

### 3.1. Extrema Heterogeneidad de Estilos Genéticos
En España peninsular, las mineralizaciones de oro no responden a un único sistema mineral, sino que engloban familias genéticas radicalmente diferentes:
1. **Orogénicos en Metasedimentos**: Filones de cuarzo encajados en pizarras y cuarcitas paleozoicas deformadas por la orogenia hercínica (Asturias, León, La Jara).
2. **Epitermales Volcánicos Neógenos**: Sistemas de alta sulfuración vinculados a magmatismo calcoalcalino terciario en el arco volcánico de Cabo de Gata (Rodalquilar).
3. **Sistemas Intrusivo-Relacionados y Skarns**: Mineralizaciones peribatolíticas de Au-Bi-As-W asociadas a plutonismo hercínico (Salave, Carles, Ossa Morena).
4. **Cizallas en Granitoides**: Estructuras frágil-dúctiles en macizos plutónicos y leucogranitos (Costa da Morte, Galicia).
5. **Placeres Aluviales Cuaternarios**: Concentraciones sedimentarias mecánicas en cuencas de drenaje actuales y terrazas (ríos Sil, Narcea, Miño, Genil).

**Limitación Epistemológica**: Un clasificador lineal único (`logistic_01`) proyecta un único hiperplano de decisión en $\mathbb{R}^{56}$. Aunque logra capturar con éxito las firmas volcánicas de Rodalquilar y las metasedimentarias de La Jara, no puede modelar con igual eficacia la multiplicidad de procesos fisicoquímicos que rigen cada tipología.

### 3.2. Ausencia de Capas Geoquímicas Aprobadas
- **Motivo de la Exclusión**: El Atlas Geoquímico de Sedimentos de Corriente disponible presentaba discontinuidades en franjas costeras y fronterizas, falta de ensayos cuantitativos continuos y una codificación cualitativa por intervalos de color que impedía su aprobación científica en Fase D sin riesgo de sesgos graves.
- **Consecuencia Práctica**: La prospección de depósitos en cizallas graníticas (como Corcoesto o Santa Comba en Galicia) depende críticamente de vectores de dispersión química secundaria (anomalías de As, Sb, Bi y Au). Al carecer de esta señal, el modelo lineal observa únicamente la unidad litológica regional "Otros granitoides" y la baja elevación costera, asignando pesos negativos y clasificando erróneamente estas zonas en rangos de favorabilidad bajos.

---

## 4. La Brecha de Transferencia Observada ($N=8$)

### 4.1. Descripción de la Discrepancia F → G
- **Rendimiento en Validación Cruzada Interna (Desarrollo, Fase F)**:
  - `ROC-AUC`: $0,7402 \pm 0,2054$
  - `deposit_recovery@5%`: $0,4389 \pm 0,1804$
- **Rendimiento en Evaluación Ciega Holdout (Test, Fase G)**:
  - `ROC-AUC`: $0,5807$
  - `deposit_recovery@5%`: $0,1250$ (1 / 8 depósitos)
  - `deposit_recovery@10%`: $0,2500$ (2 / 8 depósitos)

### 4.2. Interpretación Científica
Esta diferencia entre desarrollo y test se denomina formalmente **brecha de transferencia observada ($N=8$)**. No representa un fallo computacional ni un error de código, sino la manifestación empírica real de la autocorrelación espacial y la heterogeneidad regional. Cuando un modelo entrenado en 27 distritos se enfrenta a distritos completamente inéditos y geográficamente remotos, la capacidad de generalización disminuye sustancialmente si las tipologías geológicas de la reserva no están equilibradamente representadas en el entrenamiento.

---

## 5. Limitaciones Cartográficas y de Soporte Espacial

### 5.1. Resolución de Celda de 1 km²
- **Efecto de Soporte**: Toda la información geológica, estructural y topográfica se encuentra promediada o agregada a nivel de celda de 1 km² (100 hectáreas) sobre el dominio peninsular modelado.
- **Inaplicabilidad Directa**: La cartografía de favorabilidad identifica grandes bloques y corredores territoriales de interés, pero **no permite definir la traza exacta de un filón de 2 metros de potencia ni ubicar la boca de un sondeo de perforación**.

### 5.2. Escala de Fuentes Cartográficas
- La litología y cronoestratigrafía proceden del mapa continuo 1:200.000 (GEODE), y las fallas del mapa 1:1.000.000. Estructuras menores de segundo o tercer orden (claves para el control estructural del oro) no están reflejadas en estas capas regionales.

---

## 6. Interpretación de Coeficientes y No Causalidad

### 6.1. Hipótesis sobre el Signo de `dist_falla_cartografiada_m` ($\beta = +0,2122$)
- **Formulación Estricta como Hipótesis (No Mecanismo Demostrado)**: En el ajuste multivariante del modelo lineal regularizado, la distancia a fallas cartografiadas presenta un coeficiente estandarizado positivo ($\beta = +0,2122$, Odds Ratio = 1,236 por $+1\sigma$). Se postula como hipótesis que este comportamiento responde a la colinealidad multivariante en la regresión regularizada L2 cuando conviven otras variables estructurales (cabalgamientos y contactos intrusivos con coeficientes negativos), combinado con posibles artefactos de escala cartográfica (1:1.000.000) y la concentración del muestreo de fondo $U$ en zonas montañosas con densa fracturación cartografiada regional.
- **Advertencia**: Esto **no significa bajo ningún concepto que el oro 'evite' las fallas geológicas ni constituye un mecanismo físico demostrado**. **Queda terminantemente prohibido atribuir causalidad geológica a este coeficiente aislado**.

### 6.2. Anotación Post-Hoc de Depósitos Históricos
- En la tabla y capa vectorial de *Zonas de Prospectividad/Priorización*, las distancias a depósitos históricos más cercanos son **únicamente una anotación geográfica descriptiva post-hoc**. No formaron parte del vector de predictores $X$ ni intervinieron en el cálculo de las puntuaciones.
