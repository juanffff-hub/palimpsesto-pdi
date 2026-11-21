# Validación y fallos — evidencia y recuperación

Esta matriz delimita lo implementado. Ningún conjunto finito de pruebas demuestra ausencia de todos los errores posibles. La aplicación está diseñada para demostración local supervisada, una pieza plana por foto, con entradas JPG/PNG.

| Entrada o situación | Comportamiento y recuperación | Evidencia |
|---|---|---|
| Sin archivo, archivo vacío, varios archivos arrastrados | Mensaje en español; permanece en carga | Python + navegador |
| PDF/BMP/texto renombrado JPG, corrupción/truncamiento | Valida formato real y decodificación; rechaza | Python + navegador |
| Más de 40 MiB, más de 40 megapíxeles, lado menor de 64 px | Rechazo antes de procesamiento costoso | Python; límites de píxeles simulados en test |
| PNG animado | Pide una imagen estática | Python |
| EXIF de orientación o canal alfa | Reorienta RGB; compone alfa sobre blanco; conserva original | Python |
| Imagen vacía/casi uniforme | Rechazo con petición de nueva captura | Python |
| Poca resolución, oscuridad, sobreexposición, pocos bordes | Aviso orientativo; revisar detalle o repetir captura | Reglas explícitas; no diagnóstico de fidelidad |
| Contenido ajeno a las piezas conocidas | Alerta de alcance; oculta clase y puntuaciones cuando se activa; exige confirmación explícita y categoría manual | Pruebas stub + evaluación real + gato en navegador |
| Escena desconocida que no activa alerta | Puede pasar: confirmación de una pieza plana obligatoria en interfaz | v0.4.0: 17/30 casos externos no alertados (`results/scope/external_negatives_v1.json`). v2: 2/18 en la prueba ciega, ambos negativos difíciles (`results/scope_v2/blind.json`) |
| Retrato/pintura de retrato | Detector de presencia de rostro puede pedir revisión; no identifica personas | Heurística auxiliar, sin métrica aislada |
| JSON roto/no objeto, campos desconocidos o faltantes | 400/415 con mensaje; no procesa | Python |
| NaN/infinito, booleanos, null, listas, texto, valor fuera de rango | Rechaza antes de transformar | Python |
| Proporción | Solo 0 (estimada) o 0,1–10; inválida mantiene encuadre y permite corregir | Python + navegador |
| Cuatro esquinas repetidas, cruzadas, no convexas, fuera de foto, área mínima insuficiente, orden invertido | Rechaza geometría; usuario ajusta en canvas/teclado | Python |
| Borde neuronal incorrecto/ausente | Redetectar, contornos o borde manual; cuatro puntos revisables | Integración real + controles UI |
| Binarización de pintura | Control deshabilitado y API rechaza | Python |
| Cambio de esquinas/clase/proporción después de procesar | Invalida exportación; pide procesar de nuevo | Python + navegador |
| Enlace de resultado viejo o pestaña con otra foto | Tokens de imagen/revisión impiden mezclar resultados | Python; también vistas previas |
| Acciones simultáneas | Cola frontend y exclusión mutua del servidor local; rotación no modifica una imagen durante proceso | Test concurrente Python |
| Sesión expirada (1 h sin actividad), sin foto, límite de ocho sesiones | Mensaje, recarga o reinicio; sesiones aisladas | Python para aislamiento/expiración; límite explícito |
| Faltan pesos o pesos corruptos | Estado de IA informa degradación; modo manual/contornos; no simula inferencia | Python |
| Banco de alcance de otro modelo/manifiesto | Se desactiva filtro, informa falta de correspondencia; recalibrar | Verificación hash en carga |
| Conexión fallida / respuesta no JSON / demora >90 s | Mensaje y reintento; controles no quedan bloqueados | Corte de conexión probado en navegador; ramas de timeout/JSON implementadas |
| Ruta/método/formato exportación inexistente | Respuesta controlada; exportación válida posterior funciona | Python |
| Aviso fuera de la vista (página desplazada, celular) | Avisos fijos dentro de la ventana, bajo la cabecera si está visible; máximo 2 en celular y 4 en escritorio; error con icono, título, efecto y acción | Navegador 390 px desplazado + escritorio |
| Falla al procesar con resultado anterior en pantalla | Franja «Vista previa desactualizada», imagen atenuada, exportación bloqueada, botón Reintentar | Navegador |
| Sesión sin foto o foto cambiada en otra pestaña | Código `session`; el aviso ofrece «Cargar otra foto» en vez de un reintento inútil | Python + comprobación manual en navegador |
| Operación larga | Tiempo real transcurrido desde 2 s; «Dejar de esperar» desde 8 s; aviso de demora desde 20 s; sin porcentajes inventados | Navegador (retardo simulado de 3,2 s) |
| Descartar foto con trabajo hecho | Diálogo de confirmación, foco en «Seguir trabajando»; Escape cancela | Navegador |
| Error inesperado | Mensaje genérico al usuario, traza en consola para diagnosticar | Manejador global; no afirmar prueba de toda excepción posible |
| Cambios demasiado fuertes | Antes/después, detalle, deshacer, ajustes en cero o rechazar | Navegador; cero conserva píxeles RGB |
| No hay referencia limpia real | SSIM/PSNR no se inventan; aparecen no disponibles | Python + reportes |
| Original y salida confundidos | ZIP conserva bytes originales y SHA256; derivados separados | Python y nueve casos reales |

