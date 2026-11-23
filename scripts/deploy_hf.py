"""Publica la aplicación en Hugging Face Spaces (plan gratuito, CPU).

Requisito único: haber iniciado sesión una vez con  .venv\\Scripts\\hf auth login  (token con permiso de escritura).
Uso:  python scripts/deploy_hf.py --space USUARIO/palimpsesto   [--dry-run]

Arma una carpeta con solo lo que la aplicación necesita para correr (sin datos, resultados ni pesos: los pesos
se descargan de la release v0.4.0 y se verifican por SHA-256 al construir la imagen) y la sube al Space.
"""
import argparse
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ['palimpsesto', 'static', 'templates', 'run_public.py', 'requirements.txt',
           'models/release.json', 'models/checksums.json', 'models/scope_head.npz', 'models/scope_reference.npz']
DEPLOY = ROOT / 'deploy' / 'huggingface'


def build(target: Path):
    for item in RUNTIME:
        src = ROOT / item
        if not src.exists():
            raise FileNotFoundError(f'Falta {item}')
        dst = target / item
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            shutil.copy2(src, dst)
    shutil.copy2(DEPLOY / 'Dockerfile', target / 'Dockerfile')
    shutil.copy2(DEPLOY / 'README.md', target / 'README.md')
    return sorted(p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--space', required=True, help='USUARIO/nombre del Space')
    ap.add_argument('--dry-run', action='store_true', help='solo arma la carpeta y lista los archivos')
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        files = build(Path(tmp))
        size = sum((Path(tmp) / f).stat().st_size for f in files) / 2 ** 20
        print(f'{len(files)} archivos, {size:.1f} MB')
        if args.dry_run:
            print('\n'.join(files))
            return
        from huggingface_hub import HfApi
        api = HfApi()
        api.create_repo(args.space, repo_type='space', space_sdk='docker', exist_ok=True, private=False)
        api.upload_folder(folder_path=tmp, repo_id=args.space, repo_type='space',
                          commit_message='Despliegue de Palimpsesto desde GitHub',
                          delete_patterns=['*'])
        user, name = args.space.split('/')
        print(f'Subido. Página: https://huggingface.co/spaces/{args.space}')
        print(f'Enlace directo: https://{user.lower()}-{name.lower().replace("_", "-")}.hf.space')


if __name__ == '__main__':
    main()
