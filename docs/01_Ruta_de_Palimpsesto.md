# Palimpsesto: decisión de alcance y ruta de cinco días

Fecha de revisión: 18 de noviembre de 2026. Base principal: la definición de proyecto y prototipo más reciente suministrada por el equipo. Este documento separa requisitos de la rúbrica, compromisos de la propuesta, resultados antiguos, comprobaciones nuevas y tareas todavía pendientes.

## Decisión

Construir un asistente local para mejorar fotografías de una sola pieza plana: manuscrito, documento impreso o pintura. El usuario carga una foto, confirma la categoría sugerida por una CNN, revisa cuatro esquinas, corrige la perspectiva, ajusta mejoras conservadoras, compara y exporta PNG/PDF junto con un registro de lo realizado. Se conserva el archivo original.

La contribución retadora será combinar segmentación aprendida y geometría clásica con corrección humana y evaluación reproducible. No se entrenará un restaurador generativo. El sistema no reconstruirá letras perdidas, zonas quemadas por reflejos ni pliegues tridimensionales mediante invención de contenido.

## Evidencia que determina la ruta

- Se inventariaron 13 PDF (477 páginas), 2 Word, 18 notebooks independientes y el notebook del primer parcial dentro del ZIP. Se extrajeron textos, código y resultados disponibles, y se revisaron las imágenes del conjunto y las figuras del prototipo.
- Hay 740 archivos de imagen fuera del ZIP y 17 dentro; resultan 736 contenidos distintos por hash. Esta cifra incluye máscaras, recortes y generaciones: no representa 736 capturas independientes.
- El conjunto principal de clasificación contiene 480 fotografías, 160 por clase. La afirmación de 60 objetos físicos procede del notebook; hay que revisar la identidad de las piezas entre carpetas antes de certificar una separación nueva.
- Hay 80 fotografías anotadas con máscaras, procedentes de 18 grupos documentales, 5 escenas adicionales y dos checkpoints U-Net. El CSV de procedencia demuestra que muchas fotos anotadas son versiones de las fotos de clasificación, por lo que no se deben contar como muestras independientes.
- El clasificador previo reportó 77,08 % de accuracy y macro-F1 cercano a 0,759 en su prueba histórica. No se encontró su checkpoint dentro del material. Hace falta entrenarlo y guardar pesos, etiquetas y normalización.
- Sí se cargó la U-Net de ustedes con sus pesos y su preprocesamiento. En las 12 imágenes de prueba histórica se reprodujo Dice 0,99312 e IoU de máscara 0,98636 a 256×256. Transformar la máscara en cuadrilátero produjo IoU medio 0,96815 frente a las máscaras originales a escala máxima 960; 11/12 superaron 0,95.
- En el diagnóstico sobre las 80 imágenes anotadas, Canny/contornos sencillo alcanzó IoU ≥ 0,90 en 16/80; varias variantes clásicas, en 32/80; U-Net más cuadrilátero, en 80/80. **Esta comparación de 80 incluye entrenamiento: prueba viabilidad técnica, no generalización.**
- Se comprobaron además 24 imágenes de manuscritos/pinturas sin anotación y las 5 escenas extra. Aparecieron segmentaciones parciales de pinturas y fusiones entre objetos. No hay una tasa de acierto válida para estas muestras sin verdad-terreno. Por eso la aceptación del borde nunca será automática.
- Una página impresa sintética, con referencia exacta, mostró que el método depende del defecto: bajo sombra suave, división gaussiana elevó SSIM de 0,840 a 0,927; CLAHE aislado lo redujo a 0,701. Sauvola obtuvo F1 de tinta 0,908 frente a 0,269 de Otsu en ese caso. Son pruebas construidas, no resultados sobre patrimonio real ni parámetros universales.

## Arquitectura elegida

