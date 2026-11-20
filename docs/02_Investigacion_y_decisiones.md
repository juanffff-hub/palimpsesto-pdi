# Palimpsesto — investigación, decisiones y evidencia

18 de noviembre de 2026 · Proyecto final de Procesamiento Digital de Imágenes

## 1. La ruta que sí cabe en cinco días

La ruta elegida es un asistente local y supervisado para producir una copia de consulta de una pieza plana. Combina una CNN clasificadora, la U-Net ya entrenada por el equipo, homografía y mejoras clásicas ajustables. Una persona confirma clase, encuadre y resultado. El original se conserva y cada transformación queda registrada. Este conjunto permite demostrar aprendizaje, geometría, procesamiento y una interfaz funcional sin asumir que una red puede reconstruir información que la fotografía nunca capturó.

La investigación cambió dos decisiones iniciales. Primero, Canny no localiza de forma suficientemente consistente los documentos suministrados; se reutiliza la segmentación aprendida y se conserva el ajuste manual. Segundo, la CNN pequeña del curso mostró una brecha importante entre validación y prueba. Se mantiene como experimento académico con sus cinco variantes, pero el clasificador operativo utiliza ResNet18 congelada con una cabeza aprendida sobre los datos del equipo. La transferencia se apoya en contenidos del curso y evita entrenar un modelo grande desde cero.

La decisión no se basa en una clasificación universal de algoritmos. Se priorizaron, en este orden: fidelidad y control del resultado; funcionamiento comprobable con los datos disponibles; trazabilidad con el curso; posibilidad de evaluación honesta; tiempo de integración y mantenimiento. Un método más reciente puede ser mejor en su benchmark y peor elección para este proyecto si exige nuevas referencias, anotaciones o una cadena difícil de explicar y reproducir en cinco días.

## 2. Qué material se analizó y cómo se interpretó

Se inventariaron 13 PDF, con 477 páginas; dos documentos Word; 18 notebooks independientes y un notebook dentro del ZIP del primer parcial. Se extrajeron textos, celdas de código y salidas guardadas. Se revisaron los contactos visuales del conjunto de imágenes y las figuras del prototipo. Las salidas antiguas se trataron como antecedentes del equipo, no como experimentos ejecutados de nuevo. Los experimentos nuevos tienen scripts y archivos de resultados separados.

La definición `Palimpsesto_Neira_Gomez_Fajardo_Definicion_Proyecto_alcance_prototipo (1).docx` prevalece sobre las versiones antiguas para interpretar el alcance solicitado. La rúbrica final determina los entregables. Las instrucciones de ejercicios anteriores, sus porcentajes mínimos o la indicación de no entrenar durante una sesión de prototipado no se trasladan automáticamente al proyecto final. El requerimiento actual del usuario es investigar y construir la solución completa con la mayor automatización posible.

### Teoría: cobertura completa del material entregado

