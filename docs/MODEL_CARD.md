# Modelos de Palimpsesto 0.2.0

## Clasificador operativo

ResNet18 preentrenada ImageNet-1K oficial de torchvision, encoder congelado, cabeza lineal multiclase entrenada mediante regresión logística ponderada L2 sobre embeddings de 512 dimensiones. El archivo contiene la red completa; inferencia PyTorch CPU local. RGB redimensionado a 224×224 (INTER_AREA), /255, media [0.485,0.456,0.406], desviación [0.229,0.224,0.225]. Clases en orden: documento_impreso, manuscrito, pintura.

408 fotos de desarrollo de 41 bloques provisionales. Cuatro vistas deterministas por foto para entrenamiento; validación con original. C entre 0.01, 0.1 y 1 mediante cinco folds StratifiedGroupKFold, semilla 2026, selección por macro-F1 medio. Elegido C=0.01. Puerta de despliegue predefinida: F1 OOF ≥0.85 y recall por clase ≥0.80. Cumplida. Métricas exactas y folds: `results/transfer/evaluation.json`.

389/408 OOF; diagnóstico secundario 67/72, matriz [[24,0,0],[5,19,0],[0,0,24]]. Cinco errores manuscrito→impreso. El conjunto secundario se había observado al evaluar la CNN del curso, por lo que no es confirmación ciega. La CV participa en elección de hiperparámetro, por lo que tampoco equivale a evaluación externa sin selección. Una sola semilla, bloques sin certificación física. Las puntuaciones no están calibradas como probabilidades de certeza. Rotaciones de 90° empeoran el diagnóstico; ver robustez.

## Baselines y segmentación

CNN del curso: cuatro convoluciones 16/32/64/128, pooling, AdaptiveAvgPool 4×4, FC64→3; cinco variantes base/dropout/L2/augmentación/combinada. L2 elegida por validación; test 52/72. ANN50→32→3 sobre histogramas RGB, bordes y nitidez; 47/72. Conservar como resultados, no sustituir sus cifras por las del modelo transferido.

U-Net con encoder ResNet18, checkpoint del material suministrado y normalización ImageNet, entrada 256×256. Dice 0.9931 e IoU 0.9864 en 12 fotos de test histórico. No fue reentrenada como si tuviera partición nueva. Contornos/método manual cubren casos fuera de dominio. La sugerencia de borde exige revisión.

## Control de alcance

Banco de 408 embeddings normalizados, media de tres similitudes coseno máximas. Umbral percentil 3 de similitudes de desarrollo excluyendo vecinos del mismo grupo. Banco ligado por SHA256 al checkpoint y manifiesto. Su propósito es pedir revisión, no determinar todos los objetos que existen. Evaluación exploratoria: 9/10 negativos avisados; falso negativo astronaut. No usar estos casos para optimizar y luego volver a reportarlos como validación independiente.

Recalibrar con `scripts/calibrate_scope.py` después de cambiar clasificador/manifiesto. Un banco incompatible se desactiva explícitamente. El frontend siempre pide confirmar una pieza plana; puede aceptar una pieza válida atípica tras revisión. No identifica rostros ni personas.

## Reproducción y uso

Pesos y sus hashes en `models/`; código de entrenamiento/evaluación en `scripts/`. El paquete completo incluye todos los checkpoints, datos y resultados; la release de modelos permite inferencia sin material docente. No cambiar parámetros ni entrenar mirando nuevas fotos de prueba. Para afirmar generalización, congelar esta versión y usar piezas nuevas etiquetadas por humanos.

Uso previsto académico, fotografías de una sola pieza plana; no validado para preservación profesional ni despliegue público. El preentrenamiento y bibliotecas conservan sus licencias; no se afirma propiedad sobre modelos o fotografías del curso.