1. **Entrada y trazabilidad:** JPG/PNG, orientación EXIF, límites de tamaño, copia RGB, hash y original intacto. Copias pequeñas para inferencia y visualización; el procesamiento final parte de la imagen de mayor resolución disponible.
2. **Clasificación:** se evaluó la CNN compacta del segundo parcial, con cuatro convoluciones y 228.771 parámetros. Su prueba de 52/72 aciertos motivó usar operativamente ResNet18 congelada con una cabeza aprendida: 389/408 aciertos fuera de fold y 67/72 en diagnóstico secundario. Estas cifras siguen siendo provisionales por la agrupación y la reutilización del test. Se conservan la CNN propia y la ANN como evidencia del curso. Normalización obtenida solo de entrenamiento. Se comparan base, dropout, L2 y aumento, con el mismo presupuesto y separación; una variante combinada candidata. La clase siempre se confirma. El valor softmax se presenta como puntuación del modelo, no como garantía de acierto.
3. **Localización:** U-Net propia para documentos; contornos como alternativa y ruta inicial para pinturas. Se rechazan geometrías inválidas o ambiguas. En todo caso, cuatro puntos editables y opción de nueva foto.
4. **Perspectiva:** homografía sobre RGB original. Se explica que cuatro puntos eliminan perspectiva de un plano, pero no resuelven curvatura ni determinan por sí solos la proporción física exacta. Se ofrece proporción conocida opcional.
5. **Mejora:** iluminación por estimación de fondo, CLAHE moderado en luminancia, suavizado opcional y máscara de enfoque con aritmética flotante. Binarización Otsu/Sauvola solo como derivado opcional de texto. Pinturas parten de un tratamiento neutro y mantienen el color.
6. **Interfaz:** flujo de cinco pasos basado en el prototipo suministrado, con original, puntos, vista frontal, comparación y exportación. Para disponer de arrastre preciso de esquinas y conservar el diseño se implementa una interfaz HTML/canvas con servidor Python local ligero. Este cambio sustituye Gradio como capa gráfica; las técnicas de PDI y aprendizaje permanecen en Python y proceden del curso.
7. **Evaluación:** clasificación por clase y macro-F1; IoU geométrica y errores de esquinas cuando haya anotación; SSIM/PSNR exclusivamente con referencia alineada; nitidez/contraste como descriptores, nunca como una nota universal de calidad; latencia y prueba de uso real.

## Qué se conserva y qué cambia frente al Word

Se conservan las tres categorías, CNN propia, regularización, detección de esquinas, homografía, mejora ajustable, supervisión del usuario, exportación y evaluación. Se añade la reutilización de la U-Net del tercer parcial, con límites explícitos. Se sustituye el cronograma de semanas por cinco jornadas. La descripción antigua de regresión supervisada no describe el núcleo actual: la CNN clasifica, la U-Net segmenta y las mejoras son transformaciones deterministas.

Se corrige un punto metodológico: igualar el tamaño de dos fotografías no las alinea. SSIM/PSNR necesitan correspondencia espacial y una referencia pertinente; compararlas tras un simple resize produciría conclusiones engañosas. También se distingue mejora para consulta de un máster de conservación certificado.

## Datos y validación

Se reúnen las fotografías sin obedecer las etiquetas antiguas train/val/test. Se conserva esa procedencia únicamente para auditoría y reproducción de resultados anteriores. Se construye un manifiesto con archivo, hash, clase, pieza física, derivación y estado de revisión. Todas las vistas y variantes de una pieza deben compartir partición.

La separación objetivo es aproximadamente 70/15/15 por piezas, estratificada por clase, sin obligar porcentajes exactos si los grupos no lo permiten. La identidad física se propone automáticamente con correspondencias visuales y las anotaciones existentes; requiere confirmación humana. Se pueden entrenar versiones provisionales mientras se revisa, pero sus cifras se rotulan como provisionales.

Reutilizar una U-Net ya entrenada obliga a registrar qué piezas vio: cambiar de nombre las carpetas no borra su aprendizaje. Para medir el sistema completo se necesitan piezas realmente nuevas para ambos modelos, o reentrenar ambos bajo una separación común. La opción más barata es reservar una prueba externa pequeña de 6–9 piezas nuevas, repartidas entre las tres categorías, con dos vistas por pieza. Esa prueba sirve para describir el alcance observado, no para prometer generalización universal.

Las imágenes generadas con LoRA/difusión quedan fuera de la prueba real y del entrenamiento principal. Las degradaciones sintéticas reproducibles se aplican después de separar por pieza, a referencias conocidas, y conservan la homografía y parámetros usados.

## Cinco jornadas, una persona activa

Se presupuestan 20 horas esenciales y hasta 10 de reserva/mejora, usando la disponibilidad informada de 4–6 horas diarias. El trabajo de programación, entrenamiento, gráficos y documentos se automatiza; los tiempos son estimaciones de dedicación humana y supervisión, no garantías de tiempo de cómputo.

| Jornada | Trabajo y resultado verificable | Dedicación esencial |
|---|---|---:|
| 1 | Congelar alcance, revisar grupos propuestos, primer recorrido carga→esquinas manuales→PNG; iniciar entrenamiento | 4 h |
| 2 | CNN guardada, comparación de variantes, U-Net integrada y mejoras por clase; corregir fallos concretos | 4 h |
| 3 | Interfaz completa, exportación PNG/PDF/JSON, pruebas de errores, instalación reproducible | 4 h |
| 4 | Capturas nuevas y revisión de detalles, prueba con 3–5 personas, evaluación final sin reajustar con test | 4 h |
| 5 | README, póster, video ≤3 minutos, presentación, ensayo y comprobación de enlaces/ejecución | 4 h |

Las 1–2 horas adicionales por día son reserva para datos ambiguos, entrenamiento alternativo, fallos de instalación y revisión de entregables. Si participan los otros integrantes, uno puede verificar datos y capturar piezas nuevas; otro puede probar la interfaz y preparar la sustentación. Ninguna función esencial depende de disponer de tres programadores.

## Intervención humana imprescindible