| Fuente | Contenido que determina una decisión | Aplicación concreta |
|---|---|---|
| PDI S1 — 2026 2, 32 p. | Imagen digital, adquisición y propósito del procesamiento | Distinguir copia de consulta de restauración física; capturar con luz y enfoque adecuados |
| S2 — Pasos fundamentales PDI, 67 p. | Muestreo, cuantización, representación y etapas de PDI | RGB explícito, orientación EXIF, límites de resolución y conservación del original |
| S4 — Filtrado en frecuencia, 45 p. | FFT, filtros ideales, gaussianos y Butterworth | Experimento comparativo de frecuencia; no imponer un pasaaltos a cada imagen |
| S5 — Histograma, 33 p. | Histograma, CDF, contraste, rasgos de color/forma/textura | ANN con descriptores, CLAHE moderado en luminancia y análisis del fondo |
| S7 — ML/CV, 71 p. | Aprendizaje, particiones, representación y evaluación | Separación por grupos, métricas por clase y baseline simple |
| Backpropagation — CNN, 38 p. | Convolución, pooling, gradientes y entrenamiento | CNN propia de cuatro convoluciones; comprensión de la cabeza clasificadora |
| PDI Regularización, 25 p. | Overfitting, dropout, penalización y aumentos | Ablación base/dropout/L2/aumentos/combinada con validación separada |
| Semana 10 — Detección, 24 p. | Localización, cajas, propuestas y detectores | Una caja no identifica cuatro esquinas de una pieza en perspectiva |
| S13 — Segmentation, 29 p. | Segmentación semántica/instancias, máscaras y métricas | U-Net, umbral de máscara, componentes y cuadrilátero; Dice e IoU |
| S14 — Generative Modeling, 39 p. | Autoencoders, latentes y GAN | No usar generación no supervisada como evidencia de recuperación fiel |
| Sesión Diffusion Models, 39 p. | Difusión y adaptación generativa | Excluir LoRA de la restauración de letras y detalles; reconocer su dominio de uso |
| Sesión 12 Proyecto, 32 p. | Prototipo, estados y flujo de interacción | Cinco pasos, revisión antes/después, corrección y exportación |
| Rúbrica proyecto final, 3 p. | Sistema completo, evaluación, repositorio y comunicación | Repositorio, video ≤3 min, póster y sustentación con demostración |

### Práctica: los diecinueve notebooks

Los nombres abreviados de esta tabla corresponden a los archivos completos del inventario incluido en el proyecto.

| Notebook | Hallazgo y uso |
|---|---|
| Clase_1_A_2026_PDI_2 | NumPy, índices y operaciones elementales; varias celdas son ejercicios sin resolver. Base para entender arreglos, no código listo de producción |
| Clase_3A_PDI_JuanFelipe_Fajardo | Convoluciones y filtros espaciales. Se conserva el concepto; derivadas y acumulaciones se calculan en flotante para evitar saturación/desbordamiento |
| Clase_4_PDI | FFT y máscaras de frecuencia. Se documentan centrado, inversión y signo; tomar valor absoluto indiscriminadamente altera la respuesta |
| Ejercicio_clase_25_de_Agosto_JuanFelipe_Fajardo | Gradiente Sobel, no emparejamiento de histogramas. Se evita convertir derivadas firmadas directamente a uint8 |
| ZIP: Examen1_FajardoNeiraGomez | Filtros espaciales/frecuencia, high-boost, SIFT, correspondencias, RANSAC y panorama; fundamento de homografía, comparación y búsqueda de duplicados |
| Clase7_ANN | MLP e Iris; normalización aprendida solo en entrenamiento. Se lleva a un baseline de rasgos visuales |
| Semana7_Actividad_FajardoGomezNeira | ANN de frutas; antecedentes de sobreajuste y diferencia entrenamiento/prueba. No demuestra resultados sobre Palimpsesto |
| Clase8_CNN_PDI | CNN base para MNIST; progresión convolución/pooling/clasificación |
| Clase8_CNN_PDI_FajardoFelipe | Versión resuelta de la misma práctica; no se cuenta como una experiencia independiente |
| Clase_CNNs_2026 | CNN y Oxford Pets; organización de carga, entrenamiento e inferencia |
| clase _Pytorch_cnn_regularization | Dropout, L1/L2 y aumentos; base de las variantes controladas del clasificador propio |
| Act_Generalización_FelipeFajardo | Transferencia con VGG11. Cambiar arquitectura y regularización simultáneamente no es una ablación aislada; aquí se separan las dos comparaciones |
| Parcial_Practico_2_NeiraGomezFajardo | 480 fotografías y CNN de 228.771 parámetros; test histórico 77,08 %, checkpoint no encontrado. Incluye detección general YOLO, no un detector entrenado de esquinas |
| PDI_Laboratorio_Segmentacion_y_Deteccion_2026 | Otsu, morfología, watershed, componentes, IoU, propuestas y evaluación |
| PDI_Laboratorio_Segmentacion_y_Deteccion_2026_Fajardo_Gomez_Neira | Desarrollo de detección/segmentación, PennFudan y clases propias; los mAP guardados no se reutilizan como métricas de la aplicación nueva |
| Parcial_3_PDI_FajardoNeiraGomez | U-Net ResNet18, máscaras y entrenamiento con/sin preentrenamiento; checkpoints reutilizables. LoRA de una pintura pertenece a un problema diferente |
| Practica_Autoencoders | Autoencoders densos/convolucionales en MNIST; no hay restaurador propio de documentos con referencias que pueda integrarse sin nueva validación |
| Actividad_GAN_MNIST_JuanFelipeFajardo | Generador/discriminador; un resultado plausible no certifica contenido documental original |
| S8_modelos_difusion_solucionado | Difusión, semillas, pasos y prompts; se usa para justificar límites y no para introducir un módulo decorativo sin objetivo medible |

