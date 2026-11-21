# Progreso del control de alcance

Este documento registra iteraciones verificables del mecanismo que advierte cuando una fotografía no parece corresponder a un impreso, manuscrito o pintura plana. Una iteración solo cuenta como mejora cuando supera una regla fijada antes de mirar la prueba. Los resultados adversos también se conservan: permiten corregir el sistema sin ocultar sus límites.

## Estado inicial

El sistema v0.4.0 usa un banco de 408 *embeddings* de desarrollo y la media de sus tres similitudes coseno máximas. El umbral se calibró con positivos de desarrollo, no con los negativos externos. La comprobación inicial con diez imágenes públicas de conveniencia alertó 9/10, una muestra demasiado pequeña y homogénea para estimar el comportamiento ante entradas reales.

## Iteración 1 · Línea base externa (20 de noviembre de 2026)

**Objetivo.** Medir el filtro actual con fotografías ajenas al dominio, tomadas con celular y no usadas durante entrenamiento o calibración.

**Datos.** De 78 fotografías legibles se seleccionaron visualmente 30 antes de consultar el modelo, una por objeto físico o escena: 10 escenas, 10 objetos tridimensionales y 10 negativos difíciles. La copia pública elimina EXIF/GPS, modelo de cámara y nombres originales. El manifiesto conserva descripción, etiqueta y SHA-256 de cada archivo.

**Regla predeclarada.** `documentar_sin_recalibrar` requería al menos 27/30 alertas y 8/10 por etiqueta; `ampliar_desarrollo`, al menos 24/30 y 6/10 por etiqueta; cualquier resultado inferior activa `revision_prioritaria`.

**Resultado reproducible.** El filtro alertó 13/30 (43,3 %):

| Etiqueta | Alertas | No alertadas |
|---|---:|---:|
| Escenas | 3/10 | 7/10 |
| Objetos tridimensionales | 8/10 | 2/10 |
| Negativos difíciles | 2/10 | 8/10 |
| **Total** | **13/30** | **17/30** |

**Decisión.** `revision_prioritaria`. Esta iteración mejora el conocimiento y la validación del sistema, pero **no mejora todavía su desempeño**. La interfaz debe conservar la confirmación explícita de que existe una sola pieza plana admitida. Las 30 fotos quedan congeladas y no pueden usarse para ajustar el método y volver a presentarse como prueba independiente.

**Evidencia.** `data/external_negative_scope_v1.csv`, `results/scope/external_negatives_v1_protocol.json`, `results/scope/external_negatives_v1.json`, `results/scope/external_negatives_v1.csv`, `results/figures/negativos_externos_v1.jpg` y `scripts/evaluate_scope_external.py`.

## Iteración 2 · Desarrollo del control v2 (20 de noviembre de 2026)

**Objetivo.** Mejorar el rechazo de entradas ajenas sin perder piezas válidas, con datos nuevos de desarrollo y sin tocar los 30 negativos v1 ni la prueba ciega v2.

**Datos.**
- **Negativos de desarrollo:** 88 nuevos (`01_desarrollo_negativos_v2`): 21 escenas, 52 objetos tridimensionales y 15 negativos difíciles, sin EXIF. Se agruparon a ojo en **47 identidades** que comparten objeto o lugar (misma mesa de vidrio, sofá, taller, tienda…; `data/scope_negatives_dev_v2.csv`).
- **Positivos de ajuste:** las 408 fotos de desarrollo del manifiesto (41 bloques).
- **Regresión positiva:** las 72 de diagnóstico, descritas como conjunto reutilizado.
- **Referencia:** los 30 negativos v1 solo se informan, porque ya se habían abierto.
- **Prueba ciega:** la carpeta `02_prueba_ciega_negativos_v2_NO_ABRIR` no se abrió, listó ni evaluó.
- **Dataset externo positivo:** no se incorporó. No había uno rápido de verificar cuyas imágenes representaran fotos de celular de documentos, manuscritos y pinturas dentro del alcance; se usaron los positivos existentes, como permitía la instrucción.

