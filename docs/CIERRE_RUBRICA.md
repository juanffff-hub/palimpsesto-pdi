# Correspondencia con la rúbrica

Fuente: «Rubrica proyecto final PDI 2026-2», tres páginas, suministrada por el equipo. Esta tabla documenta evidencia disponible; no anticipa una calificación del profesor.

| Requisito | Evidencia de la entrega |
|---|---|
| Necesidad sobre arte y cultura, problemática y solución | README §1: captura documental y artística con supervisión humana |
| PDI, visión computacional y GUI integrados | README §2–4; clasificación, U-Net, homografía, mejora y exportación |
| Evaluar con datos reales registrados o capturados | 480 fotos reales, 240 con máscara (3 clases) y prueba externa congelada con 30 negativos propios; protocolos y métricas en README §5 y §7, `results/` |
| Métricas, ejemplos visuales y análisis de límites | Tablas, curvas, matrices, comparación geométrica, figura de los 30 negativos externos y casos fallidos; fichas de modelo y datos |
| Descripción | README §1 |
| Arquitectura completa | Diagrama Mermaid y tabla de módulos, README §2 |
| Metodología | README §3 |
| Implementación explicada | README §4; código, scripts y notebook |
| Datos descritos, visualizados y accesibles | README §5: Drive con todas las fotos por rol, ZIP de las releases, manifiesto y figuras |
| GUI, prototipo, instrucciones y evidencias | README §6; prototipo navegable en `docs/prototipo/` (con estados de excepción); capturas de la app en `docs/img/`; flujo de cinco pasos |
| Resultados | README §7 y fuentes numéricas en `results/` |
| Conclusiones, límites y oportunidades | README §8 |
| Instalación y ejecución reproducibles | README §9, pesos con hashes, lanzadores y dependencias |
| Video demostrativo ≤3 min | ✅ [YouTube](https://youtu.be/CjWwmcuZH_8) · 2:50, presentación y demostración real de la app (incluye el aviso ante una foto que no es una pieza); [release de entregables](https://github.com/juanffff-hub/palimpsesto-pdi/releases/tag/entregables-2026-2) |
| Póster académico | ✅ A3 en `docs/poster/` (PDF y PNG), con la estructura sugerida |
| Sustentación oral con demostración y decisiones | Diapositivas en `docs/sustentacion/` (14, para 10 minutos) y guía de preguntas en `docs/GUIA_SUSTENTACION.md`; exposición del equipo |

Los resultados se presentan con sus límites: grupos físicos provisionales, diagnóstico reutilizado, pocas pinturas y un control de alcance que, aunque mejoró de 13/30 (v0.4.0, prueba externa) a 16/18 (v2, prueba ciega única), sigue fallando con negativos difíciles. Los conjuntos de prueba se congelaron antes de inferir y no se usan para recalibrar. No se presentan las comprobaciones de software como evidencia de fidelidad patrimonial. SSIM y PSNR corresponden únicamente a referencias sintéticas alineadas.

La aplicación se ejecuta en local; las instrucciones están en la sección 9 del README.
