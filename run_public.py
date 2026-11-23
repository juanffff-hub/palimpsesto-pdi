"""Servidor de demostración HTTPS (túnel local o Hugging Face Spaces); un proceso conserva las sesiones.

Por defecto escucha solo en 127.0.0.1 para el túnel de Cloudflare. En un contenedor se configura con:
  PALIMPSESTO_PUBLIC_HOST    interfaz de escucha (0.0.0.0 en el contenedor)
  PALIMPSESTO_PUBLIC_PORT    puerto (7860 en Hugging Face Spaces)
  PALIMPSESTO_TRUSTED_PROXY  proxy que informa HTTPS con X-Forwarded-Proto (* en Spaces)
  PALIMPSESTO_EMBEDDED=1     cookie de sesión SameSite=None, para funcionar dentro del iframe de Spaces
"""
import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
from palimpsesto import server


def purge_expired():
    with server.operation_lock, server.lock:
        now = time.monotonic()
        for key in list(server.states):
            if now - server.states[key]['access'] > server.app.config['SESSION_TTL_SECONDS']:
                server.states.pop(key, None)


def cleanup_loop():
    while True:
        time.sleep(30)
        purge_expired()


def main():
    from waitress import serve
    server.app.config.update(PUBLIC_DEMO=True, SESSION_COOKIE_SECURE=True,
                             SESSION_TTL_SECONDS=900, MAX_ACTIVE_SESSIONS=5)
    if os.getenv('PALIMPSESTO_EMBEDDED') == '1':
        # Dentro de un iframe de otro sitio una cookie Strict no viaja; la comprobación de Origin sigue activa.
        server.app.config.update(SESSION_COOKIE_SAMESITE='None')
    from palimpsesto.weights import ensure_models
    ensure_models(ROOT / 'models')
    server.models = server.ModelService(ROOT / 'models')
    if any(x is None for x in (server.models.classifier, server.models.segmenter, server.models.scope_bank)):
        raise RuntimeError('No se publica una demo sin las dos redes y el filtro de alcance activos. Revisa los pesos v0.4.0.')
    threading.Thread(target=cleanup_loop, daemon=True).start()
    # Por defecto solo cloudflared en este mismo computador puede acceder al puerto.
    # Waitress reconoce HTTPS desde ese proxy, de modo que Origin y cookies
    # mantienen sus comprobaciones sin aceptar orígenes externos arbitrarios.
    serve(server.app, host=os.getenv('PALIMPSESTO_PUBLIC_HOST', '127.0.0.1'),
          port=int(os.getenv('PALIMPSESTO_PUBLIC_PORT', '8766')),
          threads=4, connection_limit=40, channel_timeout=45,
          max_request_body_size=42 * 1024 * 1024,
          trusted_proxy=os.getenv('PALIMPSESTO_TRUSTED_PROXY', '127.0.0.1'), trusted_proxy_count=1,
          trusted_proxy_headers={'x-forwarded-proto'})


if __name__ == '__main__':
    main()