**Protocolo de comparación** (`scripts/develop_scope_v2.py`). Se usa el encoder ResNet18 congelado del clasificador, con rasgos de 512 normalizados L2. La validación cruzada es de 5 folds `StratifiedGroupKFold` (semilla 2026), sin repartir piezas ni identidades. Para cada método, el umbral es el que acepta el 97 % de las válidas fuera de fold, el mismo criterio de percentil 3 de la v0.4.0. La elección predeclarada toma, de más sencilla a más compleja, la primera familia que cumple la puerta de desarrollo; dentro de ella, la C con más negativos alertados.

**Intento 2a · rasgos de la foto entera (descartado).**

| Método | Negativos alertados | Válidas aceptadas |
|---|---:|---:|
| v0.4.0 · similitud top-3 | 46/88 | 395/408 |
| Regresión logística (C = 0,01 a 10) | 41–45/88 | 395/408 |
| Mahalanobis (Ledoit-Wolf) | 30/88 | 395/408 |

Ninguno supera la línea base. Diagnóstico: las válidas y las ajenas comparten interiores, y la pieza ocupa un 38 % de la foto. Los rasgos de la foto entera describen sobre todo el fondo.

**Intento 2b · rasgos del recorte de la pieza (elegido).** Se recorta con la U-Net la caja de su mayor región (+5 %, `models.piece_crop`):

| Método | Negativos alertados | Escenas | Objetos 3D | Difíciles | Válidas aceptadas | Peor clase |
|---|---:|---:|---:|---:|---:|---:|
| Mahalanobis | 68/88 | 17/21 | 39/52 | 12/15 | 395/408 | 91,2 % |
| **Regresión logística, C = 10** | **79/88** | **17/21** | **50/52** | **12/15** | **395/408** | **90,4 % (pintura)** |
| Regresión, recorte + 5 descriptores de máscara | 80/88 | 17/21 | 50/52 | 13/15 | 395/408 | 91,2 % |

La regresión sobre el recorte cumple la puerta: ≥ 85 % de negativos, ≥ 95 % de válidas, ≥ 90 % por clase, mejora clara frente a v0.4.0 y unos 33 ms en CPU. Se elige por ser la más sencilla que cumple. Con recorte + máscara apenas se gana un negativo a cambio de más complejidad, así que no se adopta.
- **Regresión positiva:** 72/72.
- **Referencia v1, ya abierta:** alertaría 27/30 en lugar de 13/30.
- **Siguen fallando, fuera de fold:**
  - Válidas rechazadas: 13 pinturas. Diez son del mismo cuadro alto (PIN010), además de I0333, I0337 (PIN004) e I0344 (PIN005).
  - Ajenas no alertadas: DEV006 puesto de computador, DEV013 sofá, DEV015 lámpara, DEV025 puerta, DEV033 portátil sobre mesa, DEV038 regla, DEV069 jardinera, DEV070 caja de taladro y DEV086 corona en una puerta.

**Congelado antes de la prueba ciega.** Commit `b3a7ad1` (`results/scope_v2/protocol_blind.json`). Incluye el método, C = 10, el umbral de probabilidad de pieza válida 0,306, la regla y los SHA-256 de `models/scope_head.npz`, del clasificador, de la U-Net, del código y de los manifiestos. `scripts/evaluate_scope_blind_v2.py` solo corre con `--autorizado`, una vez y si nada congelado cambió.

**Regla de la prueba ciega.** Al menos 15/18 negativos alertados, al menos 4/6 por grupo y al menos 95 % de aceptación en la regresión positiva. Si se cumple, se adopta v2 y se conserva la confirmación manual. Si mejora sin cumplir, se conserva como experimento y se vuelve a v0.4.0. Si empeora, se rechaza.

**Estado.** Mejora observada **solo en desarrollo**; pendiente de la prueba ciega autorizada.

## Iteración 3 · Prueba ciega v2

*Pendiente de autorización expresa del equipo.*

## Registro

| Fecha | Cambio | Efecto declarado |
|---|---|---|
| 2026-11-20 | Conjunto externo v1 saneado, protocolo, evaluador, resultados, figura y documentación | Establece una línea base externa reproducible y revela una debilidad; no modifica pesos, banco ni umbral |
| 2026-11-20 | Negativos de desarrollo v2 agrupados, comparación de métodos, control v2 (recorte + regresión logística) y protocolo ciego congelado (`b3a7ad1`) | Mejora observada en desarrollo (46/88 → 79/88 con 97 % de válidas aceptadas); pendiente de prueba ciega |
