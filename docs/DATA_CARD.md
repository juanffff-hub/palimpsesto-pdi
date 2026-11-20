# Datos, procedencia y separación

La entrega conserva completa la carpeta original `Material Proyecto de PDI`, no solo un subconjunto de fotos. Inventario inicial: 804 archivos, aproximadamente 1.307 GB decimales; 13 PDF/477 páginas, dos Word, 18 notebooks independientes más uno en ZIP. Se identificaron 757 ocurrencias de imagen, 736 contenidos únicos, incluyendo máscaras, derivados y generadas. Los inventarios especifican cada ruta; no sumar todas como fotos independientes para aprendizaje.

Manifiesto principal: 480 fotos, 160 por clase. Las etiquetas de carpetas train/val/test eran ejercicios previos y no definen la nueva separación. Propuesta declara 60 piezas por ocho vistas, pero la correspondencia física no está comprobada. Se construyeron 50 bloques conservadores usando lotes de captura, similitud SIFT y referencias COCO conocidas: 18 impresos, 19 manuscritos, 13 pinturas. Algunos bloques agrupan más de una pieza. No llamar a los bloques piezas certificadas.

CNN propia: 336 train / 72 val / 72 test, 32/9/9 bloques. Transferencia: 408 desarrollo, con CV por 41 bloques; mismas 72 fotos para diagnóstico secundario. Hash del manifiesto en checkpoints. `group_verified` continúa false para todas las filas iniciales. La herramienta HTML de revisión permite corregir identidades y exportar CSV; `resplit_manifest.py` exige revisión y escribe un archivo nuevo.

Segmentación del curso: 80 fotos/80 máscaras, cinco extras; 18 grupos D01–D18, con correspondencia a originales. Ampliación v0.4.0: 80 manuscritos (10 bloques) y 80 pinturas (13 bloques) elegidos entre las 160 fotos de cada clase y anotados con polígonos en makesense.ai; se excluyeron piezas de bordes quemados, rasgados o perforados. Las máscaras de pintura incluyen el marco. `data/segmentation_manifest.csv` reúne las 240 fotos con su bloque del manifiesto principal y una partición por bloque (160/40/40). Su partición histórica y exposición del checkpoint no se reinician al crear un split distinto. Dataset LoRA: vistas de una pintura, recortes y generaciones; excluido de entrenamiento/evaluación como piezas reales nuevas.

SSIM/PSNR de mejora usa referencias construidas/alineadas, no ground truth de conservación. Negativos del filtro son ejemplos públicos de scikit-image elegidos por conveniencia; ver `results/scope/SOURCES.md`. La demostración de la portada es sintética y está identificada como tal.

Posibles sesgos: clases capturadas en contextos repetidos, iluminación y fondos correlacionados, múltiples vistas de una pieza, número real de piezas aún incierto, pocas pinturas únicas, manuscritos débiles confundidos con impresos. Revisión humana y capturas nuevas son necesarias antes de afirmaciones definitivas.

Material privado del equipo y del curso; no se presupone autorización de difusión pública. El paquete incluye un inventario SHA256 para comprobar que todos los originales se conservaron. No modificar ni eliminar archivos fuente durante futuras revisiones.


## Acceso de entrega

El dataset de clasificación está en la release v0.3.0 y el de segmentación de 3 clases (`segmentacion_3clases_v1.zip`, 240 fotos y máscaras) y los pesos en la release v0.4.0 de `juanffff-hub/palimpsesto-pdi`, repositorio público principal. README sección 5 incluye también los dos Drive originales. El ZIP de datos contiene 647 archivos, con hashes: 480 fotos de clasificación y los datos de segmentación. El material docente completo se conserva localmente y no forma parte de esta publicación. La consulta académica no concede una licencia abierta sobre fotografías u obras.
