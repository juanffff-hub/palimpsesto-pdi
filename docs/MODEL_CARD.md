# Modelos de Palimpsesto 0.4.0

## Clasificador operativo v0.3.0 (19 de noviembre de 2026)

Mismo encoder ResNet18 ImageNet congelado y misma arquitectura que la v0.2.0; solo cambia la cabeza lineal. Se entrenó con las cuatro vistas anteriores **más la foto original girada 90°, 180° y 270°**, con C=0,1 elegido por validación cruzada. Motivo: la v0.2.0 bajaba de 0,930 a 0,798 de macro-F1 con fotos giradas 90° en el diagnóstico de robustez.

Protocolo y regla de adopción fijados antes de ejecutar (`results/rotation/protocol.json`, `scripts/experiment_rotation.py`): mismos 5 folds por 41 bloques y misma rejilla C; solo desarrollo. Regla: macro-F1 OOF en fotos derechas ≥ base − 0,01, recall por clase ≥ 0,80 y macro-F1 OOF medio en fotos giradas ≥ base + 0,05. La variante base reprodujo exactamente la v0.2.0 (0,9531, C=0,01).

| | v0.2.0 | v0.3.0 |
|---|---:|---:|
| OOF fotos derechas (408) | 389/408 · macro-F1 0,9531 | 391/408 · macro-F1 0,9581 |
| OOF fotos giradas, media 90/180/270° | 0,8797 | 0,9548 |
| Diagnóstico secundario (72, ya abierto) | 67/72 · 0,9298 | 70/72 · 0,9722 |
| Diagnóstico con giro de 90° | 0,7979 | 0,9583 |
| Diagnóstico con brillo ×1,25 | 0,9722 | 0,9583 (un error más) |

Errores del diagnóstico v0.3.0: I0018 (impreso → manuscrito) e I0295 (manuscrito → impreso). Los 72 ya se habían abierto: **no es una prueba ciega**. El filtro de alcance se recalibró (el encoder no cambia; el umbral queda en 0,699008, por diferencias de redondeo de la CPU) y sigue alertando 9/10 negativos, 0/72 positivos. Modelo anterior conservado: `models/classifier_v0.2.0.pt` (SHA-256 `c8eaf87b…`). Hashes en `models/checksums.json`.

## Clasificador v0.2.0 (referencia histórica)

ResNet18 preentrenada ImageNet-1K oficial de torchvision, encoder congelado, cabeza lineal multiclase entrenada mediante regresión logística ponderada L2 sobre embeddings de 512 dimensiones. El archivo contiene la red completa; inferencia PyTorch CPU local. RGB redimensionado a 224×224 (INTER_AREA), /255, media [0.485,0.456,0.406], desviación [0.229,0.224,0.225]. Clases en orden: documento_impreso, manuscrito, pintura.

408 fotos de desarrollo de 41 bloques provisionales. Cuatro vistas deterministas por foto para entrenamiento; validación con original. C entre 0.01, 0.1 y 1 mediante cinco folds StratifiedGroupKFold, semilla 2026, selección por macro-F1 medio. Elegido C=0.01. Puerta de despliegue predefinida: F1 OOF ≥0.85 y recall por clase ≥0.80. Cumplida. Métricas exactas y folds: `results/transfer/evaluation.json`.

389/408 OOF; diagnóstico secundario 67/72, matriz [[24,0,0],[5,19,0],[0,0,24]]. Cinco errores manuscrito→impreso. El conjunto secundario se había observado al evaluar la CNN del curso, por lo que no es confirmación ciega. La CV participa en elección de hiperparámetro, por lo que tampoco equivale a evaluación externa sin selección. Una sola semilla, bloques sin certificación física. Las puntuaciones no están calibradas como probabilidades de certeza. Rotaciones de 90° empeoran el diagnóstico; ver robustez.

## U-Net de 3 clases v0.4.0 (20 de noviembre de 2026)

Misma arquitectura y receta del tercer parcial (`smp.Unet`, encoder ResNet18 ImageNet, 1 canal, 256×256; volteo y giro ≤12°, Soft Dice, Adam 5e-4, ReduceLROnPlateau, 35 épocas, checkpoint por pérdida de validación), entrenada con **240 fotos con máscara: 80 impresos del parcial, 80 manuscritos y 80 pinturas** anotados con polígonos en makesense.ai. En pinturas la máscara incluye el marco. Partición por bloque de pieza (`data/segmentation_manifest.csv`): 160/40/40; los impresos conservan la prueba del parcial. Checkpoint desplegado: semilla 42, época 18, Dice de validación 0,977 (`models/unet_resnet18_3clases.pth`).

