# Estado del proyecto

## Versión técnica

Palimpsesto integra clasificación supervisada por la persona, segmentación de la pieza, corrección de perspectiva, mejora clásica ajustable, comparación y exportación PNG/PDF/JSON/ZIP con el original intacto. Clasificador operativo v0.3.0; baseline anterior conservado. Las redes, los pesos y las métricas de evaluación no se modifican en el cierre de publicación.

Repositorio único: https://github.com/juanffff-hub/palimpsesto-pdi

## Evidencia existente

- 83 comprobaciones Python, nueve recorridos con modelos reales y 22 comprobaciones de navegador documentados en la revisión de la interfaz y del clasificador.
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
