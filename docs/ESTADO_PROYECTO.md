# Estado del proyecto

## Versión técnica

Palimpsesto integra clasificación supervisada por la persona, segmentación de la pieza, corrección de perspectiva, mejora clásica ajustable, comparación y exportación PNG/PDF/JSON/ZIP con el original intacto. Clasificador operativo v0.3.0; baseline anterior conservado. Las redes, los pesos y las métricas de evaluación no se modifican en el cierre de publicación.

Repositorio único: https://github.com/juanffff-hub/palimpsesto-pdi

## Evidencia existente

- 87 comprobaciones Python, nueve recorridos con modelos reales y 22 comprobaciones de navegador documentados en la revisión de la interfaz y del clasificador.
- Diagnóstico secundario: 70/72 clasificaciones correctas; es un conjunto reutilizado, no un test ciego.
- CV macro-F1 0,9581 en vistas derechas y 0,9548 en vistas giradas, con grupos provisionales.
- U-Net: IoU de cuadrilátero 0,968 en las 12 fotos de prueba histórica.
- Filtro de alcance: nueve de diez negativos de conveniencia alertados; persiste un falso negativo.
- Clasificación propia del curso y ANN conservadas como líneas base, incluidos sus fallos.

El cierre del acceso remoto añade ocho comprobaciones dirigidas a HTTPS, sesiones, espera, expiración y recuperación; no repite la evaluación científica.

## Acceso y ejecución

README sección 5 enlaza el dataset, los Drive y los pesos. La release v0.3.0 incluye los archivos descargables. `Iniciar_Palimpsesto.cmd` abre el modo local. `Iniciar_Enlace_Publico.cmd` crea una demo HTTPS temporal desde este computador, sin contratar servicios; `Detener_Enlace_Publico.cmd` cierra la publicación. Ver `DEMO_PUBLICA.md`.

## Coordinación de cambios

La aplicación compartida toma los archivos de `main` en una copia aislada. Si se reescribe la historia para corregir autores, conservar íntegros los archivos actuales, especialmente `run_public.py`, `scripts/share_public.py`, lanzadores y documentación. No partir de una instantánea anterior al cierre de publicación. No es necesario cambiar ni volver a entrenar las redes para modificar los autores de Git.

La rama de trabajo del desarrollador no se restablece automáticamente; cada integrante debe actualizar su propia copia después de una reescritura coordinada. Las sesiones de la demo no se conservan tras reinicios del servidor. La copia de entrega separada se considera sustituida por el repositorio principal.

## Entregables siguientes

Póster académico, video de máximo tres minutos y sustentación oral. Para las limitaciones experimentales, consultar `MODEL_CARD.md`, `DATA_CARD.md` y el análisis del README. Los datos de referencia y el material docente original permanecen intactos fuera del repositorio público.

## Reescritura de autores (20 de noviembre de 2026)

Se reescribió la historia de `main` para que los commits de la revisión de interfaz y clasificador figuren a nombre de DavidN09 y sin líneas de coautoría. Los archivos quedaron idénticos byte a byte (mismo árbol que el commit anterior `687fe80`); los commits de juanffff-hub conservan su autor y su fecha. No se tocaron redes, pesos, métricas ni el trabajo de la demo pública: los 12 archivos de ese cierre (`run_public.py`, `scripts/share_public.py`, lanzadores, `server.py`, pruebas…) están completos en `main`. Comprobado: 87 pruebas Python pasan.

Equivalencias de commits: `687fe80` → `0aa3877` (demo HTTPS), `6e15970` → `5c86e8d` (acceso al dataset), `d7e11f1` → `88a8b93`.

**Para actualizar una copia local** (sin cambios propios sin subir): `git fetch origin` y luego `git reset --hard origin/main`. Si `git status` muestra cambios propios, primero guardarlos con `git stash`.

**Pendiente desde la web de GitHub:** el tag `v0.3.0` sigue apuntando al commit antiguo `d7e11f1`; la release y sus archivos funcionan igual. Las ramas ya fusionadas `revision/feedback-interfaz` y `revision/fase2-calidad-rubrica` conservan la historia antigua y pueden borrarse desde la página de ramas.