Protocolo y regla fijados antes de entrenar (`results/segmentation/protocol.json`, `scripts/train_unet.py`, `scripts/evaluate_unet.py`). Métrica: IoU del cuadrilátero que propone la aplicación frente a la máscara, en 40 fotos de prueba de piezas no vistas. Comparación con la v0.3.0 en modo automático (U-Net del parcial en documentos, contornos en pinturas):

| Prueba (fotos) | v0.3.0 | v0.4.0 |
|---|---:|---:|
| Impreso (12) | 0,968 | 0,970 |
| Manuscrito (16) | 0,881 | 0,963 |
| Pintura (12) | 0,583 | 0,877 |
| Media de las 3 clases | 0,811 | 0,937 |

Se cumplieron las cuatro condiciones (media +0,03, ninguna clase −0,01, mismas o más detecciones, mejora con 3 semillas: 0,937 / 0,902 / 0,924). Tiempo mediano en CPU: 49 ms, igual que antes.

Confianza del borde (`imaging.border_confidence`): «dudosa» si el cuadrilátero encaja < 0,92 con la máscara o la franja incierta supera 5 px. En prueba marcó los 6 bordes malos de la U-Net desplegada (5 de 34 buenos como falsas alarmas). Ver `results/border_confidence/`.

Limitaciones: 8 piezas o bloques en prueba; pinturas con fondos del mismo color (PIN008) siguen siendo difíciles y solo 4/12 pinturas superan IoU 0,95. Los manuscritos elegidos tienen bordes rectos. La sugerencia de borde sigue exigiendo revisión humana. La U-Net del parcial se conserva (`unet_resnet18_imagenet.pth`) como línea base.

## Baselines y segmentación

CNN del curso: cuatro convoluciones 16/32/64/128, pooling, AdaptiveAvgPool 4×4, FC64→3; cinco variantes base/dropout/L2/augmentación/combinada. L2 elegida por validación; test 52/72. ANN50→32→3 sobre histogramas RGB, bordes y nitidez; 47/72. Conservar como resultados, no sustituir sus cifras por las del modelo transferido.

U-Net del Parcial 3 (línea base de la v0.4.0): encoder ResNet18, checkpoint del material suministrado y normalización ImageNet, entrada 256×256, entrenada solo con impresos. Dice 0.9931 e IoU 0.9864 en 12 fotos de test histórico; en pinturas, Dice 0,589. No fue reentrenada como si tuviera partición nueva. Contornos/método manual cubren casos fuera de dominio. La sugerencia de borde exige revisión.

## Control de alcance

Banco de 408 embeddings normalizados, media de tres similitudes coseno máximas. Umbral percentil 3 de similitudes de desarrollo excluyendo vecinos del mismo grupo. Banco ligado por SHA256 al checkpoint y manifiesto. Su propósito es pedir revisión, no determinar todos los objetos que existen. Evaluación exploratoria: 9/10 negativos avisados; falso negativo astronaut. No usar estos casos para optimizar y luego volver a reportarlos como validación independiente.

Recalibrar con `scripts/calibrate_scope.py` después de cambiar clasificador/manifiesto. Un banco incompatible se desactiva explícitamente. El frontend siempre pide confirmar una pieza plana; puede aceptar una pieza válida atípica tras revisión. No identifica rostros ni personas.

## Reproducción y uso

Pesos y sus hashes en `models/`; código de entrenamiento/evaluación en `scripts/`. El paquete completo incluye todos los checkpoints, datos y resultados; la release de modelos permite inferencia sin material docente. No cambiar parámetros ni entrenar mirando nuevas fotos de prueba. Para afirmar generalización, congelar esta versión y usar piezas nuevas etiquetadas por humanos.

Uso previsto académico, fotografías de una sola pieza plana; no validado para preservación profesional ni uso público masivo. La demo compartida es de alcance académico. El preentrenamiento y bibliotecas conservan sus licencias; no se afirma propiedad sobre modelos o fotografías del curso.
