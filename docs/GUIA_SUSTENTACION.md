# Guía de sustentación

Equipo: Neira, Gómez y Fajardo. Confirmar nombres completos, institución y fecha de entrega con el material oficial antes de presentar.

## Recorrido sugerido (8–10 minutos, ajustar al docente)

1. Problema y alcance: una fotografía de una pieza plana; salida de consulta con original preservado.
2. Datos: 480 fotos no son 480 piezas. Explicar bloques provisionales, derivados y fuga por objeto.
3. Red: CNN propia y sus cinco variantes; por qué 97 % de validación no bastó. Mostrar la matriz de 72 fotos.
4. Transferencia: ResNet18 congelada, 512 rasgos, cabeza lineal de tres clases. Solo se aprende esa cabeza; se exporta la red completa.
5. Segmentación: U-Net predice máscara por píxel; el cuadrilátero se deriva y se revisa. No confundir máscara con caja. Mostrar la ampliación a 3 clases: misma receta del parcial, 160 máscaras nuevas, regla fijada antes de entrenar y 0,811 → 0,937.
6. Geometría: cuatro correspondencias, matriz 3×3 hasta escala; puntos no colineales, plano y proporción física opcional.
7. Mejora: estimación de fondo, CLAHE, bilateral y unsharp; pintura inicia neutra. Mostrar el histograma y subir la iluminación al máximo en un manuscrito para enseñar el aviso de tonos recortados. Explicar signo, flotantes y canales.
8. Evaluación: macro-F1, confusión, Dice/IoU, SSIM/PSNR solo alineados. Presentar limitaciones antes de conclusiones.
9. Demo real: cargar una foto borrosa para mostrar el semáforo en rojo y otra buena; confirmar clase, mover esquina, ajustar, deshacer, exportar; abrir PDF y mostrar original/JSON.

## Preguntas que el equipo debe poder responder

- ¿Por qué la CNN no restaura? Clasifica la pieza para sugerir tratamiento; U-Net localiza; los filtros mejoran de forma determinista.
- ¿Por qué no entrenar todo desde cero? La CNN propia se probó y falló fuera de su validación; transferencia reduce parámetros aprendidos y tiempo.
- ¿Por qué no se puede decir accuracy final 93 %? Son 72 fotos correlacionadas y un diagnóstico reutilizado; falta confirmar grupos y prueba externa.
- ¿Qué información recupera unsharp? Realza contraste local de bordes existentes; no conoce letras ausentes.
- ¿Por qué dos imágenes del mismo tamaño no sirven automáticamente para SSIM? Pueden representar posiciones diferentes; hace falta registro y referencia pertinente.
- ¿Por qué no se usa difusión? Puede producir contenido plausible sin fidelidad; no hay referencias para validarla en este alcance.
- ¿Cómo saben que la U-Net nueva es mejor y no solo distinta? La regla de adopción se escribió antes de entrenar, la prueba es por pieza (piezas que la red no vio) y se compara con lo que hacía la v0.3.0 con la misma función de la aplicación; además se repitió con 3 semillas.
- ¿Por qué la máscara de las pinturas incluye el marco? El marco forma parte de la pieza fotografiada y da un borde recto y estable para la homografía; quien quiera solo el lienzo puede mover las esquinas.
- ¿Cómo mejoraron el control de alcance sin hacer trampa? El 13/30 de la v0.4.0 llevó a crear negativos nuevos de desarrollo, agrupados por identidad. Con la foto entera ningún método mejoraba, porque las fotos comparten interiores; recortar la pieza con la U-Net sí (79/88). El método, el umbral y la regla se congelaron en un commit antes de abrir una prueba ciega nueva, que se ejecutó una sola vez: 16/18. La confirmación manual se mantiene.
- ¿Para qué sirve el histograma si ya hay métricas de nitidez y contraste? Esas métricas suben con cualquier ajuste; el histograma y el recorte medido píxel a píxel muestran si el ajuste destruyó detalle (negros o blancos puros nuevos) y dónde. Con los preajustes no pasa en ninguna de 240 fotos.
- ¿Cómo sabe la app que el borde es dudoso sin conocer la respuesta correcta? Mide la coherencia de la propia red: si los cuatro puntos no encajan con su máscara (IoU < 0,92) o si el contorno es difuso (franja incierta > 5 px). Umbrales elegidos en validación; en prueba detectó los 21 bordes malos con 10 falsas alarmas de 98.
- ¿Cómo sabe el semáforo que la foto está borrosa si una pintura lisa también tiene pocos bordes? Mide solo la pieza (máscara de la U-Net), toma el bloque más nítido y usa un umbral distinto para pinturas; el temblor se detecta porque deja una dirección mucho más nítida que la otra. Umbrales calibrados con las 480 fotos y verificados con defectos controlados y revisión visual.
- ¿Qué sucede si el modelo falla? La persona corrige clase o esquinas. Si la captura perdió información, hay que repetirla.
- ¿La fotografía de una pintura conserva color exacto? No se dispone de calibración colorimétrica; se evita modificación automática pero no se certifica fidelidad.

## Cierre humano de la entrega
