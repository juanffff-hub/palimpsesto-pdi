"""Contratos nuevos del acceso remoto; no reevalúan calidad del modelo."""
import io
import threading
import time
import numpy as np
import pytest
from palimpsesto import server
from palimpsesto.imaging import encode_png
from run_public import purge_expired


class Models:
    classifier = True
    segmenter = True
    scope_bank = True
    errors = []

    def classify(self, rgb):
        return {'class': 'documento_impreso', 'available': True, 'scope': {'available': True, 'flagged': False}}

    def segment(self, rgb):
        return None


@pytest.fixture
def public(monkeypatch):
    monkeypatch.setitem(server.app.config, 'PUBLIC_DEMO', True)
    monkeypatch.setitem(server.app.config, 'SESSION_COOKIE_SECURE', True)
    monkeypatch.setitem(server.app.config, 'SESSION_TTL_SECONDS', 900)
    monkeypatch.setattr(server, 'states', {})
    monkeypatch.setattr(server, 'models', Models())
    return server.app.test_client()


def test_https_origin_and_secure_session(public):
    rgb = np.full((180,240,3),220,np.uint8)
    rgb[40:90,40:180] = 30
    response = public.post('/api/upload', data={'image': (io.BytesIO(encode_png(rgb)), 'demo.png')},
                           base_url='https://demo.trycloudflare.com', headers={'Origin': 'https://demo.trycloudflare.com'})
    assert response.status_code == 200
    cookie = response.headers['Set-Cookie']
    assert 'Secure;' in cookie and 'HttpOnly;' in cookie and 'SameSite=Strict' in cookie
    assert response.headers['Cache-Control'] == 'no-store'
    other = public.post('/api/reset', json={}, base_url='https://demo.trycloudflare.com', headers={'Origin': 'https://otro.example'})
    assert other.status_code == 403


def test_busy_response_does_not_block_health(public):
    entered = threading.Event()
    release = threading.Event()
    def hold():
        with server.operation_lock:
            entered.set()
            release.wait(5)
    worker = threading.Thread(target=hold)
    worker.start()
    assert entered.wait(2)
    try:
        response = public.post('/api/reset', json={})
        assert response.status_code == 503 and response.json['code'] == 'busy'
        assert response.headers['Retry-After'] == '3'
        assert public.get('/api/status').status_code == 200
    finally:
        release.set()
        worker.join(2)


def test_expiration_actually_removes_old_images(public):
    now = time.monotonic()
    server.states.update(old={'access': now-901}, fresh={'access': now})
    purge_expired()
    assert set(server.states) == {'fresh'}
    response = public.get('/api/status')
    assert response.json['active_sessions'] == 1 and response.json['local'] is False


def test_notice_only_in_shared_mode(public, monkeypatch):
    assert 'Cloudflare' in public.get('/').text
    monkeypatch.setitem(server.app.config, 'PUBLIC_DEMO', False)
    assert 'Cloudflare' not in public.get('/').text
