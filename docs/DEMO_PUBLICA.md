# Demo HTTPS gratuita desde el computador

## Iniciar y detener

1. Instala el proyecto según README. Los pesos v0.4.0 se descargan y verifican solos la primera vez; cuando `main` pida otros pesos, el gestor los baja de su release antes de reiniciar. Deben funcionar las dos redes y el filtro de alcance.
2. Ejecuta `Iniciar_Enlace_Publico.cmd`. Se añade Waitress si falta y se descarga el conector oficial Cloudflare 2026.11.1, verificando su SHA-256.
3. Comparte el enlace `https://…trycloudflare.com` de la consola o `.public_runtime/enlace.txt`.
4. Mantén el computador encendido, conectado y sin suspensión durante la prueba. No se modifica automáticamente la configuración energética del sistema.
5. Para cerrar, ejecuta `Detener_Enlace_Publico.cmd` o pulsa Ctrl+C en el gestor. El enlace deja de funcionar.

No requiere cuenta, tarjeta, dominio ni plan. [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) es un servicio para pruebas: URL temporal, sin garantía de disponibilidad; al reiniciar cambia. No equivale a alojamiento de producción permanente.

## Cambios de GitHub

Fuente única: `https://github.com/juanffff-hub/palimpsesto-pdi`, rama `main`. El gestor consulta cambios cada 90 segundos y trabaja en `.public_runtime/source`, sin sobrescribir la carpeta de desarrollo. La URL se conserva mientras el túnel permanece abierto. Las actualizaciones de aplicación esperan a que no haya sesiones activas; un reinicio elimina las sesiones que lleguen durante el cambio. Descargar resultados antes de actualizar.

Una reescritura de autores que conserve los archivos no reinicia la aplicación: se compara el contenido entre commits, sin exigir una historia lineal. Los cambios de dependencias requieren actualizar el entorno; los nuevos pesos deben instalarse y coincidir con `models/checksums.json`. En esos casos el gestor informa el problema y mantiene la versión anterior cuando es posible. No se instalan nuevas bibliotecas ni se entrena automáticamente al recibir un commit.

Si el servidor no puede arrancar después de un cambio, se intenta volver al commit anterior. Los registros están en `.public_runtime/launcher.log`, `server.log` y `tunnel.log`. `.public_runtime/estado.json` muestra el commit realmente ejecutado. Si se pierde Internet, cambia la red o el equipo se suspende, puede ser necesario reiniciar el gestor y compartir el enlace nuevo.

## Sesiones y privacidad

Las fotos viajan por HTTPS a través de Cloudflare al computador anfitrión. No se añaden al dataset ni se usan para entrenar. Cada navegador mantiene su propia sesión; no puede consultar la foto de otro navegador con su identificador. El servidor guarda imágenes y resultados durante la sesión; elimina sesiones inactivas tras 15 minutos, con revisión cada 30 segundos. Cerrar la pestaña por sí solo no avisa al servidor. «Trabajar otra fotografía» borra la sesión anterior.

La demo atiende hasta cinco sesiones y serializa el procesamiento. Si otro procesamiento está en curso, una operación nueva recibe una explicación y puede reintentarse; no se afirma progreso inventado. Waitress usa un único proceso y escucha solo en `127.0.0.1:8766`. Se conserva el modo local original en el puerto 8765.

Las comprobaciones específicas del acceso remoto están en `tests/test_public_demo.py`. No modifican ni recalculan las métricas científicas del modelo.

## Enlace permanente en Hugging Face Spaces

Para que la aplicación funcione sin depender de este computador se puede publicar gratis en Hugging Face Spaces (plan CPU básico: 2 CPU y 16 GB de RAM). El enlace es fijo, del tipo `https://USUARIO-palimpsesto.hf.space`. Si pasa unas 48 horas sin visitas el Space se duerme; la siguiente visita lo despierta en uno o dos minutos.

1. Crear una cuenta gratuita en huggingface.co y un token con permiso de escritura (Settings › Access Tokens).
2. Iniciar sesión una vez en esta carpeta: `.venv\Scripts\hf auth login` (el token lo pega cada persona; no se guarda en el repositorio).
3. Publicar: `.venv\Scripts\python.exe scripts/deploy_hf.py --space USUARIO/palimpsesto`.

`scripts/deploy_hf.py` sube solo lo necesario para ejecutar la aplicación (código, interfaz, `requirements.txt` y los archivos pequeños de `models/`) junto con `deploy/huggingface/Dockerfile` y la ficha `deploy/huggingface/README.md`. La imagen descarga los pesos v0.4.0 de la release de GitHub y los verifica por SHA-256 al construirse. El contenedor ejecuta `run_public.py` en el puerto 7860 con estas variables:

| Variable | Valor en Spaces | Para qué |
|---|---|---|
| `PALIMPSESTO_PUBLIC_HOST` | `0.0.0.0` | Escuchar dentro del contenedor |
| `PALIMPSESTO_PUBLIC_PORT` | `7860` | Puerto que espera Spaces |
| `PALIMPSESTO_TRUSTED_PROXY` | `*` | Reconocer HTTPS desde el proxy de Spaces (`X-Forwarded-Proto`) |
| `PALIMPSESTO_EMBEDDED` | `1` | Cookie de sesión `SameSite=None`, para que funcione dentro del iframe de la página del Space |

La comprobación de `Origin` sigue activa: una petición desde otro sitio se rechaza. Sin estas variables, `run_public.py` se comporta como antes (solo `127.0.0.1`, para el túnel de Cloudflare). Para actualizar el Space después de un cambio en `main`, basta con volver a ejecutar el paso 3.

