# Estado del proyecto

## Versión técnica

Palimpsesto integra clasificación supervisada por la persona, segmentación de la pieza, corrección de perspectiva, mejora clásica ajustable, comparación y exportación PNG/PDF/JSON/ZIP con el original intacto. Clasificador operativo v0.3.0 y U-Net de 3 clases v0.4.0; modelos anteriores conservados como líneas base. Las redes, los pesos y las métricas de evaluación no se modifican en el cierre de publicación.

Repositorio único: https://github.com/juanffff-hub/palimpsesto-pdi

## Evidencia existente

- 113 comprobaciones Python (incluidas la descarga verificada de los pesos, el semáforo de la captura, la confianza del borde, los tonos recortados y el control de alcance v2), nueve recorridos con modelos reales y 25 comprobaciones de navegador documentados en la revisión de la interfaz y del clasificador.
- Diagnóstico secundario: 70/72 clasificaciones correctas; es un conjunto reutilizado, no un test ciego.
- CV macro-F1 0,9581 en vistas derechas y 0,9548 en vistas giradas, con grupos provisionales.
- U-Net v0.4.0 (impresos, manuscritos y pinturas): IoU media del borde propuesto 0,937 en 40 fotos de prueba por pieza, frente a 0,811 de la v0.3.0 (pinturas 0,583 → 0,877; manuscritos 0,881 → 0,963; impresos 0,968 → 0,970). Regla de adopción fijada antes de entrenar.
- Histograma y tonos recortados: con los preajustes, 0 de 240 fotos pierde detalle por recorte; el aviso aparece sobre todo con iluminación alta en manuscritos (8 de 80 al 100 %).
- Confianza del borde: en fotos de prueba marca como dudosos los 21 bordes malos de las 3 U-Net (6 de 6 con la desplegada) y 10 de 98 buenos; ningún borde «seguro» resultó malo.
- Semáforo de la captura: con defectos controlados avisa en el 80–100 % de los casos (antes 2–23 %); en fotos reales marca en rojo 23 fotos, todas revisadas a ojo y justificadas.
- Control de alcance: la v0.4.0 alertó 13/30 (43,3 %) en una prueba externa congelada. El control v2 (recorte de la pieza con la U-Net + regresión logística) alertó 79/88 negativos de desarrollo y **16/18 en una prueba ciega única** (escenas 6/6, objetos 6/6, difíciles 4/6), con 72/72 positivos de regresión. Cumple la regla predeclarada y está desplegado. Sigue siendo auxiliar y la confirmación humana es obligatoria.
- Clasificación propia del curso y ANN conservadas como líneas base, incluidos sus fallos.

El cierre del acceso remoto añade ocho comprobaciones dirigidas a HTTPS, sesiones, espera, expiración y recuperación; no repite la evaluación científica.

## Acceso y ejecución

README sección 5 enlaza el dataset, los Drive y los pesos. La release v0.3.0 incluye el dataset de clasificación y la v0.4.0 los pesos actuales y el dataset de segmentación. `Iniciar_Palimpsesto.cmd` abre el modo local. `Iniciar_Enlace_Publico.cmd` crea una demo HTTPS temporal desde este computador, sin contratar servicios; `Detener_Enlace_Publico.cmd` cierra la publicación. Ver `DEMO_PUBLICA.md`.

## Coordinación de cambios

La aplicación compartida toma los archivos de `main` en una copia aislada. Si se reescribe la historia para corregir autores, conservar íntegros los archivos actuales, especialmente `run_public.py`, `scripts/share_public.py`, lanzadores y documentación. No partir de una instantánea anterior al cierre de publicación. No es necesario cambiar ni volver a entrenar las redes para modificar los autores de Git.

La rama de trabajo del desarrollador no se restablece automáticamente; cada integrante debe actualizar su propia copia después de una reescritura coordinada. Las sesiones de la demo no se conservan tras reinicios del servidor. La copia de entrega separada se considera sustituida por el repositorio principal.

## Entregables siguientes

Póster académico, video de máximo tres minutos y sustentación oral. Para las limitaciones experimentales, consultar `MODEL_CARD.md`, `DATA_CARD.md` y el análisis del README. Los datos de referencia y el material docente original permanecen intactos fuera del repositorio público.

## Continuación técnica del control de alcance

**Actualización (20 de noviembre de 2026):** la iteración v2 se completó y se adoptó; ver `docs/PROGRESO_CONTROL_ALCANCE.md`. Los conjuntos v1 y v2 ya están abiertos: una mejora futura necesita un tercer conjunto ciego. Texto original: `negativos_alcance_v1` queda cerrado como prueba externa y no se usa para ajustar el sistema. Si se continúa esta línea, el siguiente paso es crear un conjunto **diferente** de negativos de desarrollo, separado por objeto o escena; comparar allí el banco actual contra una clase negativa o un método explícito de fuera-de-distribución; predeclarar una puerta de adopción; y evaluar una sola vez en otro conjunto ciego. Hasta entonces no presentar el filtro como detector universal y conservar la confirmación explícita de una pieza válida. Los comandos y resultados están en `scripts/evaluate_scope_external.py` y `results/scope/`; el registro de iteraciones está en `docs/PROGRESO_CONTROL_ALCANCE.md`.

## Reescritura de autores (20 de noviembre de 2026)

Se reescribió la historia de `main` para que los commits de la revisión de interfaz y clasificador figuren a nombre de DavidN09 y sin líneas de coautoría. Los archivos quedaron idénticos byte a byte (mismo árbol que el commit anterior `687fe80`); los commits de juanffff-hub conservan su autor y su fecha. No se tocaron redes, pesos, métricas ni el trabajo de la demo pública: los 12 archivos de ese cierre (`run_public.py`, `scripts/share_public.py`, lanzadores, `server.py`, pruebas…) están completos en `main`. Comprobado: 87 pruebas Python pasan.

Equivalencias de commits: `687fe80` → `0aa3877` (demo HTTPS), `6e15970` → `5c86e8d` (acceso al dataset), `d7e11f1` → `88a8b93`.

**Para actualizar una copia local** (sin cambios propios sin subir): `git fetch origin` y luego `git reset --hard origin/main`. Si `git status` muestra cambios propios, primero guardarlos con `git stash`.

**Pendiente desde la web de GitHub:** el tag `v0.3.0` sigue apuntando al commit antiguo `d7e11f1`; la release y sus archivos funcionan igual. Las ramas ya fusionadas `revision/feedback-interfaz` y `revision/fase2-calidad-rubrica` conservan la historia antigua y pueden borrarse desde la página de ramas.
