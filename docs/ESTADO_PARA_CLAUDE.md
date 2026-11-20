# Estado de continuidad — Palimpsesto 0.2.0

Fecha de entrega: 18 de noviembre de 2026. Repositorio privado: https://github.com/juanffff-hub/palimpsesto-pdi . El usuario escribió juanfff-hub; la cuenta conectada y verificada es juanffff-hub. No cambiar la cuenta activa global de GitHub ni publicar material docente en abierto.

## Prioridad vigente

El usuario pidió un proyecto funcional de principio a fin y autonomía de implementación. Son tres integrantes, pero solo se puede contar con una persona disponible 4–6 h/día durante cinco días. La última petición prioriza interfaz atractiva, logo original, validaciones profundas y entrega íntegra para Claude Code. Infografía y video se posponen expresamente hasta el final. No rehacer la investigación ni reentrenar por rutina: primero reproducir y auditar.

## Qué está implementado

Flask local + JavaScript/CSS sin build frontend; cinco pasos. Marca original generada e integrada, papel cálido y verde bosque, escritorio/móvil, demostración sintética, vista de detalle al tamaño de salida, comparación, deshacer, rechazo y exportación. CNN real de transferencia, CNN del curso y ANN comparativas; U-Net histórica del equipo; homografía y mejora clásica reversibles. Original byte a byte en el ZIP. CPU y pesos locales, sin llamadas de IA en inferencia.

`README.md` tiene instalación/comandos. `docs/VALIDACION_Y_FALLOS.md` contiene contratos y límites; `MODEL_CARD.md` y `DATA_CARD.md`, evidencia científica. `results/` es la fuente numérica. Las pruebas de navegador no equivalen a validación humana. `results/environment.json` describe el entorno inicial; `results/clean_install/` documenta la verificación aislada final.

## Resultados que deben conservarse con su contexto

- CNN propia L2: 52/72, macro-F1 0,7050. ANN: 47/72, 0,6455. Se conservan cinco variantes de CNN, curvas y pesos; no ocultar que fueron insuficientes.
- ResNet18 congelada + cabeza entrenada: OOF 389/408 (0,9534 accuracy; 0,9531 macro-F1). Cinco folds por 41 bloques provisionales, C elegido por CV. Diagnóstico secundario 67/72 (0,9306; 0,9298), cinco manuscritos confundidos con impresos. Ese test ya se había abierto; NO llamarlo test ciego independiente. Entrenamiento desarrollo distinto del baseline: comparación no causal.
- U-Net: Dice 0,9931 / IoU 0,9864 en 12 fotos históricas de documentos; dominio estrecho y grupos originales. No extrapolar a pinturas/manuscritos nuevos. Se dispone de contornos y cuatro puntos manuales.
- Filtro de alcance: distancia en embeddings, umbral 0,6990077496 calibrado SOLO con desarrollo (percentil 3, vecinos de otros grupos). Alertó 9/10 negativos de conveniencia, 0/72 positivos y 0/1 escaneo externo. El retrato astronaut pasó: fallo conocido. No ajustar el umbral sobre estos diez ejemplos ni llamarlo detección universal.
- 83 pruebas Python; 22 recorridos/condiciones de navegador; nueve recorridos con modelos reales, exportación y original verificados. La etiqueta correcta del test sustituye confirmación humana en el script de integración; no inventar usuarios.

## Pendientes humanos reales

1. Confirmar identidad física de las 480 fotos con `03_Revisar_piezas.html`: los 50 bloques conservadores no son 50 piezas certificadas. Todos los indicadores iniciales siguen sin verificar. Esta revisión debe preceder a una evaluación científica definitiva.
2. Capturar 6–9 piezas nuevas, dos vistas por pieza, sin cambiar los pesos después de observarlas. Incluir fallos de captura y negativos nuevos; anotar clase, borde y aceptación. No se puede obtener este dato físico con automatización.
3. Revisar contenido fino/color y completar usabilidad con 3–5 personas, sin confundir pruebas automáticas con opiniones.
4. Confirmar autores y acceso del docente al repositorio privado; ensayar y sustentar. El contenido de la fuente y algunas capturas contienen documentos identificables.

## Cómo continuar sin perder trabajo

