"""Servidor de demostración HTTPS mediante túnel; un proceso conserva las sesiones."""
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
research_deps = ROOT.parent.parent / 'work/pydeps'
if research_deps.exists():
    sys.path.insert(0, str(research_deps))

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
    server.models = server.ModelService(ROOT / 'models')
    if any(x is None for x in (server.models.classifier, server.models.segmenter, server.models.scope_bank)):
        raise RuntimeError('No se publica una demo sin las dos redes y el filtro de alcance activos. Revisa los pesos v0.4.0.')
    threading.Thread(target=cleanup_loop, daemon=True).start()
    # Solo cloudflared en este mismo computador puede acceder al puerto.
    # Waitress reconoce HTTPS desde ese proxy, de modo que Origin y cookies
    # mantienen sus comprobaciones sin aceptar orígenes externos arbitrarios.
    serve(server.app, host='127.0.0.1', port=int(os.getenv('PALIMPSESTO_PUBLIC_PORT', '8766')),
          threads=4, connection_limit=40, channel_timeout=45,
          max_request_body_size=42 * 1024 * 1024,
          trusted_proxy='127.0.0.1', trusted_proxy_count=1,
          trusted_proxy_headers={'x-forwarded-proto'})


if __name__ == '__main__':
    main()