Usar el curso no significa incorporar cada técnica al recorrido del usuario. FFT, ANN y generación tienen un lugar claro en el análisis y los experimentos, aunque no todos sean el método elegido para producir la salida. La aplicación utiliza float32 para operaciones intermedias, conversiones RGB/Lab explícitas y bibliotecas vectorizadas; reproduce las ideas didácticas sin copiar errores accidentales de los ejercicios.

## 3. Auditoría del conjunto de imágenes

Se encontraron 740 archivos de imagen fuera del ZIP y 17 entradas dentro. Tras eliminar coincidencias de contenido resultan 736 imágenes distintas y ninguna corrupta. Este total incluye máscaras, recortes y generaciones: no equivale a 736 fotografías originales ni a 736 objetos diferentes.

El conjunto principal tiene 480 fotos, 160 por clase. El notebook describe 60 objetos físicos con ocho vistas por objeto, pero esa identidad no está codificada de forma fiable en cada archivo. Hay repeticiones entre carpetas, series con el mismo fondo y piezas muy parecidas. La propuesta automática utiliza series de captura, correspondencias SIFT/RANSAC y la relación con las anotaciones existentes. Produce 50 bloques conservadores: 18 de impresos, 19 de manuscritos y 13 de pinturas. **Estos bloques no son 50 piezas verificadas**: algunos reúnen más de una pieza y otros podrían conservar coincidencias no detectadas.

La separación provisional del experimento propio fue 336/72/72 imágenes y 32/9/9 bloques, equilibrada por clase. No se obedecieron las etiquetas antiguas de carpetas. Los bloques grandes se mantuvieron en entrenamiento y se eligieron bloques de ocho imágenes para validación y prueba; esto facilita el equilibrio, pero también puede producir un cambio de distribución. Hay que informarlo y no describirlo como muestreo aleatorio de todas las piezas posibles.

La transferencia posterior usa 408 imágenes de desarrollo, 41 bloques, con cinco particiones por grupos. Ninguna imagen del bloque de validación de un fold participa en el ajuste de su cabeza, incluidos sus aumentos. Las 72 imágenes restantes se conservan como diagnóstico secundario. Como el conjunto ya se abrió con la CNN inicial y motivó revisar el método, no es una prueba confirmatoria inédita. La validación cruzada también sirve para seleccionar C entre tres candidatos; su puntuación tiene optimismo de selección y no reemplaza una prueba externa.

El conjunto anotado contiene 80 fotografías con máscaras, de 18 grupos documentales, más cinco escenas adicionales. Son en parte versiones de las fotos del clasificador, según el CSV de procedencia. La U-Net vio algunos de esos objetos en su entrenamiento histórico. Por ello no puede proclamarse que la separación nueva del clasificador sea automáticamente independiente para el sistema completo.

Las 18 capturas de la pintura usada para LoRA, sus 18 recortes y 42 salidas generadas —cuatro duplicadas— no aportan 78 piezas reales. Las generaciones se excluyen del entrenamiento y de la prueba principal. Cualquier aumento nuevo se genera exclusivamente dentro del entrenamiento correspondiente.

## 4. Contraste de alternativas y proyectos publicados