## Qué se ejecutó

`python scripts/check.py`: 113 tests (incluye `tests/test_public_demo.py`, `tests/test_weights.py`: descarga, reemplazo de pesos viejos y ZIP corrupto, y `tests/test_capture.py`: desenfoque, temblor, poca luz, exceso de luz, reflejo frente a franja blanca, pieza cortada, pieza pequeña y funcionamiento sin U-Net, y `tests/test_border_confidence.py`: borde nítido, contorno difuso, puntos que no encajan, imagen de la máscara y API, y `tests/test_tones.py`: histograma, recorte medido píxel a píxel, píxeles ya saturados, binarización e imagen del recorte, y `tests/test_scope_v2.py`: recorte de la pieza, alerta por probabilidad, respaldo sin cabeza o sin máscara, confirmación obligatoria y correspondencia de la cabeza con el clasificador), incluyendo contratos parametrizados, homografía, EXIF, sesión, concurrencia y recuperación. Los tests API unitarios usan stubs: no miden calidad de red.

`python scripts/verify_real_pipeline.py --root RUTA`: nueve imágenes, una por bloque de prueba y tres por clase, con ambos checkpoints reales; comprueba salida PNG/PDF/JSON/ZIP y original. No sustituye revisión de trazos. `results/integration/real_pipeline.json` contiene cada caso.

`npm run test:ui` con servidor iniciado: 22 comprobaciones en Chrome/Playwright; anchos 320, 390, 768, 1024 y 1440; confirmación, valores inválidos con mensaje junto al campo, fallo de conexión y botón Reintentar del aviso, vista previa desactualizada, espera larga con tiempo transcurrido, error persistente frente a confirmación temporal, avisos sin duplicados, regiones para lector de pantalla, Escape, diálogo de descarte con foco en la opción segura, celular con la página desplazada (aviso dentro de la ventana y sin tapar el botón principal), movimiento reducido, detalle, deshacer, cuatro descargas, invalidación de resultado y foto ajena. `results/browser/verification.json` registra ausencia/presencia de errores JS. Requiere Node, `npm install` y Chrome; `CHROME_PATH` admite otra ruta. Playwright es solo herramienta de prueba.

`python scripts/evaluate_scope.py --root RUTA`: 10 negativos de conveniencia, 72 positivos provisionales y un escaneo externo. Resultado 9/10 alertas negativas, 0/72 y 0/1 positivas. **Un negativo pasa.** No es una estimación robusta de sensibilidad/especificidad en población abierta. La cara del astronaut no fue advertida por la heurística auxiliar de esta configuración. El umbral no se eligió con estos negativos.

`python scripts/develop_scope_v2.py --root RUTA --neg RUTA_NEGATIVOS_DESARROLLO`: comparación del control de alcance con validación por grupos (88 negativos y 408 positivos de desarrollo). Elegido: recorte de la pieza + regresión logística, con 79/88 negativos alertados y 395/408 válidas aceptadas (v0.4.0: 46/88). `scripts/evaluate_scope_blind_v2.py` corrió una sola vez, con autorización expresa y comprobando los hashes congelados: 16/18 alertados (6/6, 6/6, 4/6) y 72/72 positivos de regresión. Antes, un primer intento se detuvo al cargar una imagen de más de 40 MP sin producir predicciones; solo se corrigió el cargador del ejecutor (enmienda 1).

`python scripts/evaluate_scope_external.py --data RUTA_NEGATIVOS`: 30 negativos propios congelados antes de inferir, 10 por etiqueta. Resultado 13/30 alertados (43,3 %): escenas 3/10, objetos tridimensionales 8/10 y negativos difíciles 2/10. No se cambió el umbral, el banco, los pesos ni la selección tras observar las salidas. El conjunto queda reservado como prueba y no debe reutilizarse para optimizar. Ver protocolo, JSON y CSV en `results/scope/`.

## Límites funcionales que deben explicarse en la sustentación

No se recupera información tapada, quemada o fuera de foco. No se garantizan colorimetría patrimonial, autenticidad, OCR ni reconstrucción documental. La homografía no aplana páginas curvas y la proporción automática no conoce dimensiones físicas. Pueden fallar clase/borde/alcance; por eso la revisión no es decorativa. La prueba externa evidencia que el alcance automático no reemplaza la confirmación humana. Las identidades físicas del dataset de piezas tampoco están certificadas. La aplicación no está endurecida como servicio público multiusuario.

Para cualquier fallo nuevo registrar foto original (con autorización), pasos, versión, parámetros, esperado/observado y resultado tras corregir. Añadir un test que reproduzca el defecto cuando sea estable y significativo, y conservar también el caso de fallo en el informe académico.
