# Guía de sustentación

Equipo: Neira, Gómez y Fajardo. Confirmar nombres completos, institución y fecha de entrega con el material oficial antes de presentar.

## Recorrido sugerido (8–10 minutos, ajustar al docente)

1. Problema y alcance: una fotografía de una pieza plana; salida de consulta con original preservado.
2. Datos: 480 fotos no son 480 piezas. Explicar bloques provisionales, derivados y fuga por objeto.
3. Red: CNN propia y sus cinco variantes; por qué 97 % de validación no bastó. Mostrar la matriz de 72 fotos.
4. Transferencia: ResNet18 congelada, 512 rasgos, cabeza lineal de tres clases. Solo se aprende esa cabeza; se exporta la red completa.
5. Segmentación: U-Net predice máscara por píxel; el cuadrilátero se deriva y se revisa. No confundir máscara con caja.
6. Geometría: cuatro correspondencias, matriz 3×3 hasta escala; puntos no colineales, plano y proporción física opcional.
7. Mejora: estimación de fondo, CLAHE, bilateral y unsharp; pintura inicia neutra. Explicar signo, flotantes y canales.
8. Evaluación: macro-F1, confusión, Dice/IoU, SSIM/PSNR solo alineados. Presentar limitaciones antes de conclusiones.
9. Demo real: cargar, confirmar clase, mover esquina, ajustar, deshacer, exportar; abrir PDF y mostrar original/JSON.
10. Trabajo pendiente humano: agrupación, piezas nuevas, usabilidad y acceso docente.

## Preguntas que el equipo debe poder responder

- ¿Por qué la CNN no restaura? Clasifica la pieza para sugerir tratamiento; U-Net localiza; los filtros mejoran de forma determinista.
- ¿Por qué no entrenar todo desde cero? La CNN propia se probó y falló fuera de su validación; transferencia reduce parámetros aprendidos y tiempo.
- ¿Por qué no se puede decir accuracy final 93 %? Son 72 fotos correlacionadas y un diagnóstico reutilizado; falta confirmar grupos y prueba externa.
- ¿Qué información recupera unsharp? Realza contraste local de bordes existentes; no conoce letras ausentes.
- ¿Por qué dos imágenes del mismo tamaño no sirven automáticamente para SSIM? Pueden representar posiciones diferentes; hace falta registro y referencia pertinente.
- ¿Por qué no se usa difusión? Puede producir contenido plausible sin fidelidad; no hay referencias para validarla en este alcance.
- ¿Qué sucede si el modelo falla? La persona corrige clase o esquinas. Si la captura perdió información, hay que repetirla.
- ¿La fotografía de una pintura conserva color exacto? No se dispone de calibración colorimétrica; se evita modificación automática pero no se certifica fidelidad.

## Cierre humano de la entrega

Revisar identidades físicas en la herramienta HTML; ejecutar prueba nueva con pesos congelados; llenar CSV de usabilidad con observaciones reales; comprobar que los enlaces abran desde la cuenta del evaluador; ensayar la demo offline y la explicación de las fórmulas.