Esta revisión combina artículos, repositorios de los autores, documentación oficial y experimentos locales. Las cifras de distintos trabajos no se comparan como si usaran el mismo conjunto. No se descargaron ni ejecutaron todos los sistemas externos: se examinó su tarea, entradas, datos, dependencias y forma de evaluación. Los métodos ejecutados aquí se identifican en la sección experimental.

| Alternativa y fuente primaria | Aporte útil | Coste o límite para Palimpsesto | Decisión |
|---|---|---|---|
| [OpenCV Document Scanner](https://github.com/andrewdcampbell/OpenCV-Document-Scanner) | Bordes, cuadrilátero, perspectiva y corrección manual | La tasa reportada por su autor pertenece a sus fotos; nuestros contornos fallan en fondos complejos | Incorporar geometría y revisión; no transferir su accuracy |
| [DocAligner de DocsaidLab](https://github.com/DocsaidLab/DocAligner) | Predicción especializada de esquinas; opciones CPU/ONNX | Nuevos pesos y preprocesamiento; los errores a baja resolución crecen al proyectarlos | Alternativa futura si la localización sigue siendo el principal cuello de botella |
| [DocUNet](https://www3.cs.stonybrook.edu/~cvl/docunet.html) | Rectificación de documentos deformados mediante aprendizaje | Datos sintéticos y entrenamiento para deformación no plana | Fuera del núcleo plano de cinco días |
| [DewarpNet](https://github.com/cvlab-stonybrook/DewarpNet) | Modelado de forma 3D y mapeo 2D; Doc3D | Pipeline adicional, pesos y evaluación específica | No integrar por el solo hecho de ser más avanzado |
| [DocTr](https://github.com/fh2019ustc/DocTr) | Transformadores geométrico y de iluminación | Dos funciones aprendidas y nuevos supuestos; existe demostración CPU | Evaluar más adelante para páginas curvas; no afirmar que exige GPU para toda inferencia |
| [DocRes, CVPR 2024](https://github.com/ZZZHANG-jx/DocRes) | Unificación de dewarping, sombras, apariencia, desenfoque y binarización mediante prompts de tarea | Pesos, módulos y datos especializados; fidelidad de texto/pinturas aún necesita prueba propia | Comparador de investigación, no dependencia esencial |
| [BEDSR-Net, CVPR 2020](https://openaccess.thecvf.com/content_CVPR_2020/html/Lin_BEDSR-Net_A_Deep_Shadow_Removal_Network_From_a_Single_Document_CVPR_2020_paper.html) | Estimación de fondo y eliminación aprendida de sombras | Necesita datos pareados y validación del contenido | Adoptar la idea física de estimar iluminación con un método clásico controlable |
| [FSENet, ICCV 2023](https://arxiv.org/abs/2308.14221) | Tratamiento de sombras en documentos de alta resolución, separando frecuencias | Modelo especializado y conjunto de pares reales distinto del disponible | No prometer eliminación general de sombras sin referencias |
| [GCDRNet y RealDAE](https://github.com/ZZZHANG-jx/GCDRNet) | Apariencia documental con pares alineados y mejorados manualmente | Sus 600 pares no representan obras pictóricas ni todos los manuscritos locales | Referente para diseñar evaluación pareada futura |
| [DocEnTR](https://github.com/dali92002/DocEnTR) | Binarización con transformer y benchmarks documentales | Entrenamiento/dependencias adicionales; binarizar no conserva color | Preferir Otsu/Sauvola como derivados opcionales |
| [ScanTailor](https://github.com/scantailor/scantailor/wiki/Output) | Flujo práctico de color, gris y binario; control de limpieza | Despeckling agresivo puede eliminar puntos y signos | Mantener deshacer, color y revisión de trazos |
| [SmartDoc 2015](https://github.com/jchazalon/smartdoc15-ch1-dataset) | 30 modelos documentales, cinco fondos, 150 videos y anotaciones de esquinas | Sus 24.889 cuadros están correlacionados; la métrica rectifica a coordenadas del documento | Modelo de protocolo; no mezclar su IoU con la nuestra |
| U-Net propia del parcial | Pesos disponibles, integración rápida y conocimiento del equipo | Entrenamiento documental estrecho; falla con varias piezas y algunas pinturas | Integrar como sugerencia de borde para papel |
| CNN propia + ANN de descriptores | Reproducción directa del curso y ablación explicable | Datos pequeños y fondo correlacionado con clase; prueba real mostró sobreajuste | Conservar como evidencia y baseline |
| [Transferencia de aprendizaje de PyTorch](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html) | Rasgos visuales preentrenados; ajuste de cabeza pequeño | Puede heredar sesgos; necesita separación de piezas y evaluación local | Elegida para clasificación operativa tras comprobarla |

### Geometría: qué puede y qué no puede corregirse

Cuatro correspondencias no colineales permiten estimar la homografía de un plano. La imagen se transforma desde RGB de resolución completa; la previsualización no reemplaza el original. Se ordenan y validan los puntos, se rechazan cruces y áreas casi nulas, y se permite indicar ancho/alto conocido. La estimación con longitudes de lados es solo una aproximación: una homografía no descubre las medidas físicas de una pieza. Tampoco aplana curvatura de libros ni elimina oclusiones. Estas restricciones proceden del modelo geométrico, no de una preferencia de interfaz. [Documentación de OpenCV](https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html).

La máscara segmentada se convierte en componente y contorno, se aproxima un polígono y se obtiene un cuadrilátero. Hay una pérdida de información al reducir una máscara a cuatro puntos. Por eso se reporta la IoU del cuadrilátero además de la IoU de máscara; una máscara excelente no garantiza automáticamente un recorte excelente.

### Iluminación, contraste, ruido y nitidez

Un fondo suave estimado permite dividir variaciones lentas de iluminación. Sin embargo, una zona oscura de una pintura puede ser pigmento y no sombra: no se debe corregir automáticamente como si fuera papel blanco. La aplicación modifica luminancia, mezcla la corrección con el original y deja las pinturas sin mejora inicial. Trabajar en Lab reduce cambios accidentales por ecualizar R, G y B por separado, aunque no garantiza conservación colorimétrica; no hay carta de color ni perfil de cámara.

CLAHE limita la amplificación local pero no elimina todos los artefactos. Puede aumentar ruido, alterar fondos y empeorar una referencia ya correcta. La máscara de enfoque realza frecuencias existentes y puede producir halos; no recupera trazos destruidos por movimiento. El suavizado bilateral puede ayudar bajo ruido, pero también borrar textura. Por eso son controles independientes y reversibles, con valores iniciales suaves. [OpenCV: histogramas y CLAHE](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html).

Otsu usa un umbral global y puede confundir tinta con fondo sombreado. Sauvola adapta el umbral a media y desviación local; es útil en el caso sintético de sombra, pero puede borrar trazos muy débiles o textura. Se exporta como derivado de lectura, no como reemplazo del original, y se deshabilita para pinturas. [Ejemplo oficial de scikit-image](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_niblack_sauvola.html).

### Por qué la generación queda fuera

El material LoRA demuestra adaptación a la apariencia de una pintura, no recuperación de información desconocida. Un resultado visualmente convincente puede modificar texto, firmas o pinceladas. Sin pares fiables y una evaluación de fidelidad, ese módulo aumenta el riesgo y el trabajo sin satisfacer mejor el objetivo. El reto académico suficiente es integrar clasificación, segmentación, geometría y evaluación, conservando control y trazabilidad. Las guías culturales se utilizan como referencia de proceso; este prototipo no cumple ni reclama una certificación FADGI. [Guías FADGI](https://www.digitizationguidelines.gov/guidelines/digitize-technical.html).

## 5. Experimentos realmente ejecutados

### Clasificación: no confundir abrir la aplicación con una red útil

Se entrenaron cinco variantes de la CNN del parcial sobre 336 fotos, validando sobre 72. Comparten arquitectura, semilla, presupuesto máximo de 35 épocas y criterio de selección macro-F1 de validación; se detienen tras ocho épocas sin mejora, después de un mínimo de doce. Los aumentos consumen aleatoriedad adicional, así que no se afirma equivalencia exacta de orden de minibatches entre todos los tratamientos. Una sola semilla tampoco permite atribuir diferencias pequeñas con significancia estadística.

| CNN del curso | Épocas ejecutadas / mejor época | Accuracy validación | Macro-F1 validación |
|---|---:|---:|---:|
| Base | 13 / 5 | 0,9167 | 0,9150 |
| Dropout | 12 / 4 | 0,8889 | 0,8842 |
| L2 | 23 / 15 | 0,9722 | 0,9722 |
| Aumentos | 31 / 23 | 0,9583 | 0,9588 |
| Combinada | 31 / 23 | 0,9444 | 0,9454 |

La variante L2 fue seleccionada usando solo validación. Al abrir la prueba obtuvo 52/72 aciertos, accuracy 0,7222 y macro-F1 0,7050. El recall de impresos fue 10/24. Esto impidió aceptar la CNN pequeña como solución suficiente. No se ocultó el fallo ni se eligió retrospectivamente otra de las cinco variantes por su test. Los checkpoints y las curvas se conservan.

La alternativa congeló ResNet18 con pesos oficiales ImageNet y aprendió una capa lineal de tres salidas mediante regresión logística multinomial regularizada. Una capa lineal seguida de softmax es la cabeza clasificadora de esta CNN; no es una etiqueta fija ni una llamada a un servicio externo. Se extrajeron 512 rasgos por vista y se entrenó con cuatro vistas deterministas por foto. Las vistas de una pieza nunca se reparten entre train y validación de un fold. La imagen de entrada es 224×224 con normalización ImageNet; la aplicación utiliza exactamente ese preprocesamiento.

Se compararon C=0,01; 0,1; 1 en cinco folds estratificados por bloque sobre 408 fotos. C=0,01 obtuvo media de macro-F1 por fold 0,9518 y macro-F1 agregado fuera de fold 0,9531, con accuracy 389/408 = 0,9534. Recall agregado: impresos 131/136; manuscritos 123/136; pinturas 135/136. La variación entre folds está en el JSON. Se entrenó la cabeza definitiva con las 408 imágenes y se guardó toda la CNN para inferencia autónoma.

El diagnóstico secundario de 72 fotos obtuvo 67/72 = 0,9306 y macro-F1 0,9298. Los cinco fallos fueron manuscritos sugeridos como impresos; recall de manuscritos 19/24 = 0,7917. Los 24 impresos y las 24 pinturas se clasificaron correctamente en ese conjunto. La decisión de despliegue se basó en un criterio previo de CV agregado —macro-F1 ≥0,85 y recall de cada clase ≥0,80—, no en optimizar hasta alcanzar un número en test. La aplicación siempre solicita confirmación de clase.

La comparación CNN/transferencia no es una ablación de arquitectura pura: la segunda usa preentrenamiento externo, 408 imágenes de desarrollo y selección cruzada; la primera usó 336 de entrenamiento y un holdout de validación. Es evidencia operativa de una alternativa útil bajo el presupuesto, no una estimación causal de cuánto aporta cada factor.

Se añadió una ANN con 48 bins de histogramas RGB, densidad de borde y varianza logarítmica del Laplaciano. La normalización de esos 50 rasgos se ajusta solo en train. Su resultado y entrenamiento están en `results/classification/ann_baseline.json`. Este baseline comprueba cuánto puede resolverse con rasgos sencillos y hace visible el riesgo de aprender el fondo.

Las puntuaciones softmax no están calibradas. Incluso una predicción muy segura puede ser incorrecta, sobre todo fuera del dominio. No se inventa una probabilidad de fidelidad ni un detector de clases desconocidas. Con pocos objetos, ajustar temperatura y evaluarla sobre los mismos ejemplos daría una apariencia de rigor injustificada. [Guo et al., calibración de redes](https://proceedings.mlr.press/v70/guo17a.html).

### Localización y perspectiva

| Prueba | Resultado observado | Interpretación |
|---|---|---|
| Canny/contornos básico en 80 anotadas | 16/80 con IoU de cuadrilátero ≥0,90 | Insuficiente como única ruta automática |
| Variantes clásicas en las mismas 80 | 32/80 con IoU ≥0,90 | Mejoran, pero el fondo sigue siendo difícil |
| U-Net + cuadrilátero en las mismas 80 | 80/80 con IoU ≥0,90 | Diagnóstico con datos de entrenamiento incluidos; no generalización |
| U-Net en 12 de la prueba histórica | Dice medio 0,99312; IoU máscara 0,98636 a 256 px | Reproducción estrecha del dominio documental original |
| Cuadrilátero en esas 12 | IoU media 0,96815 a escala máxima 960; 11/12 ≥0,95 | Mide la salida geométrica efectivamente usada |
| 24 manuscritos/pinturas + 5 escenas extra | Revisión visual; recortes parciales y fusiones observadas | No hay GT y no se asigna una tasa de acierto |

La IoU aquí compara polígonos rasterizados con máscaras en coordenadas de imagen. No es idéntica a la medida de SmartDoc en coordenadas del documento rectificado. El tiempo de inferencia y posprocesamiento de la U-Net fue aproximadamente 55 ms de mediana en la prueba de 12, CPU con cuatro hilos; excluye carga en frío y lectura de archivo. Las pruebas de software verifican además que una homografía conocida lleve esquinas a su destino y que rechace geometría inválida.

### Mejora con una referencia construida

Se creó una página impresa sintética de 600×800 con tinta conocida. Sobre ella se aplicaron sombra suave, ruido gaussiano, desenfoque y control sin degradación. Es una sonda del comportamiento de métodos, no un benchmark representativo de patrimonio. Los parámetros se escogieron para ese experimento y no se trasladan como parámetros universales a la aplicación.

| Caso | Antes | Método y después | Lección |
|---|---|---|---|
| Sombra suave | SSIM 0,840; PSNR 10,50 dB | División gaussiana: 0,927 y 25,86 dB | Estimar iluminación puede ayudar más que aumentar contraste |
| Misma sombra | SSIM 0,840 | CLAHE aislado: 0,701 | Aplicar siempre CLAHE es una mala regla |
| Tinta bajo sombra | F1 Otsu 0,269 | F1 Sauvola 0,908 | Umbral local útil en este caso |
| Ruido | PSNR 28,26; SSIM 0,546 | Bilateral: 33,68 y 0,833 | Filtrar depende del tipo de degradación |
| Desenfoque | PSNR 19,42; SSIM 0,830 | Enfoque moderado: 19,81 y 0,847 | El beneficio es pequeño; no reconstruye texto ausente |
| Página limpia | Referencia exacta | El enfoque reduce SSIM a 0,981 | La operación identidad es una opción necesaria |

El benchmark reproducible añadido al repositorio también ensaya las funciones reales de la aplicación y una variante FFT firmada. Se diferencia de esta sonda inicial, cuyo objetivo fue comparar familias de métodos. No se presentan sus cifras como idénticas porque cambian mezcla, fondo objetivo y parámetros.

SSIM/PSNR se calculan con referencia alineada, igual forma y rango de datos explícito. Igualar dimensiones no registra dos fotos. La interfaz habitual no dispone de una referencia verdadera: por eso muestra «no disponibles» y ofrece descriptores de nitidez/contraste con su advertencia. Estos no se suman en un supuesto índice de calidad. [API oficial de métricas](https://scikit-image.org/docs/stable/api/skimage.metrics.html).

## 6. Plan de evaluación pendiente y criterio de aceptación

La verificación de ingeniería comprueba carga real de modelos, predicciones, transformaciones, aislamiento de sesiones, exportación, deshacer, datos inválidos e interfaz de escritorio/móvil. Las pruebas automáticas no sustituyen evaluación de utilidad con personas. Tampoco una colección de capturas de pantalla prueba generalización.

Antes de cerrar académicamente: (1) revisar las identidades mediante `03_Revisar_piezas.html`; (2) reservar 6–9 piezas físicas realmente nuevas, dos vistas cada una y las tres clases; (3) congelar pesos y parámetros antes de abrir esa prueba; (4) anotar clase, esquinas y aceptación de detalles; (5) medir predicción, IoU/errores de borde si se anotan, tiempo, correcciones y resultado aceptado/rechazado. Doce o dieciocho fotos siguen siendo una prueba pequeña: informar recuentos por pieza, no solo porcentajes. No mezclar fotos aumentadas como si fueran observaciones independientes.

Si se modifica la agrupación, se crea otro manifiesto y se conservan sus hashes. La independencia se verifica por pieza y por derivación. Cambiar el CSV no vuelve nuevos los pesos antiguos de la U-Net; para una evaluación integral hace falta prueba nueva o reentrenar bajo partición común. [StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html) garantiza separación según los IDs suministrados, pero no verifica que esos IDs sean verdaderos.


Una foto muy borrosa, con reflejos o información recortada debe repetirse. El modo manual permite corregir localización y categoría; no convierte una entrada ilegible en una captura válida. Los casos fallidos forman parte de la demostración y explican el alcance.

## 7. Automatización y trabajo humano

| Trabajo | Automatización disponible | Intervención humana necesaria |
|---|---|---|
| Inventario, extracción y duplicados | Scripts y hashes | Confirmar interpretación de piezas ambiguas |
| Datos y particiones | Propuesta de grupos, editor visual y script de nueva separación | Revisar identidad física; no marcar todo sin inspección |
| Entrenamiento y evaluación | Pesos, semillas, curvas, matrices y predicciones exportadas | Ninguna para ejecutar; revisión académica de conclusiones |
| Aplicación y exportaciones | Flujo local completo y pruebas automatizadas | Confirmar categoría, esquinas y aceptación del resultado |
| Referencias de calidad | Degradaciones sintéticas reproducibles | Capturar pares reales o piezas nuevas si se desea evidencia externa |
| Documentos y comunicación | Ruta, informe, notebook, póster, presentación y demo | Verificar autores, criterio docente, ensayar y sustentar |
| GitHub y acceso | Repositorio y release preparados/publicados con autorización | Probar acceso del docente; decidir qué datos identificables compartir |

Presupuesto humano orientativo: revisión de grupos 45–90 min; nuevas capturas 45–90 min; revisión de salidas y anotación 45–90 min; pruebas de uso 45–60 min; lectura/ensayo 2–3 h; accesos y verificación de entrega 20–30 min. Son estimaciones, no tiempos observados. Pueden repartirse entre los tres integrantes, pero el núcleo no depende de que los tres programen. El cronograma completo reserva 20 h esenciales y 10 h de contingencia durante cinco días.

## 8. Entregables y relación con la rúbrica

El repositorio debe abrir con un README que explique problema, autores, datos, instalación, ejecución, arquitectura, entrenamiento, evaluación y limitaciones; enlaces reales a pesos y datos accesibles para el evaluador. Los archivos privados pueden estar en una release privada, pero su acceso debe verificarse desde la cuenta del docente. No se inventan enlaces públicos ni se supone que iniciar sesión como autor equivale a acceso externo.

El póster presenta objetivo, flujo, datos, métodos, evidencia cuantitativa y límites. Las cifras provisionales se rotulan en la misma figura. El video dura como máximo tres minutos y muestra una ejecución real de la aplicación, incluidos modelo, corrección, comparación y exportación; los subtítulos no atribuyen pruebas humanas inexistentes. La presentación permite explicar CNN, transferencia, máscara, homografía, filtros y evaluación, además de responder por qué se descartó generación.

El resultado es un prototipo académico funcional, local y reproducible. Quedan fuera: OCR como prueba de fidelidad, clasificación de cualquier objeto desconocido, restauración generativa, geometría 3D, escaneo masivo y certificación patrimonial. Estas exclusiones mantienen el mismo propósito útil de la propuesta y hacen defendible el alcance de cinco días.
