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

## Iteración 2 · Trabajo siguiente

1. Reunir un conjunto **nuevo** de negativos para desarrollo, separado por identidad física o escena y sin reutilizar las 30 fotos de v1.
2. Mantener congelados el clasificador, el filtro v0.4.0 y sus resultados como línea base.
3. Comparar alternativas accesibles y conocidas: una clase negativa explícita, distancia de Mahalanobis o un detector sencillo entrenado con positivos y negativos. No introducir un método difícil de explicar sin beneficio medible.
4. Medir también el costo sobre piezas válidas: mejorar la detección de negativos no puede producir una cantidad inaceptable de falsas alarmas en impresos, manuscritos o pinturas.
5. Antes de abrir la nueva prueba, fijar por escrito métricas, umbrales y regla de adopción.
6. Capturar o reservar un segundo conjunto ciego, con objetos y escenas que no aparezcan en desarrollo, y ejecutarlo una sola vez.

La futura versión solo podrá declararse mejor si aumenta de forma medible la detección de entradas ajenas, conserva el desempeño con piezas válidas y cumple la regla de adopción predeclarada. Si no la cumple, se conserva v0.4.0 y se documenta el intento.

## Registro

| Fecha | Cambio | Efecto declarado |
|---|---|---|
| 2026-11-20 | Conjunto externo v1 saneado, protocolo, evaluador, resultados, figura y documentación | Establece una línea base externa reproducible y revela una debilidad; no modifica pesos, banco ni umbral |
