# Video de Palimpsesto · guion de voz (opcional)

El video `palimpsesto_video.mp4` dura **2:40** y se entiende solo, porque los rótulos explican cada escena. Si el equipo quiere ponerle voz, este guion encaja en los tiempos exactos del video, así que no hay que reeditar nada.

## Cómo grabar

1. Reproduzcan el video **sin sonido** en el computador.
2. Graben con el celular **mientras lo miran**, en un lugar silencioso y con el celular a unos 20 cm de la boca.
3. Hagan **un archivo por bloque** (A, B y C), empezando a hablar cuando el video llegue al tiempo indicado. Si se equivocan, repitan solo ese bloque.
4. Nombren los archivos `bloque_A`, `bloque_B` y `bloque_C`, en cualquier formato del celular (m4a, mp3 o wav).

Yo los alineo con el video, igualo el volumen y quito ruido de fondo. No pasa nada si una frase queda medio segundo antes o después. La música de fondo (original, compuesta para el video) baja automáticamente mientras hablan.

Sugerencia de reparto, para que se note la participación de todos: **bloque A** Expositor 1, **bloque B** Expositor 2 y **bloque C** Expositor 3.

Ritmo: unas 2,5 palabras por segundo. Si una frase no cabe, se puede acortar sin problema.

---

## Bloque A · Presentación (0:00 – 0:46)

| Tiempo | En pantalla | Voz |
|---|---|---|
| 0:00 – 0:06 | Portada | Somos el equipo de Palimpsesto: una nueva mirada, la misma pieza. |
| 0:06 – 0:17 | El problema | Manuscritos, documentos y pinturas suelen conocerse por fotos de celular: torcidas, con sombras o desenfoque. Y el error se descubre cuando ya no se puede repetir la foto. |
| 0:17 – 0:28 | Un asistente en cinco pasos | Palimpsesto lo resuelve en cinco pasos: cargar, identificar, encuadrar, mejorar y guardar. Las redes sugieren, el PDI clásico transforma, y el usuario decide en cada paso. |
| 0:28 – 0:37 | Datos | Usamos fotos reales tomadas por el equipo: 480 para clasificar y 240 con máscara para segmentar, separadas por pieza para no inflar las métricas. |
| 0:37 – 0:46 | Arquitectura | Una ResNet18 sugiere el tipo, una U-Net encuentra el borde, y OpenCV corrige la perspectiva y la iluminación, todo en local. |

## Bloque B · Demostración (0:46 – 1:51)

| Tiempo | Rótulo en pantalla | Voz |
|---|---|---|
| 0:46 – 0:52 | «Demostración en vivo» / «1 · Cargamos una foto…» | Veamos la aplicación. Cargamos una foto movida de una pintura… |
| 0:52 – 0:58 | «El semáforo de la captura la detecta al instante» | …y el semáforo de la captura nos pide repetirla en el momento. |
| 0:58 – 1:00 | «La repetimos: ahora la foto sirve» | La repetimos. |
| 1:00 – 1:06 | «2 · La ResNet18 sugiere el tipo de pieza» | La ResNet18 sugiere «pintura», y nosotros lo confirmamos. |
| 1:06 – 1:13 | «3 · La U-Net propone las cuatro esquinas» | La U-Net propone las cuatro esquinas y nos dice que el borde es seguro. |
| 1:13 – 1:18 | «Ver lo que vio la red» | Podemos ver la máscara en la que se basó la red… |
| 1:18 – 1:21 | «Las esquinas siempre se pueden corregir a mano» | …y corregir cualquier esquina a mano. |
| 1:21 – 1:31 | «4 · Homografía» / «Comparación antes / después» | La homografía deja la pintura en vista frontal, y comparamos el antes y el después. |
| 1:31 – 1:39 | «Mejoras clásicas ajustables» | Ajustamos el contraste local con CLAHE, y el histograma muestra cómo cambian los tonos. |
| 1:39 – 1:51 | «5 · Exportamos la copia de consulta» | Por último exportamos PNG, PDF, el registro de decisiones y un ZIP con el original intacto. |

## Bloque C · Resultados y cierre (1:51 – 2:40)

| Tiempo | En pantalla | Voz |
|---|---|---|
| 1:51 – 2:02 | La transferencia superó a la CNN propia | En resultados: la ResNet18 acertó 70 de 72 fotos de diagnóstico, frente a 52 de nuestra CNN propia, que con pocas fotos memorizaba el fondo. |
| 2:02 – 2:12 | 160 máscaras nuevas mejoraron el borde | Con 160 máscaras nuevas, la coincidencia del borde subió de 0,81 a 0,94; en pinturas, de 0,58 a 0,88. |
| 2:12 – 2:22 | ¿La foto es realmente una pieza? | Y el aviso de fotos que no son piezas pasó de detectar 13 de 30 a 16 de 18 en una prueba ciega. |
| 2:22 – 2:33 | Conclusiones | Lo central: la CNN no restaura la imagen, decide cómo debe restaurarse. Nos queda probar con más piezas nuevas. |
| 2:33 – 2:40 | Gracias | Todo está en nuestro repositorio. ¡Gracias! |
