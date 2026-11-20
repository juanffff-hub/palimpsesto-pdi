"""Comprueba los pesos y, si faltan o son de otra versión, los baja de la release.

  python scripts/fetch_models.py                 # models/ del proyecto
  python scripts/fetch_models.py DESTINO MANIFIESTO
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from palimpsesto.weights import main

if __name__ == '__main__':
    raise SystemExit(main())