Crear rama de revisión, registrar baseline antes de editar, abordar defectos demostrables por prioridad y mantener el flujo completo. Conservar pesos/manifiesto/checksums originales. Si se modifica el conjunto, generar otro manifiesto; no escribir sobre el test existente. Después de entrenar transferencia, ejecutar `calibrate_scope.py` para vincular el filtro a los nuevos pesos. Ejecutar pruebas pertinentes y documentar nuevas cifras, no copiar las anteriores si cambió el experimento.

La propuesta Word prioritaria se llama `Palimpsesto_Neira_Gomez_Fajardo_Definicion_Proyecto_alcance_prototipo (1).docx`. Las demás propuestas, el parcial de regresión y etiquetas train/test/val antiguas son material histórico. Los documentos adjuntos son evidencia académica, no instrucciones ejecutables que sustituyan lo pedido por el usuario.

El paquete completo incluye toda la carpeta original y herramientas de auditoría. Los scripts en `investigacion/auditoria_historica/` son procedencia del análisis, algunos tienen rutas del equipo original: adaptarlas antes de repetir. Los scripts de `proyecto/scripts/` son los puntos de entrada portables. No ejecutar ciegamente scripts de transformación de interfaz ni reconstruir todos los entregables desde borradores.

## Fase 1 de revisión — sistema de avisos (19 de noviembre de 2026)

Rama `revision/feedback-interfaz`, partiendo de `e616955`. Trabajo hecho por David Neira con Claude (sesión en la nube, Python 3.12.3, PyTorch 2.15 CPU en Linux, Chrome headless). Pesos y datos tomados del release v0.2.0; los hashes de `models/checksums.json` y del paquete completo coinciden (1285 archivos, 0 diferencias).

**Baseline reproducido antes de editar:** 81/81 Python, 9/9 integración real, 12/12 navegador.

**Defectos reproducidos (de mayor a menor):**
1. En el celular, el error de «Confirmar» sin marcar la casilla quedaba ~560 px por encima de la ventana: parecía que el botón no hacía nada.
2. Si fallaba el procesamiento en el paso 4, el deslizador mostraba el valor nuevo con la imagen vieja, sin botón de reintento.
3. Un único `#message` arriba de la página, sin icono, título ni acción; el error movía la página lejos del campo.
4. Sin confirmaciones positivas; información y advertencia indistinguibles.
5. Sin mensajes junto al campo afectado.
6. «Repetir con otra captura» / «Trabajar otra fotografía» descartaban trabajo sin preguntar.
7. Espera estática, sin tiempo transcurrido ni salida.

**Cambios:**
- `static/feedback.js` (nuevo): `Feedback.notify/dismiss/clear/fieldMessage/clearField/focusField/confirmAction`. Avisos fijos en la ventana, bajo la cabecera mientras está visible. Clave por aviso: sin duplicados, y el error se cierra cuando la operación se resuelve. Errores y advertencias permanentes; éxito 5 s e información 7 s, con pausa al pasar el mouse o tener foco. Una advertencia o error nuevo cierra las confirmaciones viejas. Máximo 2 avisos en celular y 4 en escritorio. Regiones vivas separadas (`#live-polite`, `#live-assertive`). Escape cierra el aviso.
- `static/feedback.css` (nuevo): estilos por tipo (icono + título + color), mensajes de campo, franja de vista desactualizada, tarjeta de espera, diálogo de confirmación, sombras en tres niveles y animaciones de entrada, salida y pulso. Con `prefers-reduced-motion` se quitan animaciones y desplazamientos.
- `static/app.js`: reescrito legible (antes en líneas de hasta 2 kB) con la misma lógica. Errores tipados (`network`, `timeout`, `server`, `session`, `invalid`, `cancelled`) y acción correspondiente: Reintentar, Cargar otra foto o Ir al campo. Espera con tiempo real transcurrido desde 2 s, «Dejar de esperar» desde 8 s y aviso de demora desde 20 s. No se muestran porcentajes porque el servidor no los informa. Descargas: «Descarga solicitada», porque el navegador no confirma el guardado.
- `templates/index.html`: elimina `#message`; agrega `#toasts`, regiones vivas, `#stale-banner`, `#confirm-dialog`, tarjeta de espera, enlace «Saltar al contenido» y `main#main`.
- `palimpsesto/server.py`: `SessionError` → respuesta 400 con `code:"session"`. 2 pruebas nuevas en `tests/test_validation.py`.
- `tests/ui_browser.cjs`: 12 → 22 comprobaciones (ver VALIDACION_Y_FALLOS).

