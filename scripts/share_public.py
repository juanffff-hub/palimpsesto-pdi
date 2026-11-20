"""Demo gratuita: Waitress + Quick Tunnel, con actualización desde main aislada."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.public_runtime'
SOURCE = STATE / 'source'
REMOTE = 'https://github.com/juanffff-hub/palimpsesto-pdi.git'
PORT = 8766
CF_URL = 'https://github.com/cloudflare/cloudflared/releases/download/2026.11.1/cloudflared-windows-amd64.exe'
CF_SHA = '341deda3db5ec498a0482254d6c38c0b7cf01a30c37bb5dd95d2216d08955e35'
MODEL_FILES = ('classifier.pt', 'unet_resnet18_imagenet.pth', 'scope_reference.npz')
GIT = shutil.which('git') or r'C:\Program Files\Git\cmd\git.exe'
CHILD_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def say(message):
    print(time.strftime('%H:%M:%S'), message, flush=True)


def git(*args, cwd=SOURCE):
    # Este repositorio es público. No se entrega ninguna credencial al servidor.
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    for key in ('GH_TOKEN', 'GITHUB_TOKEN'):
        env.pop(key, None)
    result = subprocess.run([GIT, '-c', 'credential.helper=', *args], cwd=cwd,
                            env=env, capture_output=True, text=True, encoding='utf-8',
                            errors='replace', timeout=90, creationflags=CHILD_FLAGS)
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[-1000:])
    return result.stdout.strip()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def install_models():
    checks = json.loads((SOURCE / 'models/checksums.json').read_text(encoding='utf-8'))
    for name in MODEL_FILES:
        target = SOURCE / 'models' / name
        expected = checks[name]['sha256']
        if target.exists() and digest(target) == expected:
            continue
        source = ROOT / 'models' / name
        if not source.exists() or digest(source) != expected:
            raise RuntimeError(f'Faltan pesos compatibles: {name}. Instala la release indicada por el README en la carpeta principal y vuelve a iniciar.')
        shutil.copy2(source, target)


def public_status():
    with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/api/status', timeout=3) as response:
        return json.load(response)


def stop_process(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def start_server():
    env = os.environ.copy()
    for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'HF_TOKEN', 'VERCEL_TOKEN'):
        env.pop(key, None)
    deps = ROOT.parent.parent / 'work/pydeps'
    if deps.exists():
        env['PYTHONPATH'] = str(deps)
    env['PALIMPSESTO_PUBLIC_PORT'] = str(PORT)
    env['PYTHONIOENCODING'] = 'utf-8'
    log = (STATE / 'server.log').open('a', encoding='utf-8')
    process = subprocess.Popen([sys.executable, '-u', str(SOURCE / 'run_public.py')],
                               cwd=SOURCE, env=env, stdout=log, stderr=subprocess.STDOUT,
                               creationflags=CHILD_FLAGS)
    log.close()
    for _ in range(90):
        if process.poll() is not None:
            raise RuntimeError('El servidor no arrancó. Revisa .public_runtime/server.log.')
        try:
            state = public_status()
            if all(state.get(k) for k in ('classifier', 'segmenter', 'scope_screen')) and state.get('local') is False:
                return process
        except (OSError, ValueError):
            pass
        time.sleep(1)
    stop_process(process)
    raise RuntimeError('El servidor no quedó listo en 90 segundos.')


def main():
    STATE.mkdir(exist_ok=True)
    # El bloqueo se libera también si se cierra el proceso inesperadamente.
    lockfile = (STATE / 'manager.lock').open('a+b')
    lockfile.seek(0)
    lockfile.write(b'0')
    lockfile.flush()
    lockfile.seek(0)
    if os.name == 'nt':
        import msvcrt
        try:
            msvcrt.locking(lockfile.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise RuntimeError('La demo ya está activa. Consulta .public_runtime/enlace.txt.')
    (STATE / 'stop.request').unlink(missing_ok=True)
    if not SOURCE.exists():
        git('clone', '--branch', 'main', REMOTE, str(SOURCE), cwd=ROOT)
    if git('status', '--porcelain'):
        raise RuntimeError('Hay cambios manuales en la copia de ejecución. Consérvalos antes de actualizar; no se sobrescribieron.')
    git('fetch', 'origin', '+refs/heads/main:refs/remotes/origin/main')
    git('checkout', '--detach', 'origin/main')
    install_models()
    executable = STATE / 'cloudflared.exe'
    if not executable.exists() or digest(executable) != CF_SHA:
        say('Descargando el conector gratuito oficial de Cloudflare…')
        temporary = STATE / 'cloudflared.download'
        urllib.request.urlretrieve(CF_URL, temporary)
        if digest(temporary) != CF_SHA:
            raise RuntimeError('La descarga del conector no coincide con su SHA-256. No se ejecutó.')
        temporary.replace(executable)
    server = tunnel = None
    try:
        server = start_server()
        with (STATE / 'tunnel.log').open('w', encoding='utf-8') as log:
            tunnel = subprocess.Popen([str(executable), 'tunnel', '--no-autoupdate',
                                       '--url', f'http://127.0.0.1:{PORT}', '--protocol', 'http2'],
                                      cwd=STATE, stdout=log, stderr=subprocess.STDOUT,
                                      creationflags=CHILD_FLAGS)
        url = ''
        head = git('rev-parse', 'HEAD')
        last_check = 0
        last_message = ''
        say('La demo se detiene con Detener_Enlace_Publico.cmd o Ctrl+C.')
        while not (STATE / 'stop.request').exists():
            if tunnel.poll() is not None:
                raise RuntimeError('El túnel terminó. Revisa .public_runtime/tunnel.log y vuelve a iniciar.')
            if server.poll() is not None:
                raise RuntimeError('El servidor terminó. Revisa .public_runtime/server.log y vuelve a iniciar.')
            if not url:
                match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', (STATE / 'tunnel.log').read_text(encoding='utf-8', errors='replace'))
                if match:
                    url = match.group()
                    (STATE / 'enlace.txt').write_text(url + '\n', encoding='utf-8')
                    say('ENLACE PÚBLICO: ' + url)
            now = time.monotonic()
            if now - last_check > 90:
                last_check = now
                try:
                    git('fetch', 'origin', '+refs/heads/main:refs/remotes/origin/main')
                    target = git('rev-parse', 'origin/main')
                    if target != head:
                        changes = git('diff', '--name-only', head, target).splitlines()
                        # Un cambio de autor/historia con los mismos archivos no reinicia.
                        runtime = [p for p in changes if p.startswith(('palimpsesto/', 'static/', 'templates/', 'models/', 'requirements')) or p == 'run_public.py']
                        if public_status().get('active_sessions', 0) and runtime:
                            message = 'Actualización pendiente: se aplicará cuando no haya sesiones activas.'
                        elif any(p.startswith('requirements') for p in runtime):
                            message = 'Cambiaron dependencias. Actualiza el entorno antes de reiniciar la demo.'
                        elif git('status', '--porcelain'):
                            message = 'Actualización detenida: la copia de ejecución tiene cambios manuales.'
                        else:
                            old = head
                            if runtime:
                                stop_process(server)
                            try:
                                git('checkout', '--detach', target)
                                install_models()
                                if runtime:
                                    server = start_server()
                                head = target
                                message = 'Actualizado desde main: ' + head[:8] + ('. La URL se conserva.' if runtime else '. Sin reiniciar la aplicación.')
                            except Exception:
                                git('checkout', '--detach', old)
                                install_models()
                                if runtime:
                                    server = start_server()
                                raise
                        if message != last_message:
                            say(message)
                            last_message = message
                except Exception as error:
                    message = 'No se actualizó; se conserva la versión anterior: ' + str(error)
                    if message != last_message:
                        say(message)
                        last_message = message
            (STATE / 'estado.json').write_text(json.dumps({'url': url, 'commit': head, 'updated_at': time.time(), 'manager_pid': os.getpid(), 'server_pid': server.pid, 'tunnel_pid': tunnel.pid}, indent=2), encoding='utf-8')
            time.sleep(2)
    except KeyboardInterrupt:
        say('Cerrando la demo…')
    finally:
        stop_process(tunnel)
        stop_process(server)
        (STATE / 'enlace.txt').write_text('Demo detenida. Ejecuta Iniciar_Enlace_Publico.cmd para obtener un enlace nuevo.\n', encoding='utf-8')
        (STATE / 'estado.json').unlink(missing_ok=True)
        lockfile.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        say('ERROR: ' + str(error))
        sys.exit(1)