| Tarea | Por qué no se puede certificar automáticamente | Momento |
|---|---|---|
| Confirmar agrupación de fotos por pieza | Mismo texto, marcos y fondos pueden engañar al agrupador; el equipo conoce los objetos | Antes de declarar evaluación final |
| Confirmar clase/borde y conservación de detalles en casos de uso | La utilidad y fidelidad del resultado requieren una decisión de quien conoce la pieza | Durante las pruebas y cada uso |
| Capturar piezas nuevas, si se quiere medir generalización externa | El asistente no puede fotografiar objetos físicos ausentes | Jornada 4 o antes |
| Confirmar qué fotos/datos pueden compartirse y la cuenta de entrega | La carpeta contiene certificados y obras con autor; el equipo decide el material publicable | Antes de publicación |
| Sustentar y responder preguntas | La defensa académica corresponde a los estudiantes | Jornada 5 |

El asistente puede preparar código, pesos, agrupaciones sugeridas, herramientas de revisión, pruebas, métricas, figuras, documentación, póster, presentación y un video demostrativo. No se atribuirán al equipo pruebas humanas que no se hayan realizado.

## Condiciones de cierre

El núcleo está listo cuando las tres clases pueden recorrer el flujo, hay un modelo realmente cargado, las esquinas se pueden corregir, las transformaciones inválidas se rechazan, los ajustes se pueden deshacer, las exportaciones se abren y el sistema funciona localmente sin servicio remoto de inferencia. La calidad experimental final queda condicionada a verificar grupos y ejecutar pruebas reales. Una métrica modesta explicada con honestidad es preferible a una cifra alta contaminada por piezas repetidas.

La rúbrica exige cuatro entregables: repositorio GitHub con README principal y acceso a datos/pesos; video de máximo tres minutos; póster académico; presentación y sustentación con demostración. No exige una accuracy mínima universal del 90 %. El umbral de otro ejercicio del curso no se traslada a esta rúbrica.

## Fuentes centrales de la decisión

- [OpenCV: homografía y corrección de perspectiva](https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html): justifica el modelo plano y sus límites.
- [OpenCV Document Scanner, implementación del autor](https://github.com/andrewdcampbell/OpenCV-Document-Scanner): antecedente de detección, transformación y edición manual de esquinas.
- [DocAligner, implementación de DocsaidLab](https://github.com/DocsaidLab/DocAligner): alternativa de predicción de esquinas, con complejidad y pesos adicionales; no sustituye de entrada el trabajo propio.
- [DewarpNet](https://github.com/cvlab-stonybrook/DewarpNet), [DocTr](https://github.com/fh2019ustc/DocTr) y [DocRes](https://github.com/ZZZHANG-jx/DocRes): alternativas para deformación y restauración documental más amplia. Sus tareas, datos y dependencias exceden el núcleo necesario de cinco días.
- [BEDSR-Net, CVPR 2020](https://openaccess.thecvf.com/content_CVPR_2020/html/Lin_BEDSR-Net_A_Deep_Shadow_Removal_Network_From_a_Single_Document_CVPR_2020_paper.html), [FSENet, ICCV 2023](https://arxiv.org/abs/2308.14221) y [GCDRNet/RealDAE](https://github.com/ZZZHANG-jx/GCDRNet): muestran el valor de referencias y datos específicos para sombras/apariencia; no prueban que un filtro universal funcione sobre pinturas.
- [DocEnTR](https://github.com/dali92002/DocEnTR): binarización aprendida; se pospone frente a Otsu/Sauvola por coste de integración y validación.
- [ScanTailor, opciones de salida](https://github.com/scantailor/scantailor/wiki/Output): precedente para separar derivados de texto y color y revisar pérdida de trazos.
- [SmartDoc 2015, datos y evaluación del equipo autor](https://github.com/jchazalon/smartdoc15-ch1-dataset): referencia para evaluación de bordes y separación de tareas.
- [scikit-image: métricas](https://scikit-image.org/docs/stable/api/skimage.metrics.html), [Sauvola/Niblack](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_niblack_sauvola.html) y [OpenCV: CLAHE](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html): implementación y condiciones de uso.
- [scikit-learn: grupos no solapados](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html), [PyTorch: transferencia](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html) y [Guo et al.: calibración](https://proceedings.mlr.press/v70/guo17a.html): validación, alternativa de aprendizaje y límites de las puntuaciones de confianza.
- [FADGI, guías de digitalización cultural](https://www.digitizationguidelines.gov/guidelines/digitize-technical.html): orientación sobre conservación, trazabilidad y evaluación; Palimpsesto no se presenta como sistema certificado.

La revisión ampliada, el mapa completo del curso y las comparaciones experimentales están en 02_Investigacion_y_decisiones.md y en la carpeta results del proyecto. Las recomendaciones aquí son decisiones de ingeniería basadas en las fuentes y en las pruebas locales; no una demostración de superioridad universal frente a todos los métodos publicados.