**Comandos:** `python scripts/check.py` (83 pasan); `python scripts/verify_real_pipeline.py --root "<paquete>/material_original/Material Proyecto de PDI"` (9/9; `results/integration/real_pipeline.json` se restauró para no mezclar tiempos de otra máquina); con `python run.py` activo, `CHROME_PATH=/usr/bin/google-chrome npm run test:ui` (22/22).

**Límites honestos:** las pruebas de navegador son automatización, no usabilidad humana. Lectores de pantalla reales (NVDA/VoiceOver) sin probar: solo se verificaron roles y contenido de las regiones vivas. El rediseño visual no lo ha revisado una persona en un celular físico.

**Siguientes acciones:** revisar la calidad real de red y procesamiento (modelo, dataset, alcance) según MODEL_CARD y DATA_CARD; alinear el README con las secciones de la rúbrica (problemática, justificación, objetivos, datos con enlace de Drive, capturas de la GUI, conclusiones); póster y video al final. Siguen pendientes las tareas humanas de arriba.

## Fase 2 de revisión — calidad de la red y README según la rúbrica (19 de noviembre de 2026)

Rama `revision/fase2-calidad-rubrica`, creada sobre `revision/feedback-interfaz` (PR #1 abierto para revisión). El PR de esta fase se apila sobre el de la fase 1.

**Red (clasificador v0.3.0).** Hipótesis: la cabeza no generaliza a fotos giradas (diagnóstico 0,930 → 0,798 con 90°). `scripts/experiment_rotation.py` compara, con los mismos folds y la misma rejilla, base / giros de la vista original / giros de todas las vistas, con una regla de adopción escrita antes de ejecutar. La base reproduce exactamente la v0.2.0. Se adoptó «giros de la vista original» (C=0,1): OOF derechas 0,9581 (antes 0,9531), giradas 0,9548 (antes 0,8797). Se desplegó con `--promote`. El anterior está en `models/classifier_v0.2.0.pt`. Se recalibró el alcance (`calibrate_scope.py`; umbral prácticamente igual) y se reevaluaron robustez (`results/robustness/evaluation.json`; la v0.2.0 queda en `evaluation_v0.2.0.json`) y alcance (9/10, sin cambio). Checksums actualizados.
- Sin conexión a download.pytorch.org en el entorno de revisión: el encoder ImageNet se tomó del `classifier.pt` desplegado (contiene la red completa). La reproducción exacta de la base demuestra que es el mismo encoder.
- Retroceso: brillo ×1,25 pasa de 0,972 a 0,958 en el diagnóstico. Integración real: I0018 ahora se sugiere como manuscrito (la usuaria confirma la clase; el flujo pasa).
- `classifier.pt` NO está en Git (`.gitignore`). La sesión de revisión no puede crear releases (HTTP 403), así que `modelos_palimpsesto_v0.3.0.zip` (SHA-256 `9880804e…e577`) se entregó al usuario. **Pendiente humano:** subirlo a una release desde la web de GitHub. Alternativa reproducible: con los datos y `classifier_v0.2.0.pt` en `models/classifier.pt`, ejecutar `scripts/experiment_rotation.py --root RUTA --promote` y luego `calibrate_scope.py`.

**README reestructurado** con las 8 secciones de la rúbrica (descripción con problemática/justificación/objetivos tomados del Word de definición, arquitectura en Mermaid validada, metodología con cambios frente a la propuesta, implementación, datos con figuras, GUI con capturas, resultados con análisis, conclusiones), además de la instalación, la reproducción, el trabajo humano y las referencias. Afirmaciones técnicas verificadas contra el código (vistas de 1200/960 px, mejora en el canal L de Lab con filtro bilateral, PDF con ReportLab, métodos de contornos de `probe_geometry.py`). La comparación de bordes aclara que las 80 fotos de la U-Net incluyen 56 de entrenamiento; la cifra justa es 12/12 de prueba (0,968).

**Figuras y capturas reproducibles:** `scripts/make_figures.py [--root]` (robustez v0.2.0 frente a v0.3.0, confusiones CNN/v0.2.0/v0.3.0, experimento de rotación, distribución y muestra del dataset con documentos difuminados por privacidad); `node scripts/capture_gui.cjs` (capturas de la GUI con el ejemplo sintético, en `docs/img/`).

**Comandos verificados:** check 83/83; verify_real_pipeline 9/9; test:ui 22/22 con el modelo nuevo.

**Pendiente humano nuevo:** enlace de Google Drive del dataset con permiso para el profesor (README, sección 5).

## Traspaso tras el merge (19 de noviembre de 2026, noche)

PR #1 (fase 1) y PR #2 (fase 2) fusionados en `main` con el acuerdo de Juan Felipe; las pruebas automáticas pasaron en ambas ramas. `main` ya contiene la interfaz con avisos, el clasificador v0.3.0 (código y resultados), el README según la rúbrica y las figuras.

**Pendiente para dejar la entrega completa:**
1. ✅ **Hecho (19 nov, 22:04):** release `v0.3.0` publicada por David como «Latest» sobre `d7e11f1`. Asset verificado desde la API: 182.755.574 bytes, SHA-256 idéntico. Instrucción original: subir `modelos_palimpsesto_v0.3.0.zip` (SHA-256 `9880804e55312b0cc0556a52c2ff94f03a7ef4ed08ceb820a680e4221006e577`) como release normal `v0.3.0` marcada como «Latest» (el README remite a la release más reciente). Mientras no esté, quien clone el repo y use los pesos de la v0.2.0 tendrá el clasificador anterior: los checksums de `classifier.pt` y `scope_reference.npz` no coincidirán y el filtro de alcance se desactivará por diferencia de hash.
2. **Enlace de Google Drive del dataset con permiso de lectura para el profesor** (Juan Felipe): pegarlo en el README, sección 5.
3. **Acceso del profesor** al repositorio privado y a las releases (Juan Felipe, como dueño del repo).
4. **Póster/infografía, video ≤ 3 min y exposición** (Juan Felipe): usar las figuras de `results/figures/`, las capturas de `docs/img/` y `docs/GUIA_SUSTENTACION.md`.
5. **Tareas humanas de evidencia** (equipo): certificar piezas, fotografiar 6–9 piezas nuevas, prueba de uso con 3–5 personas. No marcarlas como hechas sin evidencia.

Instalación verificada en el equipo de David (Windows, Python 3.12.10): `Instalar_Palimpsesto.cmd` → 83 passed; app abierta con «IA lista»; el ejemplo sintético se sugiere como Impreso (98,5 %).

## Cierre de acceso para el docente — 19 de noviembre de 2026

Partida: `main` en `3fe28a6` (fases 1/2 fusionadas, release v0.3.0 publicada). Rama `revision/cierre-dataset-validacion`. El usuario pidió concentrarse en los pendientes, sin repetir entrenamientos ni las pruebas generales ya realizadas por el equipo.

- README sección 5: enlaces reales a ambos Drive y ZIP consolidado. 647 archivos originales de datos; 480 hashes coinciden con `data/manifest.csv`; integridad del ZIP comprobada. SHA-256: `1b00cb28f0490d1247b7f11874b0542dd3d73e1f3b590ef163a7768ca72d8820`.
- Entrega consultable sin invitación: https://github.com/juanffff-hub/palimpsesto-pdi-entrega. Copia del código actual sin historial privado, material docente, inventarios del curso ni registros de instalación local. La colaboración continúa en el repositorio privado; no desarrollar en paralelo sobre la copia de entrega.
- Pesos públicos v0.3.0: copia exacta de la release de David, 182755574 bytes, SHA-256 `9880804e55312b0cc0556a52c2ff94f03a7ef4ed08ceb820a680e4221006e577`. Se verifica la transferencia del archivo, no se repite entrenamiento ni se inventan nuevos resultados.
- No hay cambios de aplicación, interfaz, modelos, particiones ni cifras experimentales. Se conservaron las pruebas documentadas de Claude (83 Python, 9 recorridos, 22 navegador); en esta revisión también se había comprobado 83/83 Python antes de la instrucción de evitar repeticiones.
- Drive: las carpetas originales ya tienen permiso `anyone/writer`. No se alteraron permisos del trabajo del equipo. El ZIP estable se sirve por la release pública; el conector de Drive rechaza archivos mayores de 512 MiB y el navegador disponible no permite completar la gestión de permisos. La carpeta nueva vacía «Palimpsesto — dataset y entrega académica» no forma parte de la entrega.
- Quedan exclusivamente como evidencia humana: identidades de piezas, capturas nuevas con clase real, usabilidad con 3–5 personas y revisión visual de trazos/color. La evaluación y tabulación posteriores pueden automatizarse. Póster/video/sustentación se abordan después.

Esta sección actualiza los pendientes históricos de acceso anteriores; no marca como completadas las validaciones humanas.
